"""
Smart Search for JobSite
AI-powered job search using natural language prompts and resume matching
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a job search result with AI analysis"""
    job: Dict[str, Any]
    score: float
    match_reasons: str
    concerns: str


class SmartSearcher:
    """AI-powered job searcher that matches resumes against job database"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_path = config.database_path
        
    def search_with_prompt(self, prompt: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search jobs using natural language prompt and resume matching"""
        try:
            # Get user's resume profile
            resume_profile = self._get_active_resume()
            if not resume_profile:
                self.logger.warning("No resume found - searching without resume matching")
                resume_profile = {}
            
            # Parse search criteria from prompt
            search_criteria = self._parse_search_prompt(prompt, resume_profile)
            
            # Get jobs from database
            jobs = self._query_jobs_database(search_criteria)
            
            if not jobs:
                return []
            
            # Score and rank jobs with AI
            self.logger.info(f"Scoring {len(jobs)} jobs with AI...")
            scored_jobs = self._score_jobs_with_ai(jobs, resume_profile, prompt)
            self.logger.info(f"AI scoring returned {len(scored_jobs)} scored jobs")
            
            # Sort by score and return top results
            scored_jobs.sort(key=lambda x: x['score'], reverse=True)
            
            return scored_jobs[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in smart search: {e}")
            return []
    
    def _get_active_resume(self) -> Optional[Dict[str, Any]]:
        """Get the active resume profile"""
        try:
            from utils.resume_manager import ResumeManager
            resume_manager = ResumeManager(self.config)
            profile = resume_manager.get_active_resume()
            
            if profile:
                return {
                    'skills': profile.skills,
                    'experience_years': profile.experience_years,
                    'education': profile.education,
                    'previous_roles': profile.previous_roles,
                    'summary': profile.summary,
                    'location_preferences': profile.location_preferences,
                    'salary_expectations': profile.salary_expectations,
                    'remote_preference': profile.remote_preference
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting resume: {e}")
            return None
    
    def _parse_search_prompt(self, prompt: str, resume_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Parse natural language search prompt into structured criteria"""
        try:
            # Get AI client for prompt parsing
            ai_client = self._get_ai_client()
            if not ai_client:
                # Fallback to basic keyword parsing
                return self._fallback_parse_prompt(prompt)
            
            # Create analysis prompt for AI
            analysis_prompt = f"""Analyze this job search request and extract structured search criteria:

USER REQUEST: "{prompt}"

RESUME CONTEXT: {json.dumps(resume_profile, indent=2) if resume_profile else "No resume available"}

Extract the following search criteria and return as JSON:
{{
    "keywords": ["keyword1", "keyword2", ...],
    "job_titles": ["title1", "title2", ...],
    "companies": ["company1", "company2", ...],
    "salary_min": number_or_null,
    "salary_max": number_or_null,
    "locations": ["location1", "location2", ...],
    "remote_ok": true_or_false,
    "experience_level": "entry/mid/senior/executive",
    "job_types": ["full-time", "contract", ...],
    "skills_required": ["skill1", "skill2", ...],
    "industries": ["industry1", "industry2", ...]
}}

Focus on extracting specific criteria like salary ranges, location preferences, job levels, and technical requirements.
Return only valid JSON."""

            client_type, response_text = self._get_ai_response(ai_client, analysis_prompt)
            
            # Parse AI response
            criteria = self._parse_ai_criteria(response_text)
            if criteria:
                return criteria
            
            # Fallback if AI parsing fails
            return self._fallback_parse_prompt(prompt)
            
        except Exception as e:
            self.logger.error(f"Error parsing prompt: {e}")
            return self._fallback_parse_prompt(prompt)
    
    def _fallback_parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Fallback prompt parsing using keyword extraction"""
        prompt_lower = prompt.lower()
        
        criteria = {
            "keywords": [],
            "job_titles": [],
            "companies": [],
            "salary_min": None,
            "salary_max": None,
            "locations": [],
            "remote_ok": False,
            "experience_level": None,
            "job_types": [],
            "skills_required": [],
            "industries": []
        }
        
        # Extract salary info
        if '$' in prompt:
            import re
            salary_matches = re.findall(r'\$(\d+)k?', prompt_lower)
            if salary_matches:
                salaries = [int(s.replace('k', '000') if 'k' in s else s) * (1000 if len(s) <= 3 else 1) for s in salary_matches]
                if salaries:
                    criteria["salary_min"] = max(salaries)  # Use highest mentioned salary as minimum
        
        # Extract companies
        if 'openai' in prompt_lower:
            criteria["companies"].append('OpenAI')
        if 'google' in prompt_lower:
            criteria["companies"].append('Google')
        if 'anthropic' in prompt_lower:
            criteria["companies"].append('Anthropic')
        
        # Extract job levels
        if any(word in prompt_lower for word in ['manager', 'lead', 'director', 'vp', 'principal']):
            criteria["experience_level"] = "senior"
        elif any(word in prompt_lower for word in ['senior', 'sr']):
            criteria["experience_level"] = "senior"
        
        # Extract locations
        if any(loc in prompt_lower for loc in ['sf', 'san francisco']):
            criteria["locations"].append('San Francisco')
        if any(loc in prompt_lower for loc in ['wa', 'washington', 'seattle']):
            criteria["locations"].extend(['Washington', 'Seattle'])
        if 'remote' in prompt_lower:
            criteria["remote_ok"] = True
        
        # Extract keywords from common AI/tech terms
        tech_keywords = ['ai', 'machine learning', 'ml', 'deep learning', 'nlp', 'computer vision', 
                        'infrastructure', 'infra', 'speech', 'audio', 'python', 'tensorflow', 'pytorch']
        for keyword in tech_keywords:
            if keyword in prompt_lower:
                criteria["keywords"].append(keyword)
        
        return criteria
    
    def _query_jobs_database(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query jobs database based on search criteria"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Build dynamic query
            where_conditions = []
            params = []
            
            # Company filter
            if criteria.get("companies"):
                company_conditions = []
                for company in criteria["companies"]:
                    company_conditions.append("company LIKE ?")
                    params.append(f"%{company}%")
                where_conditions.append(f"({' OR '.join(company_conditions)})")
            
            # Salary filter
            if criteria.get("salary_min"):
                where_conditions.append("(salary_min >= ? OR salary_max >= ?)")
                params.extend([criteria["salary_min"], criteria["salary_min"]])
            
            # Location filter
            if criteria.get("locations"):
                location_conditions = []
                for location in criteria["locations"]:
                    location_conditions.append("location LIKE ?")
                    params.append(f"%{location}%")
                if criteria.get("remote_ok"):
                    location_conditions.append("remote = 1")
                where_conditions.append(f"({' OR '.join(location_conditions)})")
            elif criteria.get("remote_ok"):
                where_conditions.append("remote = 1")
            
            # Keywords filter (search in title, description, requirements)
            if criteria.get("keywords"):
                keyword_conditions = []
                for keyword in criteria["keywords"]:
                    keyword_conditions.append(
                        "(title LIKE ? OR description LIKE ? OR requirements LIKE ? OR skills_required LIKE ?)"
                    )
                    params.extend([f"%{keyword}%"] * 4)
                where_conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # Build final query
            base_query = """
                SELECT id, title, company, location, remote, job_type, 
                       salary_min, salary_max, description, requirements, 
                       skills_required, experience_level, url, source,
                       scraped_date, ai_score, ai_match_reasons, ai_concerns
                FROM jobs
            """
            
            if where_conditions:
                query = base_query + " WHERE " + " AND ".join(where_conditions)
            else:
                query = base_query
            
            query += " ORDER BY scraped_date DESC LIMIT 50"
            
            # Debug: log the query
            self.logger.info(f"Search query: {query}")
            self.logger.info(f"Search params: {params}")
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            jobs = []
            for row in rows:
                job = dict(row)
                jobs.append(job)
            
            conn.close()
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error querying database: {e}")
            return []
    
    def _score_jobs_with_ai(self, jobs: List[Dict[str, Any]], resume_profile: Dict[str, Any], 
                           original_prompt: str) -> List[Dict[str, Any]]:
        """Score jobs against resume and search criteria using AI"""
        try:
            ai_client = self._get_ai_client()
            if not ai_client:
                # Fallback to basic scoring
                self.logger.warning("No AI client available, using fallback scoring")
                return self._fallback_score_jobs(jobs, resume_profile)
            
            scored_jobs = []
            
            for job in jobs:
                try:
                    # Build salary string safely
                    salary_str = "Salary not specified"
                    if job['salary_min'] and job['salary_max']:
                        salary_str = f"${job['salary_min']:,} - ${job['salary_max']:,}"
                    elif job['salary_min']:
                        salary_str = f"${job['salary_min']:,}+"
                    
                    # Create scoring prompt
                    scoring_prompt = f"""Analyze how well this job matches the user's profile and search request:

USER SEARCH REQUEST: "{original_prompt}"

USER RESUME PROFILE:
{json.dumps(resume_profile, indent=2) if resume_profile else "No resume available"}

JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Remote: {'Yes' if job['remote'] else 'No'}
Salary: {salary_str}
Description: {job['description'][:500] + '...' if job['description'] and len(job['description']) > 500 else job['description'] or 'No description'}
Requirements: {job['requirements'][:300] + '...' if job['requirements'] and len(job['requirements']) > 300 else job['requirements'] or 'No requirements listed'}
Skills: {job['skills_required'] or 'Not specified'}

Rate this job match and return JSON:
{{
    "score": float_between_0_and_10,
    "match_reasons": "Brief explanation of why this job is a good match",
    "concerns": "Brief explanation of potential concerns or gaps"
}}

Consider: salary fit, location match, skill alignment, experience level, company culture fit, career growth potential.
Return only valid JSON."""

                    client_type, response_text = self._get_ai_response(ai_client, scoring_prompt)
                    
                    # Parse AI scoring response
                    scoring = self._parse_ai_scoring(response_text)
                    
                    if scoring:
                        scored_jobs.append({
                            'job': job,
                            'score': scoring['score'],
                            'match_reasons': scoring['match_reasons'],
                            'concerns': scoring['concerns']
                        })
                    else:
                        # Fallback scoring for this job
                        fallback_score = self._calculate_fallback_score(job, resume_profile)
                        scored_jobs.append({
                            'job': job,
                            'score': fallback_score,
                            'match_reasons': 'Basic keyword matching applied',
                            'concerns': 'AI analysis unavailable'
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Error scoring job {job['title']}: {e}")
                    # Include job with minimal score
                    scored_jobs.append({
                        'job': job,
                        'score': 5.0,
                        'match_reasons': 'Could not analyze',
                        'concerns': 'Analysis failed'
                    })
            
            return scored_jobs
            
        except Exception as e:
            self.logger.error(f"Error in AI scoring: {e}")
            self.logger.info("Falling back to basic scoring...")
            return self._fallback_score_jobs(jobs, resume_profile)
    
    def _fallback_score_jobs(self, jobs: List[Dict[str, Any]], resume_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback job scoring without AI"""
        scored_jobs = []
        
        for job in jobs:
            score = self._calculate_fallback_score(job, resume_profile)
            scored_jobs.append({
                'job': job,
                'score': score,
                'match_reasons': 'Basic keyword and criteria matching',
                'concerns': 'Full AI analysis not available'
            })
        
        return scored_jobs
    
    def _calculate_fallback_score(self, job: Dict[str, Any], resume_profile: Dict[str, Any]) -> float:
        """Calculate basic job match score without AI"""
        score = 5.0  # Base score
        
        if not resume_profile:
            return score
        
        # Salary match
        if job.get('salary_min') and resume_profile.get('salary_expectations'):
            expected_min = resume_profile['salary_expectations'].get('min', 0)
            if job['salary_min'] >= expected_min:
                score += 1.5
        
        # Location match
        if resume_profile.get('location_preferences'):
            job_location = job.get('location', '').lower()
            for pref_location in resume_profile['location_preferences']:
                if pref_location.lower() in job_location:
                    score += 1.0
                    break
        
        # Remote preference
        if resume_profile.get('remote_preference') and job.get('remote'):
            score += 1.0
        
        # Skills match
        if resume_profile.get('skills') and job.get('skills_required'):
            job_skills = job['skills_required'].lower()
            user_skills = [skill.lower() for skill in resume_profile['skills']]
            matches = sum(1 for skill in user_skills if skill in job_skills)
            score += min(matches * 0.5, 2.0)
        
        # Experience level (rough estimation)
        if resume_profile.get('experience_years'):
            title = job.get('title', '').lower()
            if resume_profile['experience_years'] >= 8:
                if any(term in title for term in ['senior', 'lead', 'manager', 'principal', 'director']):
                    score += 1.0
            elif resume_profile['experience_years'] >= 5:
                if any(term in title for term in ['senior', 'sr']):
                    score += 1.0
        
        return min(score, 10.0)  # Cap at 10.0
    
    def _get_ai_client(self):
        """Get available AI client"""
        try:
            # Try Claude first
            if self.config.claude_api_key:
                import anthropic
                return ('claude', anthropic.Anthropic(api_key=self.config.claude_api_key))
            
            # Try local LLM
            elif self.config.local_llm_enabled:
                import openai
                return ('local', openai.OpenAI(
                    base_url=self.config.local_llm_base_url,
                    api_key=self.config.local_llm_api_key
                ))
            
            # Try OpenAI
            elif self.config.openai_api_key:
                import openai
                return ('openai', openai.OpenAI(api_key=self.config.openai_api_key))
            
            return None
            
        except ImportError:
            return None
    
    def _get_ai_response(self, ai_client_info, prompt: str) -> tuple:
        """Get AI response from available client"""
        client_type, ai_client = ai_client_info
        
        try:
            if client_type == "claude":
                response = ai_client.messages.create(
                    model=self.config.claude_model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )
                return client_type, response.content[0].text
                
            elif client_type == "local":
                response = ai_client.chat.completions.create(
                    model=self.config.local_llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1200,
                    temperature=0.1
                )
                return client_type, response.choices[0].message.content
                
            else:  # openai
                response = ai_client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1200,
                    temperature=0.1
                )
                return client_type, response.choices[0].message.content
                
        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}")
            raise
    
    def _parse_ai_criteria(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI criteria response"""
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
            
            return None
    
    def _parse_ai_scoring(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI scoring response"""
        return self._parse_ai_criteria(response_text)  # Same parsing logic