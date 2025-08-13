# 🔐 RTO Authentication Integration Guide

## Step 1: Install Required Packages

```bash
pip install Flask-Dance requests python-dotenv
```

## Step 2: Update requirements.txt

Add these lines to your `requirements.txt`:
```text
Flask-Dance==7.0.0
requests==2.31.0
python-dotenv==1.0.0
```

## Step 3: Azure AD App Registration (5 minutes)

### 3.1 Go to Azure Portal
- Visit: https://portal.azure.com
- Sign in with your Microsoft account (or create one - it's free)

### 3.2 Create App Registration
1. Search for "Azure Active Directory"
2. Click "App registrations" → "New registration"
3. Fill in:
   - **Name**: `RTO Assessment Validation Tool`
   - **Supported account types**: `Accounts in any organizational directory (Any Azure AD directory - Multitenant)`
   - **Redirect URI**: `Web` → `http://localhost:5001/auth/authorized`

### 3.3 Get Credentials
After registration, copy these values:
- **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Directory (tenant) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 3.4 Create Client Secret
1. Go to "Certificates & secrets" → "New client secret"
2. Description: `RTO Validation Secret`
3. Expires: `24 months`
4. **Copy the secret VALUE** (not the ID)

### 3.5 Set Permissions
1. Go to "API permissions" → "Add a permission"
2. Choose "Microsoft Graph" → "Delegated permissions"
3. Add: `openid`, `email`, `profile`, `User.Read`
4. Click "Grant admin consent for [Your Organization]"

## Step 4: Environment Configuration

### 4.1 Create .env file
Create a `.env` file in your project root:

```bash
# Azure AD Configuration
AZURE_CLIENT_ID=your-application-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-value-here
AZURE_TENANT_ID=common

# Flask Configuration
SECRET_KEY=your-super-secret-key-for-sessions
FLASK_ENV=development
```

### 4.2 Update your main.py

```python
#!/usr/bin/env python3
"""
RTO Validation MVP - Main Application with Authentication
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing agents
from agents.fetch_agent import FetchAgent
from agents.extract_agent import ExtractAgent  
from agents.mapping_agent import MappingAgent
from agents.validation_agent import ValidationAgent
from config import Config

# Import the new authentication module
from auth_module import setup_authentication

app = Flask(__name__, template_folder='ui')
app.config.from_object(Config)

# Setup authentication
auth_manager = setup_authentication(app)

# Initialize agents (same as before)
fetch_agent = FetchAgent(app.config['GEMINI_API_KEY'])
extract_agent = ExtractAgent()
mapping_agent = MappingAgent(app.config['GEMINI_API_KEY'])
validation_agent = ValidationAgent()

@app.route('/')
def index():
    """Main page - now with authentication"""
    if not auth_manager.is_authenticated():
        return render_template('login.html')
    
    user = auth_manager.get_current_user()
    return render_template('index.html', user=user)

# Add authentication to existing routes
@app.route('/fetch-uoc', methods=['POST'])
@auth_manager.require_auth
def fetch_uoc():
    """Step 1: Fetch UoC data (now protected)"""
    # Your existing code here
    pass

@app.route('/dashboard/<session_id>')
@auth_manager.require_auth
def dashboard(session_id):
    """Main validation dashboard (now protected)"""
    # Your existing code here
    pass

# Admin routes with role-based access
@app.route('/admin')
@auth_manager.require_role(['Manager', 'Compliance Officer'])
def admin_panel():
    """Admin panel - only for managers and compliance officers"""
    return render_template('admin.html')

if __name__ == '__main__':
    print("🚀 Starting RTO Validation MVP with Authentication...")
    print("📊 Visit http://localhost:5001 to start")
    print("🔐 Users will be redirected to Microsoft login")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
```

## Step 5: Create Login Template

Create `ui/login.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTO Assessment Validation - Login</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }
        
        .login-container {
            background: white;
            padding: 3rem 2rem;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }
        
        .logo {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        h1 {
            color: #333;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 2rem;
        }
        
        .login-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 1rem;
            background: #0078d4;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1.1rem;
            transition: background-color 0.2s ease;
        }
        
        .login-btn:hover {
            background: #106ebe;
        }
        
        .microsoft-icon {
            margin-right: 0.5rem;
            font-size: 1.2rem;
        }
        
        .features {
            margin-top: 2rem;
            text-align: left;
        }
        
        .feature {
            display: flex;
            align-items: center;
            margin: 0.5rem 0;
            color: #666;
            font-size: 0.9rem;
        }
        
        .feature-icon {
            margin-right: 0.5rem;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🎯</div>
        <h1>RTO Assessment Validation</h1>
        <p class="subtitle">AI-Assisted Mapping for ASQA Audits</p>
        
        <a href="{{ url_for('login') }}" class="login-btn">
            <span class="microsoft-icon">🏢</span>
            Sign in with Microsoft
        </a>
        
        <div class="features">
            <div class="feature">
                <span class="feature-icon">✅</span>
                Works with your existing Microsoft account
            </div>
            <div class="feature">
                <span class="feature-icon">🔒</span>
                Secure organizational access
            </div>
            <div class="feature">
                <span class="feature-icon">📊</span>
                ASQA audit-ready documentation
            </div>
        </div>
    </div>
</body>
</html>
```

## Step 6: Update Existing Templates

Add user information to your existing templates. Update `ui/index.html`:

```html
<!-- Add this to the header section -->
<div class="user-info">
    <span>Welcome, {{ current_user.displayName }}!</span>
    <span class="role">{{ current_user.role }}</span>
    <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
</div>
```

## Step 7: Test the Authentication

### 7.1 Start the Application
```bash
python main.py
```

### 7.2 Test Login Flow
1. Visit `http://localhost:5001`
2. You should be redirected to the login page
3. Click "Sign in with Microsoft"
4. Complete Microsoft authentication
5. You should be redirected back to your app

### 7.3 Test User Roles
The system automatically assigns roles based on job titles:
- **Assessor**: trainers, assessors, teachers
- **Manager**: managers, directors, heads
- **Compliance Officer**: compliance, quality, audit staff
- **Training Staff**: education department staff
- **Validator**: default role

## Step 8: Production Deployment

### 8.1 Update Redirect URI
In Azure portal, add your production URL:
```
https://yourdomain.com/auth/authorized
```

### 8.2 Environment Variables for Production
```bash
# Production .env
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=common
SECRET_KEY=generate-a-strong-random-key
FLASK_ENV=production
```

## Step 9: Cost Information

### Azure AD B2C Pricing (Free Tier)
- ✅ **First 50,000 authentications/month: FREE**
- ✅ **Perfect for most RTOs**
- ✅ **No setup costs**
- ✅ **No monthly subscription**

For RTOs with 50+ staff doing daily authentication, you'd hit the free limit around 1,600 authentications per day - which is very generous.

## Troubleshooting

### Common Issues:

1. **"AADSTS700054: response_type 'code' is not enabled for the application"**
   - Solution: In Azure portal, ensure redirect URI is set correctly

2. **"The reply URL specified in the request does not match"**
   - Solution: Double-check the redirect URI matches exactly

3. **"User not found"**
   - Solution: Make sure API permissions include User.Read and admin consent is granted

### Test Users:
- Use any Microsoft account (personal or organizational)
- RTOs can test with their existing Office 365 accounts
- Personal Microsoft accounts also work for testing

## Next Steps

Once authentication is working:
1. ✅ Users can securely access the validation tool
2. ✅ Audit trail includes user information
3. ✅ Role-based access for different staff levels
4. ✅ Ready to add the report generation module

**Total setup time: ~30 minutes** 🚀