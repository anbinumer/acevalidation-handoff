# 🚀 Microsoft Entra External ID Setup Guide

## Overview

Microsoft has rebranded Azure AD B2C to **Microsoft Entra External ID**. This guide will help you set up the new authentication system for the RTO Validation Tool.

## 🔄 What Changed

### From Azure AD B2C → Microsoft Entra External ID:
- ✅ **Same functionality** - all features work the same
- ✅ **Better UI** - improved admin portal
- ✅ **Enhanced security** - better threat protection
- ✅ **Same APIs** - minimal code changes needed
- 🔄 **New domain format** - `*.ciamlogin.com` instead of `*.b2clogin.com`
- 🔄 **Updated portal** - new Microsoft Entra admin center

## 📋 Prerequisites

- Microsoft Azure subscription
- Global Administrator or Application Administrator permissions
- Python 3.8+ with pip

## 🎯 Step-by-Step Setup

### Step 1: Create Microsoft Entra External ID Tenant (10 minutes)

1. **Go to Azure Portal**: https://portal.azure.com
2. **Search for "Microsoft Entra External ID"**
3. Click **"External Identities"** → **"External tenants"**
4. Click **"Create tenant"**
5. Select **"Microsoft Entra External ID"**

**Fill out the form:**
```
Tenant type: External ID (for customers)
Organization name: RTO Validation System
Initial domain: rto-validation (creates rto-validation.ciamlogin.com)
Country/Region: Australia
Resource group: Create new → rto-external-id-rg
```

6. Click **Create** (takes 3-5 minutes)

### Step 2: Switch to External ID Tenant

1. After creation, **switch directory** to your new External ID tenant
2. You'll see the new **Microsoft Entra admin center** interface

### Step 3: Register Application

1. Go to **"App registrations"**
2. Click **"New registration"**

**Fill out:**
```
Name: RTO Validation System
Supported account types: Accounts in this organizational directory only
Redirect URI: 
  Platform: Web
  URL: http://localhost:5001/auth/callback
```

3. Click **Register**

**📝 Save these values:**
```
Application (client) ID: [COPY THIS]
Directory (tenant) ID: [COPY THIS]
```

### Step 4: Create Client Secret

1. Go to **"Certificates & secrets"**
2. Click **"New client secret"**
3. Description: `RTO Validation Secret`
4. Expiry: `6 months`
5. **Copy the secret value immediately** (you won't see it again)

### Step 5: Create User Flow

1. Go to **"User flows"**
2. Click **"New user flow"**
3. Select **"Sign up and sign in"**
4. Name: `B2C_1_signupsignin`

**Configure:**
- **Identity providers**: Email signup
- **User attributes**: Email, Display Name, Given Name, Surname
- **Application claims**: Same attributes + Object ID

## 🔧 Environment Configuration

### Update your `.env` file:

```env
# Microsoft Entra External ID Configuration
AZURE_CLIENT_ID=your-application-client-id
AZURE_CLIENT_SECRET=your-client-secret-value
AZURE_TENANT_NAME=rto-validation
AZURE_POLICY_NAME=B2C_1_signupsignin
AZURE_DOMAIN_SUFFIX=ciamlogin.com

# Application Settings
SECRET_KEY=your-super-secret-key-change-in-production
APP_URL=http://localhost:5001
APP_NAME=RTO Assessment Validation Tool

# Email Configuration (Optional)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@yourdomain.com
SMTP_PASSWORD=your-email-password
FROM_EMAIL=your-email@yourdomain.com
FROM_NAME=RTO Assessment Validation System

# API Configuration
GEMINI_API_KEY=your-gemini-api-key-here
RTO_API_BASE_URL=https://training.gov.au/api/v1

# File Storage
UPLOAD_FOLDER=storage/uploads
VALIDATOR_STORAGE=storage/validators

# Testing Configuration
TESTING=False
```

## 🧪 Test the Setup

### Create test script: `test_entra_setup.py`

```python
#!/usr/bin/env python3
"""
Test Microsoft Entra External ID Configuration
"""

from dotenv import load_dotenv
import os
import sys

# Add auth directory to path
sys.path.append('auth')

load_dotenv()

def test_entra_configuration():
    """Test Entra External ID configuration"""
    print("🔍 Testing Microsoft Entra External ID Configuration...")
    print("=" * 60)
    
    # Check required environment variables
    required_vars = [
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET', 
        'AZURE_TENANT_NAME',
        'AZURE_POLICY_NAME',
        'AZURE_DOMAIN_SUFFIX'
    ]
    
    config_ok = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            display_value = value[:8] + '...' if len(value) > 8 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: MISSING!")
            config_ok = False
    
    if not config_ok:
        print("\n❌ Configuration incomplete. Please check your .env file.")
        return False
    
    # Test authorization URL generation
    print("\n🌐 Testing Authorization URL Generation:")
    try:
        from entra_external_id_auth import entra_external_id_auth
        auth_url = entra_external_id_auth.get_authorization_url()
        print(f"✅ URL generated successfully!")
        print(f"📍 {auth_url[:80]}...")
        print("\n🎯 Microsoft Entra External ID is ready!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_entra_configuration()
    sys.exit(0 if success else 1)
```

### Run the test:

```bash
python test_entra_setup.py
```

## 🚀 Run the Application

### Install dependencies:

```bash
pip install -r requirements.txt
```

### Start the application:

```bash
python app_with_auth.py
```

### Access the application:

- **Main app**: http://localhost:5001
- **Admin dashboard**: http://localhost:5001/admin
- **Login page**: http://localhost:5001/login

## 🔍 Troubleshooting

### Common Issues:

#### 1. "AADSTS700054: response_type 'code' is not enabled"
**Solution**: Ensure redirect URI is exactly `http://localhost:5001/auth/callback`

#### 2. "The reply URL specified in the request does not match"
**Solution**: Double-check redirect URI matches app registration

#### 3. "User not found"
**Solution**: Verify API permissions include User.Read

#### 4. "Invalid tenant" errors
**Solution**: Ensure AZURE_TENANT_NAME matches your External ID tenant name

### Debug Mode:

```python
# Enable detailed logging
logging.getLogger('auth').setLevel(logging.DEBUG)
```

## 📊 Migration Summary

### What's the same:
- ✅ Authentication flow (OAuth 2.0)
- ✅ JWT tokens and claims
- ✅ User management
- ✅ Most Flask integration code
- ✅ Invitation system
- ✅ Role-based access control

### What's different:
- 🔄 Portal interface (newer, better)
- 🔄 Domain format: `*.ciamlogin.com`
- 🔄 Configuration variable names
- 🔄 Better security features

### Code changes needed:
- ✅ Updated environment variables
- ✅ New authentication module
- ✅ Updated configuration
- ✅ Same Flask routes and templates

## 🎉 Success!

Your RTO Validation Tool now uses **Microsoft Entra External ID** with:

✅ **Modern authentication** with enhanced security  
✅ **Professional user experience** with Microsoft branding  
✅ **Flexible user management** for external validators  
✅ **Seamless SSO** with any Microsoft account  
✅ **Future-proof architecture** using Microsoft's latest identity platform  

**Total setup time: ~30 minutes**  
**Code changes: Minimal (95% same code)**  
**Cost: FREE (Entra External ID free tier)**

Ready to revolutionize your RTO's validator onboarding! 🚀
