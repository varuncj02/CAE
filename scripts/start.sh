#!/bin/bash

# CAE (Conversational Analysis Engine) Start Script
# This script sets up the environment and starts the FastAPI server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in the project root
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    print_error "Python 3.10 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_status "Python version check passed: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt --no-deps --quiet
print_status "Dependencies installed successfully"

# Check for .env file
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cat > .env << EOF
# LLM Configuration
LLM_API_KEY=your-api-key
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4
EMBEDDING_MODEL_API_KEY=your-api-key
EMBEDDING_MODEL_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL_NAME=text-embedding-3-large

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=conversation_analysis
DB_USER=your-db-user
DB_SECRET=your-db-password

# Application Configuration
LOG_LEVEL=INFO
LLM_TIMEOUT_SECONDS=600
EOF
    print_warning "Please update the .env file with your actual configuration values"
    exit 1
fi

# Check PostgreSQL connection
print_status "Checking PostgreSQL connection..."
if ! python3 -c "
import os
from dotenv import load_dotenv
import psycopg2
load_dotenv()
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'conversation_analysis'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_SECRET')
    )
    conn.close()
    print('PostgreSQL connection successful')
except Exception as e:
    print(f'PostgreSQL connection failed: {e}')
    exit(1)
" 2>&1; then
    print_error "Failed to connect to PostgreSQL. Please check your database configuration in .env"
    exit 1
fi

# Set environment variables for better performance
export PYTHONUNBUFFERED=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the FastAPI server
print_status "Starting CAE server..."
print_status "API will be available at http://localhost:8000"
print_status "Interactive docs at http://localhost:8000/docs"
print_status "Press Ctrl+C to stop the server"

# Run uvicorn with the FastAPI app
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    --access-log 