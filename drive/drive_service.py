from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# ==> Helper function to create Drive service
def get_drive_service(credentials: Credentials):
    service = build("drive", "v3", credentials=credentials)
    return service


def get_contexta_drive_id(service):
    results = service.drives().list().execute()
    drives = results.get("drives", [])
    if not drives:
        raise Exception("No shared drives found.")
    for shared_drive in drives:
        if shared_drive["name"] == "Contexta":
            return shared_drive["id"]
    return None


def get_file_structure(service, root_id):
    pass


def get_videos(service, drive_id):
    pass


# def search_file(file_name):
#     token_data = credential_handler.load_session_token(request)
#     if not token_data:
#         return JSONResponse({"error": "Not authenticated"}, status_code=401)
#     service = create_drive_service(token_data)
