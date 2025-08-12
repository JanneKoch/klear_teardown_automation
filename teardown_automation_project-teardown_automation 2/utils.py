import os
import uuid
import shutil
from datetime import datetime
from typing import Tuple
from urllib.parse import urlparse

def generate_unique_id() -> str:
    """Generate a unique ID for jobs and teardowns"""
    return str(uuid.uuid4())

def generate_job_id() -> str:
    """Generate a job ID with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"job_{timestamp}_{unique_id}"

def create_job_folders(job_id: str) -> Tuple[str, str]:
    """Create folder structure for a job
    
    Returns:
        Tuple of (output_folder)
    """
    # Simple job-based structure
    output_folder = os.path.join("output", job_id)
    
    os.makedirs(output_folder, exist_ok=True)
    
    return output_folder

def cleanup_job_folders(job_id: str):
    """Clean up job folders on failure"""
    try:
        output_folder = os.path.join("output", job_id)
        
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
    except Exception as e:
        print(f"Warning: Could not clean up folders for job {job_id}: {e}")

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    return "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).lower()

def get_teardown_path(output_folder: str, company_name: str) -> str:
    """Get the path for the compiled teardown file"""
    safe_name = sanitize_filename(company_name)
    return os.path.join(output_folder, f"{safe_name}_teardown.md")

def ensure_directories_exist():
    """Ensure base directories exist"""
    os.makedirs("output", exist_ok=True)
    os.makedirs("template", exist_ok=True)