import logging
import argparse
from gmail_client import GmailClient
from ai_organizer import EmailOrganizer
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(max_emails=None):
    """Main entry point for the email organizer.
    
    Args:
        max_emails (int, optional): Maximum number of emails to organize. 
                                    If None, organizes all unread emails.
    """
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
        
        # Limit the number of emails if specified
        if max_emails is not None and max_emails > 0:
            emails = emails[:max_emails]
            logger.info(f"Processing {len(emails)} emails (limited by max_emails parameter)")
        else:
            logger.info(f"Processing all {len(emails)} emails")
        
        # Track processed count
        processed_count = 0
        
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
                
                processed_count += 1
                logger.info(f"Email {email_id} processed and archived ({processed_count}/{len(emails)})")
                
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {str(e)}")
                continue
        
        logger.info(f"Email organization complete! Processed {processed_count} out of {len(emails)} emails.")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI-powered email organizer for Gmail')
    parser.add_argument(
        '--max-emails',
        type=int,
        default=None,
        help='Maximum number of emails to organize (default: all unread emails)'
    )
    parser.add_argument(
        '-n',
        type=int,
        dest='max_emails',
        help='Shorthand for --max-emails'
    )
    
    args = parser.parse_args()
    main(max_emails=args.max_emails)