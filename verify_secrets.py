#!/usr/bin/env python3
"""
Script to verify that GitHub secrets are properly configured.
Run this in Codespaces to check your environment setup.
"""

import os
import json
import sys

def check_secret(secret_name, is_json=False):
    """Check if a secret exists and is valid."""
    print(f"\n{'='*60}")
    print(f"Checking: {secret_name}")
    print(f"{'='*60}")
    
    value = os.environ.get(secret_name)
    
    if not value:
        print(f"❌ MISSING: {secret_name} is not set")
        return False
    
    print(f"✅ FOUND: {secret_name} is set")
    print(f"   Length: {len(value)} characters")
    
    if is_json:
        try:
            parsed = json.loads(value)
            print(f"✅ VALID JSON: Successfully parsed")
            print(f"   Keys: {list(parsed.keys())}")
            
            # Check credential type
            cred_type = parsed.get('type', 'authorized_user')
            print(f"   Type: {cred_type}")
            
            if cred_type == 'authorized_user':
                required_keys = ['client_id', 'client_secret', 'refresh_token']
            else:
                required_keys = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            
            missing_keys = [key for key in required_keys if key not in parsed]
            if missing_keys:
                print(f"⚠️  WARNING: Missing keys: {missing_keys}")
            else:
                print(f"✅ All required keys present")
                
            return True
        except json.JSONDecodeError as e:
            print(f"❌ INVALID JSON: {e}")
            return False
    
    return True

def main():
    """Main verification function."""
    print("\n" + "="*60)
    print("🔍 GitHub Secrets Verification for Codespaces")
    print("="*60)
    
    all_good = True
    
    # Check Gmail credentials
    all_good &= check_secret('GMAIL_CREDENTIALS_JSON', is_json=True)
    
    # Check OpenAI API key (optional)
    has_openai = check_secret('OPENAI_API_KEY', is_json=False)
    if not has_openai:
        print("   Note: OPENAI_API_KEY is optional for some features")
    
    print("\n" + "="*60)
    if all_good:
        print("✅ ALL REQUIRED SECRETS ARE PROPERLY CONFIGURED!")
        print("="*60)
        print("\nYou can now run:")
        print("  python main.py")
        print("  python test_gmail_client_integration.py")
        return 0
    else:
        print("❌ SOME SECRETS ARE MISSING OR INVALID")
        print("="*60)
        print("\nPlease add secrets at:")
        print("  https://github.com/settings/codespaces (User secrets)")
        print("  or")
        print("  https://github.com/jianranli/email-organizer-ai/settings/secrets/codespaces")
        return 1

if __name__ == "__main__":
    sys.exit(main())
