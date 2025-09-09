# Agents Configuration

This folder contains all the configuration files for the Deepgram Voice Agents.

## Structure

```
agents/
├── __init__.py              # Package initialization and exports
├── constants.py             # Personal agent configuration
├── constants_generic.py     # Generic agent configuration
├── personal_endpoint.xml    # TwiML for personal endpoint
├── generic_endpoint.xml     # TwiML for generic endpoint
└── README.md               # This file
```

## Files

### `constants.py`
Contains all configuration for the **personal agent** (`/twilio` endpoint):
- `INITIAL_PROMPT` - Main prompt with coaching instructions
- `GREETING` - Greeting message for calls
- `USER_ID` - Firebase user ID
- `DIARY_DAYS` - Number of days to fetch from diary
- `DIARY_MAX_ENTRIES` - Maximum diary entries to include
- `DIARY_MAX_CHARS` - Maximum characters for diary section
- `FALLBACK_DIARY` - Fallback diary content if Firebase fails
- `CONTACTS` - Contact list for email functionality
- `EMAIL_SERVICE_CONFIG` - Email service settings
- `EMAIL_TRIGGER_FORMAT` - Format for email triggers
- `UPDATED_INITIAL_PROMPT` - Enhanced prompt with email capabilities

### `constants_generic.py`
Contains all configuration for the **generic agent** (`/generic` endpoint):
- `INITIAL_PROMPT_GENERIC` - Professional prompt for public use
- `GREETING_GENERIC` - Professional greeting
- `DIARY_DAYS_GENERIC` - No diary data (set to 0)
- `DIARY_MAX_ENTRIES_GENERIC` - No diary data (set to 0)
- `DIARY_MAX_CHARS_GENERIC` - No diary data (set to 0)
- `FALLBACK_DIARY_GENERIC` - No fallback diary (empty)

### `personal_endpoint.xml`
TwiML configuration for the personal endpoint:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://deepgram-twillio-server.onrender.com/twilio" />
  </Connect>
</Response>
```

### `generic_endpoint.xml`
TwiML configuration for the generic endpoint:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://deepgram-twillio-server.onrender.com/generic" />
  </Connect>
</Response>
```

## Usage

### Importing Constants
```python
# Import specific constants
from agents.constants import INITIAL_PROMPT, GREETING, USER_ID
from agents.constants_generic import INITIAL_PROMPT_GENERIC, GREETING_GENERIC

# Import all constants from both files
from agents import INITIAL_PROMPT, GREETING, INITIAL_PROMPT_GENERIC, GREETING_GENERIC

# Import everything from a specific agent
from agents.constants import *
from agents.constants_generic import *
```

### Modifying Agent Behavior

1. **Personal Agent**: Edit `constants.py`
   - Modify `INITIAL_PROMPT` to change coaching style
   - Update `GREETING` to change call greeting
   - Adjust `DIARY_DAYS`, `DIARY_MAX_ENTRIES`, `DIARY_MAX_CHARS` for diary limits
   - Add contacts to `CONTACTS` dictionary

2. **Generic Agent**: Edit `constants_generic.py`
   - Modify `INITIAL_PROMPT_GENERIC` to change professional focus
   - Update `GREETING_GENERIC` to change call greeting
   - Add/remove professional information and qualifications

3. **TwiML Endpoints**: Edit the XML files
   - Update WebSocket URLs if server location changes
   - Add additional TwiML elements if needed

## Agent Types

### Personal Agent (`/twilio`)
- **Purpose**: Personal coaching and mentoring for Alessandro
- **Features**: 
  - Access to personal diary data
  - Coaching techniques and motivation
  - Personal context and identities
  - Email trigger functionality (when enabled)
- **Use Case**: Personal calls and self-coaching

### Generic Agent (`/generic`)
- **Purpose**: Professional promotion and information
- **Features**:
  - No personal data access
  - Focus on professional qualifications
  - Public-friendly responses
  - No email functionality
- **Use Case**: Public demos, potential employers, clients

## Configuration Tips

1. **Prompt Length**: Keep prompts under 25,000 characters (Deepgram limit)
2. **Diary Limits**: Adjust `DIARY_MAX_CHARS` to control prompt size
3. **Greeting Length**: Keep greetings short and natural
4. **Contact Management**: Update `CONTACTS` dictionary for email functionality
5. **Testing**: Use `quick_debug.py` to test prompt generation

## Environment Variables

The agents require these environment variables:
- `DEEPGRAM_API_KEY` - Deepgram API key
- `FIREBASE_SERVICE_ACCOUNT_PATH` - Path to Firebase service account JSON
- `GMAIL_PASSWORD` - Gmail app password (for email functionality)
- `OPENAI_API_KEY` - OpenAI API key (for email functionality)
