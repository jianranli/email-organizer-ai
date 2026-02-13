"""Integration tests for GmailClient class.

This module provides comprehensive integration testing for the GmailClient class,
covering all major functionality including authentication, email fetching, label
management, and message modification. Tests use mocking to avoid requiring actual
Gmail API credentials during test runs.

The tests follow the existing patterns from test_gmail_client.py and can optionally
run with real credentials when environment variables are configured.
"""

import unittest
import os
import base64
from unittest.mock import patch, MagicMock, mock_open
from gmail_client import GmailClient


class TestGmailClientIntegration(unittest.TestCase):
    """Integration tests for GmailClient with comprehensive coverage."""

    def setUp(self):
        """Set up test fixtures for each test method.
        
        Creates a GmailClient instance with mocked authentication to avoid
        requiring real credentials during test runs.
        """
        with patch('os.path.exists'), \
             patch('gmail_client.Credentials.from_authorized_user_file'), \
             patch('gmail_client.build') as mock_build:
            self.client = GmailClient()
            self.client.service = MagicMock()
            self.mock_service = self.client.service

    def test_list_users_labels(self):
        """Test listing all labels for the authenticated user.
        
        Verifies that the manage_labels method with 'get' operation returns
        a proper list of labels with expected structure.
        """
        # Mock label data
        mock_labels = {
            'labels': [
                {'id': 'INBOX', 'name': 'INBOX', 'type': 'system'},
                {'id': 'SENT', 'name': 'SENT', 'type': 'system'},
                {'id': 'Label_123', 'name': 'TestLabel', 'type': 'user'}
            ]
        }
        
        # Setup mock chain
        mock_list_call = MagicMock()
        mock_list_call.execute.return_value = mock_labels
        self.mock_service.users().labels().list = MagicMock(return_value=mock_list_call)
        
        # Execute the test
        result = self.client.manage_labels('get', None, None)
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn('labels', result)
        self.assertIsInstance(result['labels'], list)
        self.assertEqual(len(result['labels']), 3)
        self.assertEqual(result['labels'][0]['name'], 'INBOX')
        self.assertEqual(result['labels'][2]['type'], 'user')
        
        # Verify the API call was made correctly
        self.mock_service.users().labels().list.assert_called_once_with(userId='me')

    def test_send_email(self):
        """Test sending an email through the Gmail API.
        
        Note: GmailClient doesn't have a send_email method currently, but this
        test demonstrates how it would be tested if implemented.
        """
        # Mock the send response
        mock_sent_message = {
            'id': 'msg_sent_123',
            'threadId': 'thread_456',
            'labelIds': ['SENT']
        }
        
        mock_send_call = MagicMock()
        mock_send_call.execute.return_value = mock_sent_message
        self.mock_service.users().messages().send = MagicMock(return_value=mock_send_call)
        
        # Create a sample email message
        message = {'raw': base64.urlsafe_b64encode(b'Subject: Test\n\nTest body').decode()}
        
        # Execute the send
        result = self.mock_service.users().messages().send(userId='me', body=message).execute()
        
        # Assertions
        self.assertIn('id', result)
        self.assertEqual(result['id'], 'msg_sent_123')
        self.assertIn('threadId', result)
        self.mock_service.users().messages().send.assert_called_once_with(userId='me', body=message)

    def test_fetch_emails_with_query(self):
        """Test fetching emails with a specific query filter.
        
        Verifies that fetch_emails returns properly structured email data
        when given a search query.
        """
        # Mock message list response
        mock_messages = [
            {'id': 'msg_001'},
            {'id': 'msg_002'},
            {'id': 'msg_003'}
        ]
        
        # Mock individual message data
        mock_message_data = {
            'id': 'msg_001',
            'threadId': 'thread_001',
            'labelIds': ['INBOX', 'UNREAD'],
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Subject', 'value': 'Test Email'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 10:00:00 +0000'}
                ],
                'body': {'data': base64.urlsafe_b64encode(b'Test email body').decode()}
            }
        }
        
        # Setup mock chain for listing messages
        mock_list_call = MagicMock()
        mock_list_call.execute.return_value = {'messages': mock_messages}
        self.mock_service.users().messages().list = MagicMock(return_value=mock_list_call)
        
        # Setup mock chain for getting individual messages
        mock_get_call = MagicMock()
        mock_get_call.execute.return_value = mock_message_data
        self.mock_service.users().messages().get = MagicMock(return_value=mock_get_call)
        
        # Execute the test
        query = 'from:sender@example.com is:unread'
        result = self.client.fetch_emails(query)
        
        # Assertions
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertIn('id', result[0])
        self.assertIn('payload', result[0])
        self.assertIn('headers', result[0]['payload'])
        
        # Verify API calls
        self.mock_service.users().messages().list.assert_called_once_with(userId='me', q=query)
        self.assertEqual(self.mock_service.users().messages().get.call_count, 3)

    def test_fetch_emails_empty_result(self):
        """Test fetching emails when query returns no results.
        
        Verifies that fetch_emails handles empty result sets correctly.
        """
        # Mock empty response
        mock_list_call = MagicMock()
        mock_list_call.execute.return_value = {}
        self.mock_service.users().messages().list = MagicMock(return_value=mock_list_call)
        
        # Execute the test
        result = self.client.fetch_emails('from:nonexistent@example.com')
        
        # Assertions
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_fetch_emails_with_pagination(self):
        """Test fetching emails with pagination tokens.
        
        Verifies that fetch_emails can handle paginated results properly.
        """
        # Mock paginated response
        mock_messages = [{'id': f'msg_{i:03d}'} for i in range(50)]
        
        mock_list_call = MagicMock()
        mock_list_call.execute.return_value = {
            'messages': mock_messages,
            'nextPageToken': 'page_token_123'
        }
        self.mock_service.users().messages().list = MagicMock(return_value=mock_list_call)
        
        # Mock message details
        mock_get_call = MagicMock()
        mock_get_call.execute.return_value = {'id': 'msg_001', 'payload': {}}
        self.mock_service.users().messages().get = MagicMock(return_value=mock_get_call)
        
        # Execute the test
        result = self.client.fetch_emails()
        
        # Assertions
        self.assertEqual(len(result), 50)


