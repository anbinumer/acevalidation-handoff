#!/usr/bin/env python3
"""
Enhanced Azure AD Authentication Module for RTO Assessment Validation
Supports organizational accounts, personal Microsoft accounts, and validator invitations
"""

from flask import Flask, session, redirect, url_for, request, flash, jsonify
from flask_dance.contrib.azure import make_azure_blueprint, azure
from flask_dance.consumer import oauth_authorized
import os
from datetime import datetime, timedelta
import logging
import json
from .entra_external_id_auth import entra_external_id_auth

logger = logging.getLogger(__name__)

class RTOAuthManager:
    """Enhanced authentication manager for RTO organizations with validator invitation support"""
    
    def __init__(self, app=None):
        self.app = app
        self.azure_bp = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize authentication with Flask app"""
        
        # Microsoft Entra External ID Configuration
        app.config.setdefault('AZURE_OAUTH_CLIENT_ID', os.environ.get('AZURE_CLIENT_ID'))
        app.config.setdefault('AZURE_OAUTH_CLIENT_SECRET', os.environ.get('AZURE_CLIENT_SECRET'))
        app.config.setdefault('AZURE_TENANT_NAME', os.environ.get('AZURE_TENANT_NAME'))
        app.config.setdefault('AZURE_POLICY_NAME', os.environ.get('AZURE_POLICY_NAME', 'B2C_1_signupsignin'))
        app.config.setdefault('AZURE_DOMAIN_SUFFIX', os.environ.get('AZURE_DOMAIN_SUFFIX', 'ciamlogin.com'))
        
        # Session configuration
        app.config.setdefault('SECRET_KEY', os.environ.get('SECRET_KEY', 'rto-auth-secret-key'))
        app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(hours=8))
        
        # Create Microsoft Entra External ID blueprint
        # Note: Flask-Dance Azure blueprint still works with Entra External ID
        # but we need to configure it for the new domain format
        self.azure_bp = make_azure_blueprint(
            client_id=app.config['AZURE_OAUTH_CLIENT_ID'],
            client_secret=app.config['AZURE_OAUTH_CLIENT_SECRET'],
            tenant=app.config['AZURE_TENANT_NAME'],  # Use tenant name instead of ID
            scope=["openid", "email", "profile", "User.Read"],
            redirect_url="/auth/callback",
            storage=None  # Use Flask sessions
        )
        
        # Register blueprint
        app.register_blueprint(self.azure_bp, url_prefix="/auth")
        
        # Add auth routes
        self._add_auth_routes(app)
        
        # Add template globals
        app.jinja_env.globals['current_user'] = self.get_current_user
        app.jinja_env.globals['is_authenticated'] = self.is_authenticated
        
        logger.info("RTO Authentication initialized")
    
    def _add_auth_routes(self, app):
        """Add authentication routes to the app"""
        
        @app.route('/login')
        def login():
            """Redirect to Azure AD login"""
            if not azure.authorized:
                return redirect(url_for("azure.login"))
            return redirect(url_for('index'))
        
        @app.route('/logout')
        def logout():
            """Logout user and clear session"""
            session.clear()
            flash('You have been logged out successfully.', 'info')
            return redirect(url_for('index'))
        
        @app.route('/auth/profile')
        def auth_profile():
            """Display user profile information"""
            if not self.is_authenticated():
                return redirect(url_for('login'))
            
            user_info = self.get_current_user()
            return jsonify(user_info)
        
        # OAuth callback handler
        @oauth_authorized.connect_via(self.azure_bp)
        def azure_logged_in(blueprint, token):
            """Handle successful Azure AD login"""
            if not token:
                flash("Failed to log in with Azure AD.", "error")
                return False
            
            # Get user information
            user_info = self._get_user_info_from_token()
            if user_info:
                # Check if user is an invited validator
                from .validator_manager import ValidatorManager
                validator_manager = ValidatorManager()
                
                # Store user info in session
                session['user'] = user_info
                session['authenticated'] = True
                session['login_time'] = datetime.now().isoformat()
                session.permanent = True
                
                # Check validator status
                validator_status = validator_manager.get_validator_status(user_info['email'])
                if validator_status:
                    session['user']['validator_status'] = validator_status['status']
                    session['user']['rto_id'] = validator_status.get('rto_id')
                    session['user']['invited_by'] = validator_status.get('invited_by')
                
                # Log successful login
                logger.info(f"User logged in: {user_info.get('email', 'unknown')}")
                flash(f"Welcome, {user_info.get('displayName', 'User')}!", "success")
                
                return False  # Don't save token to storage
            else:
                flash("Failed to get user information from Azure AD.", "error")
                return False
    
    def _get_user_info_from_token(self):
        """Get user information from Azure AD using the access token"""
        if not azure.authorized:
            return None
        
        try:
            # Call Microsoft Graph API to get user info
            resp = azure.get("/v1.0/me")
            if resp.ok:
                user_data = resp.json()
                
                # Extract relevant user information for RTO context
                user_info = {
                    'id': user_data.get('id'),
                    'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                    'displayName': user_data.get('displayName'),
                    'firstName': user_data.get('givenName'),
                    'lastName': user_data.get('surname'),
                    'jobTitle': user_data.get('jobTitle'),
                    'department': user_data.get('department'),
                    'organization': user_data.get('companyName'),
                    'role': self._determine_user_role(user_data),
                    'avatar_url': None  # Can be added later if needed
                }
                
                return user_info
            else:
                logger.error(f"Failed to get user info: {resp.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
    def _determine_user_role(self, user_data):
        """Determine user role for RTO context based on job title or department"""
        job_title = (user_data.get('jobTitle') or '').lower()
        department = (user_data.get('department') or '').lower()
        
        # RTO-specific role mapping
        if any(keyword in job_title for keyword in ['admin', 'administrator', 'ceo', 'president']):
            return 'Admin'
        elif any(keyword in job_title for keyword in ['trainer', 'assessor', 'teacher', 'educator']):
            return 'Assessor'
        elif any(keyword in job_title for keyword in ['manager', 'director', 'head', 'lead']):
            return 'Manager'
        elif any(keyword in job_title for keyword in ['compliance', 'quality', 'audit']):
            return 'Compliance Officer'
        elif any(keyword in department for keyword in ['training', 'education', 'vet']):
            return 'Training Staff'
        else:
            return 'Validator'  # Default role
    
    def is_authenticated(self):
        """Check if user is currently authenticated"""
        return session.get('authenticated', False) and azure.authorized
    
    def get_current_user(self):
        """Get current user information from session"""
        if self.is_authenticated():
            return session.get('user', {})
        return None
    
    def require_auth(self, f):
        """Decorator to require authentication for routes"""
        def decorated_function(*args, **kwargs):
            if not self.is_authenticated():
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    def require_role(self, required_roles):
        """Decorator to require specific roles"""
        def decorator(f):
            def decorated_function(*args, **kwargs):
                if not self.is_authenticated():
                    return redirect(url_for('login'))
                
                user = self.get_current_user()
                user_role = user.get('role', 'Validator')
                
                if isinstance(required_roles, str):
                    required_roles_list = [required_roles]
                else:
                    required_roles_list = required_roles
                
                if user_role not in required_roles_list:
                    flash(f"Access denied. Required role: {', '.join(required_roles_list)}", "error")
                    return redirect(url_for('index'))
                
                return f(*args, **kwargs)
            decorated_function.__name__ = f.__name__
            return decorated_function
        return decorator

# Setup function for easy integration
def setup_authentication(app):
    """Setup authentication for the RTO validation app"""
    
    # Initialize authentication manager
    auth_manager = RTOAuthManager(app)
    
    # Add authentication check to existing routes
    @app.before_request
    def check_authentication():
        """Check authentication for protected routes"""
        
        # Public routes that don't require authentication
        public_routes = [
            'login', 'azure.login', 'azure.authorized', 'static', 
            'validator_signup', 'admin_invite_validator'
        ]
        
        # Check if current endpoint requires authentication
        if request.endpoint and not any(route in request.endpoint for route in public_routes):
            if not auth_manager.is_authenticated():
                return redirect(url_for('login'))
    
    # Update existing routes with user context
    @app.context_processor
    def inject_user():
        """Inject user information into templates"""
        return {
            'current_user': auth_manager.get_current_user(),
            'is_authenticated': auth_manager.is_authenticated()
        }
    
    return auth_manager