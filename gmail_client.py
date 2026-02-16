"""Gmail API client for email operations.

Provides a wrapper around the Gmail API for:
- Authenticating with OAuth2
- Fetching emails with pagination support
- Creating and managing labels
- Modifying email labels and archiving
- Trashing emails
"""

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

    def fetch_emails(self, query='', max_results=None):
        """Fetch emails matching the query with pagination support.
        
        Args:
            query (str): Gmail search query (e.g., 'in:inbox', 'is:unread')
            max_results (int, optional): Maximum number of emails to fetch. 
                                        If None, fetches all matching emails.
        
        Returns:
            List of email message dictionaries
        """
        try:
            messages = []
            page_token = None
            
            while True:
                # Fetch a page of message IDs
                if max_results and len(messages) >= max_results:
                    break
                
                results = self.service.users().messages().list(
                    userId='me', 
                    q=query,
                    pageToken=page_token,
                    maxResults=min(500, max_results - len(messages)) if max_results else 500
                ).execute()
                
                page_messages = results.get('messages', [])
                if not page_messages:
                    break
                
                messages.extend(page_messages)
                
                # Check if there are more pages
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            # Fetch full message details for each email
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
    
    def get_message_subject(self, email_id):
        """Get just the subject line of an email.
        
        Args:
            email_id: The email ID
            
        Returns:
            Subject line string (empty string if no subject)
        """
        message = self.service.users().messages().get(
            userId='me',
            id=email_id,
            format='metadata',  # Only get metadata, faster than 'full'
            metadataHeaders=['Subject']
        ).execute()
        
        headers = message.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
        return subject
    
    def get_message_headers(self, email_id) -> dict:
        """Get all email headers for unsubscribe detection.
        
        Args:
            email_id: The email ID
            
        Returns:
            Dictionary with headers including:
            - List-Unsubscribe
            - List-Unsubscribe-Post
            - From
            - Subject
        """
        message = self.service.users().messages().get(
            userId='me',
            id=email_id,
            format='metadata'
        ).execute()
        
        headers = message.get('payload', {}).get('headers', [])
        
        # Convert headers list to dictionary
        header_dict = {}
        for header in headers:
            name = header.get('name', '')
            value = header.get('value', '')
            header_dict[name] = value
        
        return header_dict
    
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
        """Create a label if it doesn't exist, return label ID.
        
        Handles Gmail system labels (SPAM, TRASH, INBOX, etc.) by mapping
        to their proper IDs instead of trying to create them.
        """
        # Map common category names to Gmail system label IDs
        SYSTEM_LABEL_MAP = {
            'spam': 'SPAM',
            'trash': 'TRASH',
            'inbox': 'INBOX',
            'sent': 'SENT',
            'draft': 'DRAFT',
            'drafts': 'DRAFT',
            'important': 'IMPORTANT',
            'starred': 'STARRED',
            'unread': 'UNREAD',
        }
        
        # Check if this is a system label (case-insensitive)
        label_lower = label_name.lower()
        if label_lower in SYSTEM_LABEL_MAP:
            return SYSTEM_LABEL_MAP[label_lower]
        
        # Get all existing labels
        labels = self.manage_labels('get', None)
        existing_labels = labels.get('labels', [])
        
        # Check if label already exists (case-insensitive match)
        for label in existing_labels:
            if label['name'].lower() == label_lower:
                return label['id']
        
        # Create new custom label
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
    
    def trash_email(self, email_id):
        """Move an email to trash."""
        self.service.users().messages().trash(
            userId='me',
            id=email_id
        ).execute()
    
    def get_message_labels(self, email_id):
        """Get the label IDs for a specific email.
        
        Args:
            email_id: The email ID
            
        Returns:
            List of label IDs applied to this email
        """
        message = self.service.users().messages().get(
            userId='me',
            id=email_id,
            format='minimal'  # Only need metadata
        ).execute()
        return message.get('labelIds', [])
    
    def get_all_labels(self):
        """Get all labels in the Gmail account."""
        return self.manage_labels('get', None)
    
    def get_custom_labels(self):
        """Get only custom labels (excludes Gmail system labels).
        
        Returns:
            List of custom label dictionaries with 'id', 'name', and 'type' keys.
        """
        # Gmail system label IDs that should NOT be deleted
        SYSTEM_LABEL_IDS = {
            'INBOX', 'SPAM', 'TRASH', 'UNREAD', 'STARRED', 'IMPORTANT',
            'SENT', 'DRAFT', 'CHAT', 'CATEGORY_PERSONAL', 'CATEGORY_SOCIAL',
            'CATEGORY_PROMOTIONS', 'CATEGORY_UPDATES', 'CATEGORY_FORUMS'
        }
        
        all_labels = self.get_all_labels()
        labels = all_labels.get('labels', [])
        
        # Filter to only custom labels (type='user' and not in system IDs)
        custom_labels = []
        for label in labels:
            label_id = label.get('id', '')
            label_type = label.get('type', '')
            
            # Keep only user-created labels
            if label_type == 'user' or (label_id not in SYSTEM_LABEL_IDS and not label_id.startswith('CATEGORY_')):
                custom_labels.append({
                    'id': label_id,
                    'name': label.get('name', ''),
                    'type': label_type
                })
        
        return custom_labels
    
    def delete_custom_label(self, label_id):
        """Delete a custom label by ID.
        
        Args:
            label_id: The ID of the label to delete
            
        Raises:
            Exception: If trying to delete a system label
        """
        # Safety check - don't delete system labels
        SYSTEM_LABEL_IDS = {
            'INBOX', 'SPAM', 'TRASH', 'UNREAD', 'STARRED', 'IMPORTANT',
            'SENT', 'DRAFT', 'CHAT'
        }
        
        if label_id in SYSTEM_LABEL_IDS or label_id.startswith('CATEGORY_'):
            raise ValueError(f"Cannot delete system label: {label_id}")
        
        self.manage_labels('delete', label_id)
    
    def delete_all_custom_labels(self, exclude_labels=None):
        """Delete all custom labels except those specified.
        
        Args:
            exclude_labels: List of label names to preserve (e.g., ['Notes', 'Github'])
            
        Returns:
            Tuple of (deleted_count, skipped_count, errors)
        """
        if exclude_labels is None:
            exclude_labels = []
        
        # Convert to lowercase for case-insensitive comparison
        exclude_labels_lower = [name.lower() for name in exclude_labels]
        
        custom_labels = self.get_custom_labels()
        deleted_count = 0
        skipped_count = 0
        errors = []
        
        for label in custom_labels:
            label_name = label['name']
            label_id = label['id']
            
            # Skip labels that should be preserved
            if label_name.lower() in exclude_labels_lower:
                skipped_count += 1
                continue
            
            try:
                self.delete_custom_label(label_id)
                deleted_count += 1
            except Exception as e:
                errors.append((label_name, str(e)))
        
        return deleted_count, skipped_count, errors

if __name__ == '__main__':
    client = GmailClient()
    # Example usage: Fetch emails with a specific query
    emails = client.fetch_emails('from:example@gmail.com')
    print(emails)