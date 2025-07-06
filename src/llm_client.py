import logging
import json
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import httpx
from config.settings import settings

@dataclass
class LLMResponse:
    """Structure for LLM responses"""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "completed"

class LLMClient:
    """LLM client supporting both OpenAI and Ollama"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.provider = settings.llm.provider
        self.httpx_client = httpx.AsyncClient(timeout=60.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.httpx_client.aclose()
    
    async def generate_content(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        """Generate content using the configured LLM provider"""
        if self.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, max_tokens)
        elif self.provider == "ollama":
            return await self._generate_ollama(prompt, system_prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        """Generate content using OpenAI API"""
        try:
            if not settings.llm.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            headers = {
                "Authorization": f"Bearer {settings.llm.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": "gpt-3.5-turbo",  # Using the free tier model
                "messages": messages,
                "max_tokens": max_tokens or settings.llm.max_tokens,
                "temperature": settings.llm.temperature
            }
            
            response = await self.httpx_client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            tokens_used = data["usage"]["total_tokens"]
            
            return LLMResponse(
                content=content,
                model="gpt-3.5-turbo",
                tokens_used=tokens_used,
                finish_reason=data["choices"][0]["finish_reason"]
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_ollama(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        """Generate content using Ollama local API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "model": settings.llm.ollama_model,
                "prompt": full_prompt,
                "options": {
                    "temperature": settings.llm.temperature,
                    "num_predict": max_tokens or settings.llm.max_tokens
                },
                "stream": False
            }
            
            response = await self.httpx_client.post(
                f"{settings.llm.ollama_base_url}/api/generate",
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["response"],
                model=settings.llm.ollama_model,
                tokens_used=0,  # Ollama doesn't provide token counts
                finish_reason="completed"
            )
            
        except Exception as e:
            self.logger.error(f"Ollama API error: {e}")
            raise
    
    def generate_article(self, web_content: List[Dict], topic: str) -> str:
        """Generate a LinkedIn article from web content"""
        content_summaries = []
        for content in web_content[:5]:  # Use top 5 articles
            summary = f"- {content.get('title', 'Unknown')}: {content.get('summary', content.get('content', '')[:200])}"
            content_summaries.append(summary)
        
        system_prompt = """You are a professional LinkedIn content creator. Your task is to create engaging, informative LinkedIn articles that provide value to professionals. 

Guidelines:
- Write in a professional but conversational tone
- Use proper LinkedIn formatting with emojis and hashtags
- Include actionable insights
- Keep the content engaging and shareable
- Aim for 1000-1500 words
- Structure with clear headings and bullet points
- End with a call to action or question for engagement"""
        
        user_prompt = f"""Create a comprehensive LinkedIn article about {topic} based on the following recent information:

{chr(10).join(content_summaries)}

The article should:
1. Have an engaging title
2. Start with a compelling hook
3. Provide valuable insights about {topic}
4. Include recent trends and developments
5. End with a question to encourage engagement
6. Use relevant hashtags
7. Include 2-3 relevant emojis

Make it professional, informative, and engaging for a LinkedIn audience."""
        
        response = asyncio.run(self.generate_content(user_prompt, system_prompt))
        return response.content
    
    def generate_slide_content(self, web_content: List[Dict], topic: str) -> Dict:
        """Generate slide deck content"""
        system_prompt = """You are creating content for a professional slide deck. Return the response as a JSON object with the following structure:
{
  "title": "Slide Deck Title",
  "slides": [
    {
      "title": "Slide Title",
      "content": ["Bullet point 1", "Bullet point 2", "Bullet point 3"],
      "notes": "Additional notes for the slide"
    }
  ]
}

Keep each slide focused on one main idea with 3-5 bullet points maximum."""
        
        content_summaries = []
        for content in web_content[:8]:  # Use top 8 articles for more comprehensive slides
            summary = f"- {content.get('title', 'Unknown')}: {content.get('summary', content.get('content', '')[:150])}"
            content_summaries.append(summary)
        
        user_prompt = f"""Create a 6-8 slide presentation about {topic} based on this information:

{chr(10).join(content_summaries)}

The presentation should cover:
1. Introduction to {topic}
2. Current trends and developments
3. Key insights and statistics
4. Practical applications
5. Future outlook
6. Key takeaways

Make it professional and suitable for LinkedIn carousel posts."""
        
        response = asyncio.run(self.generate_content(user_prompt, system_prompt))
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "title": f"Latest Insights: {topic}",
                "slides": [
                    {
                        "title": "Content Generation Error",
                        "content": ["Unable to parse slide content", "Please check the LLM response"],
                        "notes": "Error in content generation"
                    }
                ]
            }
    
    def generate_infographic_data(self, web_content: List[Dict], topic: str) -> Dict:
        """Generate data for infographic creation"""
        system_prompt = """You are creating data for an infographic. Return the response as a JSON object with the following structure:
{
  "title": "Infographic Title",
  "subtitle": "Brief description",
  "sections": [
    {
      "title": "Section Title",
      "type": "statistic|fact|trend",
      "data": "Key data point or statistic",
      "icon": "suggested icon name"
    }
  ],
  "color_scheme": ["#color1", "#color2", "#color3"]
}

Focus on key statistics, trends, and facts that would work well visually."""
        
        content_summaries = []
        for content in web_content[:5]:
            summary = f"- {content.get('title', 'Unknown')}: {content.get('summary', content.get('content', '')[:200])}"
            content_summaries.append(summary)
        
        user_prompt = f"""Create infographic data about {topic} based on this information:

{chr(10).join(content_summaries)}

Focus on:
1. Key statistics and numbers
2. Important trends
3. Interesting facts
4. Growth data
5. Market insights

Make it visually appealing and data-driven."""
        
        response = asyncio.run(self.generate_content(user_prompt, system_prompt))
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "title": f"{topic} Insights",
                "subtitle": "Key data and trends",
                "sections": [
                    {
                        "title": "Data Unavailable",
                        "type": "fact",
                        "data": "Unable to generate infographic data",
                        "icon": "info"
                    }
                ],
                "color_scheme": ["#1f77b4", "#ff7f0e", "#2ca02c"]
            }
    
    def generate_post_comment(self, content_type: str, topic: str) -> str:
        """Generate engaging comments for posts"""
        system_prompt = """You are creating engaging LinkedIn post comments. Keep them professional, conversational, and designed to encourage engagement. Include relevant emojis and hashtags."""
        
        user_prompt = f"""Create a LinkedIn post comment for a {content_type} about {topic}. The comment should:
1. Be 2-3 sentences long
2. Provide a key insight or question
3. Encourage engagement
4. Include 1-2 relevant emojis
5. Include 3-5 relevant hashtags

Make it professional but engaging."""
        
        response = asyncio.run(self.generate_content(user_prompt, system_prompt))
        return response.content
    
    async def summarize_content(self, content: str, max_length: int = 300) -> str:
        """Summarize content to a specific length"""
        system_prompt = f"You are a professional content summarizer. Summarize the following content in approximately {max_length} characters while preserving the key insights and main points."
        
        response = await self.generate_content(content, system_prompt, max_tokens=max_length//3)
        return response.content