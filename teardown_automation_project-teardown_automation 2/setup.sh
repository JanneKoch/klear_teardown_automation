#!/bin/bash

echo "🚀 Setting up Company Teardown Automation Project"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 10 ]); then
    echo "❌ Python 3.10+ required. Current version: $python_version"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create directories
echo "📁 Creating required directories..."
mkdir -p output template vector_store static/css static/js templates

# Install dependencies
echo "📦 Installing Python dependencies..."
if command -v python3.11 &> /dev/null; then
    python3.11 -m pip install -r requirements.txt
else
    python3 -m pip install -r requirements.txt
fi

# Check if template files exist
if [ ! -f "template/research_template.txt" ]; then
    echo "⚠️  Warning: template/research_template.txt not found"
    echo "This file is required for generating teardowns"
fi

if [ ! -f "template/klear_context.txt" ]; then
    echo "⚠️  Warning: template/klear_context.txt not found"
    echo "This file provides context for strategic analysis"
fi

echo ""
echo "🔑 IMPORTANT: Update your OpenAI API key"
echo "Edit app.py line 10 and replace with your actual API key:"
echo 'os.environ["OPENAI_API_KEY"] = "your-api-key-here"'
echo ""
echo "🎉 Setup complete! Run the application with:"
if command -v python3.11 &> /dev/null; then
    echo "python3.11 app.py"
else
    echo "python3 app.py"
fi
echo ""
echo "Then open http://localhost:8080 in your browser"