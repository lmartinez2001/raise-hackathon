"""
Main application routes.
Handles the home page and general application endpoints.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dependencies import get_credential_handler, get_credentials_optional
from drive.credential_handler import CredentialHandler

# Initialize router
router = APIRouter(
    tags=["main"],
    responses={
        200: {"description": "Success"},
    },
)

# Templates
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    credential_handler: CredentialHandler = Depends(get_credential_handler),
    creds=Depends(get_credentials_optional),
):
    """
    Serve the main application page.

    Shows authentication status and user information if logged in.
    """
    is_connected = creds is not None

    if creds is not None:
        try:
            user_info = credential_handler.fetch_user_info(creds)
        except Exception as e:
            print(f"Error fetching user info: {e}")
            user_info = {}
    else:
        user_info = {}

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_connected": is_connected,
            "given_name": user_info.get("given_name", ""),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", ""),
        },
    )


@router.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {"status": "healthy", "service": "contexta-backend"}


@router.get("/api/user")
def get_user_info(
    credential_handler: CredentialHandler = Depends(get_credential_handler),
    creds=Depends(get_credentials_optional),
):
    """
    Get user information in JSON format.

    Returns basic user info if authenticated, otherwise returns empty data.
    """
    if creds is None:
        return {"is_connected": False}

    try:
        user_info = credential_handler.fetch_user_info(creds)
        return {
            "is_connected": True,
            "given_name": user_info.get("given_name", ""),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", ""),
        }
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return {"is_connected": False}
