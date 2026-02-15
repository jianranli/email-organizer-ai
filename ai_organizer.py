"""OpenAI integration for email categorization and analysis.

Provides AI-powered email processing using OpenAI's GPT models:
- Email categorization
- Email summarization
- Action item extraction
- Confidence scoring

Includes automatic content truncation to prevent context length errors.
"""


from openai import OpenAI
from typing import Dict, List, Optional
from config import Config
from google_gemini_helper import GeminiEmailOrganizer

class EmailOrganizer:
    """AI-powered email organizer using OpenAI or Google Gemini."""
    def __init__(self, config=None, api_key=None):
        self.config = config or Config()
        provider = getattr(self.config, 'LLM_PROVIDER', 'openai')
        self.provider = provider
        if provider == 'gemini':
            self.llm = GeminiEmailOrganizer(config=self.config)
        else:
            # Default to OpenAI
            if self.config.OPENAI_API_KEY:
                self.llm = _OpenAIEmailOrganizer(config=self.config)
            elif api_key:
                self.llm = _OpenAIEmailOrganizer(api_key=api_key)
            else:
                raise ValueError(
                    "No API key provided. Either pass a Config object with OPENAI_API_KEY "
                    "or provide api_key parameter directly."
                )

    def categorize_email(self, email_content: str) -> Dict[str, str]:
        return self.llm.categorize_email(email_content)

    def summarize_email(self, email_content: str) -> str:
        return self.llm.summarize_email(email_content)

    def extract_action_items(self, email_content: str) -> List[str]:
        return self.llm.extract_action_items(email_content)

    def confidence_scoring(self, email_content: str) -> Dict[str, float]:
        return self.llm.confidence_scoring(email_content)


# Internal OpenAI implementation (unchanged, just renamed)
class _OpenAIEmailOrganizer:
    def __init__(self, config=None, api_key=None):
        if config and config.OPENAI_API_KEY:
            self.config = config
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.model = config.OPENAI_MODEL
            self.max_tokens = config.OPENAI_MAX_TOKENS
            self.categories = config.EMAIL_CATEGORIES
            self.max_email_length = config.MAX_EMAIL_CONTENT_LENGTH
        elif api_key:
            self.config = Config()
            self.client = OpenAI(api_key=api_key)
            self.model = 'gpt-3.5-turbo'
            self.max_tokens = 500
            self.categories = self.config.EMAIL_CATEGORIES
            self.max_email_length = self.config.MAX_EMAIL_CONTENT_LENGTH
        else:
            raise ValueError(
                "No API key provided. Either pass a Config object with OPENAI_API_KEY "
                "or provide api_key parameter directly."
            )

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
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an email categorization assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        category = response.choices[0].message.content.strip()
        return {'category': category, 'confidence': 'high'}

    def summarize_email(self, email_content: str) -> str:
        email_content = self._truncate_email_content(email_content)
        prompt = f"Summarize this email in 2-3 sentences:\n\n{email_content}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful email summarization assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content.strip()

    def extract_action_items(self, email_content: str) -> List[str]:
        email_content = self._truncate_email_content(email_content)
        prompt = (
            f"Extract any action items or tasks from this email. "
            f"List them as bullet points. If there are no action items, respond with 'None'.\n\n"
            f"Email: {email_content}"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an assistant that extracts action items from emails.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        result = response.choices[0].message.content.strip()
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
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an email analysis assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        result = response.choices[0].message.content.strip()
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
    
    def _truncate_email_content(self, email_content: str) -> str:
        """Truncate email content to avoid exceeding token limits.
        
        Args:
            email_content: Full email content
            
        Returns:
            Truncated email content if needed, with truncation notice
        """
        if len(email_content) <= self.max_email_length:
            return email_content
        
        # Truncate and add notice
        truncated = email_content[:self.max_email_length]
        # Try to truncate at a word boundary
        last_space = truncated.rfind(' ')
        if last_space > self.max_email_length * 0.9:  # Only if we're still using most of the limit
            truncated = truncated[:last_space]
        
        return truncated + "\n\n[Email content truncated due to length...]"

    def categorize_email(self, email_content: str) -> Dict[str, str]:
        """Categorize an email into predefined categories.
        
        Args:
            email_content: The email content to categorize
            
        Returns:
            Dict with 'category' and 'confidence' keys
        """
        # Truncate email content if needed
        email_content = self._truncate_email_content(email_content)
        
        categories_str = ', '.join(self.categories)
        prompt = (
            f"Categorize this email into one of these categories: {categories_str}\n\n"
            f"Email: {email_content}\n\n"
            f"Respond with just the category name."
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an email categorization assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        category = response.choices[0].message.content.strip()
        
        return {
            'category': category,
            'confidence': 'high'
        }

    def summarize_email(self, email_content: str) -> str:
        """Summarize an email in a concise way."""
        # Truncate email content if needed
        email_content = self._truncate_email_content(email_content)
        
        prompt = f"Summarize this email in 2-3 sentences:\n\n{email_content}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful email summarization assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()

    def extract_action_items(self, email_content: str) -> List[str]:
        """Extract action items from an email."""
        # Truncate email content if needed
        email_content = self._truncate_email_content(email_content)
        
        prompt = (
            f"Extract any action items or tasks from this email. "
            f"List them as bullet points. If there are no action items, respond with 'None'.\n\n"
            f"Email: {email_content}"
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an assistant that extracts action items from emails.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        result = response.choices[0].message.content.strip()
        
        if result.lower() == 'none' or not result:
            return []
        
        action_items = [
            item.strip('- •*').strip() 
            for item in result.split('\n') 
            if item.strip()
        ]
        
        return action_items

    def confidence_scoring(self, email_content: str) -> Dict[str, float]:
        """Provide confidence scoring for the categorization of an email."""
        # Truncate email content if needed
        email_content = self._truncate_email_content(email_content)
        
        categories_str = ', '.join(self.categories)
        prompt = (
            f"Rate the confidence (0-100%) that this email belongs to each category: {categories_str}\n\n"
            f"Email: {email_content}\n\n"
            f"Respond in format: CategoryName: XX%"
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an email analysis assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        result = response.choices[0].message.content.strip()
        
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