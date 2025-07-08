"""
Google Drive integration routes.
Handles file listing, downloading, and drive management.
"""

import os
import mimetypes
from io import BytesIO
from collections import defaultdict
from typing import List, Dict, Any
from googleapiclient.http import MediaIoBaseDownload
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from dependencies import get_drive_service, get_contexta_drive_id, get_settings
from settings import Settings

# Initialize router
router = APIRouter(
    prefix="/drive",
    tags=["google-drive"],
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Drive or file not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get("/files")
def list_files(
    drive_service=Depends(get_drive_service),
    contexta_drive_id: str = Depends(get_contexta_drive_id),
) -> List[Dict[str, Any]]:
    """
    List all files in the Contexta drive.

    Returns:
        List of files with id, name, and mimeType
    """
    try:
        results = (
            drive_service.files()
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


@router.get("/tree")
def get_drive_tree(
    drive_service=Depends(get_drive_service),
    contexta_drive_id: str = Depends(get_contexta_drive_id),
) -> Dict[str, Any]:
    """
    Get the hierarchical tree structure of the Contexta drive.

    Returns:
        Nested dictionary representing the drive structure
    """
    try:
        results = (
            drive_service.files()
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

        # Build tree structure
        id_to_name = {}
        children = defaultdict(list)

        for item in all_files:
            id_to_name[item["id"]] = item["name"]
            if item.get("parents"):
                children[item["parents"][0]].append(item["id"])

        def build_tree(root_id: str) -> Dict[str, Any]:
            return {id_to_name[child]: build_tree(child) for child in children[root_id]}

        tree = {contexta_drive_id: build_tree(contexta_drive_id)}
        return tree

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error building drive tree: {str(e)}"
        )


@router.get("/download/{file_id}")
def download_file(
    file_id: str, drive_service=Depends(get_drive_service)
) -> Dict[str, str]:
    """
    Download a specific file from Google Drive to local storage.

    Args:
        file_id: The Google Drive file ID

    Returns:
        Success message and local file path
    """
    try:
        # Get file metadata
        file_metadata = (
            drive_service.files().get(fileId=file_id, supportsAllDrives=True).execute()
        )
        file_name = file_metadata["name"]

        # Download file content
        request_obj = drive_service.files().get_media(
            fileId=file_id, supportsAllDrives=True
        )
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request_obj)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

        fh.seek(0)

        # Save to local file system
        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", file_name)

        with open(file_path, "wb") as f:
            f.write(fh.read())

        return {
            "message": "File downloaded successfully",
            "file_path": file_path,
            "file_name": file_name,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@router.get("/download-videos")
def download_videos(
    drive_service=Depends(get_drive_service),
    contexta_drive_id: str = Depends(get_contexta_drive_id),
) -> Dict[str, Any]:
    """
    Download all video files from the Contexta drive.

    Returns:
        Summary of downloaded videos with their details
    """
    try:
        # Get all files
        results = (
            drive_service.files()
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

            # Ensure proper file extension
            extension = mimetypes.guess_extension(mime_type)
            if not extension:
                extension = ".mp4"

            if not file_name.endswith(extension):
                file_name = os.path.splitext(file_name)[0] + extension

            # Download video
            request_obj = drive_service.files().get_media(
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
            "total_count": len(downloaded_videos),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error downloading videos: {str(e)}"
        )


@router.get("/videos")
def list_videos(
    drive_service=Depends(get_drive_service),
    contexta_drive_id: str = Depends(get_contexta_drive_id),
) -> List[Dict[str, Any]]:
    """
    List all video files in the Contexta drive without downloading.

    Returns:
        List of video files with metadata
    """
    try:
        results = (
            drive_service.files()
            .list(
                corpora="drive",
                driveId=contexta_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)",
            )
            .execute()
        )

        files = results.get("files", [])
        video_files = [f for f in files if f.get("mimeType", "").startswith("video/")]

        return video_files

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing videos: {str(e)}")
