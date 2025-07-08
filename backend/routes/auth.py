"""
Authentication routes for OAuth2 flow with Google.
Handles login, callback, and logout functionality.
"""

import ast
import time
import requests
import urllib.parse
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from dependencies import get_credential_handler, get_settings, get_credentials_optional
from drive.credential_handler import CredentialHandler
from settings import Settings

# Initialize router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Authentication required"},
        400: {"description": "Bad request"},
    },
)

# Templates (will be moved to a shared dependency later if needed)
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def login(
    credential_handler: CredentialHandler = Depends(get_credential_handler),
    settings: Settings = Depends(get_settings),
):
    """
    Initiate OAuth2 login flow.
    Redirects user to Google OAuth2 authorization URL.
    """
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


@router.get("/callback")
def auth_callback(
    request: Request,
    credential_handler: CredentialHandler = Depends(get_credential_handler),
    settings: Settings = Depends(get_settings),
):
    """
    Handle OAuth2 callback from Google.
    Exchanges authorization code for access token and creates session.
    """
    auth_response = str(request.url)

    # Handle HTTPS in production
    if settings.environment.lower() not in (
        "dev",
        "development",
    ) and auth_response.startswith("http://"):
        auth_response = auth_response.replace("http://", "https://", 1)

    flow_state = request.cookies.get("flow_state")
    if not flow_state:
        return JSONResponse({"error": "Invalid flow state"}, status_code=400)

    # Validate state parameter
    parsed_url = urllib.parse.urlparse(auth_response)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    state = query_params.get("state", [None])[0]

    # Exchange authorization code for credentials
    credentials = credential_handler.fetch_token(
        authorization_response=auth_response, flow_state=flow_state
    )
    if not credentials:
        return JSONResponse({"error": "Authentication failed"}, status_code=400)

    # Create session token
    token_data = ast.literal_eval(credentials.to_json())
    token_data["timestamp"] = time.time()
    session_token = credential_handler.create_session_token(token_data)

    # Set session cookie and redirect to frontend dashboard
    response = RedirectResponse(f"{settings.frontend_url}/dashboard")
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


@router.get("/logout")
def logout(
    request: Request,
    credential_handler: CredentialHandler = Depends(get_credential_handler),
    settings: Settings = Depends(get_settings),
):
    """
    Log out user by revoking token and clearing session.
    """
    creds = credential_handler.get_credentials(request)
    response = RedirectResponse(url=settings.frontend_url)
    response.delete_cookie("session_token")

    # Revoke token at Google if valid
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


@router.get("/status")
def auth_status(
    request: Request,
    credential_handler: CredentialHandler = Depends(get_credential_handler),
):
    """
    Check authentication status of current user.
    Returns user info if authenticated, null otherwise.
    """
    creds = credential_handler.get_credentials(request)

    if creds is None:
        return {"authenticated": False, "user": None}

    try:
        user_info = credential_handler.fetch_user_info(creds)
        return {
            "authenticated": True,
            "user": {
                "given_name": user_info.get("given_name", ""),
                "email": user_info.get("email", ""),
                "picture": user_info.get("picture", ""),
            },
        }
    except Exception as e:
        return {"authenticated": False, "user": None, "error": str(e)}
