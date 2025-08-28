"""
Pydantic models for API requests
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
import re


class FacebookCookie(BaseModel):
    """Facebook cookie model"""
    domain: str
    name: str
    value: str
    path: str = "/"
    secure: bool = True
    httpOnly: bool = False
    sameSite: Optional[str] = None
    expirationDate: Optional[float] = None
    hostOnly: bool = False
    session: bool = False
    storeId: str = "0"


class ReactionsRequest(BaseModel):
    """Request model for reactions scraping"""
    post_url: str = Field(..., description="Facebook post URL")
    limit: int = Field(default=0, ge=0, le=10000, description="Number of reactions to scrape (0 = all)")
    delay: float = Field(default=2.0, ge=1.0, le=10.0, description="Delay between requests in seconds")
    cookies: List[FacebookCookie] = Field(..., description="Facebook cookies array")
    
    @validator('post_url')
    def validate_post_url(cls, v):
        """Validate Facebook post URL"""
        if not v or not isinstance(v, str):
            raise ValueError("post_url is required")
        
        v = v.strip()
        
        # Check if it's a Facebook URL
        if not ('facebook.com' in v or 'fb.com' in v):
            raise ValueError("Must be a Facebook URL")
        
        # Check for common Facebook post patterns
        valid_patterns = [
            r'/posts/',
            r'permalink\.php',
            r'/story\.php',
            r'fbid='
        ]
        
        if not any(re.search(pattern, v) for pattern in valid_patterns):
            raise ValueError("Invalid Facebook post URL format")
        
        return v
    
    @validator('cookies')
    def validate_cookies(cls, v):
        """Validate cookies array"""
        if not v or not isinstance(v, list):
            raise ValueError("cookies array is required")
        
        # Check for required cookies
        required_cookies = {'c_user', 'xs'}
        cookie_names = {cookie.name for cookie in v}
        
        missing_cookies = required_cookies - cookie_names
        if missing_cookies:
            raise ValueError(f"Missing required cookies: {missing_cookies}")
        
        # Validate Facebook domain
        facebook_cookies = [cookie for cookie in v if cookie.domain == '.facebook.com']
        if len(facebook_cookies) < 2:
            raise ValueError("Not enough valid Facebook cookies")
        
        return v


class CommentsRequest(BaseModel):
    """Request model for comments scraping"""
    post_url: str = Field(..., description="Facebook post URL")
    max_pages: Optional[int] = Field(default=None, ge=1, le=100, description="Maximum pages to scrape")
    delay: int = Field(default=10, ge=5, le=60, description="Delay between requests in seconds")
    cookies: List[FacebookCookie] = Field(..., description="Facebook cookies array")
    
    @validator('post_url')
    def validate_post_url(cls, v):
        """Validate Facebook post URL"""
        if not v or not isinstance(v, str):
            raise ValueError("post_url is required")
        
        v = v.strip()
        
        # Check if it's a Facebook URL
        if not ('facebook.com' in v or 'fb.com' in v):
            raise ValueError("Must be a Facebook URL")
        
        # Check for common Facebook post patterns
        valid_patterns = [
            r'/posts/',
            r'permalink\.php',
            r'/story\.php',
            r'fbid='
        ]
        
        if not any(re.search(pattern, v) for pattern in valid_patterns):
            raise ValueError("Invalid Facebook post URL format")
        
        return v
    
    @validator('cookies')
    def validate_cookies(cls, v):
        """Validate cookies array"""
        if not v or not isinstance(v, list):
            raise ValueError("cookies array is required")
        
        # Check for required cookies
        required_cookies = {'c_user', 'xs'}
        cookie_names = {cookie.name for cookie in v}
        
        missing_cookies = required_cookies - cookie_names
        if missing_cookies:
            raise ValueError(f"Missing required cookies: {missing_cookies}")
        
        # Validate Facebook domain
        facebook_cookies = [cookie for cookie in v if cookie.domain == '.facebook.com']
        if len(facebook_cookies) < 2:
            raise ValueError("Not enough valid Facebook cookies")
        
        return v