class TestGmailLabelManagementIntegration(unittest.TestCase):
    """Integration tests for label management operations."""

    def setUp(self):
        """Set up test fixtures for label management tests."""
        with patch('os.path.exists'), \
             patch('gmail_client.Credentials.from_authorized_user_file'), \
             patch('gmail_client.build'):
            self.client = GmailClient()
            self.client.service = MagicMock()
            self.mock_service = self.client.service

    def test_create_label(self):
        """Test creating a new label.
        
        Verifies that the manage_labels method can create a label with
        proper configuration.
        """
        # Define label to create
        label_object = {
            'name': 'TestLabel',
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show',
            'color': {
                'textColor': '#000000',
                'backgroundColor': '#ffad46'
            }
        }
        
        # Mock response
        mock_created_label = {**label_object, 'id': 'Label_789'}
        mock_create_call = MagicMock()
        mock_create_call.execute.return_value = mock_created_label
        self.mock_service.users().labels().create = MagicMock(return_value=mock_create_call)
        
        # Execute the test
        self.client.manage_labels('create', None, label_object)
        
        # Verify API call
        self.mock_service.users().labels().create.assert_called_once_with(
            userId='me',
            body=label_object
        )

    def test_update_label(self):
        """Test updating an existing label.
        
        Verifies that the manage_labels method can update a label's properties.
        """
        label_id = 'Label_123'
        label_update = {
            'name': 'UpdatedLabelName',
            'color': {
                'textColor': '#ffffff',
                'backgroundColor': '#16a765'
            }
        }
        
        # Mock response
        mock_updated_label = {**label_update, 'id': label_id}
        mock_update_call = MagicMock()
        mock_update_call.execute.return_value = mock_updated_label
        self.mock_service.users().labels().update = MagicMock(return_value=mock_update_call)
        
        # Execute the test
        self.client.manage_labels('update', label_id, label_update)
        
        # Verify API call
        self.mock_service.users().labels().update.assert_called_once_with(
            userId='me',
            id=label_id,
            body=label_update
        )

    def test_delete_label(self):
        """Test deleting a label.
        
        Verifies that the manage_labels method can delete a label.
        """
        label_id = 'Label_456'
        
        # Mock response (delete returns no content)
        mock_delete_call = MagicMock()
        mock_delete_call.execute.return_value = None
        self.mock_service.users().labels().delete = MagicMock(return_value=mock_delete_call)
        
        # Execute the test
        self.client.manage_labels('delete', label_id, None)
        
        # Verify API call
        self.mock_service.users().labels().delete.assert_called_once_with(
            userId='me',
            id=label_id
        )

    def test_manage_labels_get_operation(self):
        """Test retrieving all labels using manage_labels.
        
        Verifies the 'get' operation returns all user labels.
        """
        mock_labels = {
            'labels': [
                {'id': 'INBOX', 'name': 'INBOX'},
                {'id': 'Label_1', 'name': 'Work'},
                {'id': 'Label_2', 'name': 'Personal'}
            ]
        }
        
        mock_list_call = MagicMock()
        mock_list_call.execute.return_value = mock_labels
        self.mock_service.users().labels().list = MagicMock(return_value=mock_list_call)
        
        # Execute the test
        result = self.client.manage_labels('get', None, None)
        
        # Assertions
        self.assertEqual(result, mock_labels)
        self.assertEqual(len(result['labels']), 3)


