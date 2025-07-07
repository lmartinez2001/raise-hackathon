from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# ==> Helper function to create Drive service
def get_drive_service(credentials: Credentials):
    service = build("drive", "v3", credentials=credentials)
    return service


def get_contexta_drive_id(service, drive_name):
    results = service.drives().list().execute()
    drives = results.get("drives", [])
    if not drives:
        raise Exception("No shared drives found.")
    for shared_drive in drives:
        if shared_drive["name"] == drive_name:
            return shared_drive["id"]
    return None


def get_file_structure(service, root_id):
    files = []
    page_token = None

    while True:
        response = (
            service.files()
            .list(
                q=f"'{root_id}' in parents",
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, parents)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return files


def get_videos(service, drive_id):
    videos = []
    page_token = None

    while True:
        response = (
            service.files()
            .list(
                q="mimeType contains 'video/'",
                corpora="drive",
                driveId=drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="nextPageToken, files(id, name, mimeType, webViewLink)",
                pageToken=page_token,
            )
            .execute()
        )

        videos.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return videos
