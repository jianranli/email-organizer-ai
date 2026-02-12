# Email Organizer AI

## Overview
Email Organizer AI is a project designed to help users manage their email more effectively through automation and intelligent sorting. It utilizes machine learning algorithms to categorize and prioritize incoming emails, ensuring that important messages are highlighted while less urgent ones are organized appropriately.

## Features
- Intelligent email sorting based on the subject and content
- Prioritization of emails based on user-defined rules
- Integration with popular email services (e.g., Gmail, Outlook)
- User-friendly dashboard for monitoring and managing emails
- Customizable settings to suit individual needs

## Installation
To get started with Email Organizer AI, follow the steps below:

1. Clone the repository:
   ```bash
   git clone https://github.com/jianranli/email-organizer-ai.git
   cd email-organizer-ai
   ```
2. Install the necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   Make sure to configure the environment variables in a `.env` file as follows:
   
   ```
   EMAIL_SERVICE=your_email_service
   API_KEY=your_api_key
   ```
4. Run the application:
   ```bash
   python app.py
   ```

## Usage
Once the application is running, you can access the dashboard at [http://localhost:5000](http://localhost:5000). Here you can view your sorted emails, adjust settings, and customize the AI's behavior.

## Contributing
We welcome contributions to Email Organizer AI! To contribute:
1. Fork the repository.
2. Create a new branch for your feature/bugfix.
3. Commit your changes and push them to your fork.
4. Create a pull request outlining your changes.

## License
This project is licensed under the MIT License.