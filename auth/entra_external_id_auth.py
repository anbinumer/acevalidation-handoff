#!/usr/bin/env python3
"""
Microsoft Entra External ID Authentication Module
Replaces Azure AD B2C with the new Microsoft Entra External ID system
"""

import requests
import jwt
from urllib.parse import urlencode
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class EntraExternalIDAuth:
    """Microsoft Entra External ID authentication handler."""
    
    def __init__(self):
        # Load configuration from environment
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.tenant_name = os.getenv('AZURE_TENANT_NAME')
        self.policy_name = os.getenv('AZURE_POLICY_NAME', 'B2C_1_signupsignin')
        self.redirect_uri = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:5001/auth/callback')
        
        # Updated domain suffix for Entra External ID
        domain_suffix = os.getenv('AZURE_DOMAIN_SUFFIX', 'ciamlogin.com')
        
        # Authority URL for Entra External ID (new format)
        self.authority = f"https://{self.tenant_name}.{domain_suffix}/{self.tenant_name}.onmicrosoft.com/{self.policy_name}"
        
        # Validate configuration
        if not all([self.client_id, self.client_secret, self.tenant_name]):
            raise ValueError("Entra External ID configuration is incomplete. Please check your environment variables.")
        
        logger.info(f"Entra External ID Auth initialized for tenant: {self.tenant_name}")
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate authorization URL for Entra External ID."""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email',
            'response_mode': 'query'
        }
        
        if state:
            params['state'] = state
        
        auth_url = f"{self.authority}/oauth2/v2.0/authorize"
        full_url = f"{auth_url}?{urlencode(params)}"
        
        logger.info(f"Generated authorization URL for tenant: {self.tenant_name}")
        return full_url
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """Exchange authorization code for tokens using Entra External ID."""
        token_url = f"{self.authority}/oauth2/v2.0/token"
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            logger.info("Exchanging authorization code for tokens...")
            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            tokens = response.json()
            logger.info("Token exchange successful")
            return tokens
            
        except requests.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            raise Exception(f"Failed to exchange authorization code: {e}")
    
    def decode_token(self, token: str) -> Dict:
        """Decode JWT token from Entra External ID."""
        try:
            # For development, decode without verification
            # In production, you should verify the signature
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded
        except Exception as e:
            logger.error(f"Token decoding failed: {e}")
            raise Exception(f"Failed to decode token: {e}")
    
    def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Entra External ID token."""
        try:
            user_info = self.decode_token(access_token)
            
            # Extract user information from token claims
            return {
                'object_id': user_info.get('oid') or user_info.get('sub'),
                'email': user_info.get('email') or user_info.get('emails', [None])[0],
                'name': user_info.get('name', ''),
                'given_name': user_info.get('given_name', ''),
                'family_name': user_info.get('family_name', ''),
                'display_name': user_info.get('name', ''),
                'job_title': user_info.get('job_title', ''),
                'department': user_info.get('department', ''),
                'organization': user_info.get('organization', '')
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise Exception(f"Failed to get user information: {e}")
    
    def validate_invitation_token(self, token: str, invitation: Dict) -> bool:
        """Validate invitation token for Entra External ID."""
        try:
            # For Entra External ID, we can use the same token validation logic
            # but with updated domain verification
            invitation_id, token_hash = token.split(':', 1)
            
            if invitation_id != invitation['id']:
                return False
            
            # Regenerate expected token
            expected_token = self._generate_invitation_token(invitation)
            expected_hash = expected_token.split(':', 1)[1]
            
            return token_hash == expected_hash
            
        except Exception as e:
            logger.error(f"Error validating invitation token: {e}")
            return False
    
    def _generate_invitation_token(self, invitation: Dict) -> str:
        """Generate secure invitation token for Entra External ID."""
        import hashlib
        
        # Create a secure token based on invitation details
        token_data = f"{invitation['id']}:{invitation['email']}:{invitation['invited_at']}"
        secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
        
        # Generate hash
        token_hash = hashlib.sha256(f"{token_data}:{secret_key}".encode()).hexdigest()
        return f"{invitation['id']}:{token_hash[:32]}"

# Global auth instance
entra_external_id_auth = EntraExternalIDAuth()