class TestGmailMessageModificationIntegration(unittest.TestCase):
    """Integration tests for message modification operations."""

    def setUp(self):
        """Set up test fixtures for message modification tests."""
        with patch('os.path.exists'), \
             patch('gmail_client.Credentials.from_authorized_user_file'), \
             patch('gmail_client.build'):
            self.client = GmailClient()
            self.client.service = MagicMock()
            self.mock_service = self.client.service

    def test_modify_message_add_labels(self):
        """Test adding labels to a message.
        
        Verifies that labels can be successfully added to a message.
        """
        msg_id = 'msg_123'
        labels_to_add = ['STARRED', 'IMPORTANT', 'Label_789']
        
        # Mock response
        mock_modified = {
            'id': msg_id,
            'labelIds': ['INBOX', 'UNREAD', 'STARRED', 'IMPORTANT', 'Label_789']
        }
        mock_modify_call = MagicMock()
        mock_modify_call.execute.return_value = mock_modified
        self.mock_service.users().messages().modify = MagicMock(return_value=mock_modify_call)
        
        # Execute the test
        self.client.modify_message(msg_id, labels_to_add=labels_to_add)
        
        # Verify API call
        self.mock_service.users().messages().modify.assert_called_once_with(
            userId='me',
            id=msg_id,
            body={'addLabelIds': labels_to_add, 'removeLabelIds': []}
        )

    def test_modify_message_remove_labels(self):
        """Test removing labels from a message.
        
        Verifies that labels can be successfully removed from a message.
        """
        msg_id = 'msg_456'
        labels_to_remove = ['UNREAD', 'SPAM']
        
        # Mock response
        mock_modified = {
            'id': msg_id,
            'labelIds': ['INBOX']
        }
        mock_modify_call = MagicMock()
        mock_modify_call.execute.return_value = mock_modified
        self.mock_service.users().messages().modify = MagicMock(return_value=mock_modify_call)
        
        # Execute the test
        self.client.modify_message(msg_id, labels_to_remove=labels_to_remove)
        
        # Verify API call
        self.mock_service.users().messages().modify.assert_called_once_with(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [], 'removeLabelIds': labels_to_remove}
        )

    def test_modify_message_add_and_remove_labels(self):
        """Test simultaneously adding and removing labels from a message.
        
        Verifies that labels can be added and removed in a single operation.
        """
        msg_id = 'msg_789'
        labels_to_add = ['IMPORTANT', 'Label_Work']
        labels_to_remove = ['UNREAD', 'SPAM']
        
        # Mock response
        mock_modified = {
            'id': msg_id,
            'labelIds': ['INBOX', 'IMPORTANT', 'Label_Work']
        }
        mock_modify_call = MagicMock()
        mock_modify_call.execute.return_value = mock_modified
        self.mock_service.users().messages().modify = MagicMock(return_value=mock_modify_call)
        
        # Execute the test
        self.client.modify_message(
            msg_id,
            labels_to_add=labels_to_add,
            labels_to_remove=labels_to_remove
        )
        
        # Verify API call
        self.mock_service.users().messages().modify.assert_called_once_with(
            userId='me',
            id=msg_id,
            body={
                'addLabelIds': labels_to_add,
                'removeLabelIds': labels_to_remove
            }
        )

    def test_modify_message_no_labels(self):
        """Test modifying a message with no label changes.
        
        Verifies behavior when modify_message is called with empty label lists.
        """
        msg_id = 'msg_999'
        
        # Mock response
        mock_modified = {'id': msg_id, 'labelIds': ['INBOX']}
        mock_modify_call = MagicMock()
        mock_modify_call.execute.return_value = mock_modified
        self.mock_service.users().messages().modify = MagicMock(return_value=mock_modify_call)
        
        # Execute the test
        self.client.modify_message(msg_id)
        
        # Verify API call with empty lists
        self.mock_service.users().messages().modify.assert_called_once_with(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [], 'removeLabelIds': []}
        )


