"""linkedin_poster.py

Lightweight wrapper around LinkedIn v2 REST API for:
1. Registering & uploading media (images / documents).
2. Publishing a UGC post with optional attachments.

This module purposefully avoids the *linkedin_api* library (which relies on
scraping) and instead uses LinkedIn's official endpoints that work with any
access token granted ``w_member_social`` scope.

Environment variables (see ``config.py``):
• LINKEDIN_ACCESS_TOKEN – OAuth token (member or organisation)
• LINKEDIN_OWNER_URN    – "urn:li:person:…" or "urn:li:organization:…"

Usage
-----
>>> body, pptx_path, img_path = generator.build_assets(raw_articles, summaries)
>>> from linkedin_poster import post
>>> post(body, slide_path=pptx_path, image_path=img_path)
"""
from __future__ import annotations

import json
import logging
import mimetypes
import os
import pathlib
import typing as _t
from datetime import datetime, timezone

import requests

import config

logger = logging.getLogger("linkedin_poster")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

API_BASE = "https://api.linkedin.com/v2"
RESTLI_HEADER = {"X-RestLi-Protocol-Version": "2.0.0"}

_TOKEN = config.LINKEDIN_ACCESS_TOKEN
_OWNER = config.LINKEDIN_OWNER_URN

if not _TOKEN or not _OWNER:
    logger.warning("LinkedIn credentials missing – linkedin_poster will run in DRY RUN mode.")

_HEADERS_AUTH = {"Authorization": f"Bearer {_TOKEN}"} if _TOKEN else {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _abs_path(path: str | pathlib.Path) -> pathlib.Path:
    return pathlib.Path(path).expanduser().resolve()


def _register_upload(recipe: str, owner: str) -> tuple[str, str]:
    """Return (asset_urn, upload_url) after calling registerUpload."""
    url = f"{API_BASE}/assets?action=registerUpload"

    payload = {
        "registerUploadRequest": {
            "recipes": [recipe],
            "owner": owner,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
            "supportedUploadMechanism": ["SYNCHRONOUS_UPLOAD"],
        }
    }

    res = requests.post(url, headers={**_HEADERS_AUTH, **RESTLI_HEADER, "Content-Type": "application/json"}, json=payload)
    if res.status_code != 200:
        raise RuntimeError(f"registerUpload failed: {res.status_code} {res.text[:200]}")

    data = res.json()
    asset = data["value"]["asset"]
    upload_mech = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
    upload_url = upload_mech["uploadUrl"]
    return asset, upload_url


def _upload_file(path: str | pathlib.Path, recipe: str) -> str:
    """Register & upload *path*, return asset URN."""
    if not _TOKEN or not _OWNER:
        logger.info("[DRY-RUN] Would upload %s via recipe %s", path, recipe)
        return f"urn:li:digitalmediaAsset:dummy_{pathlib.Path(path).stem}"

    asset, upload_url = _register_upload(recipe, owner=_OWNER)

    fp = _abs_path(path)
    mime, _ = mimetypes.guess_type(fp.name)
    mime = mime or "application/octet-stream"
    content = fp.read_bytes()

    logger.info("Uploading %s (%d bytes) to LinkedIn…", fp.name, len(content))
    res = requests.put(upload_url, data=content, headers={"Authorization": f"Bearer {_TOKEN}", "Content-Type": mime})
    if not (200 <= res.status_code < 300):
        raise RuntimeError(f"Upload failed: {res.status_code} {res.text[:200]}")

    return asset


# ---------------------------------------------------------------------------
# Public facade
# ---------------------------------------------------------------------------

def post(  # noqa: D401
    body_text: str,
    *,
    slide_path: str | pathlib.Path | None = None,
    image_path: str | pathlib.Path | None = None,
    visibility: str = "PUBLIC",
) -> None:
    """Publish a LinkedIn post with optional slide deck and image.

    Parameters
    ----------
    body_text : str
        Main textual commentary for the post.
    slide_path : str | Path | None
        Path to a PPTX or PDF to attach as a document.
    image_path : str | Path | None
        Path to an image (PNG/JPG) to attach.
    visibility : str
        One of "PUBLIC", "CONNECTIONS".
    """
    if not _OWNER or not _TOKEN:
        logger.info("[DRY-RUN] Posting to LinkedIn skipped. Body:\n%s", body_text)
        return

    # Upload media first.
    media_entries: list[dict[str, _t.Any]] = []

    if slide_path:
        asset = _upload_file(slide_path, "urn:li:digitalmediaRecipe:feedshare-document")
        media_entries.append(
            {
                "status": "READY",
                "description": {"text": "Slide deck"},
                "media": asset,
                "title": {"text": pathlib.Path(slide_path).name},
            }
        )

    if image_path:
        asset = _upload_file(image_path, "urn:li:digitalmediaRecipe:feedshare-image")
        media_entries.append(
            {
                "status": "READY",
                "description": {"text": "Graph"},
                "media": asset,
                "title": {"text": pathlib.Path(image_path).name},
            }
        )

    if media_entries:
        if len(media_entries) > 1:
            category = "CAROUSEL"
        else:
            category = "DOCUMENT" if slide_path and not image_path else "IMAGE"
    else:
        category = "NONE"

    post_data = {
        "author": _OWNER,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": body_text},
                "shareMediaCategory": category,
                "media": media_entries,
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
    }

    url = f"{API_BASE}/ugcPosts"
    res = requests.post(url, headers={**_HEADERS_AUTH, **RESTLI_HEADER, "Content-Type": "application/json"}, json=post_data)
    if res.status_code not in {201, 202}:
        raise RuntimeError(f"UGC post failed: {res.status_code} {res.text[:300]}")

    logger.info("Successfully posted to LinkedIn: %s", res.headers.get("x-restli-id"))


if __name__ == "__main__":
    # Minimal dry-run sanity check.
    os.environ.setdefault("DRY_RUN", "1")
    post("Hello world – test post via API.")