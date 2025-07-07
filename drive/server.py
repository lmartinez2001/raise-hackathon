import os
import ast
import time
import requests
import urllib.parse
import drive_service as drive

from settings import Settings

# from dotenv import load_dotenv
from collections import defaultdict
from fastapi.templating import Jinja2Templates
from credential_handler import CredentialHandler
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

# load_dotenv()
settings = Settings()
app = FastAPI()
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
    creds = credential_handler.get_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Unauthorized")

    service = drive.get_drive_service(creds)
    try:
        results = service.files().list().execute()
        items = results.get("files", [])
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files: {str(e)}")


@app.get("/drive/tree")
def list_files(request: Request):
    creds = credential_handler.get_credentials(request)
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
