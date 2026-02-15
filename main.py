"""Email Organizer AI - Main Script

Automatically categorizes and organizes Gmail emails using OpenAI GPT models.

Features:
- Fetches emails from Gmail inbox (read and unread)
- Uses AI to categorize emails
- Applies labels and archives emails in keep categories
- Moves unwanted emails to trash
- Skips emails that are already labeled
- Provides detailed progress logging and summary

Usage:
    python main.py              # Process last 10 emails (default)
    python main.py -n 50        # Process last 50 emails
    python main.py -n 0         # Process all inbox emails
"""

import logging
import argparse
import time
from gmail_client import GmailClient
from ai_organizer import EmailOrganizer
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(max_emails=None):
    """Main entry point for the email organizer.
    
    Args:
        max_emails (int, optional): Maximum number of emails to organize. 
                                    If None, organizes all inbox emails.
    """
    try:
        config = Config()
        gmail_client = GmailClient(config)
        organizer = EmailOrganizer(config)
        
        logger.info("Starting email organization process...")
        
        # Authenticate with Gmail
        service = gmail_client.authenticate()
        logger.info("Successfully authenticated with Gmail")
        
        # Fetch inbox emails (both read and unread)
        # Pass max_emails to avoid fetching more than needed
        emails = gmail_client.fetch_emails(query='in:inbox', max_results=max_emails)
        
        if max_emails is not None and max_emails > 0:
            logger.info(f"Fetched {len(emails)} inbox emails (limited to {max_emails})")
        else:
            logger.info(f"Fetched {len(emails)} inbox emails (all)")
        
        # Track processed count and categorization results
        processed_count = 0
        skipped_already_labeled = 0
        skipped_rate_limit = 0
        category_counts = {}  # Track count per category
        kept_count = 0
        trashed_count = 0
        rate_limited_emails = []  # Track emails that hit rate limits for retry
        
        # Get all existing category label IDs for filtering
        all_labels = gmail_client.get_all_labels().get('labels', [])
        category_label_ids = {}
        for label in all_labels:
            label_name = label.get('name', '')
            if label_name in config.CATEGORIES_TO_KEEP or label_name.lower() in [cat.lower() for cat in config.CATEGORIES_TO_KEEP]:
                category_label_ids[label.get('id')] = label_name
        
        logger.info(f"Will skip emails already labeled with: {', '.join(category_label_ids.values()) if category_label_ids else 'none'}")
        logger.info("")
        
        # Process each email
        for idx, email in enumerate(emails):
            try:
                # Extract email content
                email_id = email['id']
                
                # Check if email already has a category label
                existing_labels = gmail_client.get_message_labels(email_id)
                already_labeled = any(label_id in category_label_ids for label_id in existing_labels)
                
                if already_labeled:
                    # Skip this email - already processed
                    skipped_already_labeled += 1
                    continue
                
                # Get subject for logging (faster metadata-only call)
                subject = gmail_client.get_message_subject(email_id)
                # Truncate long subjects for logging
                subject_display = subject[:60] + '...' if len(subject) > 60 else subject
                
                # Get full message for AI processing
                message = gmail_client.get_message(email_id)
                
                # Organize with AI
                categorization = organizer.categorize_email(message)
                category = categorization['category']
                
                # Track category counts
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Log categorization with subject
                logger.info(f"📧 Subject: \"{subject_display}\"")
                logger.info(f"   Category: [{category}]")
                
                # Check if this category should be kept
                if category in config.CATEGORIES_TO_KEEP:
                    # Only process summary and action items for emails we keep
                    summary = organizer.summarize_email(message)
                    action_items = organizer.extract_action_items(message)
                    
                    # Create or get label
                    label_id = gmail_client.create_label_if_not_exists(category)
                    
                    # Apply label and archive
                    gmail_client.apply_label(email_id, label_id)
                    gmail_client.archive_email(email_id)
                    kept_count += 1
                    
                    logger.info(f"   ✓ Action: Labeled as '{category}' and archived ({processed_count + 1}/{len(emails)})")
                else:
                    # Delete emails that don't match our keep categories
                    gmail_client.trash_email(email_id)
                    trashed_count += 1
                    logger.info(f"   ✗ Action: Moved to trash (unwanted category)")
                
                logger.info("")  # Blank line for readability
                
                processed_count += 1
                
            except Exception as e:
                error_msg = str(e)
                # Check if it's a rate limit error
                if 'rate_limit_exceeded' in error_msg.lower() or '429' in error_msg:
                    logger.warning(f"Rate limit hit on email {email_id}. Will retry later.")
                    rate_limited_emails.append((email_id, email))
                else:
                    logger.error(f"Error processing email {email_id}: {error_msg}")
                continue
            
            # Add delay between emails to avoid rate limits (except after last email)
            if idx < len(emails) - 1 and config.RATE_LIMIT_DELAY > 0:
                logger.debug(f"Waiting {config.RATE_LIMIT_DELAY}s before next email...")
                time.sleep(config.RATE_LIMIT_DELAY)
        
        # Retry rate-limited emails with exponential backoff
        if rate_limited_emails:
            logger.info(f"\n{'='*70}")
            logger.info(f"RETRYING {len(rate_limited_emails)} RATE-LIMITED EMAILS")
            logger.info(f"{'='*70}\n")
            
            retry_delay = config.RATE_LIMIT_DELAY * 3  # Start with 3x normal delay
            max_retries = 3
            
            for retry_attempt in range(max_retries):
                if not rate_limited_emails:
                    break
                
                logger.info(f"Retry attempt {retry_attempt + 1}/{max_retries}...")
                logger.info(f"Waiting {retry_delay}s before retrying {len(rate_limited_emails)} emails...")
                time.sleep(retry_delay)
                logger.info("")
                
                remaining_emails = []
                
                for email_idx, (email_id, email) in enumerate(rate_limited_emails):
                    try:
                        # Check if already labeled (might have been processed in another run)
                        existing_labels = gmail_client.get_message_labels(email_id)
                        already_labeled = any(label_id in category_label_ids for label_id in existing_labels)
                        
                        if already_labeled:
                            skipped_already_labeled += 1
                            continue
                        
                        # Get subject for logging
                        subject = gmail_client.get_message_subject(email_id)
                        subject_display = subject[:60] + '...' if len(subject) > 60 else subject
                        
                        # Get full message for AI processing
                        message = gmail_client.get_message(email_id)
                        
                        # Organize with AI
                        categorization = organizer.categorize_email(message)
                        category = categorization['category']
                        
                        # Track category counts
                        category_counts[category] = category_counts.get(category, 0) + 1
                        
                        # Log categorization with subject
                        logger.info(f"📧 Subject: \"{subject_display}\"")
                        logger.info(f"   Category: [{category}]")
                        
                        # Check if this category should be kept
                        if category in config.CATEGORIES_TO_KEEP:
                            # Only process summary and action items for emails we keep
                            summary = organizer.summarize_email(message)
                            action_items = organizer.extract_action_items(message)
                            
                            # Create or get label
                            label_id = gmail_client.create_label_if_not_exists(category)
                            
                            # Apply label and archive
                            gmail_client.apply_label(email_id, label_id)
                            gmail_client.archive_email(email_id)
                            kept_count += 1
                            
                            logger.info(f"   ✓ Action: Labeled as '{category}' and archived (retry success)")
                        else:
                            # Delete emails that don't match our keep categories
                            gmail_client.trash_email(email_id)
                            trashed_count += 1
                            logger.info(f"   ✗ Action: Moved to trash (unwanted category)")
                        
                        logger.info("")  # Blank line for readability
                        processed_count += 1
                        
                        # Add delay between retries (but not after the last email)
                        if email_idx < len(rate_limited_emails) - 1:
                            time.sleep(retry_delay)
                        
                    except Exception as e:
                        error_msg = str(e)
                        if 'rate_limit_exceeded' in error_msg.lower() or '429' in error_msg:
                            logger.warning(f"Rate limit hit again on email {email_id}")
                            remaining_emails.append((email_id, email))
                        else:
                            logger.error(f"Error processing email {email_id}: {error_msg}")
                
                # Update the list for next retry attempt
                rate_limited_emails = remaining_emails
                
                if rate_limited_emails:
                    # Exponential backoff - double the delay for next attempt
                    retry_delay *= 2
                    logger.info(f"{len(rate_limited_emails)} emails still rate-limited, will retry with {retry_delay}s delay...\n")
            
            # After all retries, count remaining as skipped
            skipped_rate_limit = len(rate_limited_emails)
            if skipped_rate_limit > 0:
                logger.warning(f"\n⚠ {skipped_rate_limit} emails could not be processed after {max_retries} retry attempts")
                logger.warning(f"   These will be processed on the next run\n")
        
        # Print categorization results
        print("\n" + "=" * 70)
        print("CATEGORIZATION RESULTS")
        print("=" * 70)
        
        if category_counts:
            print("\nEmails by Category:")
            print("-" * 70)
            for category in sorted(category_counts.keys()):
                count = category_counts[category]
                action = "✓ KEPT" if category in config.CATEGORIES_TO_KEEP else "✗ TRASHED"
                print(f"  {category:15} {count:3} emails  →  {action}")
            
            print("-" * 70)
            print(f"\nTotal Fetched:    {len(emails)} emails")
            if skipped_already_labeled > 0:
                print(f"  ⊜ Skipped:      {skipped_already_labeled} emails (already labeled)")
            if skipped_rate_limit > 0:
                print(f"  ⚠ Skipped:      {skipped_rate_limit} emails (rate limits - failed after retries)")
            print(f"  ✓ Kept:         {kept_count} emails (labeled & archived)")
            print(f"  ✗ Trashed:      {trashed_count} emails (moved to trash)")
            print(f"Total Processed:  {processed_count} emails")
        else:
            print("\nNo emails were processed.")
            if skipped_already_labeled > 0:
                print(f"{skipped_already_labeled} emails skipped (already labeled)")
            if skipped_rate_limit > 0:
                print(f"{skipped_rate_limit} emails skipped (rate limits - failed after retries)")
        
        print("=" * 70 + "\n")
        
        # Summary log message
        summary_parts = []
        if skipped_already_labeled > 0:
            summary_parts.append(f"{skipped_already_labeled} already labeled")
        if skipped_rate_limit > 0:
            summary_parts.append(f"{skipped_rate_limit} failed after retries")
        
        summary_msg = f"Email organization complete! Processed {processed_count} out of {len(emails)} emails."
        if summary_parts:
            summary_msg += f" (Skipped: {', '.join(summary_parts)})"
        logger.info(summary_msg)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI-powered email organizer for Gmail')
    parser.add_argument(
        '--max-emails',
        type=int,
        default=None,
        help='Maximum number of emails to organize (default: all inbox emails)'
    )
    parser.add_argument(
        '-n',
        type=int,
        dest='max_emails',
        help='Shorthand for --max-emails'
    )
    
    args = parser.parse_args()
    main(max_emails=args.max_emails)