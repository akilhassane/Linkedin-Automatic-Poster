#!/bin/bash

# LinkedIn Automation System Installation Script

echo "🚀 LinkedIn Automation System Installation"
echo "=========================================="
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python $python_version is too old. Python 3.8 or higher is required."
    exit 1
fi

# Install pip if not available
if ! command -v pip3 &> /dev/null; then
    echo "📦 Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Copy environment file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "🔧 Creating .env file from template..."
        cp .env.example .env
        echo "✅ Created .env file"
        echo "📝 Please edit .env file with your actual credentials"
    else
        echo "⚠️  .env.example not found"
    fi
else
    echo "📝 .env file already exists"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p logs output temp

# Make scripts executable
chmod +x main.py setup.py

# Test basic imports
echo "🧪 Testing basic imports..."
python3 -c "
try:
    import config
    import logger
    print('✅ Basic modules imported successfully')
except Exception as e:
    print(f'❌ Import test failed: {e}')
    exit(1)
"

echo
echo "🎉 Installation completed!"
echo
echo "📋 Next Steps:"
echo "1. Edit .env file with your LinkedIn API credentials"
echo "2. Run: python3 main.py --config-check"
echo "3. Run: python3 main.py --test-components"
echo "4. Run: python3 main.py --run-once"
echo "5. Run: python3 main.py --setup-cron"
echo
echo "📚 See README.md for detailed instructions"