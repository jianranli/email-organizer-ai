import os
import base64
import json
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.labels']

class GmailClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        # Load credentials from token.json if it exists, otherwise go through OAuth flow
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:  # Save the token for future use
                token.write(self.creds.to_json())

        # Make sure the credentials are valid
        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())

        self.service = build('gmail', 'v1', credentials=self.creds)

    def fetch_emails(self, query=''):
        results = self.service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        email_data = []

        for msg in messages:
            msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
            email_data.append(msg_data)

        return email_data

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
        self.service.users().messages().modify(userId='me', id=msg_id, body={'addLabelIds': labels_to_add, 'removeLabelIds': labels_to_remove}).execute()

if __name__ == '__main__':
    client = GmailClient()
    # Example usage: Fetch emails with a specific query
    emails = client.fetch_emails('from:example@gmail.com')
    print(emails)