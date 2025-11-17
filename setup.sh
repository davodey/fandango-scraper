#!/bin/bash

# Fandango Scraper Setup Script
# This script will help you set up the project on your local machine

echo "=========================================="
echo "Fandango Scraper Setup"
echo "=========================================="
echo ""

# Step 1: Check for Python
echo "Step 1: Checking for Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✓ Found python3: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✓ Found python: $(python --version)"
else
    echo "❌ Python not found!"
    echo ""
    echo "Please install Python 3.8+ from:"
    echo "  - macOS: brew install python3"
    echo "  - Windows: https://www.python.org/downloads/"
    echo "  - Linux: sudo apt-get install python3"
    exit 1
fi

echo ""

# Step 2: Check for Chrome
echo "Step 2: Checking for Google Chrome..."
if command -v google-chrome &> /dev/null; then
    echo "✓ Chrome found"
elif command -v chromium &> /dev/null; then
    echo "✓ Chromium found"
elif [ -d "/Applications/Google Chrome.app" ]; then
    echo "✓ Chrome found (macOS)"
elif [ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ]; then
    echo "✓ Chrome found (Windows)"
else
    echo "⚠ Chrome not detected (but may still be installed)"
    echo "  If you don't have Chrome, install from: https://www.google.com/chrome/"
fi

echo ""

# Step 3: Create virtual environment
echo "Step 3: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠ Virtual environment already exists, skipping..."
else
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
fi

echo ""

# Step 4: Activate instructions
echo "Step 4: Activate virtual environment"
echo ""
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Run this command:"
    echo "  venv\\Scripts\\activate"
else
    echo "Run this command:"
    echo "  source venv/bin/activate"
fi

echo ""
echo "Then run:"
echo "  pip install -r requirements.txt"
echo "  python test_firebase.py"
echo ""
echo "=========================================="
echo "Setup script complete!"
echo "=========================================="
