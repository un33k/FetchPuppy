"""
Database models and schema for JobSite
Defines the structure for storing job data, analysis results, and metadata
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class Job:
    """Job model representing a job posting"""
    
    # Primary identifiers
    id: Optional[int] = None
    external_id: Optional[str] = None  # ID from the job site
    url: Optional[str] = None
    
    # Basic job information
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    remote: bool = False
    job_type: Optional[str] = None  # full-time, part-time, contract, internship
    
    # Salary information
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    salary_period: Optional[str] = None  # annual, hourly, etc.
    
    # Job content
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    
    # Company information
    company_size: Optional[str] = None
    industry: Optional[str] = None
    company_description: Optional[str] = None
    
    # Skills and experience
    skills_required: Optional[List[str]] = None
    experience_level: Optional[str] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    
    # Metadata
    source: Optional[str] = None  # indeed, linkedin, etc.
    scraped_date: Optional[datetime] = None
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    
    # Analysis results (populated by AI analysis)
    ai_score: Optional[float] = None
    ai_match_reasons: Optional[List[str]] = None
    ai_concerns: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization"""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        for field in ['scraped_date', 'posted_date', 'application_deadline']:
            if data[field]:
                data[field] = data[field].isoformat()
        
        # Convert lists to JSON strings for SQLite storage
        for field in ['skills_required', 'ai_match_reasons', 'ai_concerns']:
            if data[field]:
                data[field] = json.dumps(data[field])
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        # Convert ISO strings back to datetime objects
        for field in ['scraped_date', 'posted_date', 'application_deadline']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert JSON strings back to lists
        for field in ['skills_required', 'ai_match_reasons', 'ai_concerns']:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    data[field] = []
        
        return cls(**data)


@dataclass
class Resume:
    """Resume model for storing resume analysis"""
    
    id: Optional[int] = None
    file_path: str = ""
    file_hash: Optional[str] = None
    
    # Extracted information
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Skills and experience
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    education: Optional[List[Dict[str, str]]] = None
    work_history: Optional[List[Dict[str, Any]]] = None
    
    # Preferences (can be manually set or inferred)
    preferred_locations: Optional[List[str]] = None
    preferred_salary_min: Optional[int] = None
    preferred_salary_max: Optional[int] = None
    preferred_remote: bool = False
    preferred_job_types: Optional[List[str]] = None
    
    # Analysis metadata
    analyzed_date: Optional[datetime] = None
    analysis_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resume to dictionary"""
        data = asdict(self)
        
        # Convert datetime to ISO string
        if data['analyzed_date']:
            data['analyzed_date'] = data['analyzed_date'].isoformat()
        
        # Convert lists and dicts to JSON strings
        for field in ['skills', 'education', 'work_history', 'preferred_locations', 'preferred_job_types']:
            if data[field]:
                data[field] = json.dumps(data[field])
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Resume':
        """Create resume from dictionary"""
        # Convert ISO string back to datetime
        if data.get('analyzed_date'):
            data['analyzed_date'] = datetime.fromisoformat(data['analyzed_date'])
        
        # Convert JSON strings back to objects
        for field in ['skills', 'education', 'work_history', 'preferred_locations', 'preferred_job_types']:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    data[field] = [] if field != 'education' and field != 'work_history' else []
        
        return cls(**data)


class DatabaseSchema:
    """Database schema definitions"""
    
    JOBS_TABLE = """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT,
        url TEXT,
        title TEXT,
        company TEXT,
        location TEXT,
        remote BOOLEAN DEFAULT FALSE,
        job_type TEXT,
        salary_min INTEGER,
        salary_max INTEGER,
        salary_currency TEXT DEFAULT 'USD',
        salary_period TEXT,
        description TEXT,
        requirements TEXT,
        benefits TEXT,
        company_size TEXT,
        industry TEXT,
        company_description TEXT,
        skills_required TEXT,  -- JSON array
        experience_level TEXT,
        experience_years_min INTEGER,
        experience_years_max INTEGER,
        source TEXT,
        scraped_date TIMESTAMP,
        posted_date TIMESTAMP,
        application_deadline TIMESTAMP,
        ai_score REAL,
        ai_match_reasons TEXT,  -- JSON array
        ai_concerns TEXT,       -- JSON array
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    RESUMES_TABLE = """
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_hash TEXT,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT,  -- JSON array
        experience_years INTEGER,
        education TEXT,  -- JSON array
        work_history TEXT,  -- JSON array
        preferred_locations TEXT,  -- JSON array
        preferred_salary_min INTEGER,
        preferred_salary_max INTEGER,
        preferred_remote BOOLEAN DEFAULT FALSE,
        preferred_job_types TEXT,  -- JSON array
        analyzed_date TIMESTAMP,
        analysis_version TEXT DEFAULT '1.0',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_scraped_date ON jobs(scraped_date)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_salary ON jobs(salary_min, salary_max)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_external_id ON jobs(external_id, source)",
        "CREATE INDEX IF NOT EXISTS idx_resumes_file_path ON resumes(file_path)",
        "CREATE INDEX IF NOT EXISTS idx_resumes_file_hash ON resumes(file_hash)"
    ]
    
    TRIGGERS = [
        """
        CREATE TRIGGER IF NOT EXISTS update_jobs_timestamp 
        AFTER UPDATE ON jobs
        BEGIN
            UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS update_resumes_timestamp 
        AFTER UPDATE ON resumes
        BEGIN
            UPDATE resumes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """
    ]
    
    @classmethod
    def get_all_statements(cls) -> List[str]:
        """Get all SQL statements for database initialization"""
        return [cls.JOBS_TABLE, cls.RESUMES_TABLE] + cls.INDEXES + cls.TRIGGERS