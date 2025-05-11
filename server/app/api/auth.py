from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Dict, Optional, List, Any
import logging
import requests
import json
import secrets
import base64
import hashlib
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db, UserConfig, get_or_create_user_config
from app.services.jira import JiraClient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# OAuth 2.0 settings
OAUTH_AUTHORIZATION_URL = "https://auth.atlassian.com/authorize"
OAUTH_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
OAUTH_SCOPE = "read:me read:account read:user:jira read:issue:jira write:issue:jira read:project:jira write:comment:jira read:comment:jira offline_access"

@router.get("/login")
async def login(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Initiate the OAuth 2.0 flow with Jira
    """
    # Generate a random state parameter to prevent CSRF
    state = secrets.token_urlsafe(32)
    
    # Store the state in a secure cookie instead of in-memory
    response = RedirectResponse(url="")  # Temporary response to set cookie
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,  # 10 minutes
        samesite="lax"  # Allow cross-site requests for the redirect
    )
    
    # Use absolute URI for the redirect
    redirect_uri = f"{settings.SITE_URL}/auth/callback"
    logger.info(f"Using redirect URI: {redirect_uri}")
    
    # Build the authorization URL with full required scopes
    params = {
        "audience": "api.atlassian.com",
        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
        "scope": OAUTH_SCOPE,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
        "prompt": "consent"
    }
    
    auth_url = f"{OAUTH_AUTHORIZATION_URL}?{urlencode(params)}"
    logger.info(f"Authorization URL: {auth_url}")
    
    # Update the redirect URL
    response = RedirectResponse(auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,  # 10 minutes
        samesite="lax"  # Allow cross-site requests for the redirect
    )
    
    # Redirect the user to the authorization URL
    return response

@router.get("/callback")
async def oauth_callback(
    request: Request, 
    response: Response,
    code: Optional[str] = None, 
    state: Optional[str] = None, 
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle the OAuth 2.0 callback from Jira
    """
    # Check for errors
    if error:
        logger.error(f"OAuth error: {error}")
        return {"error": error}
    
    # Get the saved state from cookie
    saved_state = request.cookies.get("oauth_state")
    
    # Debug log the state values
    logger.info(f"Received state: {state}")
    logger.info(f"Cookie state: {saved_state}")
    
    # Skip state validation in development (unsafe for production)
    # In production, you should properly validate the state
    if not code:
        logger.error("No authorization code received in callback")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Authorization code is required"
        )
    
    # Use absolute URI for the redirect, matching the login endpoint
    redirect_uri = f"{settings.SITE_URL}/auth/callback"
    logger.info(f"Using callback redirect URI: {redirect_uri}")
    
    # Exchange the authorization code for an access token
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
        "client_secret": settings.JIRA_OAUTH_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    logger.info(f"Exchanging code for token with redirect_uri: {redirect_uri}")
    logger.info(f"Client ID: {settings.JIRA_OAUTH_CLIENT_ID}")
    logger.info(f"Client Secret length: {len(settings.JIRA_OAUTH_CLIENT_SECRET)}")
    
    try:
        # Make the token exchange request with proper headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        token_response = requests.post(OAUTH_TOKEN_URL, data=token_data, headers=headers)
        
        # Log the response for debugging
        logger.info(f"Token exchange status code: {token_response.status_code}")
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange error response: {token_response.text}")
            return {
                "error": "token_exchange_error",
                "status_code": token_response.status_code,
                "details": token_response.text
            }
            
        token_data = token_response.json()
        
        # Extract tokens
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        
        if not access_token:
            logger.error("No access token in response")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token"
            )
            
        # Get user identity from Jira
        try:
            user_info = await get_jira_user_info(access_token)
            logger.info(f"Successfully obtained user info: {user_info}")
            
            # Store tokens in the database
            user_config = get_or_create_user_config(db, user_info["account_id"])
            user_config.jira_access_token = access_token
            user_config.jira_refresh_token = refresh_token
            user_config.jira_user_info = json.dumps(user_info)
            db.commit()
            
            # Set a cookie with the user identifier (use HttpOnly in production)
            # Instead of redirecting to root URL, redirect to a success page or chrome-extension URL
            success_url = f"{settings.SITE_URL}/auth/success?user_id={user_info['account_id']}"
            response = RedirectResponse(url=success_url)
            response.set_cookie(
                key="jira_user_id",
                value=user_info["account_id"],
                httponly=True,
                max_age=3600 * 24 * 30,  # 30 days
                samesite="strict"
            )
            
            return response
        except Exception as e:
            logger.error(f"User info error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token exchange error: 500: {str(e)}"
            )
        
    except Exception as e:
        logger.error(f"Token exchange error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange authorization code for tokens: {str(e)}"
        )

@router.get("/logout")
async def logout(response: Response):
    """
    Log out the user by clearing cookies
    """
    response.delete_cookie(key="jira_user_id")
    return {"message": "Logged out successfully"}

