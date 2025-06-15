#!/bin/bash

# AGI House Chat UI Runner Script

echo "🏠 Starting AGI House Chat UI..."

# Check if virtual environment exists
if [ ! -d "ui_venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.10 -m venv ui_venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source ui_venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    echo "# API Configuration" > .env
    echo "API_BASE_URL=http://localhost:8000" >> .env
    echo "API_TIMEOUT=30" >> .env
    echo "" >> .env
    echo "# Logging" >> .env
    echo "LOG_LEVEL=INFO" >> .env
    echo "✅ Created .env file with default values"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run Chainlit
echo "🚀 Launching Chainlit UI on port 8080..."
echo "📱 Open http://localhost:8080 in your browser"
echo ""
chainlit run app.py --port 8080