def authenticate(config=None):
    if config:
        credentials_json = config.GMAIL_CREDENTIALS_JSON
    else:
        credentials_json = os.environ.get('GMAIL_CREDENTIALS_JSON')
    # Rest of the authentication logic...
    
# Assuming the rest of the file content remains the same