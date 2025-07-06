#!/usr/bin/env python3
"""
LinkedIn Automation System
Automated content generation and posting for LinkedIn
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime
from typing import Optional
import argparse

from config.settings import settings
from src.scheduler import LinkedInScheduler
from src.content_generator import ContentGenerator
from src.linkedin_api import LinkedInAPI
from src.mcp_client import MCPClient
from src.web_scraper import WebScraper

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.logging.file),
            logging.StreamHandler(sys.stdout)
        ]
    )

class LinkedInAutomationApp:
    """Main application class for LinkedIn automation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler = LinkedInScheduler()
        self.running = False
        
    async def initialize(self):
        """Initialize the application"""
        try:
            self.logger.info("Initializing LinkedIn Automation System...")
            
            # Validate configuration
            errors = settings.validate()
            if errors:
                self.logger.error("Configuration validation failed:")
                for error in errors:
                    self.logger.error(f"  - {error}")
                return False
            
            # Test connections
            if not await self.test_connections():
                return False
            
            self.logger.info("LinkedIn Automation System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            return False
    
    async def test_connections(self) -> bool:
        """Test all external connections"""
        try:
            self.logger.info("Testing connections...")
            
            # Test LinkedIn API
            linkedin_api = LinkedInAPI()
            if not await linkedin_api.test_connection():
                self.logger.error("LinkedIn API connection failed")
                return False
            self.logger.info("✓ LinkedIn API connection successful")
            
            # Test LLM connection
            try:
                from src.llm_client import LLMClient
                llm_client = LLMClient()
                async with llm_client:
                    test_response = await llm_client.generate_content("Test prompt", "Test system prompt")
                    if test_response.content:
                        self.logger.info("✓ LLM connection successful")
                    else:
                        self.logger.warning("LLM connection test returned empty response")
            except Exception as e:
                self.logger.warning(f"LLM connection test failed: {e}")
            
            # Test MCP Server (optional)
            try:
                mcp_client = MCPClient()
                async with mcp_client:
                    contexts = await mcp_client.search_contexts("test")
                    self.logger.info("✓ MCP Server connection successful")
            except Exception as e:
                self.logger.warning(f"MCP Server connection failed (optional): {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error testing connections: {e}")
            return False
    
    async def start(self):
        """Start the automation system"""
        try:
            self.logger.info("Starting LinkedIn Automation System...")
            
            # Start the scheduler
            await self.scheduler.start()
            self.running = True
            
            self.logger.info("LinkedIn Automation System started successfully")
            self.logger.info(f"System will post content about '{settings.content.topic}' every 24 hours")
            
            # Print scheduled jobs
            jobs = self.scheduler.get_scheduled_jobs()
            if jobs:
                self.logger.info("Scheduled jobs:")
                for job in jobs:
                    self.logger.info(f"  - {job['name']}: {job.get('next_run', 'No next run time')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting system: {e}")
            return False
    
    async def stop(self):
        """Stop the automation system"""
        try:
            self.logger.info("Stopping LinkedIn Automation System...")
            
            if self.running:
                await self.scheduler.stop()
                self.running = False
            
            self.logger.info("LinkedIn Automation System stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping system: {e}")
    
    async def run_once(self, topic: Optional[str] = None):
        """Run content generation and posting once"""
        try:
            target_topic = topic or settings.content.topic
            self.logger.info(f"Running one-time content generation for topic: {target_topic}")
            
            # Generate and post content
            await self.scheduler.generate_and_post_content(target_topic)
            
            self.logger.info("One-time content generation completed")
            
        except Exception as e:
            self.logger.error(f"Error in one-time run: {e}")
    
    async def add_topic(self, topic: str, schedule: str):
        """Add a new topic to schedule"""
        try:
            job_id = await self.scheduler.schedule_daily_posting(topic, schedule)
            self.logger.info(f"Added new topic '{topic}' with schedule '{schedule}' (Job ID: {job_id})")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error adding topic: {e}")
            return None
    
    async def remove_topic(self, job_id: str):
        """Remove a scheduled topic"""
        try:
            success = await self.scheduler.remove_job(job_id)
            if success:
                self.logger.info(f"Removed topic with job ID: {job_id}")
            else:
                self.logger.error(f"Failed to remove topic with job ID: {job_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error removing topic: {e}")
            return False
    
    async def list_jobs(self):
        """List all scheduled jobs"""
        try:
            jobs = self.scheduler.get_scheduled_jobs()
            if jobs:
                self.logger.info("Scheduled jobs:")
                for job in jobs:
                    self.logger.info(f"  ID: {job['id']}")
                    self.logger.info(f"  Name: {job['name']}")
                    self.logger.info(f"  Next Run: {job.get('next_run', 'No next run time')}")
                    self.logger.info(f"  Trigger: {job['trigger']}")
                    self.logger.info("  ---")
            else:
                self.logger.info("No scheduled jobs found")
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error listing jobs: {e}")
            return []
    
    async def get_status(self):
        """Get system status"""
        try:
            status = {
                "running": self.running,
                "scheduler_running": self.scheduler.is_running(),
                "current_time": datetime.now().isoformat(),
                "topic": settings.content.topic,
                "schedule": settings.content.posting_schedule,
                "jobs_count": len(self.scheduler.get_scheduled_jobs())
            }
            
            # Get next run times
            next_runs = await self.scheduler.get_next_run_times(24)
            status["next_runs"] = next_runs
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"error": str(e)}
    
    def is_running(self) -> bool:
        """Check if the system is running"""
        return self.running and self.scheduler.is_running()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LinkedIn Automation System")
    parser.add_argument("--run-once", action="store_true", help="Run content generation once and exit")
    parser.add_argument("--topic", type=str, help="Topic for content generation")
    parser.add_argument("--schedule", type=str, help="Schedule for content posting (cron format)")
    parser.add_argument("--add-topic", action="store_true", help="Add a new topic to schedule")
    parser.add_argument("--list-jobs", action="store_true", help="List all scheduled jobs")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--status", action="store_true", help="Show system status")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Create application instance
    app = LinkedInAutomationApp()
    
    # Initialize the application
    if not await app.initialize():
        sys.exit(1)
    
    # Handle different modes
    try:
        if args.run_once:
            await app.run_once(args.topic)
        elif args.add_topic:
            if not args.topic or not args.schedule:
                print("Error: --topic and --schedule are required when adding a topic")
                sys.exit(1)
            await app.add_topic(args.topic, args.schedule)
        elif args.list_jobs:
            await app.list_jobs()
        elif args.status:
            status = await app.get_status()
            print(f"System Status: {status}")
        else:
            # Run as daemon
            if not await app.start():
                sys.exit(1)
            
            # Setup signal handlers
            def signal_handler(signum, frame):
                print(f"\nReceived signal {signum}. Shutting down...")
                asyncio.create_task(app.stop())
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Keep the application running
            try:
                while app.is_running():
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
                await app.stop()
                
    except Exception as e:
        logging.error(f"Error in main: {e}")
        await app.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())