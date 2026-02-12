import logging
from gmail_client import GmailClient
from ai_organizer import EmailOrganizer
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the email organizer."""
    try:
        config = Config()
        gmail_client = GmailClient(config)
        organizer = EmailOrganizer(config)
        
        logger.info("Starting email organization process...")
        
        # Authenticate with Gmail
        service = gmail_client.authenticate()
        logger.info("Successfully authenticated with Gmail")
        
        # Fetch unread emails
        emails = gmail_client.fetch_emails(service, query='is:unread')
        logger.info(f"Fetched {len(emails)} unread emails")
        
        # Process each email
        for email in emails:
            try:
                # Extract email content
                email_id = email['id']
                message = gmail_client.get_message(service, email_id)
                
                # Organize with AI
                categorization = organizer.categorize_email(message)
                summary = organizer.summarize_email(message)
                action_items = organizer.extract_action_items(message)
                
                logger.info(f"Email {email_id} categorized as: {categorization['category']}")
                
                # Create or get label
                label_id = gmail_client.create_label_if_not_exists(
                    service, 
                    categorization['category']
                )
                
                # Apply label and archive
                gmail_client.apply_label(service, email_id, label_id)
                gmail_client.archive_email(service, email_id)
                
                logger.info(f"Email {email_id} processed and archived")
                
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {str(e)}")
                continue
        
        logger.info("Email organization complete!")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()