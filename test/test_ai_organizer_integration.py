        self.config = type('Config', (), {
            'OPENAI_API_KEY': api_key,
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_MAX_TOKENS': 500,
            'EMAIL_CATEGORIES': ['Work', 'Personal', 'Promotions', 'Updates'],
            'MAX_EMAIL_CONTENT_LENGTH': 8000
        })()