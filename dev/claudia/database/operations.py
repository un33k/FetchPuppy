"""
Database operations for JobSite
Provides high-level CRUD operations and data management functionality
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import csv
import sqlite3

from .connection import DatabaseConnection
from .models import Job, Resume


class DatabaseOperations:
    """High-level database operations for JobSite"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.database_path
        self.connection = DatabaseConnection(self.db_path)
        self.logger = logging.getLogger(__name__)
        
    def initialize_database(self) -> None:
        """Initialize database schema"""
        self.connection.initialize_database()
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = self.connection.get_database_info()
        
        # Add more detailed statistics
        if stats["database_exists"]:
            # Job statistics by source
            job_sources = self.connection.fetchall(
                "SELECT source, COUNT(*) as count FROM jobs GROUP BY source"
            )
            stats["jobs_by_source"] = {row[0]: row[1] for row in job_sources}
            
            # Recent activity
            recent_jobs = self.connection.fetchone(
                "SELECT COUNT(*) FROM jobs WHERE scraped_date > datetime('now', '-7 days')"
            )
            stats["jobs_last_7_days"] = recent_jobs[0] if recent_jobs else 0
            
            # Salary statistics
            salary_stats = self.connection.fetchone(
                """SELECT 
                    AVG(salary_min) as avg_min,
                    AVG(salary_max) as avg_max,
                    MIN(salary_min) as min_salary,
                    MAX(salary_max) as max_salary
                FROM jobs 
                WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL"""
            )
            if salary_stats and salary_stats[0]:
                stats["salary_stats"] = {
                    "average_min": round(salary_stats[0]) if salary_stats[0] else None,
                    "average_max": round(salary_stats[1]) if salary_stats[1] else None,
                    "minimum": salary_stats[2],
                    "maximum": salary_stats[3]
                }
            
            # Location statistics
            locations = self.connection.fetchall(
                "SELECT location, COUNT(*) as count FROM jobs WHERE location IS NOT NULL GROUP BY location ORDER BY count DESC LIMIT 10"
            )
            stats["top_locations"] = {row[0]: row[1] for row in locations}
            
            # Remote job percentage
            remote_stats = self.connection.fetchone(
                "SELECT COUNT(*) as remote_count, (SELECT COUNT(*) FROM jobs) as total_count FROM jobs WHERE remote = 1"
            )
            if remote_stats and remote_stats[1] > 0:
                stats["remote_percentage"] = round((remote_stats[0] / remote_stats[1]) * 100, 1)
        
        return stats
    
    # Job CRUD Operations
    
    def save_job(self, job: Job) -> int:
        """Save or update a job in the database"""
        job_dict = job.to_dict()
        
        if job.id is None:
            # Insert new job
            fields = list(job_dict.keys())
            fields.remove('id')  # Remove id field for insert
            
            placeholders = ', '.join(['?' for _ in fields])
            field_names = ', '.join(fields)
            values = [job_dict[field] for field in fields]
            
            query = f"INSERT INTO jobs ({field_names}) VALUES ({placeholders})"
            
            with self.connection.get_cursor(transaction=True) as cursor:
                cursor.execute(query, values)
                job_id = cursor.lastrowid
                self.logger.debug(f"Inserted job with ID {job_id}")
                return job_id
        else:
            # Update existing job
            fields = list(job_dict.keys())
            fields.remove('id')
            
            set_clause = ', '.join([f"{field} = ?" for field in fields])
            values = [job_dict[field] for field in fields] + [job.id]
            
            query = f"UPDATE jobs SET {set_clause} WHERE id = ?"
            
            with self.connection.get_cursor(transaction=True) as cursor:
                cursor.execute(query, values)
                self.logger.debug(f"Updated job with ID {job.id}")
                return job.id
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Get job by ID"""
        row = self.connection.fetchone("SELECT * FROM jobs WHERE id = ?", (job_id,))
        if row:
            return Job.from_dict(dict(row))
        return None
    
    def get_job_by_external_id(self, external_id: str, source: str) -> Optional[Job]:
        """Get job by external ID and source"""
        row = self.connection.fetchone(
            "SELECT * FROM jobs WHERE external_id = ? AND source = ?",
            (external_id, source)
        )
        if row:
            return Job.from_dict(dict(row))
        return None
    
    def search_jobs(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[Job]:
        """Search jobs with filters"""
        where_conditions = []
        params = []
        
        # Build WHERE clause from filters
        if filters.get('title'):
            where_conditions.append("title LIKE ?")
            params.append(f"%{filters['title']}%")
        
        if filters.get('company'):
            where_conditions.append("company LIKE ?")
            params.append(f"%{filters['company']}%")
        
        if filters.get('location'):
            where_conditions.append("location LIKE ?")
            params.append(f"%{filters['location']}%")
        
        if filters.get('remote') is not None:
            where_conditions.append("remote = ?")
            params.append(filters['remote'])
        
        if filters.get('job_type'):
            where_conditions.append("job_type = ?")
            params.append(filters['job_type'])
        
        if filters.get('salary_min'):
            where_conditions.append("salary_max >= ?")
            params.append(filters['salary_min'])
        
        if filters.get('salary_max'):
            where_conditions.append("salary_min <= ?")
            params.append(filters['salary_max'])
        
        if filters.get('source'):
            where_conditions.append("source = ?")
            params.append(filters['source'])
        
        if filters.get('skills'):
            # Search for skills in the requirements or skills_required fields
            skills = filters['skills'] if isinstance(filters['skills'], list) else [filters['skills']]
            skill_conditions = []
            for skill in skills:
                skill_conditions.append("(requirements LIKE ? OR skills_required LIKE ?)")
                params.extend([f"%{skill}%", f"%{skill}%"])
            if skill_conditions:
                where_conditions.append(f"({' OR '.join(skill_conditions)})")
        
        # Build query
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        query = f"""
            SELECT * FROM jobs 
            {where_clause}
            ORDER BY scraped_date DESC 
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        rows = self.connection.fetchall(query, tuple(params))
        return [Job.from_dict(dict(row)) for row in rows]
    
    def delete_job(self, job_id: int) -> bool:
        """Delete job by ID"""
        with self.connection.get_cursor(transaction=True) as cursor:
            cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            return cursor.rowcount > 0
    
    def cleanup_old_entries(self, older_than: str) -> int:
        """Clean up old database entries"""
        # Parse time period (e.g., "30d", "1w", "6m")
        if older_than.endswith('d'):
            days = int(older_than[:-1])
        elif older_than.endswith('w'):
            days = int(older_than[:-1]) * 7
        elif older_than.endswith('m'):
            days = int(older_than[:-1]) * 30
        else:
            days = 30  # Default to 30 days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.connection.get_cursor(transaction=True) as cursor:
            cursor.execute(
                "DELETE FROM jobs WHERE scraped_date < ?",
                (cutoff_date,)
            )
            deleted_count = cursor.rowcount
            
        self.logger.info(f"Cleaned up {deleted_count} old job entries")
        return deleted_count
    
    # Resume CRUD Operations
    
    def save_resume(self, resume: Resume) -> int:
        """Save or update a resume in the database"""
        # Calculate file hash for duplicate detection
        if resume.file_path and Path(resume.file_path).exists():
            with open(resume.file_path, 'rb') as f:
                resume.file_hash = hashlib.md5(f.read()).hexdigest()
        
        resume_dict = resume.to_dict()
        
        # Check if resume already exists
        existing = self.connection.fetchone(
            "SELECT id FROM resumes WHERE file_path = ?",
            (resume.file_path,)
        )
        
        if existing:
            # Update existing resume
            resume.id = existing[0]
            fields = list(resume_dict.keys())
            fields.remove('id')
            
            set_clause = ', '.join([f"{field} = ?" for field in fields])
            values = [resume_dict[field] for field in fields] + [resume.id]
            
            query = f"UPDATE resumes SET {set_clause} WHERE id = ?"
            
            with self.connection.get_cursor(transaction=True) as cursor:
                cursor.execute(query, values)
                return resume.id
        else:
            # Insert new resume
            fields = list(resume_dict.keys())
            fields.remove('id')
            
            placeholders = ', '.join(['?' for _ in fields])
            field_names = ', '.join(fields)
            values = [resume_dict[field] for field in fields]
            
            query = f"INSERT INTO resumes ({field_names}) VALUES ({placeholders})"
            
            with self.connection.get_cursor(transaction=True) as cursor:
                cursor.execute(query, values)
                return cursor.lastrowid
    
    def get_resume(self, resume_id: int) -> Optional[Resume]:
        """Get resume by ID"""
        row = self.connection.fetchone("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        if row:
            return Resume.from_dict(dict(row))
        return None
    
    def get_resume_by_path(self, file_path: str) -> Optional[Resume]:
        """Get resume by file path"""
        row = self.connection.fetchone("SELECT * FROM resumes WHERE file_path = ?", (file_path,))
        if row:
            return Resume.from_dict(dict(row))
        return None
    
    def list_resumes(self) -> List[Resume]:
        """List all resumes"""
        rows = self.connection.fetchall("SELECT * FROM resumes ORDER BY analyzed_date DESC")
        return [Resume.from_dict(dict(row)) for row in rows]
    
    # Export Operations
    
    def export_jobs(self, format: str, output_path: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """Export jobs to various formats"""
        filters = filters or {}
        jobs = self.search_jobs(filters, limit=filters.get('limit', 10000))
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'csv':
            return self._export_to_csv(jobs, output_path)
        elif format.lower() == 'json':
            return self._export_to_json(jobs, output_path)
        elif format.lower() == 'html':
            return self._export_to_html(jobs, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_csv(self, jobs: List[Job], output_path: Path) -> str:
        """Export jobs to CSV format"""
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if not jobs:
                return str(output_path)
            
            fieldnames = [
                'id', 'title', 'company', 'location', 'remote', 'job_type',
                'salary_min', 'salary_max', 'salary_currency', 'description',
                'source', 'url', 'scraped_date', 'ai_score'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in jobs:
                job_dict = job.to_dict()
                # Only include fields that exist in fieldnames
                filtered_dict = {k: v for k, v in job_dict.items() if k in fieldnames}
                writer.writerow(filtered_dict)
        
        return str(output_path)
    
    def _export_to_json(self, jobs: List[Job], output_path: Path) -> str:
        """Export jobs to JSON format"""
        jobs_data = [job.to_dict() for job in jobs]
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                'export_date': datetime.now().isoformat(),
                'total_jobs': len(jobs),
                'jobs': jobs_data
            }, jsonfile, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _export_to_html(self, jobs: List[Job], output_path: Path) -> str:
        """Export jobs to HTML format"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>JobSite Export - {total_jobs} Jobs</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .job {{ border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 5px; }}
                .job-title {{ font-size: 1.2em; font-weight: bold; color: #333; }}
                .job-company {{ color: #666; }}
                .job-location {{ color: #888; }}
                .job-salary {{ color: #2e7d2e; font-weight: bold; }}
                .job-description {{ margin-top: 10px; }}
                .remote-badge {{ background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }}
                .ai-score {{ background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>JobSite Export</h1>
                <p>Generated on {export_date} | Total Jobs: {total_jobs}</p>
            </div>
            {job_html}
        </body>
        </html>
        """
        
        job_htmls = []
        for job in jobs:
            salary_display = ""
            if job.salary_min or job.salary_max:
                if job.salary_min and job.salary_max:
                    salary_display = f"${job.salary_min:,} - ${job.salary_max:,}"
                elif job.salary_min:
                    salary_display = f"${job.salary_min:,}+"
                elif job.salary_max:
                    salary_display = f"Up to ${job.salary_max:,}"
            
            remote_badge = '<span class="remote-badge">Remote</span>' if job.remote else ''
            ai_badge = f'<span class="ai-score">AI Score: {job.ai_score:.1f}</span>' if job.ai_score else ''
            
            job_html = f"""
            <div class="job">
                <div class="job-title">{job.title or 'No Title'} {remote_badge} {ai_badge}</div>
                <div class="job-company">{job.company or 'Unknown Company'}</div>
                <div class="job-location">{job.location or 'Location not specified'}</div>
                <div class="job-salary">{salary_display}</div>
                <div class="job-description">{(job.description or 'No description')[:500]}...</div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    Source: {job.source} | <a href="{job.url}" target="_blank">View Job</a>
                </div>
            </div>
            """
            job_htmls.append(job_html)
        
        final_html = html_template.format(
            total_jobs=len(jobs),
            export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            job_html=''.join(job_htmls)
        )
        
        with open(output_path, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(final_html)
        
        return str(output_path)
    
    def close(self):
        """Close database connection"""
        self.connection.close()