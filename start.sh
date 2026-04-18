#!/bin/bash

# Blackboard Notes Generator - Quick Start Script for macOS/Linux

echo ""
echo "========================================"
echo "Blackboard Notes Generator - Startup"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        echo "Make sure Python 3.8+ is installed"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements if needed
echo "Checking dependencies..."
pip list | grep -i "fastapi\|streamlit\|pytesseract" > /dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: .env file not found!"
    echo "Please create .env file with your GROQ_API_KEY"
    echo "Copy .env.example to .env and fill in your API key"
    echo ""
    echo "Get free Groq API key from: https://console.groq.com/keys"
    echo ""
    exit 1
fi

# Check Tesseract installation
echo "Checking Tesseract OCR..."
which tesseract > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  WARNING: Tesseract OCR not found!"
    echo "Please install Tesseract OCR:"
    echo ""
    echo "macOS: brew install tesseract"
    echo "Linux: sudo apt-get install tesseract-ocr"
    echo ""
    exit 1
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "Starting Blackboard Notes Generator..."
echo ""

# Start backend and frontend in background
echo "Opening FastAPI Backend..."
python main.py &
BACKEND_PID=$!

sleep 3

echo "Opening Streamlit Frontend..."
streamlit run frontend.py &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "✅ Application started!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
