"""
LLM Connectivity Tester for Claudia
Tests connectivity and functionality of different AI providers
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Tuple

from .colors import success, error, warning, info


class LLMTester:
    """Test connectivity and functionality of AI providers"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def ping_local_llm(self) -> bool:
        """Test local LLM connectivity via LM Studio"""
        print(info("Testing local LLM connectivity..."))
        
        if not self.config.local_llm_enabled:
            print(warning("Local LLM is disabled in configuration"))
            print("To enable: set LOCAL_LLM_ENABLED=true in .env")
            return False
        
        print(f"  URL: {self.config.local_llm_base_url}")
        print(f"  Model: {self.config.local_llm_model}")
        
        try:
            import openai
            client = openai.OpenAI(
                base_url=self.config.local_llm_base_url,
                api_key=self.config.local_llm_api_key
            )
            
            # Test basic connectivity with a simple prompt
            start_time = time.time()
            response = client.chat.completions.create(
                model=self.config.local_llm_model,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
                max_tokens=10,
                temperature=0.1
            )
            end_time = time.time()
            
            response_text = response.choices[0].message.content.strip()
            response_time = round((end_time - start_time) * 1000)
            
            print(success("✓ Local LLM connection successful!"))
            print(f"  Response: {response_text}")
            print(f"  Response time: {response_time}ms")
            print(f"  Model: {response.model}")
            
            return True
            
        except ImportError:
            print(error("✗ OpenAI library not installed"))
            print("Install with: pip install openai")
            return False
        except Exception as e:
            print(error(f"✗ Local LLM connection failed: {e}"))
            print("\nTroubleshooting:")
            print("  1. Is LM Studio running?")
            print("  2. Is the local server started in LM Studio?")
            print("  3. Is the model loaded?")
            print(f"  4. Check URL: {self.config.local_llm_base_url}")
            return False
    
    def ping_claude(self) -> bool:
        """Test Claude API connectivity"""
        print(info("Testing Claude API connectivity..."))
        
        if not self.config.claude_api_key:
            print(warning("Claude API key not configured"))
            print("To configure: set CLAUDE_API_KEY in .env")
            return False
        
        api_key_preview = self.config.claude_api_key[:8] + "..." + self.config.claude_api_key[-4:]
        print(f"  API Key: {api_key_preview}")
        print(f"  Model: {self.config.claude_model}")
        
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.config.claude_api_key)
            
            start_time = time.time()
            response = client.messages.create(
                model=self.config.claude_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}]
            )
            end_time = time.time()
            
            response_text = response.content[0].text.strip()
            response_time = round((end_time - start_time) * 1000)
            
            print(success("✓ Claude API connection successful!"))
            print(f"  Response: {response_text}")
            print(f"  Response time: {response_time}ms")
            print(f"  Model: {response.model}")
            print(f"  Usage: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
            
            return True
            
        except ImportError:
            print(error("✗ Anthropic library not installed"))
            print("Install with: pip install anthropic")
            return False
        except Exception as e:
            print(error(f"✗ Claude API connection failed: {e}"))
            print("\nTroubleshooting:")
            print("  1. Check your API key is valid")
            print("  2. Check your account has credits")
            print("  3. Check internet connectivity")
            print("  4. Get API key: https://console.anthropic.com/")
            return False
    
    def ping_openai(self) -> bool:
        """Test OpenAI API connectivity"""
        print(info("Testing OpenAI API connectivity..."))
        
        if not self.config.openai_api_key:
            print(warning("OpenAI API key not configured"))
            print("To configure: set OPENAI_API_KEY in .env")
            return False
        
        api_key_preview = self.config.openai_api_key[:8] + "..." + self.config.openai_api_key[-4:]
        print(f"  API Key: {api_key_preview}")
        print(f"  Model: {self.config.openai_model}")
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.config.openai_api_key)
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
                max_tokens=10,
                temperature=0.1
            )
            end_time = time.time()
            
            response_text = response.choices[0].message.content.strip()
            response_time = round((end_time - start_time) * 1000)
            
            print(success("✓ OpenAI API connection successful!"))
            print(f"  Response: {response_text}")
            print(f"  Response time: {response_time}ms")
            print(f"  Model: {response.model}")
            print(f"  Usage: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")
            
            return True
            
        except ImportError:
            print(error("✗ OpenAI library not installed"))
            print("Install with: pip install openai")
            return False
        except Exception as e:
            print(error(f"✗ OpenAI API connection failed: {e}"))
            print("\nTroubleshooting:")
            print("  1. Check your API key is valid")
            print("  2. Check your account has credits")
            print("  3. Check internet connectivity")
            print("  4. Get API key: https://platform.openai.com/api-keys")
            return False
    
    def ping_all(self) -> bool:
        """Test all configured AI providers"""
        print(info("Testing all AI provider connections...\n"))
        
        results = {}
        
        # Test Claude
        print("=" * 50)
        results['claude'] = self.ping_claude()
        print()
        
        # Test OpenAI
        print("=" * 50)
        results['openai'] = self.ping_openai()
        print()
        
        # Test Local LLM
        print("=" * 50)
        results['local'] = self.ping_local_llm()
        print()
        
        # Summary
        print("=" * 50)
        print(info("Connection Summary:"))
        
        working_providers = []
        for provider, status in results.items():
            if status:
                print(success(f"  ✓ {provider.title()}: Connected"))
                working_providers.append(provider)
            else:
                print(error(f"  ✗ {provider.title()}: Failed"))
        
        if working_providers:
            print(success(f"\n✓ {len(working_providers)} provider(s) available: {', '.join(working_providers)}"))
            
            # Show recommendation
            if 'claude' in working_providers:
                print(info("Recommendation: Claude provides the best quality for job scraping"))
            elif 'local' in working_providers:
                print(info("Recommendation: Local LLM provides privacy and no costs"))
            elif 'openai' in working_providers:
                print(info("Recommendation: OpenAI provides reliable performance"))
        else:
            print(warning("✗ No AI providers are available"))
            print("Configure at least one provider to use JobSite's AI features:")
            print("  - Local LLM: Follow LM_STUDIO_SETUP.md")
            print("  - Claude API: Get key from https://console.anthropic.com/")
            print("  - OpenAI API: Get key from https://platform.openai.com/api-keys")
        
        return any(results.values())
    
    def test_job_scraping_capability(self, provider: str = "auto") -> bool:
        """Test AI provider's job scraping capability with a sample task"""
        print(info(f"Testing job scraping capability..."))
        
        # Sample HTML for testing
        sample_html = '''
        <div class="job-card">
            <h3 class="job-title">Senior Software Engineer</h3>
            <div class="company">Tech Corp</div>
            <div class="location">San Francisco, CA</div>
            <div class="salary">$120,000 - $180,000</div>
            <div class="description">We are looking for an experienced engineer...</div>
        </div>
        '''
        
        prompt = f"""Extract job information from this HTML and return as JSON:
        
        {sample_html}
        
        Return only JSON with title, company, location, salary fields."""
        
        try:
            if provider == "claude" and self.config.claude_api_key:
                import anthropic
                client = anthropic.Anthropic(api_key=self.config.claude_api_key)
                response = client.messages.create(
                    model=self.config.claude_model,
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                
            elif provider == "local" and self.config.local_llm_enabled:
                import openai
                client = openai.OpenAI(
                    base_url=self.config.local_llm_base_url,
                    api_key=self.config.local_llm_api_key
                )
                response = client.chat.completions.create(
                    model=self.config.local_llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.1
                )
                response_text = response.choices[0].message.content
                
            else:
                print(warning(f"Provider {provider} not available"))
                return False
            
            # Try to parse JSON response
            try:
                json.loads(response_text)
                print(success(f"✓ {provider.title()} can extract job data"))
                print(f"  Response: {response_text[:100]}...")
                return True
            except json.JSONDecodeError:
                print(warning(f"⚠ {provider.title()} responded but not in JSON format"))
                return False
                
        except Exception as e:
            print(error(f"✗ Job scraping test failed: {e}"))
            return False