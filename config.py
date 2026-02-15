    @property
    def MAX_EMAIL_CONTENT_LENGTH(self) -> int:
        """Maximum character length for email content sent to AI model.

        Prevents context/token length errors with LLM APIs.
        Default is 8,000 – suitable for OpenAI’s base models.
        Adjust via environment variable MAX_EMAIL_CONTENT_LENGTH.
        """
        return int(os.getenv('MAX_EMAIL_CONTENT_LENGTH', '8000'))
