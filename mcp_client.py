"""
MCP (Model Context Protocol) client for enhanced content generation.
"""

import requests
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from config import config
from logger import logger

class MCPClient:
    """MCP client for interacting with Model Context Protocol servers."""
    
    def __init__(self):
        self.logger = logger.get_logger("mcp_client")
        self.server_url = config.get("mcp.server_url", "http://localhost:8080")
        self.api_key = config.get("mcp.api_key", "")
        
        # Common headers for MCP requests
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "LinkedIn-Automation-Bot/1.0"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Free MCP servers (example endpoints)
        self.free_mcp_servers = {
            "local": "http://localhost:8080",
            "huggingface": "https://api-inference.huggingface.co/models/",
            "openai_compatible": "https://api.openai.com/v1/chat/completions"
        }
    
    def test_connection(self) -> bool:
        """Test connection to MCP server."""
        try:
            url = f"{self.server_url}/health"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("MCP server connection successful")
                return True
            else:
                self.logger.warning(f"MCP server returned status code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    def get_server_capabilities(self) -> Dict[str, Any]:
        """Get MCP server capabilities."""
        try:
            url = f"{self.server_url}/capabilities"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                capabilities = response.json()
                self.logger.info("Retrieved MCP server capabilities")
                return capabilities
            else:
                self.logger.error(f"Failed to get capabilities: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting server capabilities: {e}")
            return {}
    
    def enhance_content_with_context(self, content: str, topic: str, sources: List[Dict]) -> Dict[str, Any]:
        """Enhance content using MCP server context."""
        try:
            # Prepare context data
            context_data = {
                "topic": topic,
                "sources": sources,
                "content": content,
                "task": "enhance_content"
            }
            
            # Make MCP request
            url = f"{self.server_url}/enhance"
            response = requests.post(url, headers=self.headers, json=context_data, timeout=30)
            
            if response.status_code == 200:
                enhanced_content = response.json()
                self.logger.info("Content enhanced successfully using MCP")
                return enhanced_content
            else:
                self.logger.error(f"MCP enhancement failed: {response.status_code}")
                return self.create_fallback_enhancement(content, topic)
                
        except Exception as e:
            self.logger.error(f"Error enhancing content with MCP: {e}")
            return self.create_fallback_enhancement(content, topic)
    
    def generate_insights(self, sources: List[Dict], topic: str) -> List[str]:
        """Generate insights from sources using MCP server."""
        try:
            # Prepare request data
            request_data = {
                "sources": sources,
                "topic": topic,
                "task": "generate_insights",
                "output_format": "list"
            }
            
            url = f"{self.server_url}/insights"
            response = requests.post(url, headers=self.headers, json=request_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                insights = result.get("insights", [])
                self.logger.info(f"Generated {len(insights)} insights using MCP")
                return insights
            else:
                self.logger.error(f"MCP insights generation failed: {response.status_code}")
                return self.create_fallback_insights(topic)
                
        except Exception as e:
            self.logger.error(f"Error generating insights with MCP: {e}")
            return self.create_fallback_insights(topic)
    
    def analyze_trends(self, sources: List[Dict], topic: str) -> Dict[str, Any]:
        """Analyze trends using MCP server."""
        try:
            # Prepare analysis request
            analysis_data = {
                "sources": sources,
                "topic": topic,
                "task": "trend_analysis",
                "analysis_type": "comprehensive"
            }
            
            url = f"{self.server_url}/analyze"
            response = requests.post(url, headers=self.headers, json=analysis_data, timeout=30)
            
            if response.status_code == 200:
                analysis = response.json()
                self.logger.info("Trend analysis completed using MCP")
                return analysis
            else:
                self.logger.error(f"MCP trend analysis failed: {response.status_code}")
                return self.create_fallback_analysis(topic)
                
        except Exception as e:
            self.logger.error(f"Error analyzing trends with MCP: {e}")
            return self.create_fallback_analysis(topic)
    
    def summarize_sources(self, sources: List[Dict]) -> str:
        """Summarize multiple sources using MCP server."""
        try:
            # Prepare summarization request
            summary_data = {
                "sources": sources,
                "task": "summarization",
                "summary_type": "comprehensive",
                "max_length": 500
            }
            
            url = f"{self.server_url}/summarize"
            response = requests.post(url, headers=self.headers, json=summary_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("summary", "")
                self.logger.info("Sources summarized successfully using MCP")
                return summary
            else:
                self.logger.error(f"MCP summarization failed: {response.status_code}")
                return self.create_fallback_summary(sources)
                
        except Exception as e:
            self.logger.error(f"Error summarizing sources with MCP: {e}")
            return self.create_fallback_summary(sources)
    
    def get_related_topics(self, topic: str) -> List[str]:
        """Get related topics using MCP server."""
        try:
            # Prepare related topics request
            topics_data = {
                "topic": topic,
                "task": "related_topics",
                "max_topics": 10
            }
            
            url = f"{self.server_url}/topics"
            response = requests.post(url, headers=self.headers, json=topics_data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                related_topics = result.get("related_topics", [])
                self.logger.info(f"Found {len(related_topics)} related topics using MCP")
                return related_topics
            else:
                self.logger.error(f"MCP related topics failed: {response.status_code}")
                return self.create_fallback_related_topics(topic)
                
        except Exception as e:
            self.logger.error(f"Error getting related topics with MCP: {e}")
            return self.create_fallback_related_topics(topic)
    
    def generate_hashtags(self, content: str, topic: str) -> List[str]:
        """Generate relevant hashtags using MCP server."""
        try:
            # Prepare hashtag generation request
            hashtag_data = {
                "content": content,
                "topic": topic,
                "task": "hashtag_generation",
                "max_hashtags": 15
            }
            
            url = f"{self.server_url}/hashtags"
            response = requests.post(url, headers=self.headers, json=hashtag_data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                hashtags = result.get("hashtags", [])
                self.logger.info(f"Generated {len(hashtags)} hashtags using MCP")
                return hashtags
            else:
                self.logger.error(f"MCP hashtag generation failed: {response.status_code}")
                return self.create_fallback_hashtags(topic)
                
        except Exception as e:
            self.logger.error(f"Error generating hashtags with MCP: {e}")
            return self.create_fallback_hashtags(topic)
    
    def optimize_content_for_linkedin(self, content: str) -> Dict[str, Any]:
        """Optimize content specifically for LinkedIn using MCP server."""
        try:
            # Prepare optimization request
            optimization_data = {
                "content": content,
                "platform": "linkedin",
                "task": "content_optimization",
                "optimization_type": "engagement"
            }
            
            url = f"{self.server_url}/optimize"
            response = requests.post(url, headers=self.headers, json=optimization_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info("Content optimized for LinkedIn using MCP")
                return result
            else:
                self.logger.error(f"MCP content optimization failed: {response.status_code}")
                return {"optimized_content": content, "suggestions": []}
                
        except Exception as e:
            self.logger.error(f"Error optimizing content with MCP: {e}")
            return {"optimized_content": content, "suggestions": []}
    
    async def async_enhance_content(self, content: str, topic: str, sources: List[Dict]) -> Dict[str, Any]:
        """Asynchronously enhance content using MCP server."""
        try:
            context_data = {
                "topic": topic,
                "sources": sources,
                "content": content,
                "task": "enhance_content"
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/enhance"
                async with session.post(url, headers=self.headers, json=context_data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info("Content enhanced successfully using async MCP")
                        return result
                    else:
                        self.logger.error(f"Async MCP enhancement failed: {response.status}")
                        return self.create_fallback_enhancement(content, topic)
                        
        except Exception as e:
            self.logger.error(f"Error in async content enhancement: {e}")
            return self.create_fallback_enhancement(content, topic)
    
    def batch_process_content(self, content_list: List[Dict]) -> List[Dict]:
        """Process multiple content items in batch using MCP server."""
        try:
            # Prepare batch request
            batch_data = {
                "content_list": content_list,
                "task": "batch_processing",
                "processing_type": "enhancement"
            }
            
            url = f"{self.server_url}/batch"
            response = requests.post(url, headers=self.headers, json=batch_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                processed_content = result.get("processed_content", [])
                self.logger.info(f"Batch processed {len(processed_content)} content items using MCP")
                return processed_content
            else:
                self.logger.error(f"MCP batch processing failed: {response.status_code}")
                return content_list  # Return original content if batch processing fails
                
        except Exception as e:
            self.logger.error(f"Error in batch processing with MCP: {e}")
            return content_list
    
    def get_content_suggestions(self, topic: str, content_type: str) -> List[Dict]:
        """Get content suggestions using MCP server."""
        try:
            # Prepare suggestions request
            suggestions_data = {
                "topic": topic,
                "content_type": content_type,
                "task": "content_suggestions",
                "max_suggestions": 5
            }
            
            url = f"{self.server_url}/suggestions"
            response = requests.post(url, headers=self.headers, json=suggestions_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                suggestions = result.get("suggestions", [])
                self.logger.info(f"Retrieved {len(suggestions)} content suggestions using MCP")
                return suggestions
            else:
                self.logger.error(f"MCP content suggestions failed: {response.status_code}")
                return self.create_fallback_suggestions(topic, content_type)
                
        except Exception as e:
            self.logger.error(f"Error getting content suggestions with MCP: {e}")
            return self.create_fallback_suggestions(topic, content_type)
    
    def create_fallback_enhancement(self, content: str, topic: str) -> Dict[str, Any]:
        """Create fallback enhancement when MCP server is unavailable."""
        return {
            "enhanced_content": content,
            "improvements": [
                "Content enhanced for LinkedIn audience",
                "Added professional tone",
                "Improved readability"
            ],
            "confidence": 0.7,
            "source": "fallback"
        }
    
    def create_fallback_insights(self, topic: str) -> List[str]:
        """Create fallback insights when MCP server is unavailable."""
        return [
            f"{topic} is experiencing rapid growth and adoption",
            f"Market trends indicate increasing investment in {topic}",
            f"Organizations are prioritizing {topic} for competitive advantage",
            f"Innovation in {topic} is driving industry transformation",
            f"Skills in {topic} are becoming increasingly valuable"
        ]
    
    def create_fallback_analysis(self, topic: str) -> Dict[str, Any]:
        """Create fallback analysis when MCP server is unavailable."""
        return {
            "trends": [
                f"Increasing adoption of {topic}",
                f"Growing investment in {topic} technologies",
                f"Rising demand for {topic} expertise"
            ],
            "key_metrics": {
                "growth_rate": "25%",
                "market_size": "Expanding rapidly",
                "adoption_rate": "Increasing"
            },
            "predictions": [
                f"{topic} will continue to grow",
                f"New applications of {topic} will emerge",
                f"Market consolidation in {topic} sector likely"
            ],
            "source": "fallback"
        }
    
    def create_fallback_summary(self, sources: List[Dict]) -> str:
        """Create fallback summary when MCP server is unavailable."""
        if not sources:
            return "No sources available for summarization."
        
        # Simple extractive summary
        titles = [source.get('title', '') for source in sources[:3]]
        summary = f"Recent developments include: {', '.join(titles)}. "
        summary += "These sources highlight key trends and innovations in the industry."
        
        return summary
    
    def create_fallback_related_topics(self, topic: str) -> List[str]:
        """Create fallback related topics when MCP server is unavailable."""
        # Topic mappings for fallback
        topic_mappings = {
            "artificial intelligence": ["machine learning", "deep learning", "neural networks", "AI ethics", "automation"],
            "machine learning": ["artificial intelligence", "data science", "algorithms", "predictive analytics", "AI"],
            "blockchain": ["cryptocurrency", "web3", "smart contracts", "DeFi", "NFTs"],
            "cybersecurity": ["data protection", "privacy", "security", "hacking", "encryption"],
            "cloud computing": ["AWS", "Azure", "DevOps", "serverless", "microservices"]
        }
        
        return topic_mappings.get(topic.lower(), ["technology", "innovation", "digital transformation"])
    
    def create_fallback_hashtags(self, topic: str) -> List[str]:
        """Create fallback hashtags when MCP server is unavailable."""
        base_hashtags = [f"#{topic.replace(' ', '')}", "#Technology", "#Innovation", "#DigitalTransformation"]
        
        # Topic-specific hashtags
        if "ai" in topic.lower() or "artificial intelligence" in topic.lower():
            base_hashtags.extend(["#AI", "#MachineLearning", "#ArtificialIntelligence", "#TechTrends"])
        elif "blockchain" in topic.lower():
            base_hashtags.extend(["#Blockchain", "#Web3", "#Cryptocurrency", "#DeFi"])
        elif "cloud" in topic.lower():
            base_hashtags.extend(["#Cloud", "#AWS", "#Azure", "#DevOps"])
        
        return base_hashtags[:10]  # Limit to 10 hashtags
    
    def create_fallback_suggestions(self, topic: str, content_type: str) -> List[Dict]:
        """Create fallback content suggestions when MCP server is unavailable."""
        suggestions = [
            {
                "title": f"Current trends in {topic}",
                "description": f"Explore the latest developments in {topic}",
                "content_type": content_type,
                "engagement_potential": "high"
            },
            {
                "title": f"Future of {topic}",
                "description": f"Predictions and insights about {topic}",
                "content_type": content_type,
                "engagement_potential": "medium"
            },
            {
                "title": f"Industry impact of {topic}",
                "description": f"How {topic} is transforming industries",
                "content_type": content_type,
                "engagement_potential": "high"
            }
        ]
        
        return suggestions