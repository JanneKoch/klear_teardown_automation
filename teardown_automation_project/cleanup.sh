#!/bin/bash

# Company Teardown Generator - Quick Cleanup Script
# Resets database and output folders to clean state

echo "🧹 Quick Cleanup Script"
echo "======================"

# Stop any running Flask processes
echo "Stopping Flask processes..."
pkill -f "python.*app" 2>/dev/null || true
echo "✅ Flask processes stopped"

# Remove database
if [ -f "teardown_app.db" ]; then
    rm teardown_app.db
    echo "✅ Database removed"
else
    echo "ℹ️  No database file found"
fi

# Clean output folders and vector stores
echo "Cleaning output folders and vector stores..."
rm -rf output/* 2>/dev/null || true
rm -rf vector_stores/* 2>/dev/null || true
rm -rf vector_store/* 2>/dev/null || true
rm -f vector_store_status.txt 2>/dev/null || true
echo "✅ Output folders and vector stores cleaned"

# Remove Python cache
echo "Removing Python cache..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo "✅ Python cache removed"

# Recreate directories
mkdir -p output vector_stores template
echo "✅ Directories recreated"

echo ""
echo "🎉 Quick cleanup completed!"
echo "System reset to clean state. Ready to start fresh."