import logging
import asyncio
import json
import io
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import base64

from src.web_scraper import WebScraper, WebContent
from src.llm_client import LLMClient
from src.mcp_client import MCPClient
from config.settings import settings

@dataclass
class GeneratedContent:
    """Structure for generated content"""
    content_type: str
    title: str
    content: str
    image_data: Optional[bytes] = None
    image_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ContentGenerator:
    """Content generator for various types of LinkedIn content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.web_scraper = WebScraper()
        self.llm_client = LLMClient()
        self.mcp_client = MCPClient()
        
    async def generate_article_content(self, topic: str) -> GeneratedContent:
        """Generate article content with web research"""
        try:
            self.logger.info(f"Generating article content for topic: {topic}")
            
            # Gather web content
            web_content = await self.web_scraper.gather_content_async(topic, max_articles=10)
            
            if not web_content:
                raise ValueError("No web content found for the topic")
            
            # Convert to dictionary format for LLM
            content_dicts = [
                {
                    'title': content.title,
                    'content': content.content,
                    'summary': content.summary,
                    'url': content.url,
                    'relevance_score': content.relevance_score
                }
                for content in web_content
            ]
            
            # Generate article using LLM
            article_content = self.llm_client.generate_article(content_dicts, topic)
            
            # Enhance with MCP context if available
            try:
                enhanced_content = await self.mcp_client.enhance_content_with_context(article_content, topic)
                article_content = enhanced_content
            except Exception as e:
                self.logger.warning(f"MCP enhancement failed: {e}")
            
            # Generate engaging title
            title = f"Latest Insights on {topic.title()}: What You Need to Know"
            
            return GeneratedContent(
                content_type="article",
                title=title,
                content=article_content,
                metadata={
                    "topic": topic,
                    "sources_count": len(web_content),
                    "generation_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating article content: {e}")
            raise
    
    async def generate_slide_content(self, topic: str) -> GeneratedContent:
        """Generate slide deck content"""
        try:
            self.logger.info(f"Generating slide content for topic: {topic}")
            
            # Gather web content
            web_content = await self.web_scraper.gather_content_async(topic, max_articles=8)
            
            if not web_content:
                raise ValueError("No web content found for the topic")
            
            # Convert to dictionary format for LLM
            content_dicts = [
                {
                    'title': content.title,
                    'content': content.content,
                    'summary': content.summary,
                    'url': content.url
                }
                for content in web_content
            ]
            
            # Generate slide data using LLM
            slide_data = self.llm_client.generate_slide_content(content_dicts, topic)
            
            # Create slide images
            slide_images = await self.create_slide_images(slide_data)
            
            # Generate slide deck summary
            slide_summary = f"📊 {slide_data.get('title', f'{topic} Insights')}\n\n"
            slide_summary += f"Key insights about {topic} in {len(slide_data.get('slides', []))} slides:\n\n"
            
            for i, slide in enumerate(slide_data.get('slides', []), 1):
                slide_summary += f"{i}. {slide.get('title', 'Slide')}\n"
                for point in slide.get('content', [])[:2]:  # Show first 2 points
                    slide_summary += f"   • {point}\n"
                slide_summary += "\n"
            
            slide_summary += f"#LinkedIn #ProfessionalDevelopment #{topic.replace(' ', '')}"
            
            return GeneratedContent(
                content_type="slides",
                title=slide_data.get('title', f'{topic} Insights'),
                content=slide_summary,
                image_data=slide_images,
                image_name=f"{topic}_slides.png",
                metadata={
                    "topic": topic,
                    "slides_count": len(slide_data.get('slides', [])),
                    "generation_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating slide content: {e}")
            raise
    
    async def generate_graph_content(self, topic: str) -> GeneratedContent:
        """Generate graph/chart content"""
        try:
            self.logger.info(f"Generating graph content for topic: {topic}")
            
            # Gather web content
            web_content = await self.web_scraper.gather_content_async(topic, max_articles=5)
            
            if not web_content:
                raise ValueError("No web content found for the topic")
            
            # Extract numerical data or create synthetic data for visualization
            graph_data = await self.extract_graph_data(web_content, topic)
            
            # Create graph
            graph_image = await self.create_graph_image(graph_data, topic)
            
            # Generate graph description
            graph_description = f"📈 {topic.title()} Trends & Insights\n\n"
            graph_description += f"Latest data visualization showing key trends in {topic}:\n\n"
            
            if graph_data.get('insights'):
                for insight in graph_data['insights'][:3]:
                    graph_description += f"• {insight}\n"
            
            graph_description += f"\nData sources: {len(web_content)} recent articles\n"
            graph_description += f"#DataVisualization #Trends #{topic.replace(' ', '')}"
            
            return GeneratedContent(
                content_type="graph",
                title=f"{topic.title()} Data Insights",
                content=graph_description,
                image_data=graph_image,
                image_name=f"{topic}_graph.png",
                metadata={
                    "topic": topic,
                    "data_points": len(graph_data.get('data', [])),
                    "generation_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating graph content: {e}")
            raise
    
    async def generate_infographic_content(self, topic: str) -> GeneratedContent:
        """Generate infographic content"""
        try:
            self.logger.info(f"Generating infographic content for topic: {topic}")
            
            # Gather web content
            web_content = await self.web_scraper.gather_content_async(topic, max_articles=5)
            
            if not web_content:
                raise ValueError("No web content found for the topic")
            
            # Convert to dictionary format for LLM
            content_dicts = [
                {
                    'title': content.title,
                    'content': content.content,
                    'summary': content.summary
                }
                for content in web_content
            ]
            
            # Generate infographic data using LLM
            infographic_data = self.llm_client.generate_infographic_data(content_dicts, topic)
            
            # Create infographic image
            infographic_image = await self.create_infographic_image(infographic_data, topic)
            
            # Generate infographic description
            infographic_description = f"🎨 {infographic_data.get('title', f'{topic} Infographic')}\n\n"
            infographic_description += f"{infographic_data.get('subtitle', 'Key insights and data visualized')}\n\n"
            
            sections = infographic_data.get('sections', [])
            for section in sections[:4]:  # Show first 4 sections
                infographic_description += f"📊 {section.get('title', 'Insight')}: {section.get('data', 'N/A')}\n"
            
            infographic_description += f"\n#Infographic #DataVisualization #{topic.replace(' ', '')}"
            
            return GeneratedContent(
                content_type="infographic",
                title=infographic_data.get('title', f'{topic} Infographic'),
                content=infographic_description,
                image_data=infographic_image,
                image_name=f"{topic}_infographic.png",
                metadata={
                    "topic": topic,
                    "sections_count": len(sections),
                    "generation_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating infographic content: {e}")
            raise
    
    async def create_slide_images(self, slide_data: Dict[str, Any]) -> Optional[bytes]:
        """Create slide images from slide data"""
        try:
            slides = slide_data.get('slides', [])
            if not slides:
                return None
            
            # Create a combined image with all slides
            slide_width = 800
            slide_height = 600
            total_height = slide_height * len(slides)
            
            # Create combined image
            combined_image = Image.new('RGB', (slide_width, total_height), 'white')
            draw = ImageDraw.Draw(combined_image)
            
            # Try to use a font, fallback to default if not available
            try:
                title_font = ImageFont.truetype("arial.ttf", 36)
                content_font = ImageFont.truetype("arial.ttf", 24)
            except:
                title_font = ImageFont.load_default()
                content_font = ImageFont.load_default()
            
            for i, slide in enumerate(slides):
                y_offset = i * slide_height
                
                # Draw slide background
                draw.rectangle([0, y_offset, slide_width, y_offset + slide_height], 
                             fill='white', outline='black', width=2)
                
                # Draw slide title
                title = slide.get('title', f'Slide {i+1}')
                draw.text((50, y_offset + 50), title, fill='black', font=title_font)
                
                # Draw slide content
                content = slide.get('content', [])
                for j, point in enumerate(content[:4]):  # Max 4 points per slide
                    draw.text((50, y_offset + 150 + j*60), f"• {point}", 
                             fill='black', font=content_font)
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            combined_image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating slide images: {e}")
            return None
    
    async def extract_graph_data(self, web_content: List[WebContent], topic: str) -> Dict[str, Any]:
        """Extract or generate data for graph visualization"""
        try:
            # This is a simplified version - in reality, you'd use NLP to extract numerical data
            # For now, we'll create synthetic data based on the topic
            
            insights = []
            for content in web_content[:3]:
                if content.summary:
                    insights.append(content.summary[:100] + "...")
                elif content.content:
                    insights.append(content.content[:100] + "...")
            
            # Generate synthetic trend data
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
            values = np.random.randint(50, 200, len(dates))  # Random values for demonstration
            
            return {
                'type': 'line',
                'title': f'{topic.title()} Trends Over Time',
                'x_label': 'Time',
                'y_label': 'Interest Level',
                'data': list(zip(dates, values)),
                'insights': insights
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting graph data: {e}")
            return {}
    
    async def create_graph_image(self, graph_data: Dict[str, Any], topic: str) -> Optional[bytes]:
        """Create graph image from data"""
        try:
            if not graph_data or not graph_data.get('data'):
                return None
            
            # Create the plot
            plt.figure(figsize=(12, 8))
            plt.style.use('seaborn-v0_8')
            
            # Extract data
            data = graph_data['data']
            x_values = [item[0] for item in data]
            y_values = [item[1] for item in data]
            
            # Create line plot
            plt.plot(x_values, y_values, marker='o', linewidth=2, markersize=6, color='#0077B5')
            
            # Customize the plot
            plt.title(graph_data.get('title', f'{topic} Trends'), fontsize=16, fontweight='bold')
            plt.xlabel(graph_data.get('x_label', 'Time'), fontsize=12)
            plt.ylabel(graph_data.get('y_label', 'Value'), fontsize=12)
            
            # Format dates on x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            
            # Add grid
            plt.grid(True, alpha=0.3)
            
            # Tight layout
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='PNG', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            
            plt.close()  # Close the figure to free memory
            
            return img_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating graph image: {e}")
            return None
    
    async def create_infographic_image(self, infographic_data: Dict[str, Any], topic: str) -> Optional[bytes]:
        """Create infographic image from data"""
        try:
            if not infographic_data:
                return None
            
            # Create infographic
            width, height = 800, 1200
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Try to use fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 48)
                subtitle_font = ImageFont.truetype("arial.ttf", 24)
                content_font = ImageFont.truetype("arial.ttf", 20)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                content_font = ImageFont.load_default()
            
            # Colors
            colors = infographic_data.get('color_scheme', ['#0077B5', '#FF6B35', '#4ECDC4'])
            
            # Draw header
            header_color = colors[0]
            draw.rectangle([0, 0, width, 150], fill=header_color)
            
            # Draw title
            title = infographic_data.get('title', f'{topic} Infographic')
            draw.text((50, 50), title, fill='white', font=title_font)
            
            # Draw subtitle
            subtitle = infographic_data.get('subtitle', 'Key insights and data')
            draw.text((50, 100), subtitle, fill='white', font=subtitle_font)
            
            # Draw sections
            sections = infographic_data.get('sections', [])
            y_pos = 200
            
            for i, section in enumerate(sections):
                section_color = colors[i % len(colors)]
                
                # Draw section box
                draw.rectangle([50, y_pos, width-50, y_pos+120], 
                             fill=section_color, outline='black', width=2)
                
                # Draw section title
                section_title = section.get('title', f'Section {i+1}')
                draw.text((70, y_pos+20), section_title, fill='white', font=subtitle_font)
                
                # Draw section data
                section_data = section.get('data', 'No data available')
                draw.text((70, y_pos+60), section_data, fill='white', font=content_font)
                
                y_pos += 150
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating infographic image: {e}")
            return None
    
    async def generate_daily_content(self, topic: str) -> GeneratedContent:
        """Generate daily content by rotating through different types"""
        try:
            # Determine content type based on day of week
            day_of_week = datetime.now().weekday()
            
            if day_of_week == 0:  # Monday - Article
                return await self.generate_article_content(topic)
            elif day_of_week == 1:  # Tuesday - Slides
                return await self.generate_slide_content(topic)
            elif day_of_week == 2:  # Wednesday - Graph
                return await self.generate_graph_content(topic)
            elif day_of_week == 3:  # Thursday - Infographic
                return await self.generate_infographic_content(topic)
            elif day_of_week == 4:  # Friday - Article
                return await self.generate_article_content(topic)
            elif day_of_week == 5:  # Saturday - Slides
                return await self.generate_slide_content(topic)
            else:  # Sunday - Graph
                return await self.generate_graph_content(topic)
                
        except Exception as e:
            self.logger.error(f"Error generating daily content: {e}")
            # Fallback to article if other types fail
            return await self.generate_article_content(topic)
    
    async def generate_content_with_comment(self, topic: str) -> Tuple[GeneratedContent, str]:
        """Generate content with an accompanying comment"""
        try:
            # Generate main content
            content = await self.generate_daily_content(topic)
            
            # Generate comment
            comment = self.llm_client.generate_post_comment(content.content_type, topic)
            
            return content, comment
            
        except Exception as e:
            self.logger.error(f"Error generating content with comment: {e}")
            raise