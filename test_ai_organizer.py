import unittest
from unittest.mock import patch, MagicMock
from ai_organizer import EmailOrganizer


class TestEmailOrganizerInitialization(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions']
        })()
    
    @patch('openai.ChatCompletion.create')
    def test_initialization(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer(config=self.mock_config)
        self.assertIsNotNone(email_organizer)


class TestEmailOrganizerCategorization(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions']
        })()
    
    @patch('openai.ChatCompletion.create')
    def test_categorization(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"category": "Work"}'))]
        mock_openai.return_value = mock_response
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        categories = email_organizer.categorize_email('Test email content')
        self.assertIn('category', categories)


class TestEmailOrganizerSummarization(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions']
        })()
    
    @patch('openai.ChatCompletion.create')
    def test_summarization(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='Test summary'))]
        mock_openai.return_value = mock_response
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        summary = email_organizer.summarize_email('Test email content')
        self.assertIsInstance(summary, str)


class TestEmailOrganizerActionItems(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions']
        })()
    
    @patch('openai.ChatCompletion.create')
    def test_action_items(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='["Task 1", "Task 2"]'))]
        mock_openai.return_value = mock_response
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        action_items = email_organizer.extract_action_items('Test email content')
        self.assertIsInstance(action_items, list)


class TestEmailOrganizerConfidenceScoring(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions']
        })()
    
    @patch('openai.ChatCompletion.create')
    def test_confidence_scoring(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"Work": 0.8, "Personal": 0.1, "Promotions": 0.1}'))]
        mock_openai.return_value = mock_response
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        confidence = email_organizer.confidence_scoring('Test email content')
        self.assertIsInstance(confidence, dict)


class TestEmailOrganizerAPICallParameters(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions']
        })()
    
    @patch('openai.ChatCompletion.create')
    def test_api_call_parameters(self, mock_openai):
        mock_openai.return_value = MagicMock()
        email_organizer = EmailOrganizer(config=self.mock_config)
        
        # Test that the model is set correctly
        self.assertEqual(email_organizer.model, 'gpt-3.5-turbo')


if __name__ == '__main__':
    unittest.main()