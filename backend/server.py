import os
import ast
import time
import requests
import urllib.parse
import mimetypes
import drive.service as drive
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload

from settings import Settings
from collections import defaultdict
from fastapi.templating import Jinja2Templates
from drive.credential_handler import CredentialHandler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

settings = Settings()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")

if settings.environment.lower() in ("dev", "development"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# ==> Handler
credential_handler = CredentialHandler(
    client_secrets_file=settings.credential_file,
    redirect_uri=settings.redirect_uri,
    scopes=settings.scope.split(","),
    session_duration=settings.session_duration,
    secret_key=settings.secret_key,
)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    creds = credential_handler.get_credentials(request)
    is_connected = creds is not None

    if creds is not None:
        user_info = credential_handler.fetch_user_info(creds)
    else:
        user_info = {}

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_connected": is_connected,
            "given_name": user_info.get("given_name", ""),
        },
    )


@app.get("/auth/login")
def login():
    auth_url, state, flow_state = credential_handler.get_auth_url()
    response = RedirectResponse(url=auth_url)

    response.set_cookie(
        "flow_state",
        flow_state,
        max_age=300,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


@app.get("/auth/callback")
def auth_callback(request: Request):
    auth_response = str(request.url)
    if settings.environment.lower() not in (
        "dev",
        "development",
    ) and auth_response.startswith("http://"):
        auth_response = auth_response.replace("http://", "https://", 1)

    flow_state = request.cookies.get("flow_state")
    if not flow_state:
        return JSONResponse({"error": "Invalid flow state"}, status_code=400)

    parsed_url = urllib.parse.urlparse(auth_response)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    state = query_params.get("state", [None])[0]

    credentials = credential_handler.fetch_token(
        authorization_response=auth_response, flow_state=flow_state
    )
    if not credentials:
        return JSONResponse({"error": "Authentication failed"}, status_code=400)

    token_data = ast.literal_eval(credentials.to_json())
    token_data["timestamp"] = time.time()
    session_token = credential_handler.create_session_token(token_data)

    response = RedirectResponse("/")
    response.delete_cookie("flow_state")
    response.set_cookie(
        "session_token",
        session_token,
        max_age=settings.session_duration,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


@app.get("/auth/logout")
def logout(request: Request):
    creds = credential_handler.get_credentials(request)
    response = RedirectResponse(url="/")
    response.delete_cookie("session_token")

    if creds and creds.valid:
        try:
            requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": creds.token},
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
        except Exception as e:
            # Continue with logout even if revocation fails
            print(f"Error revoking token: {e}")

    return response


# ==> Functionalities
@app.get("/drive/files")
def list_files(request: Request):
    creds = credential_handler.validate_credentials_or_redirect(request)
    if isinstance(creds, JSONResponse):
        return creds

    service = drive.get_drive_service(creds)
    try:
        contexta_drive_id = drive.get_contexta_drive_id(
            service, settings.target_drive_name
        )
        if contexta_drive_id is None:
            raise HTTPException(status_code=404, detail="Contexta drive not found")

        results = (
            service.files()
            .list(
                corpora="drive",
                driveId=contexta_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="files(id, name, mimeType)",
            )
            .execute()
        )

        return results.get("files", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files: {str(e)}")


@app.get("/drive/tree")
def list_files(request: Request):
    creds = credential_handler.validate_credentials_or_redirect(request)
    if isinstance(creds, JSONResponse):
        return creds

    service = drive.get_drive_service(creds)

    contexta_drive_id = drive.get_contexta_drive_id(service, settings.target_drive_name)
    if contexta_drive_id is None:
        raise HTTPException(status_code=404, detail="Contexta drive not found")

    results = (
        service.files()
        .list(
            corpora="drive",
            driveId=contexta_drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="nextPageToken, files(id, name, mimeType, parents, createdTime, webViewLink, webContentLink, iconLink)",
        )
        .execute()
    )

    all_files = results.get("files", [])

    id_to_name = {}
    children = defaultdict(list)
    for item in all_files:
        id_to_name[item["id"]] = item["name"]
        children[item["parents"][0]].append(item["id"])

    def build_tree(root_id):
        return {id_to_name[child]: build_tree(child) for child in children[root_id]}

    tree = {contexta_drive_id: build_tree(contexta_drive_id)}
    return tree


@app.get("/drive/download/{file_id}")
def download_file(file_id: str, request: Request):
    creds = credential_handler.validate_credentials_or_redirect(request)
    if isinstance(creds, JSONResponse):
        return creds

    service = drive.get_drive_service(creds)

    file_metadata = (
        service.files().get(fileId=file_id, supportsAllDrives=True).execute()
    )
    file_name = file_metadata["name"]

    request_obj = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request_obj)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")

    fh.seek(0)

    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", file_name)

    with open(file_path, "wb") as f:
        f.write(fh.read())
        f.close()

    return {"message": "File downloaded successfully", "file_path": file_path}


@app.get("/drive/download-videos")
def download_videos(request: Request):
    creds = credential_handler.validate_credentials_or_redirect(request)
    if isinstance(creds, JSONResponse):
        return creds

    service = drive.get_drive_service(creds)

    try:
        contexta_drive_id = drive.get_contexta_drive_id(
            service, settings.target_drive_name
        )
        if contexta_drive_id is None:
            raise HTTPException(status_code=404, detail="Contexta drive not found")

        results = (
            service.files()
            .list(
                corpora="drive",
                driveId=contexta_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="files(id, name, mimeType)",
            )
            .execute()
        )

        files = results.get("files", [])
        video_files = [f for f in files if f.get("mimeType", "").startswith("video/")]

        downloaded_videos = []
        os.makedirs("data/videos", exist_ok=True)

        for video in video_files:
            file_id = video["id"]
            file_name = video["name"]
            mime_type = video["mimeType"]

            extension = mimetypes.guess_extension(mime_type)
            if not extension:
                extension = ".mp4"

            if not file_name.endswith(extension):
                file_name = os.path.splitext(file_name)[0] + extension

            request_obj = service.files().get_media(
                fileId=file_id, supportsAllDrives=True
            )
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request_obj)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Downloading {file_name}: {int(status.progress() * 100)}%.")

            fh.seek(0)
            file_path = os.path.join("data/videos", file_name)

            with open(file_path, "wb") as f:
                f.write(fh.read())

            downloaded_videos.append(
                {
                    "id": file_id,
                    "name": file_name,
                    "path": file_path,
                    "mime_type": mime_type,
                }
            )

        return {
            "message": f"Downloaded {len(downloaded_videos)} videos",
            "videos": downloaded_videos,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error downloading videos: {str(e)}"
        )
