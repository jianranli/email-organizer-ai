#!/usr/bin/env python3
"""
Generate Gmail OAuth credentials with proper scopes for Email Organizer AI.

This script helps you create the GMAIL_CREDENTIALS_JSON that you need to 
set in your GitHub Codespaces secrets.
"""

import json
import os
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Required scopes for the Email Organizer AI
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

def open_url_in_codespaces(url):
    """Open URL in host browser from Codespaces."""
    try:
        # In Codespaces, $BROWSER should open in the host browser
        if os.environ.get('CODESPACES'):
            os.system(f'"{os.environ.get("BROWSER", "xdg-open")}" {url}')
        else:
            webbrowser.open(url)
    except:
        pass

def main():
    print("\n" + "="*70)
    print("Gmail OAuth Credentials Generator")
    print("="*70)
    print("\nThis will generate credentials with the following scopes:")
    for scope in SCOPES:
        print(f"  • {scope}")
    print("\n" + "="*70)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("\n❌ ERROR: credentials.json not found!")
        print("\nYou need to download OAuth 2.0 Client credentials first:")
        print("\n📋 STEPS TO GET credentials.json:")
        print("="*70)
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Click 'Create Credentials' → 'OAuth client ID'")
        print("3. Set Application type: 'Desktop app'")
        print("4. Name it something like 'Email Organizer AI'")
        print("5. Click 'Create'")
        print("6. Download the JSON file")
        print("7. Save it as 'credentials.json' in this directory")
        print("\n8. Then run this script again")
        print("="*70)
        return
    
    print("\n✅ Found credentials.json")
    print("\n🔐 Starting OAuth flow...")
    print("\n" + "="*70)
    print("CODESPACES USERS: A browser will open automatically")
    print("Click 'Open' when prompted to open the OAuth page")
    print("="*70)
    print("\nPress Enter to start...")
    input()
    
    try:
        # Run the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', 
            SCOPES
        )
        
        # Try to run local server - Codespaces will auto-forward the port
        try:
            creds = flow.run_local_server(
                port=8080,
                prompt='consent',
                success_message='✅ Authentication successful! You can close this tab.',
                open_browser=True
            )
        except Exception as local_error:
            print(f"\n⚠️  Local server failed: {local_error}")
            print("\n📋 USING MANUAL METHOD INSTEAD")
            print("="*70)
            
            # Fallback to manual method
            auth_url, state = flow.authorization_url(
                prompt='consent',
                access_type='offline'
            )
            
            print("\n1. Open this URL in your browser:")
            print(f"\n{auth_url}\n")
            print("2. After authorization, you'll be redirected to a URL")
            print("3. Copy the ENTIRE URL from your browser address bar")
            print("   (Even if it says 'localhost refused to connect')")
            print("   (The URL will contain 'code=' in it)")
            print("4. Paste it below\n")
            
            try:
                response_url = input('Paste the full redirect URL here: ').strip()
                
                # Parse the authorization response
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(response_url)
                query_params = parse_qs(parsed.query)
                
                if 'code' in query_params:
                    code = query_params['code'][0]
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                else:
                    print("\n❌ Invalid URL. No authorization code found.")
                    return 1
            except Exception as e:
                print(f"\n❌ Failed to process authorization: {e}")
                return 1
        
        print("\n" + "="*70)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*70)
        
        # Save to token.json for local use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("\n✅ Saved credentials to token.json (for local testing)")
        
        # Generate the JSON format for GitHub secrets
        creds_dict = json.loads(creds.to_json())
        
        print("\n" + "="*70)
        print("📋 COPY THIS TO YOUR GITHUB CODESPACES SECRET")
        print("="*70)
        print("\n1. Go to: https://github.com/settings/codespaces")
        print("   or: https://github.com/jianranli/email-organizer-ai/settings/secrets/codespaces")
        print("\n2. Create or update secret: GMAIL_CREDENTIALS_JSON")
        print("\n3. Copy and paste the JSON below as the value:")
        print("\n" + "-"*70)
        print(json.dumps(creds_dict, indent=2))
        print("-"*70)
        
        print("\n" + "="*70)
        print("✅ SETUP COMPLETE!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Copy the JSON above to GMAIL_CREDENTIALS_JSON secret")
        print("  2. Restart your Codespace or reload environment variables")
        print("  3. Run: python main.py -n 1")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("  • Make sure you authorized all requested permissions")
        print("  • Check that credentials.json is valid")
        print("  • Try running the script again")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
