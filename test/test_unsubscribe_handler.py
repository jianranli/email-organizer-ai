"""Unit tests for UnsubscribeHandler."""

import unittest
from unittest.mock import patch, MagicMock, Mock
from unsubscribe_handler import UnsubscribeHandler


class TestUnsubscribeHandler(unittest.TestCase):
    """Test cases for UnsubscribeHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = MagicMock()
        self.config.AUTO_UNSUBSCRIBE_ENABLED = True
        self.config.UNSUBSCRIBE_CATEGORIES = ['Promotions', 'Newsletters', 'Spam']
        self.config.UNSUBSCRIBE_SENDER_PATTERNS = ['noreply@', 'no-reply@', 'donotreply@']
        self.config.UNSUBSCRIBE_DRY_RUN = True
        self.config.UNSUBSCRIBE_TIMEOUT = 10
        
        self.handler = UnsubscribeHandler(self.config)

    def test_extract_list_unsubscribe_header(self):
        """Test parsing List-Unsubscribe header."""
        headers = {
            'List-Unsubscribe': '<https://example.com/unsubscribe?id=123>',
            'From': 'newsletter@example.com',
            'Subject': 'Weekly Newsletter'
        }
        
        result = self.handler.extract_unsubscribe_info('Email body text', headers)
        
        self.assertTrue(result['has_unsubscribe'])
        self.assertEqual(result['method'], 'http')
        self.assertEqual(result['url'], 'https://example.com/unsubscribe?id=123')

    def test_extract_list_unsubscribe_one_click(self):
        """Test parsing List-Unsubscribe-Post header for one-click unsubscribe."""
        headers = {
            'List-Unsubscribe': '<https://example.com/unsubscribe?id=123>',
            'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
            'From': 'newsletter@example.com'
        }
        
        result = self.handler.extract_unsubscribe_info('Email body text', headers)
        
        self.assertTrue(result['has_unsubscribe'])
        self.assertEqual(result['method'], 'one-click')
        self.assertEqual(result['url'], 'https://example.com/unsubscribe?id=123')
        self.assertIsNotNone(result['list_unsubscribe_post'])

    def test_extract_mailto_unsubscribe(self):
        """Test parsing mailto: unsubscribe links."""
        headers = {
            'List-Unsubscribe': '<mailto:unsubscribe@example.com>',
            'From': 'newsletter@example.com'
        }
        
        result = self.handler.extract_unsubscribe_info('Email body text', headers)
        
        self.assertTrue(result['has_unsubscribe'])
        self.assertEqual(result['method'], 'mailto')
        self.assertEqual(result['url'], 'mailto:unsubscribe@example.com')

    def test_detect_unsubscribe_link_in_body(self):
        """Test detecting unsubscribe links in email body."""
        email_body = """
        Thank you for subscribing!
        
        If you wish to unsubscribe, please visit:
        https://example.com/unsubscribe?token=abc123
        
        Best regards,
        The Team
        """
        
        result = self.handler.extract_unsubscribe_info(email_body, {})
        
        self.assertTrue(result['has_unsubscribe'])
        self.assertEqual(result['method'], 'web')
        self.assertIn('unsubscribe', result['url'])

    def test_detect_opt_out_link_in_body(self):
        """Test detecting opt-out links in email body."""
        email_body = """
        Marketing email content here.
        
        To opt-out, click here: https://example.com/opt-out?id=xyz
        """
        
        result = self.handler.extract_unsubscribe_info(email_body, {})
        
        self.assertTrue(result['has_unsubscribe'])
        self.assertEqual(result['method'], 'web')
        self.assertIn('opt-out', result['url'])

    def test_should_unsubscribe_by_category(self):
        """Test category-based filtering."""
        email_message = "Test email content"
        
        # Should unsubscribe from Promotions
        result = self.handler.should_unsubscribe(
            email_message, 
            'Promotions', 
            'noreply@example.com'
        )
        self.assertTrue(result)
        
        # Should not unsubscribe from Work
        result = self.handler.should_unsubscribe(
            email_message, 
            'Work', 
            'noreply@example.com'
        )
        self.assertFalse(result)

    def test_should_unsubscribe_by_sender_pattern(self):
        """Test sender pattern matching."""
        email_message = "Test email content"
        
        # Should unsubscribe from noreply@ sender
        result = self.handler.should_unsubscribe(
            email_message, 
            'Promotions', 
            'noreply@example.com'
        )
        self.assertTrue(result)
        
        # Should not unsubscribe from regular sender
        result = self.handler.should_unsubscribe(
            email_message, 
            'Promotions', 
            'john.doe@example.com'
        )
        self.assertFalse(result)

    def test_should_unsubscribe_disabled(self):
        """Test that unsubscribe doesn't happen when disabled."""
        self.config.AUTO_UNSUBSCRIBE_ENABLED = False
        handler = UnsubscribeHandler(self.config)
        
        result = handler.should_unsubscribe(
            "Test email", 
            'Promotions', 
            'noreply@example.com'
        )
        self.assertFalse(result)

    @patch('unsubscribe_handler.requests.post')
    def test_one_click_unsubscribe_success(self, mock_post):
        """Test RFC 8058 one-click unsubscribe success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        self.config.UNSUBSCRIBE_DRY_RUN = False
        handler = UnsubscribeHandler(self.config)
        
        unsubscribe_info = {
            'has_unsubscribe': True,
            'method': 'one-click',
            'url': 'https://example.com/unsubscribe',
            'list_unsubscribe_post': 'List-Unsubscribe=One-Click'
        }
        
        result = handler.unsubscribe(unsubscribe_info, 'email123', dry_run=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['method_used'], 'one-click')
        self.assertEqual(result['action_taken'], 'automated-unsubscribe')
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'https://example.com/unsubscribe')
        self.assertIn('List-Unsubscribe', call_args[1]['headers'])

    @patch('unsubscribe_handler.requests.get')
    def test_http_get_unsubscribe_success(self, mock_get):
        """Test HTTP GET unsubscribe success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        self.config.UNSUBSCRIBE_DRY_RUN = False
        handler = UnsubscribeHandler(self.config)
        
        unsubscribe_info = {
            'has_unsubscribe': True,
            'method': 'http',
            'url': 'https://example.com/unsubscribe',
            'list_unsubscribe_post': None
        }
        
        result = handler.unsubscribe(unsubscribe_info, 'email123', dry_run=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['method_used'], 'http')
        self.assertEqual(result['action_taken'], 'automated-unsubscribe')
        
        mock_get.assert_called_once()

    def test_dry_run_mode(self):
        """Test that dry-run doesn't actually unsubscribe."""
        unsubscribe_info = {
            'has_unsubscribe': True,
            'method': 'one-click',
            'url': 'https://example.com/unsubscribe',
            'list_unsubscribe_post': 'List-Unsubscribe=One-Click'
        }
        
        # Dry run should succeed without making actual request
        result = self.handler.unsubscribe(unsubscribe_info, 'email123', dry_run=True)
        
        self.assertTrue(result['success'])
        self.assertIn('dry-run', result['action_taken'])
        self.assertIn('DRY RUN', result['message'])

    def test_mailto_requires_manual_action(self):
        """Test that mailto links require manual action."""
        self.config.UNSUBSCRIBE_DRY_RUN = False
        handler = UnsubscribeHandler(self.config)
        
        unsubscribe_info = {
            'has_unsubscribe': True,
            'method': 'mailto',
            'url': 'mailto:unsubscribe@example.com',
            'list_unsubscribe_post': None
        }
        
        result = handler.unsubscribe(unsubscribe_info, 'email123', dry_run=False)
        
        self.assertEqual(result['action_taken'], 'manual-required')
        self.assertIn('Manual action required', result['message'])

    def test_web_requires_manual_action(self):
        """Test that web form links require manual action."""
        self.config.UNSUBSCRIBE_DRY_RUN = False
        handler = UnsubscribeHandler(self.config)
        
        unsubscribe_info = {
            'has_unsubscribe': True,
            'method': 'web',
            'url': 'https://example.com/unsubscribe-form',
            'list_unsubscribe_post': None
        }
        
        result = handler.unsubscribe(unsubscribe_info, 'email123', dry_run=False)
        
        self.assertEqual(result['action_taken'], 'manual-required')
        self.assertIn('Manual action required', result['message'])

    def test_url_validation_blocks_ip_address(self):
        """Test that URLs with IP addresses are blocked."""
        url = 'http://192.168.1.1/unsubscribe'
        self.assertFalse(self.handler._is_safe_url(url))

    def test_url_validation_blocks_suspicious_domains(self):
        """Test that suspicious domains are blocked."""
        suspicious_urls = [
            'http://example.tk/unsubscribe',
            'http://example.ml/unsubscribe',
            'http://bit.ly/abc123'
        ]
        
        for url in suspicious_urls:
            self.assertFalse(self.handler._is_safe_url(url))

    def test_url_validation_allows_safe_urls(self):
        """Test that legitimate URLs are allowed."""
        safe_urls = [
            'https://example.com/unsubscribe',
            'https://newsletter.company.com/opt-out',
            'http://legitimate-site.org/preferences'
        ]
        
        for url in safe_urls:
            self.assertTrue(self.handler._is_safe_url(url))

    def test_url_validation_allows_mailto(self):
        """Test that mailto links are allowed."""
        self.assertTrue(self.handler._is_safe_url('mailto:unsubscribe@example.com'))

    def test_no_unsubscribe_info_found(self):
        """Test behavior when no unsubscribe info is found."""
        result = self.handler.extract_unsubscribe_info('Plain email with no links', {})
        
        self.assertFalse(result['has_unsubscribe'])
        self.assertIsNone(result['method'])
        self.assertIsNone(result['url'])

    def test_unsubscribe_without_info(self):
        """Test unsubscribe attempt without unsubscribe info."""
        unsubscribe_info = {
            'has_unsubscribe': False,
            'method': None,
            'url': None,
            'list_unsubscribe_post': None
        }
        
        result = self.handler.unsubscribe(unsubscribe_info, 'email123')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'No unsubscribe method found')

    @patch('unsubscribe_handler.requests.post')
    def test_unsubscribe_http_error(self, mock_post):
        """Test handling of HTTP error during unsubscribe."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        self.config.UNSUBSCRIBE_DRY_RUN = False
        handler = UnsubscribeHandler(self.config)
        
        unsubscribe_info = {
            'has_unsubscribe': True,
            'method': 'one-click',
            'url': 'https://example.com/unsubscribe',
            'list_unsubscribe_post': 'List-Unsubscribe=One-Click'
        }
        
        result = handler.unsubscribe(unsubscribe_info, 'email123', dry_run=False)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['action_taken'], 'failed')
        self.assertIn('500', result['message'])

    def test_rate_limiting(self):
        """Test that rate limiting delays are applied."""
        import time
        
        self.handler.min_request_interval = 0.1  # Short interval for testing
        
        start_time = time.time()
        self.handler._apply_rate_limit()
        self.handler._apply_rate_limit()
        elapsed = time.time() - start_time
        
        # Should have at least the minimum interval
        self.assertGreaterEqual(elapsed, 0.1)


if __name__ == '__main__':
    unittest.main()
