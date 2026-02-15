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
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()
    
    @patch('ai_organizer.OpenAI')
    def test_initialization(self, mock_openai_class):
        """Test EmailOrganizer initialization."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        self.assertIsNotNone(email_organizer)
        self.assertEqual(email_organizer.llm.model, 'gpt-3.5-turbo')


class TestEmailOrganizerCategorization(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()
    
    @patch('ai_organizer.OpenAI')
    def test_categorization(self, mock_openai_class):
        """Test email categorization."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = 'Work'
        
        # Setup mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        categories = email_organizer.categorize_email('Test email content')
        
        self.assertIn('category', categories)
        self.assertEqual(categories['category'], 'Work')


class TestEmailOrganizerSummarization(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()
    
    @patch('ai_organizer.OpenAI')
    def test_summarization(self, mock_openai_class):
        """Test email summarization."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = 'Test summary of the email content.'
        
        # Setup mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        summary = email_organizer.summarize_email('Test email content')
        
        self.assertIsInstance(summary, str)
        self.assertEqual(summary, 'Test summary of the email content.')


class TestEmailOrganizerActionItems(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()
    
    @patch('ai_organizer.OpenAI')
    def test_action_items(self, mock_openai_class):
        """Test action item extraction."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = '- Task 1: Review document\n- Task 2: Send reply'
        
        # Setup mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        action_items = email_organizer.extract_action_items('Test email content')
        
        self.assertIsInstance(action_items, list)
        self.assertGreater(len(action_items), 0)


class TestEmailOrganizerConfidenceScoring(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()
    
    @patch('ai_organizer.OpenAI')
    def test_confidence_scoring(self, mock_openai_class):
        """Test confidence scoring."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = 'Work: 85%\nPersonal: 10%\nPromotions: 5%'
        
        # Setup mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        confidence = email_organizer.confidence_scoring('Test email content')
        
        self.assertIsInstance(confidence, dict)
        self.assertIn('Work', confidence)
        self.assertGreaterEqual(confidence['Work'], 0)


class TestEmailOrganizerAPICallParameters(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mock config."""
        self.mock_config = type('Config', (), {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()
    
    @patch('ai_organizer.OpenAI')
    def test_api_call_parameters(self, mock_openai_class):
        """Test API call parameters."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        email_organizer = EmailOrganizer(config=self.mock_config)
        
        # Test that the organizer has the correct model and settings
        self.assertEqual(email_organizer.llm.model, 'gpt-3.5-turbo')
        self.assertEqual(email_organizer.llm.max_tokens, 500)
        self.assertIsNotNone(email_organizer.llm.categories)


if __name__ == '__main__':
    unittest.main()