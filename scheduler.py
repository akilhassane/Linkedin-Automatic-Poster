"""
Scheduler for automated LinkedIn posting every 24 hours.
"""

import schedule
import time
import random
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from crontab import CronTab
import threading
import signal
import sys
from config import config
from logger import logger
from web_scraper import WebScraper
from content_generator import ContentGenerator
from linkedin_poster import LinkedInPoster
from mcp_client import MCPClient

class LinkedInScheduler:
    """Scheduler for automated LinkedIn content posting."""
    
    def __init__(self):
        self.logger = logger.get_logger("scheduler")
        self.config = config
        self.running = False
        self.current_job = None
        
        # Initialize components
        self.web_scraper = WebScraper()
        self.content_generator = ContentGenerator()
        self.linkedin_poster = LinkedInPoster()
        self.mcp_client = MCPClient()
        
        # Scheduling configuration
        self.post_frequency = config.get("content.post_frequency", 24)  # hours
        self.current_topic = config.get("content.current_topic", "artificial intelligence")
        self.content_types = config.get("content.content_types", ["article", "slide", "graph"])
        self.max_sources = config.get("content.max_sources", 5)
        
        # Content rotation
        self.content_type_index = 0
        self.topic_index = 0
        self.topics = config.get("content.topics", ["artificial intelligence", "machine learning", "technology trends"])
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info("Shutdown signal received, stopping scheduler...")
        self.stop()
        sys.exit(0)
    
    def setup_cron_job(self) -> bool:
        """Set up cron job for automated posting."""
        try:
            # Create cron job
            cron = CronTab(user=True)
            
            # Remove existing jobs for this script
            cron.remove_all(comment='linkedin_automation')
            
            # Add new job (run every 24 hours at a random time between 9 AM and 5 PM)
            random_hour = random.randint(9, 17)
            random_minute = random.randint(0, 59)
            
            job = cron.new(command=f'cd {os.getcwd()} && python main.py --run-once', comment='linkedin_automation')
            job.setall(f"{random_minute} {random_hour} * * *")
            
            # Write cron job
            cron.write()
            
            self.logger.info(f"Cron job set up to run daily at {random_hour:02d}:{random_minute:02d}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up cron job: {e}")
            return False
    
    def start_scheduler(self):
        """Start the scheduler."""
        self.logger.info("Starting LinkedIn automation scheduler...")
        self.running = True
        
        # Validate LinkedIn credentials
        if not self.linkedin_poster.validate_credentials():
            self.logger.error("LinkedIn credentials validation failed. Please check your configuration.")
            return
        
        # Test MCP connection
        if not self.mcp_client.test_connection():
            self.logger.warning("MCP server connection failed. Will use fallback content generation.")
        
        # Schedule the job
        # Run every 24 hours with some randomization to avoid detection
        random_minutes = random.randint(0, 59)
        schedule.every(self.post_frequency).hours.at(f":{random_minutes:02d}").do(self.run_posting_job)
        
        # Also schedule a job to run soon after startup (for testing)
        schedule.every(1).minutes.do(self.run_posting_job).tag('startup')
        
        self.logger.info(f"Scheduler started. Next post will be in {self.post_frequency} hours.")
        
        # Run the scheduler
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received, stopping scheduler...")
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait before continuing
        
        self.logger.info("Scheduler stopped.")
    
    def run_posting_job(self):
        """Run the main posting job."""
        self.logger.info("Starting automated posting job...")
        
        try:
            # Clear startup jobs after first run
            schedule.clear('startup')
            
            # Get current topic and content type
            current_topic = self.get_current_topic()
            content_type = self.get_current_content_type()
            
            self.logger.info(f"Creating {content_type} content about {current_topic}")
            
            # Step 1: Gather information
            self.logger.info("Gathering information from web sources...")
            sources = self.web_scraper.gather_information(current_topic, self.max_sources)
            
            if not sources:
                self.logger.warning("No sources found. Using fallback content generation.")
                sources = []
            
            # Step 2: Generate content based on type
            if content_type == "article":
                result = self.create_and_post_article(current_topic, sources)
            elif content_type == "slide":
                result = self.create_and_post_slides(current_topic, sources)
            elif content_type == "graph":
                result = self.create_and_post_graph(current_topic, sources)
            else:
                self.logger.error(f"Unknown content type: {content_type}")
                return
            
            # Step 3: Log results
            if result.get("success"):
                self.logger.info(f"Successfully posted {content_type} content about {current_topic}")
                
                # Update rotation indices
                self.rotate_content_type()
                
                # Occasionally rotate topic
                if random.random() < 0.3:  # 30% chance to rotate topic
                    self.rotate_topic()
                
            else:
                self.logger.error(f"Failed to post {content_type} content: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            self.logger.error(f"Error in posting job: {e}")
    
    def create_and_post_article(self, topic: str, sources: List[Dict]) -> Dict[str, Any]:
        """Create and post an article."""
        try:
            # Generate article content
            article_content = self.content_generator.generate_article_content(sources, topic)
            
            # Enhance with MCP if available
            enhanced_content = self.mcp_client.enhance_content_with_context(
                str(article_content), topic, sources
            )
            
            if enhanced_content.get("enhanced_content"):
                # Update content with enhanced version
                article_content["introduction"] = enhanced_content["enhanced_content"]
            
            # Generate additional hashtags using MCP
            mcp_hashtags = self.mcp_client.generate_hashtags(
                article_content.get("introduction", ""), topic
            )
            
            # Merge hashtags
            all_hashtags = list(set(article_content.get("hashtags", []) + mcp_hashtags))
            article_content["hashtags"] = all_hashtags[:10]  # Limit to 10 hashtags
            
            # Post to LinkedIn
            return self.linkedin_poster.post_article(article_content)
            
        except Exception as e:
            self.logger.error(f"Error creating article: {e}")
            return {"success": False, "error": str(e)}
    
    def create_and_post_slides(self, topic: str, sources: List[Dict]) -> Dict[str, Any]:
        """Create and post a slide carousel."""
        try:
            # Generate slide content
            slide_content = self.content_generator.generate_slide_content(sources, topic)
            
            # Create visual slides
            slide_images = []
            
            # Create title slide
            title_slide_image = self.content_generator.create_visual_slide(
                slide_content.get("title_slide", {}), 0
            )
            if title_slide_image:
                slide_images.append(title_slide_image)
            
            # Create content slides
            for i, slide in enumerate(slide_content.get("slides", []), 1):
                slide_image = self.content_generator.create_visual_slide(slide, i)
                if slide_image:
                    slide_images.append(slide_image)
            
            # Create conclusion slide
            conclusion_slide_image = self.content_generator.create_visual_slide(
                slide_content.get("conclusion_slide", {}), len(slide_content.get("slides", [])) + 1
            )
            if conclusion_slide_image:
                slide_images.append(conclusion_slide_image)
            
            if not slide_images:
                return {"success": False, "error": "Failed to create slide images"}
            
            # Post carousel to LinkedIn
            return self.linkedin_poster.post_carousel(slide_content, slide_images)
            
        except Exception as e:
            self.logger.error(f"Error creating slides: {e}")
            return {"success": False, "error": str(e)}
    
    def create_and_post_graph(self, topic: str, sources: List[Dict]) -> Dict[str, Any]:
        """Create and post a graph/chart."""
        try:
            # Generate graph content
            graph_content = self.content_generator.generate_graph_content(sources, topic)
            
            # Get data points for visualization
            data_points = self.content_generator.extract_data_points(sources, topic)
            
            # Create visualization
            visualizations = graph_content.get("visualizations", [])
            if not visualizations:
                return {"success": False, "error": "No visualizations generated"}
            
            # Create the first visualization
            viz_data = visualizations[0]
            chart_image = self.content_generator.create_data_visualization(viz_data, data_points)
            
            if not chart_image:
                return {"success": False, "error": "Failed to create chart image"}
            
            # Enhance insights with MCP
            mcp_insights = self.mcp_client.generate_insights(sources, topic)
            all_insights = list(set(graph_content.get("insights", []) + mcp_insights))
            
            # Update graph content with enhanced insights
            graph_content["insights"] = all_insights[:5]  # Limit to 5 insights
            
            # Post graph to LinkedIn
            return self.linkedin_poster.post_graph(graph_content, chart_image)
            
        except Exception as e:
            self.logger.error(f"Error creating graph: {e}")
            return {"success": False, "error": str(e)}
    
    def get_current_topic(self) -> str:
        """Get the current topic for content creation."""
        if self.topic_index >= len(self.topics):
            self.topic_index = 0
        return self.topics[self.topic_index]
    
    def get_current_content_type(self) -> str:
        """Get the current content type for creation."""
        if self.content_type_index >= len(self.content_types):
            self.content_type_index = 0
        return self.content_types[self.content_type_index]
    
    def rotate_content_type(self):
        """Rotate to the next content type."""
        self.content_type_index = (self.content_type_index + 1) % len(self.content_types)
        self.logger.info(f"Rotated to content type: {self.get_current_content_type()}")
    
    def rotate_topic(self):
        """Rotate to the next topic."""
        self.topic_index = (self.topic_index + 1) % len(self.topics)
        new_topic = self.get_current_topic()
        self.logger.info(f"Rotated to topic: {new_topic}")
        
        # Update config
        config.set("content.current_topic", new_topic)
    
    def run_once(self):
        """Run the posting job once (for testing or manual execution)."""
        self.logger.info("Running posting job once...")
        
        # Validate credentials
        if not self.linkedin_poster.validate_credentials():
            self.logger.error("LinkedIn credentials validation failed")
            return False
        
        # Run the job
        self.run_posting_job()
        return True
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        self.logger.info("Scheduler stop requested")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self.running,
            "next_run": self.get_next_run_time(),
            "current_topic": self.get_current_topic(),
            "current_content_type": self.get_current_content_type(),
            "post_frequency": self.post_frequency,
            "topics": self.topics,
            "content_types": self.content_types
        }
    
    def update_schedule(self, frequency_hours: int):
        """Update the posting frequency."""
        self.post_frequency = frequency_hours
        config.set("content.post_frequency", frequency_hours)
        
        # Clear existing jobs and reschedule
        schedule.clear()
        random_minutes = random.randint(0, 59)
        schedule.every(frequency_hours).hours.at(f":{random_minutes:02d}").do(self.run_posting_job)
        
        self.logger.info(f"Updated posting frequency to {frequency_hours} hours")
    
    def add_topic(self, topic: str):
        """Add a new topic to the rotation."""
        if topic not in self.topics:
            self.topics.append(topic)
            config.set("content.topics", self.topics)
            self.logger.info(f"Added new topic: {topic}")
    
    def remove_topic(self, topic: str):
        """Remove a topic from the rotation."""
        if topic in self.topics and len(self.topics) > 1:
            self.topics.remove(topic)
            config.set("content.topics", self.topics)
            
            # Reset index if needed
            if self.topic_index >= len(self.topics):
                self.topic_index = 0
            
            self.logger.info(f"Removed topic: {topic}")
    
    def set_current_topic(self, topic: str):
        """Set the current topic."""
        if topic in self.topics:
            self.topic_index = self.topics.index(topic)
            config.set("content.current_topic", topic)
            self.logger.info(f"Set current topic to: {topic}")
    
    def run_in_background(self):
        """Run the scheduler in a background thread."""
        self.logger.info("Starting scheduler in background thread...")
        
        def run_scheduler():
            self.start_scheduler()
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread