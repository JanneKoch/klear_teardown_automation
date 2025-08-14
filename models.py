from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TeardownJob:
    id: str
    company_name: str
    company_url: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_folder: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'company_url': self.company_url,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'output_folder': self.output_folder
        }

@dataclass
class Teardown:
    id: str
    job_id: str
    company_name: str
    company_url: str
    content: str
    created_at: datetime
    file_path: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'company_name': self.company_name,
            'company_url': self.company_url,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'file_path': self.file_path
        }