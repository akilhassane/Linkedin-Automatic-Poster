# LinkedIn Automation System

An automated system that posts high-quality content to LinkedIn every 24 hours. The system browses the web to gather information, synthesizes it using AI, and creates various types of content including articles, slides, graphs, and infographics.

## Features

- **Automated Content Generation**: Creates articles, slide decks, graphs, and infographics
- **Web Research**: Automatically gathers latest information from the web
- **AI-Powered Synthesis**: Uses LLM (OpenAI or Ollama) to create engaging content
- **MCP Integration**: Enhanced context awareness using Model Context Protocol
- **Flexible Scheduling**: Customizable posting schedules
- **Multiple Content Types**: Rotates between different content formats
- **LinkedIn API Integration**: Direct posting to LinkedIn
- **No Human Intervention**: Fully automated operation

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Scraper   │    │   LLM Client    │    │   MCP Client    │
│                 │    │                 │    │                 │
│ • Google Search │    │ • OpenAI API    │    │ • Context Mgmt  │
│ • RSS Feeds     │    │ • Ollama Local  │    │ • Recommendations│
│ • News Sources  │    │ • Content Gen   │    │ • Analysis      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │Content Generator│
                    │                 │
                    │ • Articles      │
                    │ • Slides        │
                    │ • Graphs        │
                    │ • Infographics  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │    Scheduler    │
                    │                 │
                    │ • Cron Jobs     │
                    │ • Job Mgmt      │
                    │ • Automation    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │ LinkedIn API    │
                    │                 │
                    │ • Post Creation │
                    │ • Image Upload  │
                    │ • Analytics     │
                    └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- LinkedIn Developer Account
- Chrome/Chromium browser (for web scraping)
- OpenAI API key (optional) or Ollama (for free local LLM)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd linkedin-automation
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install system dependencies:**
```bash
# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y chromium-browser

# For macOS
brew install chromium
```

4. **Set up LinkedIn API:**
   - Go to [LinkedIn Developer Portal](https://developer.linkedin.com/)
   - Create a new app
   - Get your Client ID and Client Secret
   - Set up OAuth redirect URI: `http://localhost:8000/callback`

5. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

6. **Configure LLM (Choose one):**

   **Option A: OpenAI (Paid)**
   ```bash
   # Set in .env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key
   ```

   **Option B: Ollama (Free Local)**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Download a model
   ollama pull llama2
   
   # Set in .env
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama2
   ```

7. **Set up MCP Server (Optional):**
   - Install a compatible MCP server
   - Configure MCP_SERVER_URL in .env

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# LinkedIn API
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# Content Configuration
CONTENT_TOPIC=artificial intelligence
POSTING_SCHEDULE=0 9 * * *  # Daily at 9 AM
MAX_CONTENT_LENGTH=3000
ENABLE_GRAPHS=true
ENABLE_SLIDES=true

# LLM Configuration
LLM_PROVIDER=ollama  # or openai
OLLAMA_MODEL=llama2
OPENAI_API_KEY=your_api_key  # if using OpenAI

# MCP Server (Optional)
MCP_SERVER_URL=http://localhost:8080
MCP_API_KEY=your_mcp_api_key
```

### LinkedIn OAuth Setup

1. **Get Authorization Code:**
   - Visit: `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/callback&scope=r_liteprofile%20r_emailaddress%20w_member_social`
   - Copy the authorization code from the callback URL

2. **Exchange for Access Token:**
   ```bash
   curl -X POST \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code&code=YOUR_AUTH_CODE&redirect_uri=http://localhost:8000/callback&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET" \
     "https://www.linkedin.com/oauth/v2/accessToken"
   ```

3. **Add Access Token to .env:**
   ```bash
   LINKEDIN_ACCESS_TOKEN=your_access_token
   ```

## Usage

### Basic Usage

1. **Run the system:**
```bash
python main.py
```

2. **Run once (for testing):**
```bash
python main.py --run-once --topic "artificial intelligence"
```

3. **Check status:**
```bash
python main.py --status
```

4. **List scheduled jobs:**
```bash
python main.py --list-jobs
```

### Advanced Usage

1. **Add a new topic:**
```bash
python main.py --add-topic --topic "blockchain technology" --schedule "0 10 * * *"
```

2. **Run as daemon:**
```bash
python main.py --daemon
```

3. **Custom topic for single run:**
```bash
python main.py --run-once --topic "machine learning trends"
```

### Cron Schedule Format

The system uses cron format for scheduling:
- `0 9 * * *` - Daily at 9 AM
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1-5` - Weekdays at 9 AM
- `0 12 * * 0` - Sundays at noon

## Content Types

The system rotates through different content types based on the day of the week:

- **Monday**: Articles (Long-form content)
- **Tuesday**: Slide Decks (Multi-slide presentations)
- **Wednesday**: Graphs (Data visualizations)
- **Thursday**: Infographics (Visual summaries)
- **Friday**: Articles
- **Saturday**: Slide Decks
- **Sunday**: Graphs

## API Reference

### Main Commands

```bash
# Start the automation system
python main.py

# Run content generation once
python main.py --run-once [--topic TOPIC]

# Add a new scheduled topic
python main.py --add-topic --topic TOPIC --schedule SCHEDULE

# List all scheduled jobs
python main.py --list-jobs

# Show system status
python main.py --status
```

### Configuration Options

All configuration is done through environment variables or the `.env` file. See [Configuration](#configuration) section for details.

## Monitoring and Logs

### Log Files

- Main log: `logs/linkedin_automation.log`
- Error logs: Included in main log with ERROR level

### Monitoring Commands

```bash
# Check system status
python main.py --status

# View recent logs
tail -f logs/linkedin_automation.log

# Check scheduled jobs
python main.py --list-jobs
```

## Troubleshooting

### Common Issues

1. **LinkedIn API Authentication Failed**
   - Check your LinkedIn app credentials
   - Verify the access token is still valid
   - Ensure proper OAuth scope permissions

2. **Web Scraping Issues**
   - Install Chrome/Chromium browser
   - Check internet connectivity
   - Verify user agent string

3. **LLM Connection Failed**
   - For OpenAI: Check API key and billing
   - For Ollama: Ensure Ollama is running and model is downloaded

4. **Content Generation Failed**
   - Check web scraping is working
   - Verify LLM configuration
   - Review log files for specific errors

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python main.py
```

## Docker Deployment

### Build and Run

```bash
# Build the container
docker build -t linkedin-automation .

# Run with environment file
docker run -d --name linkedin-bot --env-file .env linkedin-automation

# Run with volume for logs
docker run -d --name linkedin-bot --env-file .env -v ./logs:/app/logs linkedin-automation
```

### Docker Compose

```yaml
version: '3.8'
services:
  linkedin-automation:
    build: .
    env_file: .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
```

## Security Considerations

1. **API Keys**: Store all API keys securely in environment variables
2. **Access Tokens**: Regularly rotate LinkedIn access tokens
3. **Network**: Consider running behind a firewall
4. **Logs**: Ensure log files don't contain sensitive information
5. **Rate Limiting**: Respect LinkedIn's API rate limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue on the repository
4. Include relevant log snippets and configuration (without sensitive data)

## Disclaimer

This tool is for educational and legitimate business use only. Users are responsible for:
- Complying with LinkedIn's Terms of Service
- Ensuring content quality and relevance
- Managing API usage within rate limits
- Following applicable laws and regulations

Use this tool responsibly and ethically.