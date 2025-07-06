# LinkedIn Automation System

A comprehensive system that automatically posts articles, slide carousels, and data visualizations to LinkedIn every 24 hours. The system gathers information from the web, synthesizes it using AI/LLM models, and posts diverse content types without human intervention.

## Features

- **Automated Content Creation**: Generates articles, slide presentations, and data visualizations
- **Web Scraping**: Gathers information from RSS feeds, Google News, Reddit, and GitHub
- **AI-Powered Content**: Uses OpenAI GPT or free alternatives for content synthesis
- **MCP Integration**: Leverages Model Context Protocol servers for enhanced content generation
- **Multiple Content Types**: 
  - Professional articles with insights and takeaways
  - Visual slide carousels with charts and statistics
  - Data visualizations (bar charts, line graphs, pie charts, scatter plots)
- **Scheduled Posting**: Runs every 24 hours with randomized timing
- **Topic Rotation**: Automatically rotates through different topics
- **LinkedIn API Integration**: Native LinkedIn posting with image uploads
- **Cron Job Support**: Can be set up as a system service
- **Interactive CLI**: Command-line interface for management and testing

## Prerequisites

- Python 3.8 or higher
- LinkedIn Developer Account and API credentials
- Chrome browser (for web scraping)
- Optional: OpenAI API key for enhanced content generation
- Optional: MCP server for advanced content processing

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd linkedin-automation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Chrome driver:**
   The system will automatically download and manage Chrome WebDriver through `webdriver-manager`.

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your actual credentials.

## LinkedIn API Setup

