"""
Content generator using LLM to create LinkedIn posts, articles, and visual content.
"""

import openai
import requests
import json
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import plotly.graph_objects as go
import plotly.express as px
from plotly.io import to_image
import base64
import io
from PIL import Image, ImageDraw, ImageFont
from config import config
from logger import logger

class ContentGenerator:
    """Content generator for creating various types of LinkedIn content."""
    
    def __init__(self):
        self.logger = logger.get_logger("content_generator")
        self.openai_api_key = config.get("openai.api_key")
        self.model = config.get("openai.model", "gpt-3.5-turbo")
        self.max_tokens = config.get("openai.max_tokens", 2000)
        self.temperature = config.get("openai.temperature", 0.7)
        
        # Initialize OpenAI client
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_article_content(self, sources: List[Dict], topic: str) -> Dict[str, Any]:
        """Generate article content from gathered sources."""
        try:
            # Prepare source information
            source_summaries = []
            for source in sources:
                summary = f"Title: {source.get('title', 'N/A')}\n"
                summary += f"Summary: {source.get('summary', source.get('text', 'N/A'))[:500]}...\n"
                summary += f"Source: {source.get('source', 'N/A')}\n"
                source_summaries.append(summary)
            
            sources_text = "\n\n".join(source_summaries)
            
            # Create prompt for article generation
            prompt = f"""
            Based on the following sources about {topic}, create a comprehensive LinkedIn article:
            
            {sources_text}
            
            Please create:
            1. A compelling headline (60-80 characters)
            2. An engaging introduction paragraph
            3. 3-5 main points with detailed explanations
            4. Key takeaways or insights
            5. A call-to-action conclusion
            6. 5-10 relevant hashtags
            
            Format the response as JSON with the following structure:
            {{
                "headline": "...",
                "introduction": "...",
                "main_points": ["...", "...", "..."],
                "takeaways": ["...", "...", "..."],
                "conclusion": "...",
                "hashtags": ["...", "...", "..."]
            }}
            
            Make it professional, engaging, and suitable for LinkedIn audience.
            """
            
            response = self.generate_with_llm(prompt)
            
            try:
                content = json.loads(response)
                self.logger.info("Successfully generated article content")
                return content
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                self.logger.warning("Failed to parse JSON response, using fallback")
                return {
                    "headline": f"Latest Insights on {topic}",
                    "introduction": response[:200] + "...",
                    "main_points": [response[200:400], response[400:600], response[600:800]],
                    "takeaways": ["Key insight 1", "Key insight 2", "Key insight 3"],
                    "conclusion": response[-200:],
                    "hashtags": [f"#{topic.replace(' ', '')}", "#Technology", "#Innovation", "#LinkedIn"]
                }
                
        except Exception as e:
            self.logger.error(f"Error generating article content: {e}")
            return self.generate_fallback_content(topic)
    
    def generate_slide_content(self, sources: List[Dict], topic: str) -> Dict[str, Any]:
        """Generate slide presentation content."""
        try:
            source_summaries = []
            for source in sources:
                summary = f"{source.get('title', 'N/A')}: {source.get('summary', source.get('text', 'N/A'))[:300]}..."
                source_summaries.append(summary)
            
            sources_text = "\n".join(source_summaries)
            
            prompt = f"""
            Based on the following sources about {topic}, create a LinkedIn carousel post with 5-7 slides:
            
            {sources_text}
            
            Create slide content in JSON format:
            {{
                "title_slide": {{
                    "title": "Main Title",
                    "subtitle": "Brief description"
                }},
                "slides": [
                    {{
                        "title": "Slide Title",
                        "content": ["Bullet point 1", "Bullet point 2", "Bullet point 3"],
                        "key_stat": "Optional key statistic"
                    }},
                    ...
                ],
                "conclusion_slide": {{
                    "title": "Key Takeaways",
                    "content": ["Main takeaway 1", "Main takeaway 2", "Main takeaway 3"]
                }},
                "hashtags": ["#tag1", "#tag2", "#tag3"]
            }}
            
            Make each slide concise and visually appealing for LinkedIn.
            """
            
            response = self.generate_with_llm(prompt)
            
            try:
                content = json.loads(response)
                self.logger.info("Successfully generated slide content")
                return content
            except json.JSONDecodeError:
                return self.generate_fallback_slide_content(topic)
                
        except Exception as e:
            self.logger.error(f"Error generating slide content: {e}")
            return self.generate_fallback_slide_content(topic)
    
    def generate_graph_content(self, sources: List[Dict], topic: str) -> Dict[str, Any]:
        """Generate content for graphs and data visualizations."""
        try:
            # Extract data points from sources
            data_points = self.extract_data_points(sources, topic)
            
            prompt = f"""
            Based on the topic "{topic}" and the following data points, suggest 3 different data visualizations:
            
            Data available: {data_points}
            
            Return JSON format:
            {{
                "visualizations": [
                    {{
                        "type": "bar_chart|line_chart|pie_chart|scatter_plot",
                        "title": "Chart Title",
                        "description": "What this chart shows",
                        "data_structure": "Description of required data format"
                    }},
                    ...
                ],
                "insights": ["Key insight 1", "Key insight 2", "Key insight 3"],
                "hashtags": ["#tag1", "#tag2", "#tag3"]
            }}
            """
            
            response = self.generate_with_llm(prompt)
            
            try:
                content = json.loads(response)
                self.logger.info("Successfully generated graph content")
                return content
            except json.JSONDecodeError:
                return self.generate_fallback_graph_content(topic)
                
        except Exception as e:
            self.logger.error(f"Error generating graph content: {e}")
            return self.generate_fallback_graph_content(topic)
    
    def generate_with_llm(self, prompt: str) -> str:
        """Generate content using the configured LLM."""
        try:
            if self.openai_api_key:
                # Use OpenAI API
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional LinkedIn content creator and data analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                return response.choices[0].message.content
            else:
                # Try local LLM or alternative free service
                return self.generate_with_local_llm(prompt)
                
        except Exception as e:
            self.logger.error(f"Error generating content with LLM: {e}")
            return f"Error generating content: {str(e)}"
    
    def generate_with_local_llm(self, prompt: str) -> str:
        """Generate content using local LLM or free alternative."""
        try:
            # Try Hugging Face Inference API (free tier)
            hf_api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            
            headers = {
                "Authorization": f"Bearer {config.get('huggingface.api_key', '')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "return_full_text": False
                }
            }
            
            response = requests.post(hf_api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "No content generated")
                else:
                    return str(result)
            else:
                self.logger.warning(f"HuggingFace API failed: {response.status_code}")
                return self.generate_fallback_text(prompt)
                
        except Exception as e:
            self.logger.error(f"Error with local LLM: {e}")
            return self.generate_fallback_text(prompt)
    
    def generate_fallback_text(self, prompt: str) -> str:
        """Generate fallback text when LLM services are unavailable."""
        # Simple template-based generation
        if "article" in prompt.lower():
            return '{"headline": "Latest Technology Trends", "introduction": "The tech industry continues to evolve...", "main_points": ["Point 1", "Point 2", "Point 3"], "takeaways": ["Takeaway 1", "Takeaway 2"], "conclusion": "Stay informed about these trends.", "hashtags": ["#Technology", "#Innovation", "#TechTrends"]}'
        elif "slide" in prompt.lower():
            return '{"title_slide": {"title": "Technology Update", "subtitle": "Latest trends and insights"}, "slides": [{"title": "Key Trend 1", "content": ["Important development", "Market impact", "Future outlook"], "key_stat": "Growing by 25% annually"}], "conclusion_slide": {"title": "Key Takeaways", "content": ["Technology is evolving rapidly", "Stay updated with trends", "Adapt to changes"]}, "hashtags": ["#TechTrends", "#Innovation"]}'
        else:
            return '{"visualizations": [{"type": "bar_chart", "title": "Technology Adoption", "description": "Shows adoption rates", "data_structure": "Categories and percentages"}], "insights": ["Growing adoption", "Market changes", "Future potential"], "hashtags": ["#DataVisualization", "#TechTrends"]}'
    
    def create_visual_slide(self, slide_data: Dict[str, Any], slide_index: int) -> str | None:
        """Create a visual slide image."""
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.axis('off')
            
            # Title
            title = slide_data.get('title', f'Slide {slide_index}')
            ax.text(0.5, 0.9, title, fontsize=24, fontweight='bold', 
                   ha='center', va='top', transform=ax.transAxes)
            
            # Content
            content = slide_data.get('content', [])
            y_pos = 0.75
            
            for i, point in enumerate(content):
                ax.text(0.1, y_pos - i*0.1, f"• {point}", fontsize=16, 
                       ha='left', va='top', transform=ax.transAxes)
            
            # Key stat if available
            if slide_data.get('key_stat'):
                ax.text(0.5, 0.2, slide_data['key_stat'], fontsize=20, 
                       fontweight='bold', ha='center', va='center', 
                       transform=ax.transAxes, 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
            
            # Save image
            filename = f"slide_{slide_index}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error creating visual slide: {e}")
            return None
    
    def create_data_visualization(self, viz_data: Dict[str, Any], data_points: List[Dict]) -> str | None:
        """Create data visualization based on the specification."""
        try:
            viz_type = viz_data.get('type', 'bar_chart')
            title = viz_data.get('title', 'Data Visualization')
            
            if viz_type == 'bar_chart':
                return self.create_bar_chart(title, data_points)
            elif viz_type == 'line_chart':
                return self.create_line_chart(title, data_points)
            elif viz_type == 'pie_chart':
                return self.create_pie_chart(title, data_points)
            elif viz_type == 'scatter_plot':
                return self.create_scatter_plot(title, data_points)
            else:
                return self.create_bar_chart(title, data_points)
                
        except Exception as e:
            self.logger.error(f"Error creating data visualization: {e}")
            return None
    
    def create_bar_chart(self, title: str, data_points: List[Dict]) -> str | None:
        """Create a bar chart."""
        try:
            # Sample data if no real data available
            if not data_points:
                categories = ['AI', 'ML', 'Cloud', 'IoT', 'Blockchain']
                values = [85, 78, 92, 65, 45]
            else:
                categories = [point.get('category', f'Item {i}') for i, point in enumerate(data_points)]
                values = [point.get('value', np.random.randint(20, 100)) for point in data_points]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(categories, values, color=sns.color_palette("husl", len(categories)))
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_ylabel('Value', fontsize=12)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                       f'{value}', ha='center', va='bottom', fontweight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            filename = f"chart_{title.replace(' ', '_').lower()}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error creating bar chart: {e}")
            return None
    
    def create_line_chart(self, title: str, data_points: List[Dict]) -> str:
        """Create a line chart."""
        try:
            # Sample time series data
            dates = pd.date_range(start='2023-01-01', periods=12, freq='M')
            values = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(dates, values, marker='o', linewidth=2, markersize=8)
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_ylabel('Value', fontsize=12)
            ax.set_xlabel('Date', fontsize=12)
            
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            filename = f"line_{title.replace(' ', '_').lower()}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error creating line chart: {e}")
            return None
    
    def create_pie_chart(self, title: str, data_points: List[Dict]) -> str:
        """Create a pie chart."""
        try:
            # Sample data
            labels = ['AI/ML', 'Cloud Computing', 'IoT', 'Blockchain', 'Others']
            sizes = [35, 25, 20, 15, 5]
            colors = sns.color_palette("husl", len(labels))
            
            fig, ax = plt.subplots(figsize=(10, 8))
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                            startangle=90, textprops={'fontsize': 10})
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            
            filename = f"pie_{title.replace(' ', '_').lower()}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error creating pie chart: {e}")
            return None
    
    def create_scatter_plot(self, title: str, data_points: List[Dict]) -> str:
        """Create a scatter plot."""
        try:
            # Sample data
            x = np.random.randn(100)
            y = 2 * x + np.random.randn(100)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(x, y, alpha=0.6, s=50)
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel('X Value', fontsize=12)
            ax.set_ylabel('Y Value', fontsize=12)
            
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            filename = f"scatter_{title.replace(' ', '_').lower()}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error creating scatter plot: {e}")
            return None
    
    def extract_data_points(self, sources: List[Dict], topic: str) -> List[Dict]:
        """Extract data points from sources for visualization."""
        data_points = []
        
        for source in sources:
            # Extract numerical data if available
            text = source.get('text', source.get('summary', ''))
            
            # Look for percentages, numbers, statistics
            import re
            numbers = re.findall(r'\d+\.?\d*%?', text)
            
            if numbers:
                data_points.append({
                    'source': source.get('title', 'Unknown'),
                    'numbers': numbers,
                    'context': text[:200]
                })
        
        return data_points
    
    def generate_fallback_content(self, topic: str) -> Dict[str, Any]:
        """Generate fallback content when LLM fails."""
        return {
            "headline": f"Latest Insights on {topic}",
            "introduction": f"Exploring the latest developments in {topic} and their implications for the industry.",
            "main_points": [
                f"Current trends in {topic} are shaping the future",
                f"Key players are investing heavily in {topic} technologies",
                f"Market adoption of {topic} solutions is accelerating"
            ],
            "takeaways": [
                f"{topic} is becoming increasingly important",
                "Organizations need to adapt to these changes",
                "Early adoption provides competitive advantages"
            ],
            "conclusion": f"Stay informed about {topic} developments to remain competitive in the market.",
            "hashtags": [f"#{topic.replace(' ', '')}", "#Technology", "#Innovation", "#BusinessStrategy"]
        }
    
    def generate_fallback_slide_content(self, topic: str) -> Dict[str, Any]:
        """Generate fallback slide content."""
        return {
            "title_slide": {
                "title": f"{topic} Update",
                "subtitle": "Latest trends and insights"
            },
            "slides": [
                {
                    "title": "Current State",
                    "content": [
                        f"{topic} is rapidly evolving",
                        "Market adoption is increasing",
                        "New technologies emerging"
                    ],
                    "key_stat": "Growing at 25% annually"
                },
                {
                    "title": "Key Trends",
                    "content": [
                        "Innovation in core technologies",
                        "Integration with existing systems",
                        "Focus on user experience"
                    ]
                },
                {
                    "title": "Future Outlook",
                    "content": [
                        "Continued growth expected",
                        "New applications emerging",
                        "Market consolidation likely"
                    ]
                }
            ],
            "conclusion_slide": {
                "title": "Key Takeaways",
                "content": [
                    f"{topic} is transforming industries",
                    "Early adoption provides advantages",
                    "Continuous learning is essential"
                ]
            },
            "hashtags": [f"#{topic.replace(' ', '')}", "#TechTrends", "#Innovation"]
        }
    
    def generate_fallback_graph_content(self, topic: str) -> Dict[str, Any]:
        """Generate fallback graph content."""
        return {
            "visualizations": [
                {
                    "type": "bar_chart",
                    "title": f"{topic} Adoption Rates",
                    "description": "Shows adoption rates across different sectors",
                    "data_structure": "Sectors and adoption percentages"
                },
                {
                    "type": "line_chart",
                    "title": f"{topic} Growth Trend",
                    "description": "Growth trend over time",
                    "data_structure": "Time series data"
                },
                {
                    "type": "pie_chart",
                    "title": f"{topic} Market Share",
                    "description": "Market share distribution",
                    "data_structure": "Categories and percentages"
                }
            ],
            "insights": [
                f"{topic} adoption is accelerating",
                "Market leaders are emerging",
                "Investment is increasing significantly"
            ],
            "hashtags": [f"#{topic.replace(' ', '')}", "#DataVisualization", "#MarketTrends"]
        }