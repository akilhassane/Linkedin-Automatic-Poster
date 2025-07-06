import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import json
import os

from src.content_generator import ContentGenerator
from src.linkedin_api import LinkedInAPI
from src.mcp_client import MCPClient
from config.settings import settings

@dataclass
class ScheduledJob:
    """Structure for scheduled job information"""
    job_id: str
    topic: str
    schedule: str
    next_run: datetime
    last_run: Optional[datetime] = None
    status: str = "active"

class LinkedInScheduler:
    """Scheduler for automated LinkedIn posting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler = AsyncIOScheduler()
        self.content_generator = ContentGenerator()
        self.linkedin_api = LinkedInAPI()
        self.mcp_client = MCPClient()
        self.jobs_file = "data/scheduled_jobs.json"
        self.running = False
        
    async def start(self):
        """Start the scheduler"""
        try:
            self.logger.info("Starting LinkedIn automation scheduler...")
            
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Load existing jobs
            await self.load_scheduled_jobs()
            
            # Add default job if none exist
            if not self.scheduler.get_jobs():
                await self.schedule_daily_posting(
                    topic=settings.content.topic,
                    schedule=settings.content.posting_schedule
                )
            
            # Start the scheduler
            self.scheduler.start()
            self.running = True
            
            self.logger.info("LinkedIn automation scheduler started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        try:
            self.logger.info("Stopping LinkedIn automation scheduler...")
            
            if self.running:
                self.scheduler.shutdown()
                self.running = False
                
                # Save job states
                await self.save_scheduled_jobs()
                
            self.logger.info("LinkedIn automation scheduler stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    async def schedule_daily_posting(self, topic: str, schedule: str) -> str:
        """Schedule daily posting for a topic"""
        try:
            job_id = f"daily_post_{topic.replace(' ', '_')}"
            
            # Parse cron schedule
            cron_parts = schedule.split()
            if len(cron_parts) != 5:
                raise ValueError("Invalid cron schedule format")
            
            minute, hour, day, month, day_of_week = cron_parts
            
            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Schedule the job
            self.scheduler.add_job(
                self.generate_and_post_content,
                trigger=trigger,
                id=job_id,
                args=[topic],
                replace_existing=True,
                name=f"Daily LinkedIn Post - {topic}"
            )
            
            self.logger.info(f"Scheduled daily posting for topic '{topic}' with schedule '{schedule}'")
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error scheduling daily posting: {e}")
            raise
    
    async def schedule_interval_posting(self, topic: str, interval_hours: int = 24) -> str:
        """Schedule interval-based posting"""
        try:
            job_id = f"interval_post_{topic.replace(' ', '_')}"
            
            # Create interval trigger
            trigger = IntervalTrigger(hours=interval_hours)
            
            # Schedule the job
            self.scheduler.add_job(
                self.generate_and_post_content,
                trigger=trigger,
                id=job_id,
                args=[topic],
                replace_existing=True,
                name=f"Interval LinkedIn Post - {topic}"
            )
            
            self.logger.info(f"Scheduled interval posting for topic '{topic}' every {interval_hours} hours")
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error scheduling interval posting: {e}")
            raise
    
    async def generate_and_post_content(self, topic: str):
        """Generate and post content for a topic"""
        try:
            self.logger.info(f"Starting content generation and posting for topic: {topic}")
            
            # Check LinkedIn API connection
            if not await self.linkedin_api.test_connection():
                self.logger.error("LinkedIn API connection failed")
                return
            
            # Generate content
            content, comment = await self.content_generator.generate_content_with_comment(topic)
            
            # Post content based on type
            if content.content_type == "article":
                response = await self.linkedin_api.create_article_post(
                    title=content.title,
                    content=content.content
                )
            elif content.image_data:
                response = await self.linkedin_api.create_image_post(
                    content=content.content,
                    image_data=content.image_data,
                    image_name=content.image_name or f"{topic}_image.png"
                )
            else:
                response = await self.linkedin_api.create_text_post(
                    content=content.content
                )
            
            # Log results
            if response.success:
                self.logger.info(f"Successfully posted content: {response.post_id}")
                
                # Store content history in MCP
                try:
                    await self.mcp_client.store_content_history(
                        content_type=content.content_type,
                        content=content.content,
                        metadata={
                            "topic": topic,
                            "post_id": response.post_id,
                            "title": content.title,
                            "comment": comment,
                            "generation_metadata": content.metadata
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to store content history: {e}")
                
            else:
                self.logger.error(f"Failed to post content: {response.message}")
                
        except Exception as e:
            self.logger.error(f"Error in generate_and_post_content: {e}")
    
    async def add_one_time_job(self, topic: str, run_time: datetime) -> str:
        """Add a one-time job to run at specific time"""
        try:
            job_id = f"onetime_{topic.replace(' ', '_')}_{run_time.strftime('%Y%m%d_%H%M%S')}"
            
            self.scheduler.add_job(
                self.generate_and_post_content,
                trigger='date',
                run_date=run_time,
                id=job_id,
                args=[topic],
                name=f"One-time LinkedIn Post - {topic}"
            )
            
            self.logger.info(f"Scheduled one-time posting for topic '{topic}' at {run_time}")
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error scheduling one-time job: {e}")
            raise
    
    async def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed scheduled job: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing job {job_id}: {e}")
            return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        try:
            self.scheduler.pause_job(job_id)
            self.logger.info(f"Paused scheduled job: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            self.logger.info(f"Resumed scheduled job: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming job {job_id}: {e}")
            return False
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                    "args": job.args,
                    "kwargs": job.kwargs
                }
                jobs.append(job_info)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error getting scheduled jobs: {e}")
            return []
    
    async def load_scheduled_jobs(self):
        """Load scheduled jobs from file"""
        try:
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                
                for job_data in jobs_data:
                    try:
                        await self.schedule_daily_posting(
                            topic=job_data['topic'],
                            schedule=job_data['schedule']
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to restore job {job_data.get('job_id', 'unknown')}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error loading scheduled jobs: {e}")
    
    async def save_scheduled_jobs(self):
        """Save scheduled jobs to file"""
        try:
            jobs_data = []
            for job in self.scheduler.get_jobs():
                if job.args and len(job.args) > 0:
                    job_data = {
                        "job_id": job.id,
                        "topic": job.args[0],
                        "schedule": str(job.trigger),
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                        "name": job.name
                    }
                    jobs_data.append(job_data)
            
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving scheduled jobs: {e}")
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                    "args": job.args,
                    "kwargs": job.kwargs
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting job status for {job_id}: {e}")
            return None
    
    async def run_job_now(self, job_id: str):
        """Run a specific job immediately"""
        try:
            job = self.scheduler.get_job(job_id)
            if job and job.args:
                topic = job.args[0]
                await self.generate_and_post_content(topic)
                self.logger.info(f"Manually executed job: {job_id}")
            else:
                self.logger.error(f"Job not found or invalid: {job_id}")
                
        except Exception as e:
            self.logger.error(f"Error running job {job_id}: {e}")
    
    async def update_job_schedule(self, job_id: str, new_schedule: str):
        """Update the schedule of an existing job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job and job.args:
                topic = job.args[0]
                
                # Remove old job
                self.scheduler.remove_job(job_id)
                
                # Add new job with updated schedule
                await self.schedule_daily_posting(topic, new_schedule)
                
                self.logger.info(f"Updated schedule for job {job_id}")
                
        except Exception as e:
            self.logger.error(f"Error updating job schedule {job_id}: {e}")
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.running and self.scheduler.running
    
    async def get_next_run_times(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get next run times for all jobs within specified hours"""
        try:
            next_runs = []
            cutoff_time = datetime.now() + timedelta(hours=hours)
            
            for job in self.scheduler.get_jobs():
                if job.next_run_time and job.next_run_time <= cutoff_time:
                    next_runs.append({
                        "job_id": job.id,
                        "job_name": job.name,
                        "topic": job.args[0] if job.args else "Unknown",
                        "next_run": job.next_run_time.isoformat(),
                        "time_until_run": str(job.next_run_time - datetime.now())
                    })
            
            return sorted(next_runs, key=lambda x: x["next_run"])
            
        except Exception as e:
            self.logger.error(f"Error getting next run times: {e}")
            return []