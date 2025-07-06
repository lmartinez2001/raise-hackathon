from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# ==> Helper function to create Drive service
def create_drive_service(credentials_data):
    """Create a Google Drive service object from credentials data."""
    credentials = Credentials(
        token=credentials_data["token"],
        refresh_token=credentials_data.get("refresh_token"),
        token_uri=credentials_data.get("token_uri"),
        client_id=credentials_data.get("client_id"),
        client_secret=credentials_data.get("client_secret"),
        scopes=credentials_data.get("scopes", []),
    )

    service = build("drive", "v3", credentials=credentials)
    return service


# def search_file(file_name):
#     token_data = credential_handler.load_session_token(request)
#     if not token_data:
#         return JSONResponse({"error": "Not authenticated"}, status_code=401)
#     service = create_drive_service(token_data)
