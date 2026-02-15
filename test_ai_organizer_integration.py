import os
import openai
import pytest
from email_organizer_ai import EmailOrganizer

class TestEmailOrganizer:

    @classmethod
    def setup_class(cls):
        # Set the OpenAI API key from environment variable
        openai.api_key = os.getenv('OPENAI_API_KEY')
        cls.email_organizer = EmailOrganizer()

    def test_categorize_email(self):
        email_content = "Hello team, we need to discuss the budget for the next project."
        category = self.email_organizer.categorize_email(email_content)
        assert category in ['Finance', 'Project', 'General']  # Example categories

    def test_summarize_email(self):
        email_content = "Dear client, the project is on track and will finish by the end of the month."
        summary = self.email_organizer.summarize_email(email_content)
        assert "project is on track" in summary

    def test_extract_action_items(self):
        email_content = "Please review the attached document and send your feedback by Friday."
        action_items = self.email_organizer.extract_action_items(email_content)
        assert len(action_items) > 0
        assert "send feedback by Friday" in action_items

    def test_confidence_scoring(self):
        email_content = "We have a meeting scheduled on Wednesday at 10 AM."
        confidence_score = self.email_organizer.confidence_scoring(email_content)
        assert confidence_score >= 0.0 and confidence_score <= 1.0


if __name__ == '__main__':
    pytest.main()