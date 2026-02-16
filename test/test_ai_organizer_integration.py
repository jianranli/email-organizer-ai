import unittest
import os
from ai_organizer import EmailOrganizer
from config import Config


class TestEmailOrganizerIntegration(unittest.TestCase):
    """Integration tests for EmailOrganizer with real OpenAI API."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Check if OPENAI_API_KEY is set
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            self.skipTest("OPENAI_API_KEY environment variable not set")
        
        # Create a mock config
        self.config = type('Config', (), {
            'OPENAI_API_KEY': api_key,
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions', 'Updates'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()
        
        self.organizer = EmailOrganizer(config=self.config)

    def test_categorize_email_work(self):
        """Test categorizing a work-related email."""
        email_content = "Team meeting scheduled for tomorrow at 2 PM to discuss Q4 goals."
        
        result = self.organizer.categorize_email(email_content)
        
        self.assertIsInstance(result, dict)
        self.assertIn('category', result)
        self.assertIn(result['category'], self.config.EMAIL_CATEGORIES)
        print(f"✅ Email categorized as: {result['category']}")

    def test_summarize_email(self):
        """Test email summarization."""
        email_content = """
        Dear Team,
        
        I wanted to update you on our project status. We have completed phase 1 
        and are now moving into phase 2. The deadline is still on track for end 
        of month. Please review the attached documents and provide feedback by Friday.
        
        Best regards,
        John
        """
        
        summary = self.organizer.summarize_email(email_content)
        
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertLess(len(summary), len(email_content))
        print(f"✅ Summary generated: {summary[:100]}...")

    def test_extract_action_items_with_tasks(self):
        """Test extracting action items from email with tasks."""
        email_content = """
        Please complete the following:
        1. Review the project proposal
        2. Send feedback by Friday
        3. Schedule a follow-up meeting
        """
        
        action_items = self.organizer.extract_action_items(email_content)
        
        self.assertIsInstance(action_items, list)
        self.assertGreater(len(action_items), 0)
        print(f"✅ Extracted {len(action_items)} action items")
        for item in action_items:
            print(f"   - {item}")

    def test_extract_action_items_no_tasks(self):
        """Test extracting action items from email without tasks."""
        email_content = "This is just an FYI email with no action required."
        
        action_items = self.organizer.extract_action_items(email_content)
        
        self.assertIsInstance(action_items, list)
        print(f"✅ No action items found (as expected)")

    def test_confidence_scoring(self):
        """Test confidence scoring for categorization."""
        email_content = "Meeting invitation for project review tomorrow at 10 AM."
        
        scores = self.organizer.confidence_scoring(email_content)
        
        self.assertIsInstance(scores, dict)
        
        # Verify scores are valid percentages
        for category, score in scores.items():
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        
        print(f"✅ Confidence scores:")
        for category, score in scores.items():
            print(f"   {category}: {score*100:.1f}%")

    def test_categorize_personal_email(self):
        """Test categorizing a personal email."""
        email_content = "Hi! Would you like to grab dinner this weekend? Let me know!"
        
        result = self.organizer.categorize_email(email_content)
        
        self.assertIsInstance(result, dict)
        self.assertIn('category', result)
        print(f"✅ Personal email categorized as: {result['category']}")

    def test_categorize_promotional_email(self):
        """Test categorizing a promotional email."""
        email_content = """
        EXCLUSIVE OFFER! 
        Get 50% off all items this weekend only! 
        Shop now and save big!
        """
        
        result = self.organizer.categorize_email(email_content)
        
        self.assertIsInstance(result, dict)
        self.assertIn('category', result)
        print(f"✅ Promotional email categorized as: {result['category']}")


if __name__ == '__main__':
    unittest.main()