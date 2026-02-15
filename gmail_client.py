import os
import base64
import json
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

class GmailClient:
    def __init__(self, config=None):
        """Initialize Gmail client with config."""
        self.config = config
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Gmail API using multiple methods."""
        
        # Method 1: Try config object first (preferred)
        credentials_json = None
        if self.config:
            credentials_json = self.config.GMAIL_CREDENTIALS_JSON
        
        # Method 2: Fallback to environment variable for backward compatibility
        if not credentials_json:
            credentials_json = os.environ.get('GMAIL_CREDENTIALS_JSON')
        
        # Try to authenticate with JSON credentials
        if credentials_json:
            try:
                credentials_info = json.loads(credentials_json)
                cred_type = credentials_info.get('type', 'authorized_user')
                
                if cred_type == 'service_account':
                    self.creds = service_account.Credentials.from_service_account_info(
                        credentials_info,
                        scopes=SCOPES
                    )
                else:
                    # For authorized_user type, load credentials
                    self.creds = Credentials.from_authorized_user_info(
                        credentials_info,
                        scopes=SCOPES
                    )
                    
                    # Check if the token has the required scopes
                    if hasattr(self.creds, 'scopes') and self.creds.scopes:
                        missing_scopes = set(SCOPES) - set(self.creds.scopes)
                        if missing_scopes:
                            raise ValueError(
                                f"Credentials are missing required scopes: {missing_scopes}\\n"
                                f"Please regenerate your credentials with the following scopes:\\n"
                                f"  - https://www.googleapis.com/auth/gmail.readonly\\n"
                                f"  - https://www.googleapis.com/auth/gmail.modify\\n"
                                f"  - https://www.googleapis.com/auth/gmail.labels"
                            )
                
                self.service = build('gmail', 'v1', credentials=self.creds)
                return
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                error_msg = str(e)
                if 'invalid_scope' in error_msg.lower() or 'scope' in error_msg.lower():
                    raise ValueError(
                        f"SCOPE ERROR: Your Gmail credentials don't have the required permissions.\\n\\n"
                        f"This usually means the refresh token was created with limited scopes.\\n\\n"
                        f"SOLUTION:\\n"
                        f"1. Go to: https://console.cloud.google.com/apis/credentials\\n"
                        f"2. Delete the existing OAuth 2.0 Client ID or create a new one\\n"
                        f"3. Run the OAuth flow again to generate new credentials with these scopes:\\n"
                        f"   - https://www.googleapis.com/auth/gmail.readonly\\n"
                        f"   - https://www.googleapis.com/auth/gmail.modify\\n"
                        f"   - https://www.googleapis.com/auth/gmail.labels\\n"
                        f"4. Update your GMAIL_CREDENTIALS_JSON environment variable\\n\\n"
                        f"Original error: {e}"
                    )
                raise
        
        # Method 3: Try token.json (for local development with saved token)
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Method 4: Try credentials.json (for first-time OAuth flow)
        elif os.path.exists('credentials.json'):
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        else:
            raise FileNotFoundError(
                "No credentials found. Please either:\n"
                "1. Set GMAIL_CREDENTIALS_JSON environment variable, or\n"
                "2. Provide credentials.json file"
            )

        # Refresh expired credentials
        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())

        self.service = build('gmail', 'v1', credentials=self.creds)

    def fetch_emails(self, query=''):
        try:
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            email_data = []

            for msg in messages:
                msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                email_data.append(msg_data)

            return email_data
        except Exception as e:
            error_msg = str(e)
            if 'invalid_scope' in error_msg.lower():
                raise ValueError(
                    f"\\n{'='*70}\\n"
                    f"GMAIL API SCOPE ERROR\\n"
                    f"{'='*70}\\n"
                    f"Your Gmail credentials don't have the required permissions.\\n\\n"
                    f"The refresh token was created with insufficient scopes and needs to be\\n"
                    f"regenerated with the proper permissions.\\n\\n"
                    f"REQUIRED SCOPES:\\n"
                    f"  • https://www.googleapis.com/auth/gmail.readonly\\n"
                    f"  • https://www.googleapis.com/auth/gmail.modify\\n"
                    f"  • https://www.googleapis.com/auth/gmail.labels\\n\\n"
                    f"HOW TO FIX:\\n"
                    f"1. Go to Google Cloud Console OAuth consent screen\\n"
                    f"2. Revoke access for the current app (or delete old token)\\n"
                    f"3. Re-run the OAuth flow with the required scopes\\n"
                    f"4. Update GMAIL_CREDENTIALS_JSON with the new credentials\\n\\n"
                    f"For local testing: Delete token.json and re-authenticate\\n"
                    f"{'='*70}\\n"
                ) from e
            raise

    def manage_labels(self, operation, label_id, label_object=None):
        if operation == 'create':
            self.service.users().labels().create(userId='me', body=label_object).execute()
        elif operation == 'delete':
            self.service.users().labels().delete(userId='me', id=label_id).execute()
        elif operation == 'update':
            self.service.users().labels().update(userId='me', id=label_id, body=label_object).execute()
        elif operation == 'get':
            return self.service.users().labels().list(userId='me').execute()

    def modify_message(self, msg_id, labels_to_add=[], labels_to_remove=[]):
        self.service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'addLabelIds': labels_to_add, 'removeLabelIds': labels_to_remove}
        ).execute()

    def get_message(self, email_id):
        """Get full message details by email ID."""
        message = self.service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()
        
        # Extract the body content
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        # Get subject and sender
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        
        # Extract body text
        body = self._get_message_body(payload)
        
        return f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    def _get_message_body(self, payload):
        """Extract message body from payload."""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif 'parts' in part:
                    body = self._get_message_body(part)
                    if body:
                        break
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    def create_label_if_not_exists(self, label_name):
        """Create a label if it doesn't exist, return label ID."""
        # Get all existing labels
        labels = self.manage_labels('get', None)
        existing_labels = labels.get('labels', [])
        
        # Check if label already exists
        for label in existing_labels:
            if label['name'] == label_name:
                return label['id']
        
        # Create new label
        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        created_label = self.service.users().labels().create(
            userId='me',
            body=label_object
        ).execute()
        
        return created_label['id']
    
    def apply_label(self, email_id, label_id):
        """Apply a label to an email."""
        self.modify_message(email_id, labels_to_add=[label_id])
    
    def archive_email(self, email_id):
        """Archive an email by removing INBOX label."""
        self.modify_message(email_id, labels_to_remove=['INBOX'])

if __name__ == '__main__':
    client = GmailClient()
    # Example usage: Fetch emails with a specific query
    emails = client.fetch_emails('from:example@gmail.com')
    print(emails)