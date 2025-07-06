import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from config.settings import settings

@dataclass
class MCPContext:
    """Structure for MCP context information"""
    context_id: str
    topic: str
    data: Dict[str, Any]
    timestamp: str
    relevance_score: float = 0.0

class MCPClient:
    """Model Context Protocol client for enhanced context awareness"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.httpx_client = httpx.AsyncClient(timeout=30.0)
        self.server_url = settings.mcp.server_url
        self.api_key = settings.mcp.api_key
        self.context_cache = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.httpx_client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for MCP API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def create_context(self, topic: str, data: Dict[str, Any]) -> Optional[MCPContext]:
        """Create a new context in the MCP server"""
        try:
            payload = {
                "topic": topic,
                "data": data,
                "context_type": "linkedin_automation",
                "metadata": {
                    "source": "web_scraper",
                    "timestamp": str(asyncio.get_event_loop().time())
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.server_url}/v1/contexts",
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                context = MCPContext(
                    context_id=result["context_id"],
                    topic=topic,
                    data=data,
                    timestamp=result["timestamp"],
                    relevance_score=result.get("relevance_score", 0.0)
                )
                self.context_cache[context.context_id] = context
                return context
            else:
                self.logger.warning(f"Failed to create context: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating MCP context: {e}")
            return None
    
    async def get_context(self, context_id: str) -> Optional[MCPContext]:
        """Retrieve context from MCP server"""
        try:
            # Check cache first
            if context_id in self.context_cache:
                return self.context_cache[context_id]
            
            response = await self.httpx_client.get(
                f"{self.server_url}/v1/contexts/{context_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                context = MCPContext(
                    context_id=result["context_id"],
                    topic=result["topic"],
                    data=result["data"],
                    timestamp=result["timestamp"],
                    relevance_score=result.get("relevance_score", 0.0)
                )
                self.context_cache[context_id] = context
                return context
            else:
                self.logger.warning(f"Context not found: {context_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error retrieving MCP context: {e}")
            return None
    
    async def update_context(self, context_id: str, data: Dict[str, Any]) -> bool:
        """Update existing context"""
        try:
            payload = {
                "data": data,
                "metadata": {
                    "updated_at": str(asyncio.get_event_loop().time())
                }
            }
            
            response = await self.httpx_client.patch(
                f"{self.server_url}/v1/contexts/{context_id}",
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                # Update cache
                if context_id in self.context_cache:
                    self.context_cache[context_id].data.update(data)
                return True
            else:
                self.logger.warning(f"Failed to update context: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating MCP context: {e}")
            return False
    
    async def search_contexts(self, query: str, topic: Optional[str] = None) -> List[MCPContext]:
        """Search for relevant contexts"""
        try:
            params = {"query": query}
            if topic:
                params["topic"] = topic
            
            response = await self.httpx_client.get(
                f"{self.server_url}/v1/contexts/search",
                headers=self._get_headers(),
                params=params
            )
            
            if response.status_code == 200:
                results = response.json()
                contexts = []
                for result in results.get("contexts", []):
                    context = MCPContext(
                        context_id=result["context_id"],
                        topic=result["topic"],
                        data=result["data"],
                        timestamp=result["timestamp"],
                        relevance_score=result.get("relevance_score", 0.0)
                    )
                    contexts.append(context)
                return contexts
            else:
                self.logger.warning(f"Search failed: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching MCP contexts: {e}")
            return []
    
    async def get_recommendations(self, topic: str, context_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get content recommendations from MCP server"""
        try:
            payload = {
                "topic": topic,
                "context": context_data,
                "recommendation_type": "content_generation",
                "parameters": {
                    "max_recommendations": 10,
                    "include_trends": True,
                    "include_keywords": True
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.server_url}/v1/recommendations",
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("recommendations", [])
            else:
                self.logger.warning(f"Recommendations failed: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def analyze_content(self, content: str, content_type: str) -> Dict[str, Any]:
        """Analyze content using MCP server"""
        try:
            payload = {
                "content": content,
                "content_type": content_type,
                "analysis_type": "comprehensive",
                "parameters": {
                    "sentiment_analysis": True,
                    "keyword_extraction": True,
                    "readability_score": True,
                    "engagement_prediction": True
                }
            }
            
            response = await self.httpx_client.post(
                f"{self.server_url}/v1/analyze",
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Content analysis failed: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error analyzing content: {e}")
            return {}
    
    async def get_trending_topics(self, category: Optional[str] = None) -> List[str]:
        """Get trending topics from MCP server"""
        try:
            params = {}
            if category:
                params["category"] = category
            
            response = await self.httpx_client.get(
                f"{self.server_url}/v1/trends/topics",
                headers=self._get_headers(),
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("topics", [])
            else:
                self.logger.warning(f"Trending topics failed: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting trending topics: {e}")
            return []
    
    async def store_content_history(self, content_type: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Store content generation history"""
        try:
            payload = {
                "content_type": content_type,
                "content": content,
                "metadata": metadata,
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            response = await self.httpx_client.post(
                f"{self.server_url}/v1/history",
                headers=self._get_headers(),
                json=payload
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error storing content history: {e}")
            return False
    
    async def get_content_history(self, content_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get content generation history"""
        try:
            params = {"limit": limit}
            if content_type:
                params["content_type"] = content_type
            
            response = await self.httpx_client.get(
                f"{self.server_url}/v1/history",
                headers=self._get_headers(),
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("history", [])
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting content history: {e}")
            return []
    
    def create_fallback_context(self, topic: str, data: Dict[str, Any]) -> MCPContext:
        """Create a fallback context when MCP server is unavailable"""
        context_id = f"fallback_{hash(topic + str(data))}"
        context = MCPContext(
            context_id=context_id,
            topic=topic,
            data=data,
            timestamp=str(asyncio.get_event_loop().time()),
            relevance_score=0.5
        )
        self.context_cache[context_id] = context
        return context
    
    async def enhance_content_with_context(self, content: str, topic: str) -> str:
        """Enhance content using MCP context"""
        try:
            # Search for relevant contexts
            contexts = await self.search_contexts(topic, topic)
            
            if not contexts:
                return content
            
            # Get recommendations based on context
            context_data = {
                "existing_content": content,
                "topic": topic,
                "contexts": [ctx.data for ctx in contexts[:3]]  # Use top 3 contexts
            }
            
            recommendations = await self.get_recommendations(topic, context_data)
            
            # Apply recommendations to enhance content
            enhanced_content = content
            for rec in recommendations:
                if rec.get("type") == "keyword_addition":
                    keywords = rec.get("keywords", [])
                    # Add keywords naturally to content (simplified)
                    enhanced_content += f"\n\nKey terms: {', '.join(keywords)}"
                elif rec.get("type") == "content_expansion":
                    expansion = rec.get("content", "")
                    enhanced_content += f"\n\n{expansion}"
            
            return enhanced_content
            
        except Exception as e:
            self.logger.error(f"Error enhancing content with context: {e}")
            return content  # Return original content if enhancement fails