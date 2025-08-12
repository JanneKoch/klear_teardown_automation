import sqlite3
from datetime import datetime
from typing import List, Optional
from models import TeardownJob, Teardown, JobStatus

class Database:
    def __init__(self, db_path: str = "teardown_app.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    company_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    error_message TEXT,
                    output_folder TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teardowns (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    company_url TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            conn.commit()
    
    # Job operations
    def create_job(self, job: TeardownJob) -> TeardownJob:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO jobs (id, company_name, company_url, status, 
                   created_at, started_at, completed_at, error_message, output_folder) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job.id, job.company_name, job.company_url,
                    job.status.value, job.created_at.isoformat(),
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.error_message, job.output_folder
                )
            )
            conn.commit()
        return job
    
    def update_job(self, job: TeardownJob) -> TeardownJob:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE jobs SET status = ?, started_at = ?, completed_at = ?, 
                   error_message = ?, output_folder = ? WHERE id = ?""",
                (
                    job.status.value,
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.error_message,
                    job.output_folder,
                    job.id
                )
            )
            conn.commit()
        return job
    
    def get_job(self, job_id: str) -> Optional[TeardownJob]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT id, company_name, company_url, status, created_at,
                   started_at, completed_at, error_message, output_folder FROM jobs WHERE id = ?""",
                (job_id,)
            )
            row = cursor.fetchone()
            if row:
                return TeardownJob(
                    id=row[0],
                    company_name=row[1],
                    company_url=row[2],
                    status=JobStatus(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    started_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    error_message=row[7],
                    output_folder=row[8]
                )
        return None
    
    def get_all_jobs(self) -> List[TeardownJob]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT id, company_name, company_url, status, created_at,
                   started_at, completed_at, error_message, output_folder FROM jobs 
                   ORDER BY created_at DESC"""
            )
            return [
                TeardownJob(
                    id=row[0],
                    company_name=row[1],
                    company_url=row[2],
                    status=JobStatus(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    started_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    error_message=row[7],
                    output_folder=row[8]
                )
                for row in cursor.fetchall()
            ]
    
    # Teardown operations
    def create_teardown(self, teardown: Teardown) -> Teardown:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO teardowns (id, job_id, company_name, company_url,
                   content, created_at, file_path) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    teardown.id, teardown.job_id, teardown.company_name,
                    teardown.company_url, teardown.content,
                    teardown.created_at.isoformat(), teardown.file_path
                )
            )
            conn.commit()
        return teardown
    
    def get_teardown(self, teardown_id: str) -> Optional[Teardown]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT id, job_id, company_name, company_url, content,
                   created_at, file_path FROM teardowns WHERE id = ?""",
                (teardown_id,)
            )
            row = cursor.fetchone()
            if row:
                return Teardown(
                    id=row[0],
                    job_id=row[1],
                    company_name=row[2],
                    company_url=row[3],
                    content=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    file_path=row[6]
                )
        return None
    
    def get_teardown_by_job(self, job_id: str) -> Optional[Teardown]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT id, job_id, company_name, company_url, content,
                   created_at, file_path FROM teardowns WHERE job_id = ?""",
                (job_id,)
            )
            row = cursor.fetchone()
            if row:
                return Teardown(
                    id=row[0],
                    job_id=row[1],
                    company_name=row[2],
                    company_url=row[3],
                    content=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    file_path=row[6]
                )
        return None
    
    def get_all_teardowns(self) -> List[Teardown]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT id, job_id, company_name, company_url, content,
                   created_at, file_path FROM teardowns ORDER BY created_at DESC"""
            )
            return [
                Teardown(
                    id=row[0],
                    job_id=row[1],
                    company_name=row[2],
                    company_url=row[3],
                    content=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    file_path=row[6]
                )
                for row in cursor.fetchall()
            ]