"""Unsubscribe Handler for Email Organizer AI.

Automatically detect and unsubscribe from marketing emails, newsletters, and promotional messages.

Features:
- Parse List-Unsubscribe header from email headers (RFC 2369)
- Parse List-Unsubscribe-Post header for one-click unsubscribe (RFC 8058)
- Detect unsubscribe links in email body using regex patterns
- Support multiple unsubscribe types (one-click POST, HTTP GET, web URLs, mailto links)
- URL validation and safety features
- Rate limiting for HTTP requests
"""

import re
import time
import logging
from typing import Dict, Optional, List
from urllib.parse import urlparse, parse_qs
import requests

logger = logging.getLogger(__name__)


class UnsubscribeHandler:
    """Handler for automatic email unsubscribe operations."""

    # Common unsubscribe link patterns in email body
    UNSUBSCRIBE_PATTERNS = [
        r'https?://[^\s<>"]+?unsubscribe[^\s<>"]*',
        r'https?://[^\s<>"]+?opt[_-]?out[^\s<>"]*',
        r'https?://[^\s<>"]+?stop[_-]?receiving[^\s<>"]*',
        r'https?://[^\s<>"]+?manage[_-]?preferences[^\s<>"]*',
        r'https?://[^\s<>"]+?email[_-]?preferences[^\s<>"]*',
    ]

    # Suspicious domain patterns (for phishing protection)
    SUSPICIOUS_PATTERNS = [
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
        r'[a-z0-9-]+\.tk$',  # Free .tk domains
        r'[a-z0-9-]+\.ml$',  # Free .ml domains
        r'bit\.ly',  # URL shorteners (can hide destination)
        r'tinyurl\.com',
        r'goo\.gl',
    ]

    def __init__(self, config=None):
        """Initialize with config for unsubscribe preferences.
        
        Args:
            config: Configuration object with unsubscribe settings
        """
        self.config = config
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests

    def extract_unsubscribe_info(self, email_message: str, headers: Dict[str, str] = None) -> Dict:
        """Extract unsubscribe information from email headers and body.
        
        Args:
            email_message: Full email message text
            headers: Dictionary of email headers
            
        Returns:
            Dictionary with:
            {
                'has_unsubscribe': bool,
                'method': 'one-click' | 'http' | 'mailto' | 'web',
                'url': str,
                'list_unsubscribe_post': str (if available)
            }
        """
        result = {
            'has_unsubscribe': False,
            'method': None,
            'url': None,
            'list_unsubscribe_post': None
        }

        if headers is None:
            headers = {}

        # First, check List-Unsubscribe header (RFC 2369)
        list_unsubscribe = headers.get('List-Unsubscribe', '')
        list_unsubscribe_post = headers.get('List-Unsubscribe-Post', '')

        if list_unsubscribe:
            # Parse List-Unsubscribe header
            # Format: <mailto:unsubscribe@example.com>, <https://example.com/unsubscribe>
            urls = re.findall(r'<([^>]+)>', list_unsubscribe)
            
            # Check for one-click unsubscribe (RFC 8058)
            if list_unsubscribe_post and 'List-Unsubscribe=One-Click' in list_unsubscribe_post:
                # Find first HTTP URL for one-click
                for url in urls:
                    if url.startswith('http'):
                        result['has_unsubscribe'] = True
                        result['method'] = 'one-click'
                        result['url'] = url
                        result['list_unsubscribe_post'] = list_unsubscribe_post
                        return result
            
            # Check for HTTP GET unsubscribe
            for url in urls:
                if url.startswith('http'):
                    result['has_unsubscribe'] = True
                    result['method'] = 'http'
                    result['url'] = url
                    return result
            
            # Check for mailto unsubscribe
            for url in urls:
                if url.startswith('mailto:'):
                    result['has_unsubscribe'] = True
                    result['method'] = 'mailto'
                    result['url'] = url
                    return result

        # If no header found, search email body
        unsubscribe_url = self._find_unsubscribe_in_body(email_message)
        if unsubscribe_url:
            result['has_unsubscribe'] = True
            result['method'] = 'web'
            result['url'] = unsubscribe_url
            return result

        return result

    def _find_unsubscribe_in_body(self, email_body: str) -> Optional[str]:
        """Find unsubscribe link in email body using regex patterns.
        
        Args:
            email_body: Email body text
            
        Returns:
            URL string if found, None otherwise
        """
        # Try each pattern
        for pattern in self.UNSUBSCRIBE_PATTERNS:
            matches = re.findall(pattern, email_body, re.IGNORECASE)
            if matches:
                # Return first match, clean up any trailing characters
                url = matches[0].rstrip('.,;:)')
                return url
        
        return None

    def should_unsubscribe(self, email_message: str, category: str, sender: str) -> bool:
        """Determine if this email should be unsubscribed based on filters.
        
        Args:
            email_message: Full email message text
            category: Email category from AI classification
            sender: Email sender address
            
        Returns:
            True if email should be unsubscribed, False otherwise
        """
        if not self.config or not self.config.AUTO_UNSUBSCRIBE_ENABLED:
            return False

        # Check if category matches target categories
        target_categories = self.config.UNSUBSCRIBE_CATEGORIES
        if category not in target_categories:
            return False

        # Check if sender matches target patterns
        sender_patterns = self.config.UNSUBSCRIBE_SENDER_PATTERNS
        sender_lower = sender.lower()
        
        for pattern in sender_patterns:
            if pattern.lower() in sender_lower:
                return True

        return False

    def unsubscribe(self, unsubscribe_info: Dict, email_id: str, dry_run: bool = False) -> Dict:
        """Attempt to unsubscribe from the mailing list.
        
        Args:
            unsubscribe_info: Dictionary from extract_unsubscribe_info()
            email_id: Email ID for logging
            dry_run: If True, log what would be done but don't actually unsubscribe
            
        Returns:
            Dictionary with:
            {
                'success': bool,
                'method_used': str,
                'action_taken': str,
                'message': str
            }
        """
        result = {
            'success': False,
            'method_used': unsubscribe_info.get('method'),
            'action_taken': 'none',
            'message': ''
        }

        if not unsubscribe_info.get('has_unsubscribe'):
            result['message'] = 'No unsubscribe method found'
            return result

        url = unsubscribe_info.get('url')
        method = unsubscribe_info.get('method')

        # Validate URL before proceeding
        if url and not self._is_safe_url(url):
            result['message'] = 'URL failed safety validation (possible phishing)'
            logger.warning(f"Suspicious URL detected for email {email_id}: {url}")
            return result

        # Handle dry-run mode
        if dry_run:
            result['success'] = True
            result['action_taken'] = f'dry-run: would unsubscribe via {method}'
            result['message'] = f'DRY RUN: Would unsubscribe using {method} method to {url}'
            return result

        # Perform actual unsubscribe based on method
        try:
            if method == 'one-click':
                return self._unsubscribe_one_click(unsubscribe_info, email_id)
            elif method == 'http':
                return self._unsubscribe_http_get(url, email_id)
            elif method == 'mailto':
                result['action_taken'] = 'manual-required'
                result['message'] = f'Manual action required: Send email to {url}'
                logger.info(f"Manual unsubscribe needed for {email_id}: {url}")
                return result
            elif method == 'web':
                result['action_taken'] = 'manual-required'
                result['message'] = f'Manual action required: Visit {url}'
                logger.info(f"Manual unsubscribe needed for {email_id}: {url}")
                return result
            else:
                result['message'] = f'Unsupported unsubscribe method: {method}'
                return result

        except Exception as e:
            result['message'] = f'Error during unsubscribe: {str(e)}'
            logger.error(f"Error unsubscribing from email {email_id}: {e}")
            return result

    def _unsubscribe_one_click(self, unsubscribe_info: Dict, email_id: str) -> Dict:
        """Perform one-click unsubscribe via HTTP POST (RFC 8058).
        
        Args:
            unsubscribe_info: Unsubscribe information dictionary
            email_id: Email ID for logging
            
        Returns:
            Result dictionary
        """
        url = unsubscribe_info['url']
        
        # Rate limiting
        self._apply_rate_limit()

        # Get timeout from config
        timeout = self.config.UNSUBSCRIBE_TIMEOUT if self.config else 10

        try:
            response = requests.post(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Email-Organizer-AI/1.0)',
                    'List-Unsubscribe': 'One-Click'
                },
                timeout=timeout,
                allow_redirects=True,
                verify=True  # Verify SSL certificates
            )

            if response.status_code in [200, 201, 202, 204]:
                return {
                    'success': True,
                    'method_used': 'one-click',
                    'action_taken': 'automated-unsubscribe',
                    'message': f'Successfully unsubscribed via one-click (status: {response.status_code})'
                }
            else:
                return {
                    'success': False,
                    'method_used': 'one-click',
                    'action_taken': 'failed',
                    'message': f'Unsubscribe failed with status code: {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'method_used': 'one-click',
                'action_taken': 'failed',
                'message': 'Request timeout'
            }
        except requests.exceptions.SSLError:
            return {
                'success': False,
                'method_used': 'one-click',
                'action_taken': 'failed',
                'message': 'SSL certificate verification failed'
            }
        except Exception as e:
            return {
                'success': False,
                'method_used': 'one-click',
                'action_taken': 'failed',
                'message': f'Request failed: {str(e)}'
            }

    def _unsubscribe_http_get(self, url: str, email_id: str) -> Dict:
        """Perform unsubscribe via HTTP GET request.
        
        Args:
            url: Unsubscribe URL
            email_id: Email ID for logging
            
        Returns:
            Result dictionary
        """
        # Rate limiting
        self._apply_rate_limit()

        # Get timeout from config
        timeout = self.config.UNSUBSCRIBE_TIMEOUT if self.config else 10

        try:
            response = requests.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Email-Organizer-AI/1.0)'
                },
                timeout=timeout,
                allow_redirects=True,
                verify=True
            )

            if response.status_code in [200, 201, 202, 204]:
                return {
                    'success': True,
                    'method_used': 'http',
                    'action_taken': 'automated-unsubscribe',
                    'message': f'Successfully unsubscribed via HTTP GET (status: {response.status_code})'
                }
            else:
                return {
                    'success': False,
                    'method_used': 'http',
                    'action_taken': 'failed',
                    'message': f'Unsubscribe failed with status code: {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'method_used': 'http',
                'action_taken': 'failed',
                'message': 'Request timeout'
            }
        except requests.exceptions.SSLError:
            return {
                'success': False,
                'method_used': 'http',
                'action_taken': 'failed',
                'message': 'SSL certificate verification failed'
            }
        except Exception as e:
            return {
                'success': False,
                'method_used': 'http',
                'action_taken': 'failed',
                'message': f'Request failed: {str(e)}'
            }

    def _is_safe_url(self, url: str) -> bool:
        """Validate URL to prevent phishing attacks.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL appears safe, False otherwise
        """
        if not url:
            return False

        # Skip validation for mailto links
        if url.startswith('mailto:'):
            return True

        try:
            parsed = urlparse(url)
            
            # Must have a scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False

            # Must be HTTP or HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False

            # Check against suspicious patterns
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, parsed.netloc, re.IGNORECASE):
                    return False

            return True

        except Exception:
            return False

    def _apply_rate_limit(self):
        """Apply rate limiting between HTTP requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
