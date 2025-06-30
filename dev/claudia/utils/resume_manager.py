"""
Resume Manager for JobSite
Handles resume upload, parsing, and analysis for job matching
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ResumeProfile:
    """Represents a parsed resume profile"""
    file_path: str
    file_name: str
    file_hash: str
    uploaded_date: str
    skills: List[str]
    experience_years: Optional[int]
    education: List[str]
    previous_roles: List[Dict[str, str]]
    summary: str
    location_preferences: List[str]
    salary_expectations: Optional[Dict[str, int]]
    remote_preference: bool
    raw_text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResumeProfile':
        return cls(**data)


class ResumeManager:
    """Manages resume upload and analysis"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.resume_dir = config.resume_dir
        self.resume_dir.mkdir(exist_ok=True)
        self.profiles_file = config.data_dir / "resume_profiles.json"
        
    def upload_resume(self, file_path: str, analyze: bool = True) -> Optional[ResumeProfile]:
        """Upload and analyze a resume file"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.error(f"Resume file not found: {file_path}")
                return None
            
            # Calculate file hash for deduplication
            file_hash = self._calculate_file_hash(source_path)
            
            # Check if already uploaded
            existing_profile = self._get_profile_by_hash(file_hash)
            if existing_profile:
                self.logger.info(f"Resume already uploaded: {existing_profile.file_name}")
                return existing_profile
            
            # Copy file to resume directory
            dest_filename = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source_path.name}"
            dest_path = self.resume_dir / dest_filename
            shutil.copy2(source_path, dest_path)
            
            # Extract text content
            raw_text = self._extract_text(dest_path)
            if not raw_text:
                self.logger.error("Failed to extract text from resume")
                return None
            
            # Create basic profile
            profile = ResumeProfile(
                file_path=str(dest_path),
                file_name=source_path.name,
                file_hash=file_hash,
                uploaded_date=datetime.now().isoformat(),
                skills=[],
                experience_years=None,
                education=[],
                previous_roles=[],
                summary="",
                location_preferences=[],
                salary_expectations=None,
                remote_preference=False,
                raw_text=raw_text
            )
            
            # Analyze resume if requested
            if analyze:
                profile = self._analyze_resume_with_ai(profile)
            
            # Save profile
            self._save_profile(profile)
            
            self.logger.info(f"Resume uploaded successfully: {dest_filename}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Error uploading resume: {e}")
            return None
    
    def list_resumes(self) -> List[ResumeProfile]:
        """List all uploaded resumes"""
        return self._load_profiles()
    
    def get_active_resume(self) -> Optional[ResumeProfile]:
        """Get the most recently uploaded resume"""
        profiles = self._load_profiles()
        if not profiles:
            return None
        
        # Return most recent
        return max(profiles, key=lambda p: p.uploaded_date)
    
    def delete_resume(self, file_hash: str) -> bool:
        """Delete a resume by hash"""
        try:
            profiles = self._load_profiles()
            profile_to_delete = None
            
            for profile in profiles:
                if profile.file_hash == file_hash:
                    profile_to_delete = profile
                    break
            
            if not profile_to_delete:
                self.logger.warning(f"Resume not found: {file_hash}")
                return False
            
            # Remove file
            file_path = Path(profile_to_delete.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Remove from profiles
            profiles = [p for p in profiles if p.file_hash != file_hash]
            self._save_profiles(profiles)
            
            self.logger.info(f"Resume deleted: {profile_to_delete.file_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting resume: {e}")
            return False
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from resume file"""
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                return self._extract_docx_text(file_path)
            elif file_path.suffix.lower() == '.txt':
                return file_path.read_text(encoding='utf-8')
            else:
                self.logger.warning(f"Unsupported file type: {file_path.suffix}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            return ""
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except ImportError:
            self.logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except ImportError:
            self.logger.warning("python-docx not installed. Install with: pip install python-docx")
            return ""
        except Exception as e:
            self.logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    def _analyze_resume_with_ai(self, profile: ResumeProfile) -> ResumeProfile:
        """Analyze resume content using AI"""
        try:
            # Get AI client (reuse from other modules)
            from utils.config import ClaudiaConfig
            config = ClaudiaConfig()
            
            # Try different AI providers
            ai_client = None
            
            if config.claude_api_key:
                import anthropic
                ai_client = anthropic.Anthropic(api_key=config.claude_api_key)
                client_type = "claude"
            elif config.local_llm_enabled:
                import openai
                ai_client = openai.OpenAI(
                    base_url=config.local_llm_base_url,
                    api_key=config.local_llm_api_key
                )
                client_type = "local"
            elif config.openai_api_key:
                import openai
                ai_client = openai.OpenAI(api_key=config.openai_api_key)
                client_type = "openai"
            
            if not ai_client:
                self.logger.warning("No AI client available for resume analysis")
                return profile
            
            # Create analysis prompt
            prompt = f"""Analyze this resume and extract key information in JSON format:

{profile.raw_text}

Extract the following information and return as JSON:
{{
    "skills": ["skill1", "skill2", ...],
    "experience_years": number_or_null,
    "education": ["degree1", "degree2", ...],
    "previous_roles": [
        {{"title": "role", "company": "company", "duration": "years"}},
        ...
    ],
    "summary": "brief professional summary",
    "location_preferences": ["city1", "city2", ...],
    "remote_preference": true_or_false
}}

Focus on technical skills, management experience, AI/ML background, and leadership roles.
Return only valid JSON."""

            # Get AI response
            if client_type == "claude":
                response = ai_client.messages.create(
                    model=config.claude_model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            elif client_type == "local":
                response = ai_client.chat.completions.create(
                    model=config.local_llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.1
                )
                response_text = response.choices[0].message.content
            else:  # openai
                response = ai_client.chat.completions.create(
                    model=config.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.1
                )
                response_text = response.choices[0].message.content
            
            # Parse AI response
            analysis = self._parse_ai_analysis(response_text)
            
            # Update profile with analysis
            if analysis:
                profile.skills = analysis.get("skills", [])
                profile.experience_years = analysis.get("experience_years")
                profile.education = analysis.get("education", [])
                profile.previous_roles = analysis.get("previous_roles", [])
                profile.summary = analysis.get("summary", "")
                profile.location_preferences = analysis.get("location_preferences", [])
                profile.remote_preference = analysis.get("remote_preference", False)
            
            self.logger.info("Resume analysis completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in AI resume analysis: {e}")
        
        return profile
    
    def _parse_ai_analysis(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI analysis response"""
        try:
            # Try to parse as direct JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Look for JSON within the response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                try:
                    json_text = response_text[start:end]
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass
            
            self.logger.warning("Could not parse AI analysis response")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_profile_by_hash(self, file_hash: str) -> Optional[ResumeProfile]:
        """Get profile by file hash"""
        profiles = self._load_profiles()
        for profile in profiles:
            if profile.file_hash == file_hash:
                return profile
        return None
    
    def _load_profiles(self) -> List[ResumeProfile]:
        """Load resume profiles from file"""
        try:
            if not self.profiles_file.exists():
                return []
            
            with open(self.profiles_file, 'r') as f:
                data = json.load(f)
            
            return [ResumeProfile.from_dict(profile_data) for profile_data in data]
            
        except Exception as e:
            self.logger.error(f"Error loading profiles: {e}")
            return []
    
    def _save_profile(self, profile: ResumeProfile) -> None:
        """Save a single profile"""
        profiles = self._load_profiles()
        
        # Remove existing profile with same hash
        profiles = [p for p in profiles if p.file_hash != profile.file_hash]
        
        # Add new profile
        profiles.append(profile)
        
        self._save_profiles(profiles)
    
    def _save_profiles(self, profiles: List[ResumeProfile]) -> None:
        """Save all profiles to file"""
        try:
            data = [profile.to_dict() for profile in profiles]
            
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving profiles: {e}")