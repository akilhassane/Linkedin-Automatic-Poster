"""
LinkedIn poster for publishing content to LinkedIn automatically.
"""

import requests
import json
import base64
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode
from config import config
from logger import logger

class LinkedInPoster:
    """LinkedIn poster for automated content publishing."""
    
    def __init__(self):
        self.logger = logger.get_logger("linkedin_poster")
        self.client_id = config.get("linkedin.client_id")
        self.client_secret = config.get("linkedin.client_secret")
        self.access_token = config.get("linkedin.access_token")
        self.user_id = config.get("linkedin.user_id")
        
        # LinkedIn API endpoints
        self.base_url = "https://api.linkedin.com"
        self.api_version = "v2"
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    def validate_credentials(self) -> bool:
        """Validate LinkedIn API credentials."""
        if not all([self.client_id, self.client_secret, self.access_token]):
            self.logger.error("Missing LinkedIn API credentials")
            return False
        
        try:
            # Test API access by getting user profile
            url = f"{self.base_url}/{self.api_version}/people/~"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                self.logger.info("LinkedIn API credentials validated successfully")
                return True
            else:
                self.logger.error(f"LinkedIn API validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating LinkedIn credentials: {e}")
            return False
    
    def post_text_update(self, content: str, hashtags: List[str] | None = None) -> Dict[str, Any]:
        """Post a text update to LinkedIn."""
        try:
            # Prepare post content
            if hashtags:
                content += "\n\n" + " ".join(hashtags)
            
            # Create post data
            post_data = {
                "author": f"urn:li:person:{self.user_id}",
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
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Make API request
            url = f"{self.base_url}/{self.api_version}/ugcPosts"
            response = requests.post(url, headers=self.headers, json=post_data)
            
            if response.status_code == 201:
                self.logger.info("Text update posted successfully")
                return {"success": True, "post_id": response.json().get("id")}
            else:
                self.logger.error(f"Failed to post text update: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error posting text update: {e}")
            return {"success": False, "error": str(e)}
    
    def post_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post an article to LinkedIn."""
        try:
            # Create article content
            article_content = f"{article_data.get('headline', '')}\n\n"
            article_content += f"{article_data.get('introduction', '')}\n\n"
            
            # Add main points
            main_points = article_data.get('main_points', [])
            for i, point in enumerate(main_points, 1):
                article_content += f"{i}. {point}\n\n"
            
            # Add takeaways
            takeaways = article_data.get('takeaways', [])
            if takeaways:
                article_content += "Key Takeaways:\n"
                for takeaway in takeaways:
                    article_content += f"• {takeaway}\n"
                article_content += "\n"
            
            # Add conclusion
            article_content += article_data.get('conclusion', '')
            
            # Add hashtags
            hashtags = article_data.get('hashtags', [])
            
            return self.post_text_update(article_content, hashtags)
            
        except Exception as e:
            self.logger.error(f"Error posting article: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """Upload an image to LinkedIn and return the asset URN."""
        try:
            # Step 1: Register upload
            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{self.user_id}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }
            
            register_url = f"{self.base_url}/{self.api_version}/assets?action=registerUpload"
            register_response = requests.post(register_url, headers=self.headers, json=register_data)
            
            if register_response.status_code != 200:
                self.logger.error(f"Failed to register image upload: {register_response.status_code}")
                return None
            
            register_result = register_response.json()
            asset_id = register_result["value"]["asset"]
            upload_url = register_result["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            
            # Step 2: Upload image
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream"
            }
            
            upload_response = requests.post(upload_url, headers=upload_headers, data=image_data)
            
            if upload_response.status_code == 201:
                self.logger.info(f"Image uploaded successfully: {asset_id}")
                return asset_id
            else:
                self.logger.error(f"Failed to upload image: {upload_response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading image: {e}")
            return None
    
    def post_image_with_text(self, image_path: str, content: str, hashtags: List[str] | None = None) -> Dict[str, Any]:
        """Post an image with text content to LinkedIn."""
        try:
            # Upload image first
            asset_id = self.upload_image(image_path)
            if not asset_id:
                return {"success": False, "error": "Failed to upload image"}
            
            # Prepare post content
            if hashtags:
                content += "\n\n" + " ".join(hashtags)
            
            # Create post data with image
            post_data = {
                "author": f"urn:li:person:{self.user_id}",
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
                                    "text": "Data visualization"
                                },
                                "media": asset_id,
                                "title": {
                                    "text": "Chart"
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Make API request
            url = f"{self.base_url}/{self.api_version}/ugcPosts"
            response = requests.post(url, headers=self.headers, json=post_data)
            
            if response.status_code == 201:
                self.logger.info("Image post created successfully")
                return {"success": True, "post_id": response.json().get("id")}
            else:
                self.logger.error(f"Failed to post image: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error posting image: {e}")
            return {"success": False, "error": str(e)}
    
    def post_carousel(self, slide_data: Dict[str, Any], slide_images: List[str]) -> Dict[str, Any]:
        """Post a carousel of images to LinkedIn."""
        try:
            # Upload all images
            asset_ids = []
            for image_path in slide_images:
                asset_id = self.upload_image(image_path)
                if asset_id:
                    asset_ids.append(asset_id)
            
            if not asset_ids:
                return {"success": False, "error": "Failed to upload carousel images"}
            
            # Prepare carousel content
            title = slide_data.get('title_slide', {}).get('title', 'Carousel Post')
            content = f"{title}\n\n"
            content += slide_data.get('title_slide', {}).get('subtitle', '')
            
            # Add hashtags
            hashtags = slide_data.get('hashtags', [])
            if hashtags:
                content += "\n\n" + " ".join(hashtags)
            
            # Create media objects for carousel
            media_objects = []
            for i, asset_id in enumerate(asset_ids):
                media_objects.append({
                    "status": "READY",
                    "description": {
                        "text": f"Slide {i+1}"
                    },
                    "media": asset_id,
                    "title": {
                        "text": f"Slide {i+1}"
                    }
                })
            
            # Create post data
            post_data = {
                "author": f"urn:li:person:{self.user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "IMAGE",
                        "media": media_objects
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Make API request
            url = f"{self.base_url}/{self.api_version}/ugcPosts"
            response = requests.post(url, headers=self.headers, json=post_data)
            
            if response.status_code == 201:
                self.logger.info("Carousel post created successfully")
                return {"success": True, "post_id": response.json().get("id")}
            else:
                self.logger.error(f"Failed to post carousel: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error posting carousel: {e}")
            return {"success": False, "error": str(e)}
    
    def post_graph(self, graph_data: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """Post a graph/chart to LinkedIn."""
        try:
            # Create descriptive content for the graph
            content = f"📊 {graph_data.get('title', 'Data Insights')}\n\n"
            
            # Add insights
            insights = graph_data.get('insights', [])
            if insights:
                content += "Key Insights:\n"
                for insight in insights:
                    content += f"• {insight}\n"
                content += "\n"
            
            # Add call to action
            content += "What trends are you seeing in your industry? Share your thoughts below! 👇"
            
            # Add hashtags
            hashtags = graph_data.get('hashtags', [])
            
            return self.post_image_with_text(image_path, content, hashtags)
            
        except Exception as e:
            self.logger.error(f"Error posting graph: {e}")
            return {"success": False, "error": str(e)}
    
    def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a specific post."""
        try:
            url = f"{self.base_url}/{self.api_version}/socialActions/{post_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get post analytics: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting post analytics: {e}")
            return {}
    
    def delete_post(self, post_id: str) -> bool:
        """Delete a specific post."""
        try:
            url = f"{self.base_url}/{self.api_version}/ugcPosts/{post_id}"
            response = requests.delete(url, headers=self.headers)
            
            if response.status_code == 204:
                self.logger.info(f"Post {post_id} deleted successfully")
                return True
            else:
                self.logger.error(f"Failed to delete post: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting post: {e}")
            return False
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        try:
            url = f"{self.base_url}/{self.api_version}/people/~"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get user profile: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return {}
    
    def schedule_post(self, post_data: Dict[str, Any], schedule_time: str) -> Dict[str, Any]:
        """Schedule a post for later publication."""
        # Note: LinkedIn API doesn't support scheduling posts directly
        # This would typically be handled by a job scheduler or cron job
        # For now, we'll store the post data and schedule it using the system scheduler
        
        try:
            scheduled_post = {
                "post_data": post_data,
                "schedule_time": schedule_time,
                "status": "scheduled"
            }
            
            # In a real implementation, you would store this in a database
            # For this example, we'll just return the scheduled post data
            self.logger.info(f"Post scheduled for {schedule_time}")
            return {"success": True, "scheduled_post": scheduled_post}
            
        except Exception as e:
            self.logger.error(f"Error scheduling post: {e}")
            return {"success": False, "error": str(e)}
    
    def refresh_access_token(self) -> bool:
        """Refresh the LinkedIn access token."""
        try:
            # This would typically involve using the refresh token
            # LinkedIn API tokens are long-lived, so refresh might not be needed often
            # Implementation depends on your OAuth flow
            
            self.logger.info("Access token refresh not implemented - LinkedIn tokens are long-lived")
            return True
            
        except Exception as e:
            self.logger.error(f"Error refreshing access token: {e}")
            return False