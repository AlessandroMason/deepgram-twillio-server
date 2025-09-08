# Server Endpoints

This server now supports two different endpoints for different use cases:

## 1. Personal Endpoint (`/twilio`)

**URL**: `wss://deepgram-twillio-server.onrender.com/twilio`

**Purpose**: Your personal assistant with access to your diary data and personal information.

**Features**:
- Uses your personal prompt with coaching and mentoring
- Accesses your diary entries from Firebase
- Includes email trigger functionality
- Personalized greeting: "Hi Alessandro! Kayros here."
- Contains your personal context and identities

**TwiML Example**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://deepgram-twillio-server.onrender.com/twilio" />
  </Connect>
</Response>
```

## 2. Generic Endpoint (`/generic`)

**URL**: `wss://deepgram-twillio-server.onrender.com/generic`

**Purpose**: Public-facing assistant that promotes you professionally without personal information.

**Features**:
- Professional AI assistant focused on your qualifications
- No access to personal diary data
- No email trigger functionality
- Generic greeting: "Hello! I'm here to tell you about Alessandro Mason..."
- Highlights your technical skills and why people should hire you

**TwiML Example**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://deepgram-twillio-server.onrender.com/generic" />
  </Connect>
</Response>
```

## Key Differences

| Feature | Personal (`/twilio`) | Generic (`/generic`) |
|---------|---------------------|---------------------|
| Personal Data | ✅ Full access | ❌ None |
| Diary Integration | ✅ Yes | ❌ No |
| Email Triggers | ✅ Yes | ❌ No |
| Professional Focus | ❌ No | ✅ Yes |
| Public Use | ❌ No | ✅ Yes |
| Coaching Style | ✅ Personal | ❌ Professional |

## Usage

- **For your personal calls**: Use the `/twilio` endpoint
- **For sharing with potential employers/clients**: Use the `/generic` endpoint
- **For public demos**: Use the `/generic` endpoint

Both endpoints use the same underlying technology but serve completely different purposes and audiences.
