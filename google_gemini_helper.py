"""Google Gemini integration helper for email categorization and analysis."""

import os
from typing import Dict, List
import google.genai as genai

class GeminiEmailOrganizer:
    """AI-powered email organizer using Google Gemini."""
    def __init__(self, config=None, api_key=None):
        import logging
        # google.genai expects API key via environment variable GOOGLE_API_KEY
        if config and getattr(config, 'GOOGLE_API_KEY', None):
            self.api_key = config.GOOGLE_API_KEY
            os.environ['GOOGLE_API_KEY'] = self.api_key
        elif api_key:
            self.api_key = api_key
            os.environ['GOOGLE_API_KEY'] = self.api_key
        else:
            raise ValueError("No Gemini API key provided. Set GOOGLE_API_KEY in config or pass api_key.")
        
        # Create the genai client
        self.client = genai.Client()
        
        # Set model name (use gemini-2.0-flash as default instead of deprecated gemini-pro)
        self.model_name = getattr(config, 'GEMINI_MODEL', 'gemini-2.0-flash') if config else 'gemini-2.0-flash'
        self.categories = getattr(config, 'EMAIL_CATEGORIES', ['Notes', 'Github']) if config else ['Notes', 'Github']
        self.max_email_length = getattr(config, 'MAX_EMAIL_CONTENT_LENGTH', 8000) if config else 8000

    def _truncate_email_content(self, email_content: str) -> str:
        if len(email_content) <= self.max_email_length:
            return email_content
        truncated = email_content[:self.max_email_length]
        last_space = truncated.rfind(' ')
        if last_space > self.max_email_length * 0.9:
            truncated = truncated[:last_space]
        return truncated + "\n\n[Email content truncated due to length...]"

    def categorize_email(self, email_content: str) -> Dict[str, str]:
        email_content = self._truncate_email_content(email_content)
        categories_str = ', '.join(self.categories)
        prompt = (
            f"Categorize this email into one of these categories: {categories_str}\n\n"
            f"Email: {email_content}\n\n"
            f"Respond with just the category name."
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        category = response.text.strip() if hasattr(response, 'text') else ''
        return {'category': category, 'confidence': 'high'}

    def summarize_email(self, email_content: str) -> str:
        email_content = self._truncate_email_content(email_content)
        prompt = f"Summarize this email in 2-3 sentences:\n\n{email_content}"
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text.strip() if hasattr(response, 'text') else ''

    def extract_action_items(self, email_content: str) -> List[str]:
        email_content = self._truncate_email_content(email_content)
        prompt = (
            f"Extract any action items or tasks from this email. "
            f"List them as bullet points. If there are no action items, respond with 'None'.\n\n"
            f"Email: {email_content}"
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        result = response.text.strip() if hasattr(response, 'text') else ''
        if result.lower() == 'none' or not result:
            return []
        action_items = [item.strip('- •*').strip() for item in result.split('\n') if item.strip()]
        return action_items

    def confidence_scoring(self, email_content: str) -> Dict[str, float]:
        email_content = self._truncate_email_content(email_content)
        categories_str = ', '.join(self.categories)
        prompt = (
            f"Rate the confidence (0-100%) that this email belongs to each category: {categories_str}\n\n"
            f"Email: {email_content}\n\n"
            f"Respond in format: CategoryName: XX%"
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        result = response.text.strip() if hasattr(response, 'text') else ''
        scores = {}
        for line in result.split('\n'):
            if ':' in line:
                category, score = line.split(':', 1)
                category = category.strip()
                score = score.strip().rstrip('%')
                try:
                    scores[category] = float(score) / 100.0
                except ValueError:
                    pass
        return scores
