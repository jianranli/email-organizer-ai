# Email Organizer AI

Automatically categorize and organize your Gmail emails using AI-powered language models (OpenAI GPT or Google Gemini). The system intelligently sorts emails into categories, applies labels, and archives or trashes messages based on configurable rules.

## Features

- 🤖 **AI-Powered Categorization**: Uses OpenAI GPT or Google Gemini to intelligently categorize emails
- 🔄 **Multiple LLM Providers**: Switch between OpenAI and Google Gemini with a simple configuration flag
- 🏷️ **Smart Label Management**: Automatically creates and applies Gmail labels
- 🗑️ **Selective Organization**: Keep important categories (Notes, Github), trash the rest
- ⚡ **Rate Limit Protection**: Built-in delays, automatic retries with exponential backoff for rate-limited emails
- 📊 **Detailed Logging**: See exactly what's happening with each email
- 🔒 **Safe Operations**: System labels protected, confirmation prompts for destructive actions
- ♻️ **Smart Retry Logic**: Automatically retries rate-limited emails up to 3 times with increasing delays
- 🚫 **Automatic Unsubscribe**: Automatically detect and unsubscribe from marketing emails and newsletters

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/jianranli/email-organizer-ai.git
cd email-organizer-ai

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file or set environment variables:

```bash
# LLM Provider Selection
LLM_PROVIDER=gemini                     # 'openai' or 'gemini' (default: openai)

# Google Gemini Configuration (if using Gemini)
GOOGLE_API_KEY=your_google_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash           # Fast and cost-effective model

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini                # Recommended for better rate limits
OPENAI_MAX_TOKENS=500

# Email Processing Settings
MAX_EMAIL_CONTENT_LENGTH=8000           # Prevent context length errors
CATEGORIES_TO_KEEP=Notes,Github         # Comma-separated list
LABELS_TO_PRESERVE=important,starred    # Labels to never delete
```

**Getting API Keys:**

- **Google Gemini**: Get your free API key at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **OpenAI**: Get your API key at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 3. Setup Gmail Credentials

```bash
# Generate OAuth credentials (first time only)
python generate_credentials.py

# Verify credentials are working
python verify_secrets.py
```

### 4. Run the Organizer

```bash
# Process last 10 emails (default)
python main.py

# Process specific number of emails
python main.py -n 50

# Process with custom configuration
CATEGORIES_TO_KEEP=Notes,Github,Work python main.py -n 20

# Use Google Gemini instead of OpenAI
LLM_PROVIDER=gemini python main.py -n 10
```

## Main Scripts

### `main.py` - Email Organizer

The primary script that processes emails, categorizes them, and organizes your inbox.

**Usage:**
```bash
python main.py [-n NUMBER]
```

**Options:**
- `-n, --num-emails`: Number of recent emails to process (default: 10)

**Example Output:**
```
INFO:__main__:Processing last 10 emails from inbox...

📧 Subject: [Github] Build successful / Category: Github / ✓ Labeled and archived

📧 Subject: Meeting notes from today / Category: Notes / ✓ Labeled and archived

📧 Subject: Newsletter weekly / Category: Primary / ✗ Moved to trash

📧 Subject: Spam offer / Category: Spam / ✗ Moved to trash

=== Categorization Summary ===
✓ Kept (labeled & archived):
  - Github: 3 emails
  - Notes: 2 emails

✗ Trashed (unwanted categories):
  - Primary: 4 emails
  - Spam: 1 email
```

**What it does:**
1. Fetches recent emails from Gmail inbox
2. Uses OpenAI to categorize each email
3. For categories in `CATEGORIES_TO_KEEP`: applies label and archives
4. For all other categories: moves to trash
5. Applies rate limiting between API calls
6. Shows detailed progress with subject lines



## Utility Scripts

### `verify_secrets.py` - Credential Verifier

Verifies that Gmail credentials are properly configured.

```bash
python verify_secrets.py
```

### `generate_credentials.py` - Credential Generator

Interactive OAuth flow to generate Gmail API credentials.

