"""
Centralized API Configuration
Single source of truth for all API endpoints and keys
"""

class APIConfig:
    """API Configuration for the entire project"""
    
    # Gemini AI API Configuration
    GEMINI_API_URL = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
    
    # API Request Configuration
    API_TIMEOUT = 10  # seconds
    API_MAX_RETRIES = 3
    
    # Response Configuration
    RESPONSE_FORMAT = "json"
    
    @classmethod
    def get_gemini_url(cls):
        """Get Gemini API URL"""
        return cls.GEMINI_API_URL
    
    @classmethod
    def update_gemini_url(cls, new_url):
        """Update Gemini API URL"""
        cls.GEMINI_API_URL = new_url
        print(f"✅ API URL updated to: {new_url[:60]}...")
    
    @classmethod
    def get_api_headers(cls):
        """Get standard API headers"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    @classmethod
    def get_request_config(cls):
        """Get request configuration"""
        return {
            'timeout': cls.API_TIMEOUT,
            'max_retries': cls.API_MAX_RETRIES
        }

# Global instance
api_config = APIConfig()

def get_api_config():
    """Get API configuration instance"""
    return api_config

def update_api_key(new_api_key):
    """
    Update API key across the project
    
    Args:
        new_api_key: New API key string
    """
    new_url = f"https://backend.buildpicoapps.com/aero/run/llm-api?pk={new_api_key}"
    api_config.update_gemini_url(new_url)
    return new_url
