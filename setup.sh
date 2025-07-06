#!/bin/bash

# LinkedIn Automation System Setup Script
# This script helps you set up the LinkedIn automation system

set -e

echo "🚀 LinkedIn Automation System Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3.8+ is installed
check_python() {
    echo "📋 Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        echo "✅ Python $PYTHON_VERSION found"
        
        # Check if version is 3.8 or higher
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            echo "✅ Python version is compatible"
        else
            echo -e "${RED}❌ Python 3.8+ is required. Current version: $PYTHON_VERSION${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    echo "📦 Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            echo "📋 Detected Ubuntu/Debian system"
            sudo apt-get update
            sudo apt-get install -y chromium-browser python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            echo "📋 Detected RedHat/CentOS system"
            sudo yum install -y chromium python3-pip python3-venv
        else
            echo -e "${YELLOW}⚠️ Unknown Linux distribution. Please install Chromium and Python manually.${NC}"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "📋 Detected macOS system"
        if command -v brew &> /dev/null; then
            brew install chromium python@3.11
        else
            echo -e "${YELLOW}⚠️ Homebrew not found. Please install Chromium and Python manually.${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Unknown operating system. Please install dependencies manually.${NC}"
    fi
}

# Create virtual environment
setup_virtualenv() {
    echo "🐍 Setting up Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment already exists"
    fi
    
    source venv/bin/activate
    echo "✅ Virtual environment activated"
}

# Install Python dependencies
install_python_deps() {
    echo "📦 Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Python dependencies installed"
}

# Setup environment file
setup_env_file() {
    echo "⚙️ Setting up environment configuration..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "✅ Environment file created (.env)"
        echo -e "${YELLOW}📝 Please edit .env file with your configuration${NC}"
    else
        echo "✅ Environment file already exists"
    fi
}

# Setup Ollama (free LLM)
setup_ollama() {
    echo "🤖 Setting up Ollama (free local LLM)..."
    
    read -p "Do you want to install Ollama for free local LLM? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v ollama &> /dev/null; then
            echo "✅ Ollama already installed"
        else
            echo "📦 Installing Ollama..."
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
        
        echo "📥 Downloading Llama2 model (this may take a while)..."
        ollama pull llama2
        echo "✅ Ollama setup complete"
        
        # Update .env file to use Ollama
        if [ -f ".env" ]; then
            sed -i 's/LLM_PROVIDER=.*/LLM_PROVIDER=ollama/' .env
            sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=llama2/' .env
            echo "✅ Environment configured to use Ollama"
        fi
    else
        echo "⏭️ Skipping Ollama installation"
        echo -e "${YELLOW}📝 You'll need to configure OpenAI API key in .env file${NC}"
    fi
}

# Create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    mkdir -p logs data templates
    echo "✅ Directories created"
}

# Test installation
test_installation() {
    echo "🧪 Testing installation..."
    source venv/bin/activate
    
    if python -c "import sys; sys.exit(0)"; then
        echo "✅ Python environment working"
    else
        echo -e "${RED}❌ Python environment test failed${NC}"
        exit 1
    fi
    
    # Test import of main modules
    if python -c "from config.settings import settings; print('Config loaded')"; then
        echo "✅ Configuration module working"
    else
        echo -e "${RED}❌ Configuration module test failed${NC}"
        exit 1
    fi
    
    echo "✅ Installation test completed"
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "=============================="
    echo ""
    echo "Next steps:"
    echo "1. 📝 Edit .env file with your LinkedIn API credentials:"
    echo "   nano .env"
    echo ""
    echo "2. 🔗 Set up LinkedIn API:"
    echo "   - Go to https://developer.linkedin.com/"
    echo "   - Create a new app"
    echo "   - Get Client ID and Secret"
    echo "   - Set up OAuth (see README.md for details)"
    echo ""
    echo "3. 🚀 Test the system:"
    echo "   source venv/bin/activate"
    echo "   python main.py --run-once --topic \"artificial intelligence\""
    echo ""
    echo "4. ▶️ Start the automation:"
    echo "   source venv/bin/activate"
    echo "   python main.py"
    echo ""
    echo "📚 For detailed instructions, see README.md"
    echo ""
    echo -e "${GREEN}Happy automating! 🚀${NC}"
}

# Main execution
main() {
    echo "Starting setup process..."
    echo ""
    
    check_python
    install_system_deps
    setup_virtualenv
    install_python_deps
    create_directories
    setup_env_file
    setup_ollama
    test_installation
    show_next_steps
}

# Run main function
main "$@"