1. **Create a LinkedIn Developer Application:**
   - Go to [LinkedIn Developer Portal](https://developer.linkedin.com/)
   - Create a new app
   - Request access to the LinkedIn Share API
   - Note your Client ID and Client Secret

2. **Generate Access Token:**
   - Use LinkedIn's OAuth 2.0 flow to get an access token
   - The token should have `w_member_social` scope
   - Get your LinkedIn User ID from the profile API

3. **Configure credentials in `.env`:**
   ```bash
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_ACCESS_TOKEN=your_access_token
   LINKEDIN_USER_ID=your_user_id
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LINKEDIN_CLIENT_ID` | LinkedIn app client ID | Yes |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app client secret | Yes |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn access token | Yes |
| `LINKEDIN_USER_ID` | Your LinkedIn user ID | Yes |
| `OPENAI_API_KEY` | OpenAI API key for content generation | No |
| `HUGGINGFACE_API_KEY` | Hugging Face API key (free alternative) | No |
| `MCP_SERVER_URL` | MCP server URL | No |
| `MCP_API_KEY` | MCP server API key | No |

### Content Configuration

Edit `config.json` or use environment variables:

```json
{
  "content": {
    "topics": ["artificial intelligence", "machine learning", "blockchain"],
    "current_topic": "artificial intelligence",
    "post_frequency": 24,
    "content_types": ["article", "slide", "graph"],
    "max_sources": 5
  }
}
```

## Usage

### Command Line Interface

```bash
# Run once for testing
python main.py --run-once

# Run with specific topic
python main.py --run-once --topic "blockchain"

# Run with specific content type
python main.py --run-once --content-type "slide"

# Start daemon mode (runs continuously)
python main.py --daemon

# Set up cron job for automation
python main.py --setup-cron

# Check configuration
python main.py --config-check

# Test all components
python main.py --test-components

# Show system status
python main.py --status

# List available topics
python main.py --list-topics

# Add new topic
python main.py --add-topic "cybersecurity"

# Remove topic
python main.py --remove-topic "old-topic"

# Update posting frequency (in hours)
python main.py --frequency 12

# Interactive mode
python main.py
```

### Interactive Mode

Run `python main.py` to enter interactive mode with a menu-driven interface.

## Content Types

### 1. Articles
- Comprehensive LinkedIn articles with introduction, main points, and conclusion
- Generated from multiple web sources
- Includes relevant hashtags and call-to-action

### 2. Slide Carousels
- Visual presentations with multiple slides
- Title slide, content slides, and conclusion slide
- Professional formatting with charts and statistics

### 3. Data Visualizations
- Bar charts, line graphs, pie charts, and scatter plots
- Generated from extracted data points
- Includes insights and analysis

## Web Sources

The system gathers information from:
- **RSS Feeds**: TechCrunch, Wired, The Verge, Ars Technica, etc.
- **Google News**: Latest news articles
- **Reddit**: Technology-related subreddits
- **GitHub**: Trending repositories

## AI/LLM Integration

### OpenAI GPT (Recommended)
- High-quality content generation
- Requires API key (paid service)
- Best results for professional content

### Hugging Face (Free Alternative)
- Free inference API
- Good for basic content generation
- May have rate limits

### Fallback Generation
- Template-based content generation
- Used when AI services are unavailable
- Ensures system continues running

## MCP Integration

The system supports Model Context Protocol (MCP) servers for enhanced content generation:

- **Content Enhancement**: Improves generated content quality
- **Trend Analysis**: Provides market insights and trends
- **Hashtag Generation**: Creates relevant hashtags
- **Content Optimization**: Optimizes content for LinkedIn engagement

## Automation Setup

### Cron Job (Recommended)
```bash
# Set up automatic cron job
python main.py --setup-cron

# Manual cron job setup
crontab -e
# Add: 0 9 * * * cd /path/to/linkedin-automation && python main.py --run-once
```

### Systemd Service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/linkedin-automation.service
```

```ini
[Unit]
Description=LinkedIn Automation Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/linkedin-automation
ExecStart=/usr/bin/python3 main.py --daemon
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable linkedin-automation
sudo systemctl start linkedin-automation
```

## Monitoring and Logging

- **Log Files**: All activities logged to `linkedin_automation.log`
- **Rotating Logs**: Automatic log rotation (10MB max, 5 backups)
- **Status Monitoring**: Use `--status` command to check system health
- **Component Testing**: Use `--test-components` to verify all parts work

## Troubleshooting

### Common Issues

1. **LinkedIn API Errors**
   - Check access token validity
   - Verify API permissions
   - Ensure correct user ID

2. **Web Scraping Issues**
   - Chrome driver not found: Will auto-download
   - Network timeouts: Check internet connection
   - Rate limiting: System includes delays

3. **Content Generation Issues**
   - OpenAI API key invalid: Check environment variables
   - Hugging Face rate limits: Switch to fallback mode
   - MCP server unavailable: System uses fallback

4. **Permission Errors**
   - Cron job setup: Check user permissions
   - File access: Verify directory permissions
   - Chrome driver: Check execution permissions

### Debug Mode

```bash
# Run with debug logging
python main.py --debug --test-components
```

## Security Considerations

- **API Keys**: Store in environment variables, not code
- **Rate Limits**: Built-in delays and respectful scraping
- **User Agent**: Identifies as automation bot
- **Content Filtering**: Checks topic relevance before posting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and personal use. Ensure compliance with:
- LinkedIn's Terms of Service
- Web scraping policies of target sites
- Rate limiting and respectful API usage
- Content originality and attribution

## Support

For issues, feature requests, or questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Test individual components
4. Create an issue with detailed information

## Architecture

```
├── main.py                 # Main entry point and CLI
├── config.py              # Configuration management
├── logger.py              # Logging setup
├── scheduler.py           # 24-hour automation scheduler
├── web_scraper.py         # Web information gathering
├── content_generator.py   # AI-powered content creation
├── linkedin_poster.py     # LinkedIn API integration
├── mcp_client.py          # MCP server communication
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Roadmap

- [ ] Web dashboard for monitoring
- [ ] More content types (videos, polls)
- [ ] Advanced analytics and engagement tracking
- [ ] Multi-platform support (Twitter, Facebook)
- [ ] Content A/B testing
- [ ] Integration with more MCP servers
- [ ] Advanced topic modeling and trend detection