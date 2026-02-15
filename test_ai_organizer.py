import unittest
from unittest.mock import patch, MagicMock
from ai_organizer import EmailOrganizer
from config import Config


class TestEmailOrganizerInitialization(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_initialization(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer()
        self.assertIsNotNone(email_organizer)


class TestEmailOrganizerCategorization(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_categorization(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer()
        categories = email_organizer.categorize_email('Test email content')
        self.assertIn('category', categories)


class TestEmailOrganizerSummarization(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_summarization(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer()
        summary = email_organizer.summarize_email('Test email content')
        self.assertIsInstance(summary, str)


class TestEmailOrganizerActionItems(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_action_items(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer()
        action_items = email_organizer.extract_action_items('Test email content')
        self.assertIsInstance(action_items, list)


class TestEmailOrganizerConfidenceScoring(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_confidence_scoring(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer()
        confidence = email_organizer.score_confidence('Test email content')
        self.assertGreaterEqual(confidence, 0)


class TestEmailOrganizerAPICallParameters(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_api_call_parameters(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer()
        params = email_organizer.get_api_parameters()
        self.assertIn('model', params)


if __name__ == '__main__':
    unittest.main()