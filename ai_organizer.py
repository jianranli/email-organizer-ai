import openai
from typing import Dict, List, Optional

class EmailOrganizer:
    """AI-powered email organizer using OpenAI."""
    
    def __init__(self, config=None, api_key=None):
        """Initialize EmailOrganizer.
        
        Args:
            config: Config object with OPENAI_API_KEY and other settings
            api_key: Direct API key (for backward compatibility)
        """
        self.config = config
        
        # Get API key from config first, then fallback to direct api_key param
        if config and config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
            self.model = config.OPENAI_MODEL
            self.max_tokens = config.OPENAI_MAX_TOKENS
            self.categories = config.EMAIL_CATEGORIES
        elif api_key:
            openai.api_key = api_key
            self.model = 'gpt-3.5-turbo'
            self.max_tokens = 500
            self.categories = ['Primary', 'Social', 'Promotions', 'Updates', 'Forums']
        else:
            raise ValueError(
                "No API key provided. Either pass a Config object with OPENAI_API_KEY "
                "or provide api_key parameter directly."
            )

    def categorize_email(self, email_content: str) -> Dict[str, str]:
        """Categorize an email into predefined categories.
        
        Args:
            email_content: The email content to categorize
            
        Returns:
            Dict with 'category' and 'confidence' keys
        """
        categories_str = ', '.join(self.categories)
        prompt = (
            f"Categorize this email into one of these categories: {categories_str}\n\n"
            f"Email: {email_content}\n\n"
            f"Respond with just the category name."
        )
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an email categorization assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        category = response['choices'][0]['message']['content'].strip()
        
        return {
            'category': category,
            'confidence': 'high'
        }

    def summarize_email(self, email_content: str) -> str:
        """Summarize an email in a concise way."""
        prompt = f"Summarize this email in 2-3 sentences:\n\n{email_content}"
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful email summarization assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        return response['choices'][0]['message']['content'].strip()

    def extract_action_items(self, email_content: str) -> List[str]:
        """Extract action items from an email."""
        prompt = (
            f"Extract any action items or tasks from this email. "
            f"List them as bullet points. If there are no action items, respond with 'None'.\n\n"
            f"Email: {email_content}"
        )
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an assistant that extracts action items from emails.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        result = response['choices'][0]['message']['content'].strip()
        
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
        categories_str = ', '.join(self.categories)
        prompt = (
            f"Rate the confidence (0-100%) that this email belongs to each category: {categories_str}\n\n"
            f"Email: {email_content}\n\n"
            f"Respond in format: CategoryName: XX%"
        )
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are an email analysis assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=self.max_tokens
        )
        
        result = response['choices'][0]['message']['content'].strip()
        
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