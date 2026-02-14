import unittest
import os
import json
import base64
from email.mime.text import MIMEText
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account

class TestGmailClientIntegration(unittest.TestCase):
    def setUp(self):
        # Get credentials from environment variable (GitHub secret)
        try:
            credentials_json = os.environ.get('GMAIL_CREDENTIALS_JSON')
            if not credentials_json:
                self.skipTest("GMAIL_CREDENTIALS_JSON environment variable not set")
            
            credentials_info = json.loads(credentials_json)
            
            # Check credential type and load accordingly
            cred_type = credentials_info.get('type', 'authorized_user')
            
            if cred_type == 'service_account':
                # Service account credentials
                SCOPES = [
                    'https://www.googleapis.com/auth/gmail.modify',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.labels'
                ]
                self.credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=SCOPES
                )
                # For service accounts with domain-wide delegation, you may need to specify a user
                # self.credentials = self.credentials.with_subject('user@yourdomain.com')
            else:
                # OAuth2 authorized user credentials
                self.credentials = Credentials.from_authorized_user_info(credentials_info)
            
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.skipTest(f"Invalid credentials format: {e}")

    def test_list_users_labels(self):
        """Test to list labels for the authorized user"""
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        self.assertIsInstance(labels, list)
        self.assertGreater(len(labels), 0, "Expected at least one label")
        
        # Verify common labels exist
        label_names = [label['name'] for label in labels]
        self.assertIn('INBOX', label_names, "INBOX label should exist")
        print(f"✅ Found {len(labels)} labels in Gmail account")
        
        # Print all label names in a readable format
        print("   Label names:")
        for label in labels:
            print(f"      - {label['name']}")

    def test_list_recent_emails(self):
        """Test to list recent emails and print their subjects"""
        # List messages from inbox (max 3)
        results = self.service.users().messages().list(
            userId='me', 
            maxResults=3
        ).execute()
        messages = results.get('messages', [])
        
        # Handle empty inbox case
        if not messages:
            print("✅ Inbox is empty (no emails found)")
            return
        
        # Verify we got valid data
        self.assertIsInstance(messages, list)
        self.assertGreater(len(messages), 0)
        
        print(f"✅ Found {len(messages)} recent email(s):")
        
        # Get full message details and extract subjects
        for idx, message in enumerate(messages, start=1):
            # Fetch full message details
            msg = self.service.users().messages().get(
                userId='me', 
                id=message['id']
            ).execute()
            
            # Verify message structure
            self.assertIn('id', msg)
            self.assertIn('payload', msg)
            
            # Extract subject from headers
            headers = msg['payload'].get('headers', [])
            subject = None
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break
            
            # Handle case where subject might be missing
            if subject is None:
                subject = "(No subject)"
            
            # Verify subject is a string
            self.assertIsInstance(subject, str)
            
            print(f"   {idx}. Subject: \"{subject}\"")

    @unittest.skipUnless(
        os.environ.get('SEND_REAL_EMAILS', '').lower() in ['true', '1', 'yes'],
        "Set SEND_REAL_EMAILS=true to test actual email sending"
    )
    def test_send_email(self):
        """Test sending an actual email to yourself"""
        # Get the authenticated user's email
        profile = self.service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')
        
        # Create a proper email message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = MIMEText(
            f'This is a test email sent from integration tests.\n\n'
            f'Timestamp: {timestamp}\n'
            f'Test: test_send_email\n\n'
            f'If you see this email, the integration test is working correctly!'
        )
        message['to'] = user_email  # Send to yourself
        message['subject'] = f'[Integration Test] Email Send Test - {timestamp}'
        
        # Encode the message properly
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the email
        sent_message = self.service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        # Verify response
        self.assertIn('id', sent_message)
        self.assertIsInstance(sent_message['id'], str)
        print(f"✅ Test email sent successfully!")
        print(f"   Message ID: {sent_message['id']}")
        print(f"   Recipient: {user_email}")
        print(f"   Check your inbox for the test email!")

    def test_get_user_profile(self):
        """Test retrieving user profile information"""
        profile = self.service.users().getProfile(userId='me').execute()
        
        self.assertIn('emailAddress', profile)
        self.assertIn('messagesTotal', profile)
        self.assertIn('threadsTotal', profile)
        
        email = profile.get('emailAddress')
        total_messages = profile.get('messagesTotal')
        total_threads = profile.get('threadsTotal')
        
        self.assertIsInstance(email, str)
        self.assertIsInstance(total_messages, int)
        self.assertIsInstance(total_threads, int)
        
        print(f"✅ Profile retrieved successfully")
        print(f"   Account: {email}")
        print(f"   Total messages: {total_messages}")
        print(f"   Total threads: {total_threads}")

if __name__ == '__main__':
    unittest.main()