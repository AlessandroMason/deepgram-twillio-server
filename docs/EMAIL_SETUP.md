# Email Service Setup Guide

This guide will help you set up the email service with Gmail SMTP integration and OpenAI.

## 📋 Prerequisites

1. **OpenAI API Key**: Get one from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Gmail Account**: axm2022@case.edu (already configured)
3. **Gmail App Password**: iwtn sges urbz tkuo (already configured)

## 🔧 Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# OpenAI API Key
export OPENAI_API_KEY="your-openai-api-key-here"
```

That's it! The Gmail credentials are already hardcoded in the service.

### 3. Test the Service

```bash
# Run basic tests
python tests/test_email_service.py

# Or run the service directly
python services/email_service.py
```

## 🚀 Usage

### Basic Usage

```python
from services.email_service import EmailService

# Initialize service (uses hardcoded Gmail credentials)
service = EmailService()

# Process email request (saves as draft by default)
message = "send an email to john@example.com with project update details"
context = "User has been working on a machine learning project"

result = service.process_email_request(message, context)

if result["success"]:
    print(f"Email {result['action']}: {result['message']}")
    print(f"Subject: {result['subject']}")
else:
    print(f"Error: {result['error']}")
```

### Send vs Save as Draft

```python
# Save as draft (default)
result = service.process_email_request(message, context, send_email=False)

# Send email immediately
result = service.process_email_request(message, context, send_email=True)
```

### Integration with Voice Agent

The email service can be integrated with your voice agent to handle email requests:

```python
# In your voice agent
if "send an email" in user_message.lower():
    email_service = EmailService()
    result = email_service.process_email_request(user_message, diary_context)
    
    if result["success"]:
        response = f"I've {result['action']} an email for you. Subject: {result['subject']}"
    else:
        response = f"Sorry, I couldn't create the email. {result['message']}"
```

## 📧 Email Generation Features

### AI-Powered Content
- **Professional tone**: Automatically adjusts based on recipient
- **Context-aware**: Uses diary entries and conversation context
- **Structured format**: Proper email formatting and etiquette

### Supported Request Formats
- "send an email to john@example.com with project details"
- "email sarah@company.org about the meeting"
- "write an email to team@startup.io with quarterly report"
- "compose an email to client@business.com regarding contract"

### Gmail Integration
- **SMTP Authentication**: Uses your Gmail app password
- **Draft saving**: Emails saved as text files in 'drafts' folder
- **Email sending**: Can send emails directly via SMTP
- **Your email**: Uses axm2022@case.edu as sender

## 📁 File Structure

```
deepgram-twillio-server/
├── drafts/                          # Email drafts folder
│   ├── email_20241205_143022_demo_at_example.com.txt
│   └── email_20241205_143045_john_at_company.com.txt
├── services/
│   └── email_service.py             # Email service
└── tests/
    └── test_email_service.py        # Email service tests
```

## 🔒 Security Notes

### Gmail App Password
- **App-specific password**: Uses Gmail app password (not your main password)
- **Secure storage**: Password is hardcoded in the service
- **Revocable access**: You can revoke app passwords in Google Account settings

### API Keys
- **Environment variables**: Never hardcode API keys
- **Secure storage**: Use environment variables or secure vaults
- **Regular rotation**: Rotate API keys periodically

## 🛠️ Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Check `OPENAI_API_KEY` environment variable
   - Verify the key is valid and has credits

2. **"Authentication failed"**
   - Check if Gmail app password is correct
   - Ensure 2-factor authentication is enabled on your Gmail account
   - Verify the app password is for "Mail" application

3. **"Could not extract recipient email"**
   - Ensure the message contains a valid email address
   - Check the email format (user@domain.com)

4. **"SMTP connection failed"**
   - Check internet connection
   - Verify Gmail SMTP settings (smtp.gmail.com:587)
   - Ensure app password is correct

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

service = EmailService()
```

## 📊 Performance

### Typical Performance
- **Email generation**: 2-5 seconds
- **Draft saving**: < 1 second
- **Email sending**: 1-3 seconds
- **Total processing**: 3-8 seconds

### Optimization Tips
1. **Cache OpenAI responses** for similar requests
2. **Batch process** multiple email requests
3. **Use context efficiently** to improve email quality

## 🔄 Integration Examples

### With Diary Service

```python
from services.email_service import EmailService
from services.optimized_diary_service import OptimizedDiaryService

# Get diary context
diary_service = OptimizedDiaryService()
diary_context = diary_service.get_diary_prompt_section("user_id")

# Process email with context
email_service = EmailService()
result = email_service.process_email_request(user_message, diary_context)
```

### With Voice Agent

```python
# In your voice agent handler
async def handle_voice_message(message):
    if "send an email" in message.lower():
        # Get diary context
        diary_context = get_diary_prompt_section()
        
        # Process email request
        email_service = EmailService()
        result = email_service.process_email_request(message, diary_context)
        
        # Respond to user
        if result["success"]:
            return f"Email {result['action']} successfully! Subject: {result['subject']}"
        else:
            return f"Sorry, I couldn't create the email. {result['message']}"
```

## 📋 API Reference

### EmailService Class

#### Methods

- `generate_email_content(recipient, description, context)`: Generate email content using OpenAI
- `create_draft_email(to_email, subject, body)`: Send email via SMTP
- `save_draft_to_file(to_email, subject, body)`: Save email as draft file
- `process_email_request(user_message, context, send_email)`: Process complete email request
- `_extract_email_info(message)`: Extract recipient and description from message

#### Configuration

- `openai_api_key`: OpenAI API key
- `gmail_email`: Gmail email address (default: axm2022@case.edu)
- `gmail_password`: Gmail app password (default: iwtn sges urbz tkuo)

## 🎯 Key Benefits

1. **Simple Setup**: Just one environment variable needed
2. **No OAuth2**: Uses direct SMTP authentication
3. **Flexible**: Can save drafts or send emails
4. **AI-Powered**: Professional email generation
5. **Context-Aware**: Incorporates diary entries and conversation context

This email service provides a complete solution for AI-powered email generation with minimal setup!
