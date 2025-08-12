#!/usr/bin/env python3
"""
Cleanup Script for Company Teardown Generator
Resets the database and output folders to initial clean state
"""

import os
import shutil
import sqlite3
from pathlib import Path

def cleanup_database():
    """Remove the database file to reset all data"""
    db_file = "teardown_app.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"✅ Removed database: {db_file}")
    else:
        print(f"ℹ️  Database file not found: {db_file}")

def cleanup_output_folders():
    """Clean up all output and vector store folders"""
    folders_to_clean = [
        "output",
        "vector_stores",
        "vector_store",  # Alternative naming
        "template"
    ]
    
    # Also clean vector store status files
    status_files = [
        "vector_store_status.txt"
    ]
    
    for folder in folders_to_clean:
        if os.path.exists(folder):
            # Remove all contents but keep the folder
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"✅ Removed directory: {item_path}")
                else:
                    os.remove(item_path)
                    print(f"✅ Removed file: {item_path}")
        else:
            # Create the folder if it doesn't exist
            os.makedirs(folder, exist_ok=True)
            print(f"✅ Created directory: {folder}")
    
    # Remove vector store status files
    for status_file in status_files:
        if os.path.exists(status_file):
            os.remove(status_file)
            print(f"✅ Removed status file: {status_file}")

def cleanup_cache_files():
    """Remove Python cache files"""
    cache_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache"
    ]
    
    for root, dirs, files in os.walk("."):
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            cache_dir = os.path.join(root, "__pycache__")
            shutil.rmtree(cache_dir)
            print(f"✅ Removed cache: {cache_dir}")
        
        # Remove .pyc and .pyo files
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"✅ Removed cache file: {file_path}")

def main():
    """Main cleanup function"""
    print("🧹 Starting cleanup process...")
    print("=" * 50)
    
    # Stop any running processes first
    print("\n1. Stopping any running Flask processes...")
    os.system("pkill -f 'python.*app' 2>/dev/null || true")
    print("✅ Stopped Flask processes")
    
    # Clean database
    print("\n2. Cleaning database...")
    cleanup_database()
    
    # Clean output folders
    print("\n3. Cleaning output folders...")
    cleanup_output_folders()
    
    # Clean cache files
    print("\n4. Cleaning Python cache files...")
    cleanup_cache_files()
    
    # Recreate initial directory structure
    print("\n5. Recreating initial directory structure...")
    initial_dirs = [
        "output",
        "vector_stores",
        "template",
        "static/css",
        "static/js",
        "templates"
    ]
    
    for dir_path in initial_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    print("✅ Initial directory structure created")
    
    print("\n" + "=" * 50)
    print("🎉 Cleanup completed successfully!")
    print("\nYour system is now reset to initial clean state:")
    print("  • Database cleared")
    print("  • Output folders cleaned")
    print("  • Vector stores cleared")
    print("  • Cache files removed")
    print("  • Directory structure recreated")
    print("\nYou can now start fresh with:")
    print("  python3.11 app.py")

if __name__ == "__main__":
    # Confirmation prompt
    response = input("⚠️  This will delete all teardowns, jobs, and output files. Continue? (y/N): ")
    if response.lower() in ['y', 'yes']:
        main()
    else:
        print("❌ Cleanup cancelled")