```bash
python generate_credentials.py
```

## Configuration Reference

### LLM Provider Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider: `openai` or `gemini` |

### Google Gemini Settings (if using Gemini)

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | *Required* | Your Google Gemini API key from [AI Studio](https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Model to use. Options: `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-pro` |

### OpenAI Settings (if using OpenAI)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *Required* | Your OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use. Recommend `gpt-4o-mini` or `gpt-3.5-turbo` for better rate limits |
| `OPENAI_MAX_TOKENS` | `500` | Maximum tokens for OpenAI API responses |

### Email Processing Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_EMAIL_CONTENT_LENGTH` | `8000` | Max characters per email (prevents context errors) |
| `CATEGORIES_TO_KEEP` | `Notes,Github` | Comma-separated list of categories to keep |
| `LABELS_TO_PRESERVE` | *(empty)* | Comma-separated labels to protect from deletion |

## How It Works

1. **Fetch Emails**: Retrieves recent emails from Gmail using the Gmail API
2. **AI Categorization**: Sends email content to your chosen LLM provider (OpenAI GPT or Google Gemini) for classification
3. **Smart Organization**:
   - **Keep**: Categories in `CATEGORIES_TO_KEEP` → labeled and archived
   - **Trash**: All other categories → moved to trash
4. **Automatic Retries**: If rate limits are hit, emails are automatically retried up to 3 times with exponential backoff
5. **Logging**: Shows detailed progress with email subjects and actions

## Troubleshooting

### Rate Limit Errors (429)

**Problem**: Too many requests to LLM API

**Automatic Handling**: The script automatically retries rate-limited emails with increasing delays. Most rate limit issues resolve automatically.

**If problems persist**:

1. **Switch to Google Gemini** (generous free tier):
   ```bash
   export LLM_PROVIDER=gemini
   export GOOGLE_API_KEY=your_gemini_api_key
   ```

2. **For OpenAI**: Switch to `gpt-4o-mini` or `gpt-3.5-turbo`:
   ```bash
   export OPENAI_MODEL=gpt-4o-mini
   ```

3. **Process fewer emails at once**:
   ```bash
   python main.py -n 10  # Start with smaller batches
   ```

### Context Length Errors

**Problem**: Email content too long (exceeds model's token limit)

**Solution**: Reduce max content length:
```bash
export MAX_EMAIL_CONTENT_LENGTH=6000  # Lower from 8000
```

### Invalid Label Name Errors

**Problem**: Trying to create system labels (like "Spam", "Trash")

**Solution**: The system now automatically maps these to Gmail system labels (SPAM, TRASH). No action needed.

### Not Seeing Expected Emails in Trash

**Problem**: Emails you expect to be trashed are being kept

**Cause**: They're being categorized into `CATEGORIES_TO_KEEP`

**Solution**: Adjust your categories:
```bash
# Run with fewer categories to keep
CATEGORIES_TO_KEEP=Notes python main.py -n 10
```

## Automatic Unsubscribe Feature

Automatically detect and unsubscribe from marketing emails, newsletters, and promotional messages.

### Configuration

Enable the feature by setting environment variables:

```bash
# Enable auto-unsubscribe
export AUTO_UNSUBSCRIBE_ENABLED=true

# Target specific categories
export UNSUBSCRIBE_CATEGORIES=Promotions,Newsletters,Spam

# Target specific sender patterns
export UNSUBSCRIBE_SENDER_PATTERNS=noreply@,@zillow.com,@marketing.

# Start with dry-run mode (recommended)
export UNSUBSCRIBE_DRY_RUN=true
```

### How It Works

1. **Detection**: Scans emails for unsubscribe links in headers and body
   - Parses `List-Unsubscribe` header (RFC 2369)
   - Parses `List-Unsubscribe-Post` header for one-click unsubscribe (RFC 8058)
   - Searches email body for common unsubscribe link patterns

2. **Filtering**: Only processes emails matching configured categories and sender patterns
   - Category-based filtering (e.g., Promotions, Newsletters)
   - Sender pattern matching (e.g., noreply@, @zillow.com)

3. **Unsubscribe Methods**:
   - **One-click unsubscribe (RFC 8058)**: Automated HTTP POST ✓
   - **HTTP GET links**: Automated click ✓
   - **Web forms**: Logged for manual action ⚠
   - **mailto: links**: Logged for manual action ⚠

### Safety Features

- **Dry-run mode**: Preview what would be unsubscribed without taking action
- **Domain validation**: Prevents clicking on phishing links
- **Rate limiting**: Prevents overwhelming servers with requests
- **SSL verification**: Ensures secure connections
- **Detailed logging**: Track all unsubscribe attempts

### Example Usage

```bash
# Preview unsubscribe actions (dry-run)
AUTO_UNSUBSCRIBE_ENABLED=true UNSUBSCRIBE_DRY_RUN=true python main.py -n 50

# Actually unsubscribe
AUTO_UNSUBSCRIBE_ENABLED=true UNSUBSCRIBE_DRY_RUN=false python main.py -n 50

# Target specific senders
UNSUBSCRIBE_SENDER_PATTERNS=@zillow.com,@redfin.com python main.py -n 20
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_UNSUBSCRIBE_ENABLED` | `false` | Enable automatic unsubscribe feature |
| `UNSUBSCRIBE_CATEGORIES` | `Promotions,Newsletters,Social,Spam` | Categories to target for unsubscribe |
| `UNSUBSCRIBE_SENDER_PATTERNS` | `noreply@,no-reply@,donotreply@` | Sender email patterns to match |
| `UNSUBSCRIBE_DRY_RUN` | `true` | Dry run mode (detect but don't unsubscribe) |
| `UNSUBSCRIBE_TIMEOUT` | `10` | Timeout for HTTP requests in seconds |

### Expected Output

When running with unsubscribe enabled:

```
📧 Subject: "Weekly Newsletter from Zillow"
   Category: [Newsletters]
   ✓ Unsubscribed: Successfully unsubscribed via one-click (status: 200)
   ✗ Action: Moved to trash (unwanted category)

=== UNSUBSCRIBE SUMMARY ===
✓ Successfully unsubscribed: 12 emails
⚠ Failed to unsubscribe: 2 emails
ℹ Manual action needed: 3 emails
```

## Project Structure

```
email-organizer-ai/
├── main.py                          # Main email organizer
├── gmail_client.py                  # Gmail API client
├── ai_organizer.py                  # LLM integration (OpenAI/Gemini)
├── google_gemini_helper.py          # Google Gemini implementation
├── unsubscribe_handler.py           # Automatic unsubscribe handler
├── config.py                        # Configuration management
├── verify_secrets.py                # Credential verifier
├── generate_credentials.py          # Credential generator
├── test_*.py                        # Unit & integration tests
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt             # Development dependencies
├── .env.example                     # Environment variable template
├── README.md                        # This file
└── *.json                           # Credentials (gitignored)
```

## Advanced Usage

### Custom Category Configuration

Keep different categories for different runs:

```bash
# Keep only work-related emails
CATEGORIES_TO_KEEP=Work,Important python main.py -n 50

# Keep everything except spam
CATEGORIES_TO_KEEP=Notes,Github,Primary,Social,Promotions python main.py
```

### Batch Processing with Rate Limiting

Process large email volumes safely:

```bash
# Process 100 emails with longer delays
RATE_LIMIT_DELAY=5 python main.py -n 100
```

### Testing Before Full Run

Verify setup before processing emails:

```bash
# Verify Gmail credentials work
python verify_secrets.py

# Test with a small batch first
python main.py -n 5
```

### Switching Between LLM Providers

Easily switch between OpenAI and Google Gemini:

```bash
# Use Google Gemini (free tier available)
export LLM_PROVIDER=gemini
export GOOGLE_API_KEY=your_gemini_key
python main.py -n 10

# Use OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your_openai_key
python main.py -n 10
```

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.