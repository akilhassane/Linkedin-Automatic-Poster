import logging
import asyncio
import json
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from urllib.parse import urlencode
import time
from config.settings import settings

@dataclass
class LinkedInPost:
    """Structure for LinkedIn post data"""
    content: str
    title: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    visibility: str = "PUBLIC"
    content_type: str = "text"

@dataclass
class LinkedInResponse:
    """Structure for LinkedIn API responses"""
    success: bool
    post_id: Optional[str] = None
    message: str = ""
    error_code: Optional[str] = None

class LinkedInAPI:
    """LinkedIn API client for posting content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.httpx_client = httpx.AsyncClient(timeout=30.0)
        self.access_token = settings.linkedin.access_token
        self.api_base_url = "https://api.linkedin.com/v2"
        self.person_id = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.httpx_client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for LinkedIn API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        try:
            response = await self.httpx_client.get(
                f"{self.api_base_url}/people/~",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                self.person_id = profile_data.get("id")
                return profile_data
            else:
                self.logger.error(f"Failed to get profile: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting profile: {e}")
            return {}
    
    async def create_text_post(self, content: str, visibility: str = "PUBLIC") -> LinkedInResponse:
        """Create a text-only post"""
        try:
            if not self.person_id:
                await self.get_profile()
            
            post_data = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.api_base_url}/ugcPosts",
                headers=self._get_headers(),
                json=post_data
            )
            
            if response.status_code == 201:
                result = response.json()
                post_id = result.get("id")
                return LinkedInResponse(
                    success=True,
                    post_id=post_id,
                    message="Post created successfully"
                )
            else:
                error_msg = f"Failed to create post: {response.status_code}"
                self.logger.error(error_msg)
                return LinkedInResponse(
                    success=False,
                    message=error_msg,
                    error_code=str(response.status_code)
                )
                
        except Exception as e:
            error_msg = f"Error creating text post: {e}"
            self.logger.error(error_msg)
            return LinkedInResponse(
                success=False,
                message=error_msg
            )
    
    async def create_article_post(self, title: str, content: str, visibility: str = "PUBLIC") -> LinkedInResponse:
        """Create an article post"""
        try:
            if not self.person_id:
                await self.get_profile()
            
            # LinkedIn articles are created using the publishing API
            article_data = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": f"{title}\n\n{content}"
                        },
                        "shareMediaCategory": "ARTICLE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.api_base_url}/ugcPosts",
                headers=self._get_headers(),
                json=article_data
            )
            
            if response.status_code == 201:
                result = response.json()
                post_id = result.get("id")
                return LinkedInResponse(
                    success=True,
                    post_id=post_id,
                    message="Article posted successfully"
                )
            else:
                error_msg = f"Failed to create article: {response.status_code}"
                self.logger.error(error_msg)
                return LinkedInResponse(
                    success=False,
                    message=error_msg,
                    error_code=str(response.status_code)
                )
                
        except Exception as e:
            error_msg = f"Error creating article post: {e}"
            self.logger.error(error_msg)
            return LinkedInResponse(
                success=False,
                message=error_msg
            )
    
    async def upload_image(self, image_data: bytes, image_name: str) -> Optional[str]:
        """Upload image to LinkedIn"""
        try:
            if not self.person_id:
                await self.get_profile()
            
            # Step 1: Register upload
            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{self.person_id}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.api_base_url}/assets?action=registerUpload",
                headers=self._get_headers(),
                json=register_data
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to register upload: {response.status_code}")
                return None
            
            register_result = response.json()
            upload_mechanism = register_result["value"]["uploadMechanism"]
            upload_url = upload_mechanism["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset_id = register_result["value"]["asset"]
            
            # Step 2: Upload image
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream"
            }
            
            upload_response = await self.httpx_client.post(
                upload_url,
                headers=upload_headers,
                content=image_data
            )
            
            if upload_response.status_code == 201:
                return asset_id
            else:
                self.logger.error(f"Failed to upload image: {upload_response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading image: {e}")
            return None
    
    async def create_image_post(self, content: str, image_data: bytes, image_name: str, visibility: str = "PUBLIC") -> LinkedInResponse:
        """Create a post with an image"""
        try:
            if not self.person_id:
                await self.get_profile()
            
            # Upload image first
            asset_id = await self.upload_image(image_data, image_name)
            if not asset_id:
                return LinkedInResponse(
                    success=False,
                    message="Failed to upload image"
                )
            
            # Create post with image
            post_data = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "IMAGE",
                        "media": [
                            {
                                "status": "READY",
                                "description": {
                                    "text": content
                                },
                                "media": asset_id,
                                "title": {
                                    "text": image_name
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.api_base_url}/ugcPosts",
                headers=self._get_headers(),
                json=post_data
            )
            
            if response.status_code == 201:
                result = response.json()
                post_id = result.get("id")
                return LinkedInResponse(
                    success=True,
                    post_id=post_id,
                    message="Image post created successfully"
                )
            else:
                error_msg = f"Failed to create image post: {response.status_code}"
                self.logger.error(error_msg)
                return LinkedInResponse(
                    success=False,
                    message=error_msg,
                    error_code=str(response.status_code)
                )
                
        except Exception as e:
            error_msg = f"Error creating image post: {e}"
            self.logger.error(error_msg)
            return LinkedInResponse(
                success=False,
                message=error_msg
            )
    
    async def create_carousel_post(self, content: str, images: List[bytes], image_names: List[str], visibility: str = "PUBLIC") -> LinkedInResponse:
        """Create a carousel post with multiple images"""
        try:
            if not self.person_id:
                await self.get_profile()
            
            # Upload all images
            asset_ids = []
            for image_data, image_name in zip(images, image_names):
                asset_id = await self.upload_image(image_data, image_name)
                if asset_id:
                    asset_ids.append(asset_id)
            
            if not asset_ids:
                return LinkedInResponse(
                    success=False,
                    message="Failed to upload images"
                )
            
            # Create carousel post
            media_items = []
            for i, asset_id in enumerate(asset_ids):
                media_items.append({
                    "status": "READY",
                    "description": {
                        "text": f"Slide {i+1}"
                    },
                    "media": asset_id,
                    "title": {
                        "text": image_names[i] if i < len(image_names) else f"Slide {i+1}"
                    }
                })
            
            post_data = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "IMAGE",
                        "media": media_items
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.api_base_url}/ugcPosts",
                headers=self._get_headers(),
                json=post_data
            )
            
            if response.status_code == 201:
                result = response.json()
                post_id = result.get("id")
                return LinkedInResponse(
                    success=True,
                    post_id=post_id,
                    message="Carousel post created successfully"
                )
            else:
                error_msg = f"Failed to create carousel post: {response.status_code}"
                self.logger.error(error_msg)
                return LinkedInResponse(
                    success=False,
                    message=error_msg,
                    error_code=str(response.status_code)
                )
                
        except Exception as e:
            error_msg = f"Error creating carousel post: {e}"
            self.logger.error(error_msg)
            return LinkedInResponse(
                success=False,
                message=error_msg
            )
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a specific post"""
        try:
            response = await self.httpx_client.get(
                f"{self.api_base_url}/socialActions/{post_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get analytics: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting post analytics: {e}")
            return {}
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete a specific post"""
        try:
            response = await self.httpx_client.delete(
                f"{self.api_base_url}/ugcPosts/{post_id}",
                headers=self._get_headers()
            )
            
            return response.status_code == 204
            
        except Exception as e:
            self.logger.error(f"Error deleting post: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated"""
        return self.access_token is not None
    
    async def test_connection(self) -> bool:
        """Test the LinkedIn API connection"""
        try:
            profile = await self.get_profile()
            return bool(profile.get("id"))
        except Exception as e:
            self.logger.error(f"LinkedIn API connection test failed: {e}")
            return False