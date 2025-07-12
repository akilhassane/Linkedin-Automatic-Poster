#!/usr/bin/env python3
"""
Main entry point for LinkedIn automation system.
"""

import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any
from config import config
from logger import logger
from scheduler import LinkedInScheduler
from web_scraper import WebScraper
from content_generator import ContentGenerator
from linkedin_poster import LinkedInPoster
from mcp_client import MCPClient

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LinkedIn Automation System")
    parser.add_argument(
        "--run-once", 
        action="store_true", 
        help="Run the posting job once and exit"
    )
    parser.add_argument(
        "--daemon", 
        action="store_true", 
        help="Run as daemon (background scheduler)"
    )
    parser.add_argument(
        "--setup-cron", 
        action="store_true", 
        help="Set up cron job for automated posting"
    )
    parser.add_argument(
        "--test-components", 
        action="store_true", 
        help="Test all system components"
    )
    parser.add_argument(
        "--config-check", 
        action="store_true", 
        help="Check configuration and credentials"
    )
    parser.add_argument(
        "--topic", 
        type=str, 
        help="Override the current topic"
    )
    parser.add_argument(
        "--content-type", 
        choices=["article", "slide", "graph"], 
        help="Override the content type"
    )
    parser.add_argument(
        "--frequency", 
        type=int, 
        help="Set posting frequency in hours"
    )
    parser.add_argument(
        "--add-topic", 
        type=str, 
        help="Add a new topic to the rotation"
    )
    parser.add_argument(
        "--remove-topic", 
        type=str, 
        help="Remove a topic from the rotation"
    )
    parser.add_argument(
        "--list-topics", 
        action="store_true", 
        help="List all available topics"
    )
    parser.add_argument(
        "--status", 
        action="store_true", 
        help="Show system status"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        config.set("logging.level", "DEBUG")
        logger.setup_logging()
    
    # Initialize system
    system = LinkedInAutomationSystem()
    
    try:
        # Handle different command-line options
        if args.config_check:
            return system.check_configuration()
        
        elif args.test_components:
            return system.test_all_components()
        
        elif args.setup_cron:
            return system.setup_cron_job()
        
        elif args.list_topics:
            return system.list_topics()
        
        elif args.status:
            return system.show_status()
        
        elif args.add_topic:
            return system.add_topic(args.add_topic)
        
        elif args.remove_topic:
            return system.remove_topic(args.remove_topic)
        
        elif args.frequency:
            return system.update_frequency(args.frequency)
        
        elif args.run_once:
            return system.run_once(args.topic, args.content_type)
        
        elif args.daemon:
            return system.run_daemon()
        
        else:
            # Default behavior: run interactive mode
            return system.run_interactive()
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

class LinkedInAutomationSystem:
    """Main system class for LinkedIn automation."""
    
    def __init__(self):
        self.logger = logger.get_logger("main")
        self.scheduler = LinkedInScheduler()
        self.web_scraper = WebScraper()
        self.content_generator = ContentGenerator()
        self.linkedin_poster = LinkedInPoster()
        self.mcp_client = MCPClient()
    
    def check_configuration(self) -> int:
        """Check system configuration and credentials."""
        self.logger.info("Checking system configuration...")
        
        # Check required configuration
        if not config.validate_required_keys():
            self.logger.error("Configuration validation failed")
            return 1
        
        # Check LinkedIn credentials
        if not self.linkedin_poster.validate_credentials():
            self.logger.error("LinkedIn credentials validation failed")
            return 1
        
        # Test MCP connection
        if not self.mcp_client.test_connection():
            self.logger.warning("MCP server connection failed (will use fallback)")
        
        self.logger.info("Configuration check completed successfully")
        return 0
    
    def test_all_components(self) -> int:
        """Test all system components."""
        self.logger.info("Testing all system components...")
        
        tests_passed = 0
        total_tests = 4
        
        # Test 1: Configuration
        if config.validate_required_keys():
            self.logger.info("✓ Configuration test passed")
            tests_passed += 1
        else:
            self.logger.error("✗ Configuration test failed")
        
        # Test 2: LinkedIn API
        if self.linkedin_poster.validate_credentials():
            self.logger.info("✓ LinkedIn API test passed")
            tests_passed += 1
        else:
            self.logger.error("✗ LinkedIn API test failed")
        
        # Test 3: Web scraping
        try:
            sources = self.web_scraper.gather_information("test topic", 1)
            self.logger.info("✓ Web scraping test passed")
            tests_passed += 1
        except Exception as e:
            self.logger.error(f"✗ Web scraping test failed: {e}")
        
        # Test 4: MCP client
        if self.mcp_client.test_connection():
            self.logger.info("✓ MCP client test passed")
            tests_passed += 1
        else:
            self.logger.warning("✗ MCP client test failed (will use fallback)")
        
        self.logger.info(f"Tests passed: {tests_passed}/{total_tests}")
        return 0 if tests_passed >= 3 else 1  # Allow MCP to fail
    
    def setup_cron_job(self) -> int:
        """Set up cron job for automated posting."""
        self.logger.info("Setting up cron job...")
        
        if self.scheduler.setup_cron_job():
            self.logger.info("Cron job set up successfully")
            return 0
        else:
            self.logger.error("Failed to set up cron job")
            return 1
    
    def list_topics(self) -> int:
        """List all available topics."""
        topics = config.get("content.topics", [])
        current_topic = config.get("content.current_topic", "")
        
        print("Available topics:")
        for i, topic in enumerate(topics, 1):
            marker = "★" if topic == current_topic else " "
            print(f"{marker} {i}. {topic}")
        
        return 0
    
    def show_status(self) -> int:
        """Show system status."""
        status = self.scheduler.get_status()
        
        print("LinkedIn Automation System Status:")
        print(f"Running: {status['running']}")
        print(f"Next run: {status['next_run']}")
        print(f"Current topic: {status['current_topic']}")
        print(f"Current content type: {status['current_content_type']}")
        print(f"Post frequency: {status['post_frequency']} hours")
        print(f"Topics: {', '.join(status['topics'])}")
        print(f"Content types: {', '.join(status['content_types'])}")
        
        return 0
    
    def add_topic(self, topic: str) -> int:
        """Add a new topic."""
        self.scheduler.add_topic(topic)
        self.logger.info(f"Added topic: {topic}")
        return 0
    
    def remove_topic(self, topic: str) -> int:
        """Remove a topic."""
        self.scheduler.remove_topic(topic)
        self.logger.info(f"Removed topic: {topic}")
        return 0
    
    def update_frequency(self, frequency: int) -> int:
        """Update posting frequency."""
        self.scheduler.update_schedule(frequency)
        self.logger.info(f"Updated frequency to {frequency} hours")
        return 0
    
    def run_once(self, topic: str | None = None, content_type: str | None = None) -> int:
        """Run the posting job once."""
        self.logger.info("Running posting job once...")
        
        # Override topic if provided
        if topic:
            self.scheduler.set_current_topic(topic)
        
        # Override content type if provided
        if content_type:
            # Temporarily set content type
            original_types = self.scheduler.content_types.copy()
            self.scheduler.content_types = [content_type]
            self.scheduler.content_type_index = 0
        
        # Run the job
        success = self.scheduler.run_once()
        
        # Restore original content types if overridden
        if content_type:
            self.scheduler.content_types = original_types
        
        return 0 if success else 1
    
    def run_daemon(self) -> int:
        """Run as daemon (background scheduler)."""
        self.logger.info("Starting daemon mode...")
        
        try:
            self.scheduler.start_scheduler()
            return 0
        except Exception as e:
            self.logger.error(f"Daemon mode failed: {e}")
            return 1
    
    def run_interactive(self) -> int:
        """Run interactive mode."""
        print("LinkedIn Automation System")
        print("==========================")
        print()
        print("Available commands:")
        print("1. Run posting job once")
        print("2. Start daemon mode")
        print("3. Check configuration")
        print("4. Test components")
        print("5. Show status")
        print("6. List topics")
        print("7. Add topic")
        print("8. Remove topic")
        print("9. Update frequency")
        print("10. Set up cron job")
        print("0. Exit")
        print()
        
        while True:
            try:
                choice = input("Enter your choice (0-10): ").strip()
                
                if choice == "0":
                    print("Goodbye!")
                    return 0
                
                elif choice == "1":
                    topic = input("Enter topic (or press Enter for current): ").strip()
                    content_type = input("Enter content type (article/slide/graph or press Enter for current): ").strip()
                    
                    self.run_once(
                        topic if topic else None,
                        content_type if content_type else None
                    )
                
                elif choice == "2":
                    print("Starting daemon mode... (Press Ctrl+C to stop)")
                    return self.run_daemon()
                
                elif choice == "3":
                    self.check_configuration()
                
                elif choice == "4":
                    self.test_all_components()
                
                elif choice == "5":
                    self.show_status()
                
                elif choice == "6":
                    self.list_topics()
                
                elif choice == "7":
                    topic = input("Enter new topic: ").strip()
                    if topic:
                        self.add_topic(topic)
                
                elif choice == "8":
                    topic = input("Enter topic to remove: ").strip()
                    if topic:
                        self.remove_topic(topic)
                
                elif choice == "9":
                    try:
                        frequency = int(input("Enter frequency in hours: ").strip())
                        self.update_frequency(frequency)
                    except ValueError:
                        print("Invalid frequency. Please enter a number.")
                
                elif choice == "10":
                    self.setup_cron_job()
                
                else:
                    print("Invalid choice. Please enter a number between 0 and 10.")
                
                print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                return 0
            except EOFError:
                print("\nGoodbye!")
                return 0
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    sys.exit(main())