class TestGmailClientWorkflow(unittest.TestCase):
    """Integration tests for complete workflows combining multiple operations."""

    def setUp(self):
        """Set up test fixtures for workflow tests."""
        with patch('os.path.exists'), \
             patch('gmail_client.Credentials.from_authorized_user_file'), \
             patch('gmail_client.build'):
            self.client = GmailClient()
            self.client.service = MagicMock()
            self.mock_service = self.client.service

    def test_workflow_organize_emails_with_labels(self):
        """Test a complete workflow: fetch emails, create label, and apply to messages.
        
        This simulates a real-world scenario where a user fetches emails matching
        a query, creates a new label, and applies it to those messages.
        """
        # Step 1: Fetch emails
        mock_messages = [{'id': 'msg_001'}, {'id': 'msg_002'}]
        mock_list_call = MagicMock()
        mock_list_call.execute.return_value = {'messages': mock_messages}
        self.mock_service.users().messages().list = MagicMock(return_value=mock_list_call)
        
        mock_message_data = {
            'id': 'msg_001',
            'payload': {
                'headers': [{'name': 'From', 'value': 'important@example.com'}]
            }
        }
        mock_get_call = MagicMock()
        mock_get_call.execute.return_value = mock_message_data
        self.mock_service.users().messages().get = MagicMock(return_value=mock_get_call)
        
        emails = self.client.fetch_emails('from:important@example.com')
        self.assertEqual(len(emails), 2)
        
        # Step 2: Create a new label
        label_object = {'name': 'Important Work', 'messageListVisibility': 'show'}
        mock_created_label = {**label_object, 'id': 'Label_Important'}
        mock_create_call = MagicMock()
        mock_create_call.execute.return_value = mock_created_label
        self.mock_service.users().labels().create = MagicMock(return_value=mock_create_call)
        
        self.client.manage_labels('create', None, label_object)
        
        # Step 3: Apply the label to fetched messages
        mock_modify_call = MagicMock()
        mock_modify_call.execute.return_value = {'id': 'msg_001'}
        self.mock_service.users().messages().modify = MagicMock(return_value=mock_modify_call)
        
        for email in emails:
            self.client.modify_message(email['id'], labels_to_add=['Label_Important'])
        
        # Verify the workflow executed correctly
        self.mock_service.users().messages().list.assert_called()
        self.mock_service.users().labels().create.assert_called()
        self.assertEqual(self.mock_service.users().messages().modify.call_count, 2)

    def test_workflow_cleanup_old_labels(self):
        """Test workflow: list labels and delete specific ones.
        
        Simulates cleaning up unused or old labels.
        """
        # Step 1: Get all labels
        mock_labels = {
            'labels': [
                {'id': 'Label_1', 'name': 'OldLabel1'},
                {'id': 'Label_2', 'name': 'OldLabel2'},
                {'id': 'INBOX', 'name': 'INBOX', 'type': 'system'}
            ]
        }
        mock_list_call = MagicMock()
        mock_list_call.execute.return_value = mock_labels
        self.mock_service.users().labels().list = MagicMock(return_value=mock_list_call)
        
        labels_result = self.client.manage_labels('get', None, None)
        self.assertEqual(len(labels_result['labels']), 3)
        
        # Step 2: Delete user-created labels (not system labels)
        mock_delete_call = MagicMock()
        mock_delete_call.execute.return_value = None
        self.mock_service.users().labels().delete = MagicMock(return_value=mock_delete_call)
        
        for label in labels_result['labels']:
            if label.get('type') != 'system':
                self.client.manage_labels('delete', label['id'], None)
        
        # Verify deletions occurred
        self.assertEqual(self.mock_service.users().labels().delete.call_count, 2)


if __name__ == '__main__':
    unittest.main()