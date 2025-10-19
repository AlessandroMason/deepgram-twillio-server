#!/usr/bin/env python3
"""
Simple test to make an outbound call to the existing /twilio endpoint
This bypasses the reminder logic and just connects to Kayros like a normal call
"""

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from twilio.rest import Client

def make_test_call():
    """Make a simple outbound call that connects to /twilio endpoint"""
    
    # Get Twilio credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
    target_number = os.getenv("REMINDER_PHONE_NUMBER", "+12162589844")
    
    if not all([account_sid, auth_token, twilio_number]):
        print("❌ Missing Twilio credentials!")
        print("   Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")
        return
    
    print("📞 Simple Outbound Call Test")
    print("=" * 60)
    print(f"   From: {twilio_number}")
    print(f"   To: {target_number}")
    print(f"   Connecting to: /twilio endpoint (normal Kayros)")
    print()
    
    response = input("⚠️  This will make a real phone call. Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Test cancelled")
        return
    
    # Create TwiML that connects directly to /twilio
    server_url = "wss://deepgram-twillio-server.onrender.com/twilio"
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{server_url}" />
    </Connect>
</Response>"""
    
    print()
    print("📞 Making call...")
    print(f"   TwiML connects to: {server_url}")
    print()
    
    try:
        client = Client(account_sid, auth_token)
        
        call = client.calls.create(
            twiml=twiml,
            to=target_number,
            from_=twilio_number
        )
        
        print("✅ Call initiated successfully!")
        print(f"   Call SID: {call.sid}")
        print()
        print("💡 What should happen:")
        print("   1. Your phone rings")
        print("   2. You answer")
        print("   3. Kayros says: 'Hi Alessandro! Kayros here.'")
        print("   4. You can talk to him normally")
        print()
        print("   If you hear Kayros, the issue is with /reminder endpoint")
        print("   If you hear silence, the issue is with outbound calls in general")
        
    except Exception as e:
        print(f"❌ Error making call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    make_test_call()

