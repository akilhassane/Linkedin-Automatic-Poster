import logging
import mimetypes
from pathlib import Path
from typing import Optional

import requests

LINKEDIN_API = "https://api.linkedin.com/v2"


def _headers(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }


def _register_image_upload(access_token: str, member_urn: str) -> tuple[str, str]:
    """Return (upload_url, asset)"""
    url = f"{LINKEDIN_API}/assets?action=registerUpload"
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": member_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
    logging.debug("Registering image upload")
    res = requests.post(url, json=payload, headers=_headers(access_token))
    res.raise_for_status()
    data = res.json()
    upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset = data["value"]["asset"]
    return upload_url, asset


def _upload_image(upload_url: str, image_path: Path):
    with image_path.open("rb") as fh:
        headers = {
            "Content-Type": mimetypes.guess_type(image_path)[0] or "image/png"
        }
        logging.debug("Uploading image binary %s", image_path)
        res = requests.put(upload_url, data=fh, headers=headers)
        res.raise_for_status()


def post_to_linkedin(access_token: str, member_urn: str, text: str, image_path: Optional[Path] = None):
    asset = None
    if image_path and image_path.exists():
        upload_url, asset = _register_image_upload(access_token, member_urn)
        _upload_image(upload_url, image_path)

    post_url = f"{LINKEDIN_API}/ugcPosts"
    payload = {
        "author": member_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE" if asset else "NONE",
                "media": [
                    {
                        "status": "READY",
                        "description": {"text": "Daily digest graph"},
                        "media": asset,
                        "title": {"text": "Daily digest"}
                    }
                ] if asset else []
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    logging.info("Posting update to LinkedIn (%s chars)...", len(text))
    res = requests.post(post_url, json=payload, headers=_headers(access_token))
    if res.status_code >= 400:
        logging.error("LinkedIn post failed: %s", res.text)
        res.raise_for_status()
    logging.info("Post successful - URN: %s", res.headers.get("x-restli-id"))