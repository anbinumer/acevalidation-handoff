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
        from auth.entra_external_id_auth import entra_external_id_auth
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
