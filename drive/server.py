import os
import ast
import time
import requests
import urllib.parse

from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from credential_handler import CredentialHandler
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

CREDENTIAL_FILE = os.getenv("CREDENTIAL_FILE")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE").split(",")
print(SCOPE)
SESSION_DURATION = int(os.getenv("SESSION_DURATION", 300))


flow_sessions = {}

# create handler
credential_handler = CredentialHandler(
    client_secrets_file=CREDENTIAL_FILE,
    redirect_uri=REDIRECT_URI,
    scopes=SCOPE,  # Use a list for scopes
    session_duration=SESSION_DURATION,
)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    token_data = credential_handler.load_session_token(request)
    is_connected = token_data is not None

    return templates.TemplateResponse(
        "index.html", {"request": request, "is_connected": is_connected}
    )


@app.get("/auth/login")
def login():
    auth_url, state, flow = credential_handler.get_authorization_url()
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

    response = RedirectResponse("/")
    session_token = credential_handler.create_session_token(token_data)
    response.set_cookie(
        "session_token",
        session_token,
        max_age=SESSION_DURATION,
        httponly=True,
    )
    return response


@app.get("/drive/folders")
def list_folders(request: Request):
    token_data = credential_handler.load_session_token(request)
    if not token_data:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    access_token = token_data["token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    query = "mimeType='application/vnd.google-apps.folder'"
    params = {
        "q": query,
        "fields": "files(id, name, driveId, parents)",
        "pageSize": 100,
        "includeItemsFromAllDrives": "true",
        "supportsAllDrives": "true",
    }
    res = requests.get(
        "https://www.googleapis.com/drive/v3/files", headers=headers, params=params
    )
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail=res.json())
    return res.json()
