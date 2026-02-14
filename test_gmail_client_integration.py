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

    def test_create_and_delete_category(self):
        """Test creating a new label/category and then deleting it"""
        # Create a unique label name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label_name = f"TestCategory_{timestamp}"
        
        # Create the label
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',  # Show in label list
            'messageListVisibility': 'show',     # Show messages with this label
            'type': 'user'                        # User-created label
        }
        
        created_label = self.service.users().labels().create(
            userId='me',
            body=label_body
        ).execute()
        
        # Verify the label was created
        self.assertIn('id', created_label)
        self.assertIn('name', created_label)
        self.assertEqual(created_label['name'], label_name)
        
        label_id = created_label['id']
        print(f"✅ Label created successfully!")
        print(f"   Label ID: {label_id}")
        print(f"   Label Name: {label_name}")
        
        # Verify it appears in the labels list
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        label_names = [label['name'] for label in labels]
        self.assertIn(label_name, label_names, "Created label should appear in labels list")
        
        # Clean up: Delete the test label
        try:
            self.service.users().labels().delete(
                userId='me',
                id=label_id
            ).execute()
            print(f"✅ Test label deleted successfully (cleanup)")
        except Exception as e:
            print(f"⚠️  Warning: Could not delete test label: {e}")

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
