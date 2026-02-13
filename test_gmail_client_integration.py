import unittest
import os
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class TestGmailClientIntegration(unittest.TestCase):
    def setUp(self):
        # Get credentials from environment variable (GitHub secret)
        try:
            credentials_json = os.environ.get('GMAIL_CREDENTIALS_JSON')
            if not credentials_json:
                self.skipTest("GMAIL_CREDENTIALS_JSON environment variable not set")
            
            credentials_info = json.loads(credentials_json)
            self.credentials = Credentials.from_authorized_user_info(credentials_info)
            self.service = build('gmail', 'v1', credentials=self.credentials)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.skipTest(f"Invalid credentials format: {e}")

    def test_list_users_labels(self):
        # Test to list labels for the authorized user
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        self.assertIsInstance(labels, list)
        self.assertGreater(len(labels), 0, "Expected at least one label")

    def test_send_email(self):
        # Test to send an email
        message = {'raw': 'Base64 encoded email content'}  # Replace with actual email content
        sent_message = self.service.users().messages().send(userId='me', body=message).execute()
        self.assertIn('id', sent_message)
        self.assertIsInstance(sent_message['id'], str)

if __name__ == '__main__':
    unittest.main()