#!/usr/bin/env python3
"""
Setup script for LinkedIn Automation System.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is adequate."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    return True

def setup_environment_file():
    """Set up environment file."""
    print("🔧 Setting up environment configuration...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    if env_file.exists():
        response = input("📝 .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("⏭️  Skipping environment file setup")
            return True
    
    # Copy example to actual env file
    shutil.copy(env_example, env_file)
    print("✅ Created .env file from template")
    print("📝 Please edit .env file with your actual credentials")
    
    return True

def check_chrome_installation():
    """Check if Chrome is installed."""
    print("🔍 Checking Chrome installation...")
    
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable", 
        "/usr/bin/chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome found at: {path}")
            return True
    
    # Check if chrome is in PATH
    if shutil.which("google-chrome") or shutil.which("chrome") or shutil.which("chromium-browser"):
        print("✅ Chrome found in PATH")
        return True
    
    print("⚠️  Chrome not found. Please install Google Chrome for web scraping functionality")
    print("   The system will attempt to download ChromeDriver automatically")
    return False

def create_directories():
    """Create necessary directories."""
    print("📁 Creating necessary directories...")
    
    directories = ["logs", "output", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def test_installation():
    """Test the installation."""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        print("   Testing module imports...")
        import config
        import logger
        import web_scraper
        import content_generator
        import linkedin_poster
        import mcp_client
        import scheduler
        
        print("✅ All modules imported successfully")
        
        # Test configuration
        print("   Testing configuration...")
        from config import config
        print("✅ Configuration loaded successfully")
        
        print("🎉 Installation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user."""
    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETED!")
    print("="*60)
    print()
    print("📋 NEXT STEPS:")
    print()
    print("1. 🔑 Get LinkedIn API credentials:")
    print("   - Go to https://developer.linkedin.com/")
    print("   - Create a new app")
    print("   - Request access to LinkedIn Share API")
    print("   - Get your Client ID, Client Secret, and Access Token")
    print()
    print("2. ✏️  Edit the .env file with your credentials:")
    print("   nano .env")
    print()
    print("3. 🧪 Test the configuration:")
    print("   python main.py --config-check")
    print()
    print("4. 🔍 Test all components:")
    print("   python main.py --test-components")
    print()
    print("5. 🚀 Run your first post:")
    print("   python main.py --run-once")
    print()
    print("6. ⏰ Set up automation:")
    print("   python main.py --setup-cron")
    print()
    print("📚 For more information, see README.md")
    print()

def main():
    """Main setup function."""
    print("🚀 LinkedIn Automation System Setup")
    print("="*60)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Set up environment file
    if not setup_environment_file():
        sys.exit(1)
    
    # Check Chrome installation
    check_chrome_installation()
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("⚠️  Installation test failed, but you can try to continue")
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()