# Email Trigger Setup

This document explains how to set up the email trigger functionality in the Deepgram Twilio server.

## Overview

The server now includes email functionality that automatically sends a test email to `axm2022@case.edu` whenever the agent's response contains the word "email".

## Environment Variables Required

Set the following environment variables:

```bash
export GMAIL_PASSWORD="your_gmail_app_password"
export OPENAI_API_KEY="your_openai_api_key"
```

### Gmail App Password Setup

1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account settings > Security > 2-Step Verification > App passwords
3. Generate an app password for "Mail"
4. Use this 16-character password (without spaces) as `GMAIL_PASSWORD`

## How It Works

1. When the agent receives a message and generates a response
2. The server checks if the agent's response contains the word "email" (case-insensitive)
3. If it does, it automatically sends a test email to `axm2022@case.edu` with:
   - Subject: "Testing"
   - Body: "testing"

## Testing

Run the test script to verify the setup:

```bash
python test_email_trigger.py
```

## Email Service Features

The `EmailService` class provides:

- `send_test_email()`: Sends a simple test email
- `check_and_trigger_email()`: Checks agent response and triggers email if needed
- `generate_email_content()`: Uses OpenAI to generate professional email content
- `create_draft_email()`: Sends emails via Gmail SMTP
- `save_draft_to_file()`: Saves email drafts to files

## Integration

The email service is integrated into the main server (`server.py`) and will:

- Initialize automatically when the server starts
- Monitor all agent responses in real-time
- Trigger emails based on response content
- Handle errors gracefully if email service is not available

## Troubleshooting

- **Email service not available**: Check that `GMAIL_PASSWORD` environment variable is set
- **SMTP authentication failed**: Verify the Gmail app password is correct
- **No emails sent**: Check that agent responses actually contain the word "email"
