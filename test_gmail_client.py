import unittest
from unittest.mock import patch, MagicMock, mock_open
from gmail_client import GmailClient

class TestGmailClientAuthentication(unittest.TestCase):
    """Test Gmail authentication flows."""

    @patch('os.path.exists')
    @patch('gmail_client.Credentials.from_authorized_user_file')
    @patch('gmail_client.build')
    @patch('gmail_client.Request')
    def test_authenticate_with_existing_token(self, mock_request, mock_build, mock_creds_from_file, mock_exists):
        """Test authentication when token.json already exists."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_creds_from_file.return_value = mock_creds
        
        client = GmailClient()
        
        mock_creds_from_file.assert_called_once()
        mock_build.assert_called_once()
        self.assertIsNotNone(client.service)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('gmail_client.InstalledAppFlow.from_client_secrets_file')
    @patch('gmail_client.build')
    def test_authenticate_with_oauth_flow(self, mock_build, mock_flow, mock_file, mock_exists):
        """Test authentication when token.json doesn't exist (OAuth flow)."""
        mock_exists.return_value = False
        mock_flow_instance = MagicMock()
        mock_creds = MagicMock()
        mock_creds.to_json.return_value = '{"token": "test"}'
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.return_value = mock_flow_instance
        
        client = GmailClient()
        
        mock_flow.assert_called_once()
        mock_file.assert_called()
        mock_build.assert_called_once()

    @patch('os.path.exists')
    @patch('gmail_client.Credentials.from_authorized_user_file')
    @patch('gmail_client.build')
    @patch('gmail_client.Request')
    def test_refresh_expired_token(self, mock_request, mock_build, mock_creds_from_file, mock_exists):
        """Test that expired tokens are refreshed."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "test_refresh_token"
        mock_creds_from_file.return_value = mock_creds
        
        client = GmailClient()
        
        mock_creds.refresh.assert_called_once()


class TestGmailClientFetchEmails(unittest.TestCase):
    """Test email fetching functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('os.path.exists'), \
             patch('gmail_client.Credentials.from_authorized_user_file'), \
             patch('gmail_client.build'):
            self.client = GmailClient()
            self.client.service = MagicMock()

    def test_fetch_emails_with_query(self):
        """Test fetching emails with a specific query."""
        mock_messages = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        self.client.service.users().messages().list().execute.return_value = {
            'messages': mock_messages
        }
        
        mock_message_data = {
            'id': '1',
            'payload': {
                'headers': [{'name': 'From', 'value': 'sender@example.com'}]
            }
        }
        self.client.service.users().messages().get().execute.return_value = mock_message_data
        
        result = self.client.fetch_emails('from:example@gmail.com')
        
        self.assertEqual(len(result), 3)
        self.client.service.users().messages().list.assert_called_once()

    def test_fetch_emails_empty_result(self):
        """Test fetching emails when no emails match the query."""
        self.client.service.users().messages().list().execute.return_value = {}
        
        result = self.client.fetch_emails('from:nonexistent@example.com')
        
        self.assertEqual(result, [])

    def test_fetch_emails_no_query(self):
        """Test fetching all emails without a query."""
        mock_messages = [{'id': '1'}]
        self.client.service.users().messages().list().execute.return_value = {
            'messages': mock_messages
        }
        self.client.service.users().messages().get().execute.return_value = {'id': '1'}
        
        result = self.client.fetch_emails()
        
        self.client.service.users().messages().list.assert_called_with(userId='me', q='')


class TestGmailClientLabels(unittest.TestCase):
    """Test label management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('os.path.exists'), \
             patch('gmail_client.Credentials.from_authorized_user_file'), \
             patch('gmail_client.build'):
            self.client = GmailClient()
            self.client.service = MagicMock()

    def test_create_label(self):
        """Test creating a new label."""
        label_object = {
            'name': 'TestLabel',
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        
        self.client.manage_labels('create', None, label_object)
        
        self.client.service.users().labels().create.assert_called_once_with(
            userId='me', body=label_object
        )

    def test_delete_label(self):
        """Test deleting a label."""
        self.client.manage_labels('delete', 'LABEL_123', None)
        
        self.client.service.users().labels().delete.assert_called_once_with(
            userId='me', id='LABEL_123'
        )

    def test_update_label(self):
        """Test updating a label."""
        label_object = {'name': 'UpdatedLabel'}
        
        self.client.manage_labels('update', 'LABEL_123', label_object)
        
        self.client.service.users().labels().update.assert_called_once_with(
            userId='me', id='LABEL_123', body=label_object
        )

    def test_get_all_labels(self):
        """Test getting all labels."""
        mock_labels = {'labels': [{'id': '1', 'name': 'Label1'}]}
        self.client.service.users().labels().list().execute.return_value = mock_labels
        
        result = self.client.manage_labels('get', None, None)
        
        self.assertEqual(result, mock_labels)


class TestGmailClientModifyMessage(unittest.TestCase):
    """Test message modification functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('os.path.exists'), \
             patch('gmail_client.Credentials.from_authorized_user_file'), \
             patch('gmail_client.build'):
            self.client = GmailClient()
            self.client.service = MagicMock()

    def test_modify_message_add_labels(self):
        """Test adding labels to a message."""
        msg_id = 'msg_123'
        labels_to_add = ['LABEL_1', 'LABEL_2']
        
        self.client.modify_message(msg_id, labels_to_add=labels_to_add)
        
        self.client.service.users().messages().modify.assert_called_once_with(
            userId='me',
            id=msg_id,
            body={'addLabelIds': labels_to_add, 'removeLabelIds': []}
        )

    def test_modify_message_remove_labels(self):
        """Test removing labels from a message."""
        msg_id = 'msg_123'
        labels_to_remove = ['LABEL_1']
        
        self.client.modify_message(msg_id, labels_to_remove=labels_to_remove)
        
        self.client.service.users().messages().modify.assert_called_once_with(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [], 'removeLabelIds': labels_to_remove}
        )

    def test_modify_message_add_and_remove_labels(self):
        """Test adding and removing labels simultaneously."""
        msg_id = 'msg_123'
        labels_to_add = ['LABEL_1']
        labels_to_remove = ['LABEL_2']
        
        self.client.modify_message(msg_id, labels_to_add=labels_to_add, labels_to_remove=labels_to_remove)
        
        self.client.service.users().messages().modify.assert_called_once_with(
            userId='me',
            id=msg_id,
            body={'addLabelIds': labels_to_add, 'removeLabelIds': labels_to_remove}
        )


if __name__ == '__main__':
    unittest.main()