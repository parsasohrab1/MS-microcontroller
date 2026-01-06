"""
OAuth 2.0 / OpenID Connect Implementation
پیاده‌سازی OAuth 2.0 و OpenID Connect برای احراز هویت استاندارد
"""

from typing import Optional, Dict, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger
import httpx
import os


# ============================================================================
# Configuration
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OAuth 2.0 / OIDC Configuration
OAUTH2_AUTHORIZATION_URL = os.getenv("OAUTH2_AUTHORIZATION_URL", "")
OAUTH2_TOKEN_URL = os.getenv("OAUTH2_TOKEN_URL", "")
OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID", "")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET", "")
OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI", "")
OIDC_DISCOVERY_URL = os.getenv("OIDC_DISCOVERY_URL", "")

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_authorization_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=OAUTH2_AUTHORIZATION_URL,
    tokenUrl=OAUTH2_TOKEN_URL
)


# ============================================================================
# Models
# ============================================================================

class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None


class TokenData(BaseModel):
    """Token data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    scopes: List[str] = []


class OIDCUserInfo(BaseModel):
    """OpenID Connect User Info"""
    sub: str  # Subject (user ID)
    email: Optional[str] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: Optional[bool] = None


# ============================================================================
# OAuth 2.0 / OIDC Provider
# ============================================================================

class OAuth2Provider:
    """OAuth 2.0 Provider"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.discovery_cache: Optional[Dict] = None
        self.discovery_cache_time: Optional[datetime] = None
    
    async def discover_oidc_config(self) -> Dict:
        """
        دریافت OIDC discovery configuration
        
        Returns:
            OIDC configuration
        """
        if self.discovery_cache and self.discovery_cache_time:
            # استفاده از cache (1 hour)
            if (datetime.now() - self.discovery_cache_time).total_seconds() < 3600:
                return self.discovery_cache
        
        if not OIDC_DISCOVERY_URL:
            raise ValueError("OIDC_DISCOVERY_URL not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(OIDC_DISCOVERY_URL)
                response.raise_for_status()
                config = response.json()
                
                self.discovery_cache = config
                self.discovery_cache_time = datetime.now()
                
                return config
        
        except Exception as e:
            logger.error(f"Error discovering OIDC config: {e}")
            raise
    
    def get_authorization_url(self, state: str, scopes: List[str] = None) -> str:
        """
        دریافت authorization URL
        
        Args:
            state: State parameter برای CSRF protection
            scopes: لیست scopes
        
        Returns:
            Authorization URL
        """
        if not scopes:
            scopes = ["openid", "profile", "email"]
        
        params = {
            "response_type": "code",
            "client_id": OAUTH2_CLIENT_ID,
            "redirect_uri": OAUTH2_REDIRECT_URI,
            "scope": " ".join(scopes),
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{OAUTH2_AUTHORIZATION_URL}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        تبدیل authorization code به access token
        
        Args:
            code: Authorization code
        
        Returns:
            Token response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    OAUTH2_TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": OAUTH2_REDIRECT_URI,
                        "client_id": OAUTH2_CLIENT_ID,
                        "client_secret": OAUTH2_CLIENT_SECRET
                    }
                )
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise
    
    async def get_user_info(self, access_token: str) -> OIDCUserInfo:
        """
        دریافت user info از OIDC provider
        
        Args:
            access_token: Access token
        
        Returns:
            User info
        """
        try:
            # دریافت userinfo endpoint از discovery
            config = await self.discover_oidc_config()
            userinfo_endpoint = config.get("userinfo_endpoint")
            
            if not userinfo_endpoint:
                raise ValueError("userinfo_endpoint not found in OIDC config")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_info = response.json()
                
                return OIDCUserInfo(**user_info)
        
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            New token response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    OAUTH2_TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": OAUTH2_CLIENT_ID,
                        "client_secret": OAUTH2_CLIENT_SECRET
                    }
                )
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise


# ============================================================================
# Token Management
# ============================================================================

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    ایجاد access token
    
    Args:
        data: داده برای encode
        expires_delta: مدت زمان انقضا
    
    Returns:
        Access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """
    ایجاد refresh token
    
    Args:
        data: داده برای encode
    
    Returns:
        Refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    بررسی و decode token
    
    Args:
        token: Token برای بررسی
    
    Returns:
        Token data یا None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        scopes: List[str] = payload.get("scopes", [])
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, email=email, scopes=scopes)
    
    except JWTError:
        return None


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Dependency برای دریافت user فعلی از token
    
    Args:
        token: Access token
    
    Returns:
        Token data
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    return token_data


# Singleton instance
_oauth2_provider: Optional[OAuth2Provider] = None


def get_oauth2_provider() -> OAuth2Provider:
    """دریافت instance OAuth2 provider"""
    global _oauth2_provider
    if _oauth2_provider is None:
        _oauth2_provider = OAuth2Provider()
    return _oauth2_provider

