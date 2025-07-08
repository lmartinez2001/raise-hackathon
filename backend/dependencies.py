"""
Dependency injection module for FastAPI application.
Provides singleton instances and request-scoped dependencies.
"""

from functools import lru_cache
from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from google.oauth2.credentials import Credentials

from settings import Settings
from drive.credential_handler import CredentialHandler
import drive.service as drive


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache to ensure singleton behavior.
    """
    return Settings()


@lru_cache()
def get_credential_handler() -> CredentialHandler:
    """
    Get cached credential handler instance.
    Using lru_cache to ensure singleton behavior.
    """
    settings = get_settings()
    return CredentialHandler(
        client_secrets_file=settings.credential_file,
        redirect_uri=settings.redirect_uri,
        scopes=settings.scope.split(","),
        session_duration=settings.session_duration,
        secret_key=settings.secret_key,
    )


def get_credentials(
    request: Request,
    credential_handler: CredentialHandler = Depends(get_credential_handler),
) -> Credentials:
    """
    Extract and validate credentials from request.
    Returns credentials if valid, raises HTTPException otherwise.
    """
    result = credential_handler.validate_credentials_or_redirect(request)
    if isinstance(result, JSONResponse):
        raise HTTPException(status_code=401, detail="Authentication required")
    return result


def get_credentials_optional(
    request: Request,
    credential_handler: CredentialHandler = Depends(get_credential_handler),
) -> Credentials | None:
    """
    Extract credentials from request without validation.
    Returns credentials if available, None otherwise.
    """
    return credential_handler.get_credentials(request)


def get_drive_service(credentials: Credentials = Depends(get_credentials)):
    """
    Get Google Drive service instance with validated credentials.
    """
    return drive.get_drive_service(credentials)


def get_contexta_drive_id(
    drive_service=Depends(get_drive_service), settings: Settings = Depends(get_settings)
) -> str:
    """
    Get the Contexta drive ID, raising HTTPException if not found.
    """
    contexta_drive_id = drive.get_contexta_drive_id(
        drive_service, settings.target_drive_name
    )
    if contexta_drive_id is None:
        raise HTTPException(status_code=404, detail="Contexta drive not found")
    return contexta_drive_id
