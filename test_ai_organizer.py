import unittest
from unittest.mock import patch, MagicMock
from email_organizer import EmailOrganizer  # Adjust the import based on your package structure


class TestEmailOrganizer(unittest.TestCase):
    
    @patch('email_organizer.config')  # Mock config module
    def test_initialization_with_config(self, mock_config):
        mock_config.return_value = {'some_key': 'some_value'}
        organizer = EmailOrganizer(config=mock_config)
        self.assertEqual(organizer.config['some_key'], 'some_value')

    @patch('email_organizer.api_client')  # Mocking an API client
    def test_initialization_with_api_key(self, mock_api_client):
        mock_api_client.return_value = MagicMock()  # Simulated API client
        organizer = EmailOrganizer(api_key='test_api_key')
        self.assertEqual(organizer.api_key, 'test_api_key')

    @patch('email_organizer.categorize_email_function')
    def test_categorize_email(self, mock_categorize_email):
        organizer = EmailOrganizer(api_key='test_api_key')
        mock_categorize_email.return_value = 'Work'
        category = organizer.categorize_email('email content')
        self.assertEqual(category, 'Work')
        mock_categorize_email.assert_called_once_with('email content')

    @patch('email_organizer.summarize_email_function')
    def test_summarize_email(self, mock_summarize_email):
        organizer = EmailOrganizer(api_key='test_api_key')
        mock_summarize_email.return_value = 'Email summary'
        summary = organizer.summarize_email('email content')
        self.assertEqual(summary, 'Email summary')
        mock_summarize_email.assert_called_once_with('email content')

    @patch('email_organizer.extract_action_items_function')
    def test_extract_action_items(self, mock_extract_action_items):
        organizer = EmailOrganizer(api_key='test_api_key')
        mock_extract_action_items.return_value = ['Action 1', 'Action 2']
        actions = organizer.extract_action_items('email content')
        self.assertEqual(actions, ['Action 1', 'Action 2'])
        mock_extract_action_items.assert_called_once_with('email content')

    @patch('email_organizer.confidence_score_function')
    def test_confidence_scoring(self, mock_confidence_score):
        organizer = EmailOrganizer(api_key='test_api_key')
        mock_confidence_score.return_value = 0.95
        confidence = organizer.confidence_scoring('email content')
        self.assertEqual(confidence, 0.95)
        mock_confidence_score.assert_called_once_with('email content')


if __name__ == '__main__':
    unittest.main()