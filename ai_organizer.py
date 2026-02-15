# Updated ai_organizer.py

from openai import OpenAI

# Initialize client with your API key (replace 'your-api-key' with an actual API key)
client = OpenAI(api_key='your-api-key')

# Example of using the new OpenAI API

def get_chat_response(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Other functionality of the ai_organizer.py stays the same.
