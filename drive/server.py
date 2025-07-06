import os
import ast
import time
import requests
import urllib.parse
import drive_service as drive

from dotenv import load_dotenv
from collections import defaultdict
from fastapi.templating import Jinja2Templates
from credential_handler import CredentialHandler
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# ==> Env variables
CREDENTIAL_FILE = os.getenv("CREDENTIAL_FILE")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE").split(",")
SESSION_DURATION = int(os.getenv("SESSION_DURATION", 300))

# For dev
flow_sessions = {}

# ==> Handler
credential_handler = CredentialHandler(
    client_secrets_file=CREDENTIAL_FILE,
    redirect_uri=REDIRECT_URI,
    scopes=SCOPE,  # Use a list for scopes
    session_duration=SESSION_DURATION,
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
    auth_url, state, flow = credential_handler.get_auth_url()
    flow_sessions[state] = flow  # Store flow for callback
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
def auth_callback(request: Request):
    auth_response = str(request.url)
    parsed_url = urllib.parse.urlparse(auth_response)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    state = query_params.get("state", [None])[0]
    flow = flow_sessions.pop(state)

    credentials = credential_handler.fetch_token(
        authorization_response=auth_response, flow=flow
    )
    token_data = ast.literal_eval(credentials.to_json())
    token_data["timestamp"] = time.time()
    session_token = credential_handler.create_session_token(token_data)

    response = RedirectResponse("/")
    response.set_cookie(
        "session_token",
        session_token,
        max_age=SESSION_DURATION,
        httponly=True,
    )
    return response


# ==> Functionalities
@app.get("/drive/files")
def list_files(request: Request):
    creds = credential_handler.get_credentials(request)
    service = drive.get_drive_service(creds)
    results = service.files().list().execute()
    items = results.get("files", [])
    return items


@app.get("/drive/tree")
def list_files(request: Request):
    creds = credential_handler.get_credentials(request)
    service = drive.get_drive_service(creds)

    contexta_drive_id = drive.get_contexta_drive_id(service)
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