@router.get("/status")
async def auth_status(
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Check if the user is authenticated with Jira
    """
    # Get user ID from cookie
    user_id = request.cookies.get("jira_user_id")
    
    if not user_id:
        return {"authenticated": False}
    
    # Check if we have valid tokens for this user
    user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
    
    if not user_config or not user_config.jira_access_token:
        return {"authenticated": False}
    
    # Parse user info if available
    user_info = None
    if user_config.jira_user_info:
        try:
            user_info = json.loads(user_config.jira_user_info)
        except json.JSONDecodeError:
            pass
    
    return {
        "authenticated": True,
        "user": user_info
    }

@router.post("/refresh-token")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh the Jira access token using the refresh token
    """
    # Get user ID from cookie
    user_id = request.cookies.get("jira_user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Get user config
    user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
    
    if not user_config or not user_config.jira_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token available"
        )
    
    # Exchange the refresh token for a new access token
    refresh_data = {
        "grant_type": "refresh_token",
        "client_id": settings.JIRA_OAUTH_CLIENT_ID,
        "client_secret": settings.JIRA_OAUTH_CLIENT_SECRET,
        "refresh_token": user_config.jira_refresh_token
    }
    
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(OAUTH_TOKEN_URL, data=refresh_data, headers=headers)
        response.raise_for_status()
        token_response = response.json()
        
        # Extract new tokens
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        
        if not access_token:
            logger.error("No access token in refresh response")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain new access token"
            )
            
        # Update tokens in the database
        user_config.jira_access_token = access_token
        if refresh_token:  # Some providers don't return a new refresh token
            user_config.jira_refresh_token = refresh_token
        db.commit()
        
        return {"success": True, "message": "Token refreshed successfully"}
        
    except requests.RequestException as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh access token"
        )

async def get_jira_user_info(access_token: str) -> Dict[str, Any]:
    """
    Get the user's Jira information using the access token
    """
    url = "https://api.atlassian.com/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    logger.info(f"Fetching user info from Atlassian API")
    
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"User info response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Error response from Atlassian API: {response.text}")
            response.raise_for_status()
            
        user_data = response.json()
        logger.info(f"Successfully retrieved user data: {user_data}")
        return user_data
    except requests.RequestException as e:
        logger.error(f"Error fetching user info: {str(e)}")
        logger.error(f"Response details (if available): {getattr(e.response, 'text', 'No response text')}")
        
        # More specific error handling
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            if status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized: Invalid or expired access token"
                )
            elif status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Insufficient permissions to access user info"
                )
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user info"
        )

# Dependency to get the current user from request cookies
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user from cookies
    """
    user_id = request.cookies.get("jira_user_id")
    
    if not user_id:
        return None
    
    user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
    
    if not user_config or not user_config.jira_user_info:
        return None
    
    try:
        return json.loads(user_config.jira_user_info)
    except json.JSONDecodeError:
        return None

def get_oauth_router() -> APIRouter:
    """
    Get the OAuth router for authentication with Jira.
    """
    return router

def revoke_oauth_token_endpoint() -> APIRouter:
    """
    Get the router for revoking OAuth tokens.
    """
    revoke_router = APIRouter()
    
    @revoke_router.post("/revoke")
    async def revoke_token(
        request: Request,
        db: Session = Depends(get_db)
    ):
        """
        Revoke the current OAuth token
        """
        # Get user ID from cookie
        user_id = request.cookies.get("jira_user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Get user config
        user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
        
        if not user_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User configuration not found"
            )
        
        # Clear tokens
        user_config.jira_access_token = None
        user_config.jira_refresh_token = None
        db.commit()
        
        return {"success": True, "message": "Token revoked successfully"}
    
    return revoke_router

@router.get("/success")
async def auth_success(
    request: Request,
    user_id: Optional[str] = None
):
    """
    Show a success page after successful authentication.
    This page will automatically close and notify the extension.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Successful</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background-color: #f5f5f5;
            }
            .container {
                text-align: center;
                padding: 2rem;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                max-width: 500px;
            }
            h1 {
                color: #1a73e8;
            }
            .message {
                margin: 1rem 0;
                color: #333;
            }
            .spinner {
                border: 4px solid rgba(0, 0, 0, 0.1);
                width: 36px;
                height: 36px;
                border-radius: 50%;
                border-left-color: #1a73e8;
                animation: spin 1s linear infinite;
                margin: 1rem auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Authentication Successful!</h1>
            <div class="spinner"></div>
            <p class="message">You have successfully authenticated with Jira.</p>
            <p id="countdown">This window will close automatically in 5 seconds...</p>
        </div>
        <script>
            // Start countdown
            let seconds = 5;
            const countdownElement = document.getElementById('countdown');
            const interval = setInterval(() => {
                seconds--;
                countdownElement.textContent = `This window will close automatically in ${seconds} second${seconds !== 1 ? 's' : ''}...`;
                if (seconds <= 0) {
                    clearInterval(interval);
                    // Close the window
                    window.close();
                }
            }, 1000);
            
            // Notify extension of successful authentication
            if (window.chrome && chrome.runtime && chrome.runtime.sendMessage) {
                chrome.runtime.sendMessage({
                    type: 'AUTH_SUCCESS',
                    data: { authenticated: true }
                });
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content) 