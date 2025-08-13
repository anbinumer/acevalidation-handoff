#!/usr/bin/env python3
"""
Azure AD Authentication Module for RTO Assessment Validation
Supports both organizational and personal Microsoft accounts
"""

from flask import Flask, session, redirect, url_for, request, flash, jsonify
from flask_dance.contrib.azure import make_azure_blueprint, azure
from flask_dance.consumer import oauth_authorized
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RTOAuthManager:
    """Authentication manager for RTO organizations using Azure AD"""
    
    def __init__(self, app=None):
        self.app = app
        self.azure_bp = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize authentication with Flask app"""
        
        # Azure AD Configuration
        app.config.setdefault('AZURE_OAUTH_CLIENT_ID', os.environ.get('AZURE_CLIENT_ID'))
        app.config.setdefault('AZURE_OAUTH_CLIENT_SECRET', os.environ.get('AZURE_CLIENT_SECRET'))
        app.config.setdefault('AZURE_OAUTH_TENANT_ID', os.environ.get('AZURE_TENANT_ID', 'common'))
        
        # Session configuration
        app.config.setdefault('SECRET_KEY', os.environ.get('SECRET_KEY', 'rto-auth-secret-key'))
        app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(hours=8))
        
        # Create Azure blueprint
        self.azure_bp = make_azure_blueprint(
            client_id=app.config['AZURE_OAUTH_CLIENT_ID'],
            client_secret=app.config['AZURE_OAUTH_CLIENT_SECRET'],
            tenant=app.config['AZURE_OAUTH_TENANT_ID'],
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
                # Store user info in session
                session['user'] = user_info
                session['authenticated'] = True
                session['login_time'] = datetime.now().isoformat()
                session.permanent = True
                
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
        if any(keyword in job_title for keyword in ['trainer', 'assessor', 'teacher', 'educator']):
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

# Usage example for integration with main app
def setup_authentication(app):
    """Setup authentication for the RTO validation app"""
    
    # Initialize authentication manager
    auth_manager = RTOAuthManager(app)
    
    # Add authentication check to existing routes
    @app.before_request
    def check_authentication():
        """Check authentication for protected routes"""
        
        # Public routes that don't require authentication
        public_routes = ['login', 'azure.login', 'azure.authorized', 'static']
        
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

# Example usage in main.py
"""
# Add to your main.py imports
from auth_module import setup_authentication

# After creating your Flask app
app = Flask(__name__)
auth_manager = setup_authentication(app)

# Use decorators on routes that need authentication
@app.route('/dashboard/<session_id>')
@auth_manager.require_auth
def dashboard(session_id):
    # Your existing dashboard code
    pass

# Use role-based access control
@app.route('/admin')
@auth_manager.require_role(['Manager', 'Compliance Officer'])
def admin_panel():
    return render_template('admin.html')
"""

# Configuration setup instructions
SETUP_INSTRUCTIONS = """
🔧 Azure AD Setup Instructions for RTOs:

1. Go to Azure Portal (portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Set:
   - Name: "RTO Assessment Validation Tool"
   - Supported account types: "Accounts in any organizational directory (Any Azure AD directory - Multitenant)"
   - Redirect URI: "Web" -> "http://localhost:5001/auth/authorized"

5. After registration, note down:
   - Application (client) ID
   - Directory (tenant) ID

6. Go to "Certificates & secrets" > "New client secret"
   - Description: "RTO Validation Secret"
   - Expires: 24 months
   - Copy the secret VALUE (not ID)

7. Go to "API permissions"
   - Click "Add a permission"
   - Choose "Microsoft Graph"
   - Choose "Delegated permissions"
   - Add: openid, email, profile, User.Read
   - Click "Grant admin consent"

8. Set environment variables:
   export AZURE_CLIENT_ID="your-application-id"
   export AZURE_CLIENT_SECRET="your-client-secret"
   export AZURE_TENANT_ID="common"  # or your specific tenant ID

9. Install required packages:
   pip install Flask-Dance requests

10. For production, update redirect URI to your domain:
    "https://yourdomain.com/auth/authorized"
"""

if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)