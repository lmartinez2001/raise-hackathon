"""
Main application routes.
Handles the home page and general application endpoints.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
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


@router.get("/user")
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


import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


@router.get("/wikis")
def get_wikis(q: str = ""):
    """
    Get wikis from markdown files in docs directory.
    """
    docs_dir = Path(__file__).parent.parent / "docs"
    wikis = []

    if not docs_dir.exists():
        return []

    for md_file in docs_dir.glob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            title = md_file.stem.replace("-", " ").replace("_", " ").title()

            lines = content.split("\n")
            first_heading = next(
                (line.lstrip("# ").strip() for line in lines if line.startswith("#")),
                title,
            )

            summary_lines = [
                line.strip()
                for line in lines
                if line.strip()
                and not line.startswith("#")
                and not line.startswith("```")
            ][:3]
            summary = " ".join(summary_lines)[:200] + (
                "..." if len(" ".join(summary_lines)) > 200 else ""
            )

            wiki = {
                "id": md_file.stem,
                "title": first_heading,
                "summary": summary or f"Documentation for {title}",
                "sources": {"meetings": 0, "docs": 1, "slack": 0},
                "lastUpdated": datetime.fromtimestamp(md_file.stat().st_mtime).strftime(
                    "%Y-%m-%d"
                ),
                "tags": [tag.strip() for tag in md_file.stem.split("-")],
                "href": f"/wikis/{md_file.stem}",
                "content": content,
            }

            if q.lower():
                if (
                    q.lower() in title.lower()
                    or q.lower() in summary.lower()
                    or q.lower() in content.lower()
                    or any(q.lower() in tag.lower() for tag in wiki["tags"])
                ):
                    wikis.append(wiki)
            else:
                wikis.append(wiki)

        except Exception as e:
            print(f"Error processing {md_file}: {e}")
            continue

    return wikis


@router.get("/wikis/{wiki_id}")
def get_wiki(wiki_id: str):
    """
    Get a specific wiki by ID.
    """
    docs_dir = Path(__file__).parent.parent / "docs"
    md_file = docs_dir / f"{wiki_id}.md"

    if not md_file.exists():
        raise HTTPException(status_code=404, detail="Wiki not found")

    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        title = md_file.stem.replace("-", " ").replace("_", " ").title()
        lines = content.split("\n")
        first_heading = next(
            (line.lstrip("# ").strip() for line in lines if line.startswith("#")), title
        )

        summary_lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.startswith("#") and not line.startswith("```")
        ][:3]
        summary = " ".join(summary_lines)[:200] + (
            "..." if len(" ".join(summary_lines)) > 200 else ""
        )

        return {
            "id": wiki_id,
            "title": first_heading,
            "summary": summary or f"Documentation for {title}",
            "sources": {"meetings": 0, "docs": 1, "slack": 0},
            "lastUpdated": datetime.fromtimestamp(md_file.stat().st_mtime).strftime(
                "%Y-%m-%d"
            ),
            "tags": [tag.strip() for tag in md_file.stem.split("-")],
            "href": f"/wikis/{wiki_id}",
            "content": content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading wiki: {e}")
