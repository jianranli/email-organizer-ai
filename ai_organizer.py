import openai

class AICategorizer:
    def __init__(self, api_key):
        openai.api_key = api_key

    def categorize_email(self, email_content):
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'user', 'content': f'Categorize this email: {email_content}'}
            ]
        )
        return response['choices'][0]['message']['content']

    def summarize_email(self, email_content):
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'user', 'content': f'Summarize this email: {email_content}'}
            ]
        )
        return response['choices'][0]['message']['content']

    def extract_action_items(self, email_content):
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'user', 'content': f'Extract action items from this email: {email_content}'}
            ]
        )
        return response['choices'][0]['message']['content']

    def confidence_scoring(self, email_content):
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'user', 'content': f'Provide confidence scoring for the categorization of this email: {email_content}'}
            ]
        )
        return response['choices'][0]['message']['content']

# Usage Example:
# api_key = 'your-openai-api-key'
# email_content = 'Dear team, please review the attached report and send me feedback.'
# categorizer = AICategorizer(api_key)
# category = categorizer.categorize_email(email_content)
# summary = categorizer.summarize_email(email_content)
# action_items = categorizer.extract_action_items(email_content)
# confidence = categorizer.confidence_scoring(email_content)