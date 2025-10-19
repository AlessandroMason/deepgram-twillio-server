#!/usr/bin/env python3
"""
Quick script to check if the /reminder endpoint is accessible
"""

import asyncio
import websockets
import json

async def test_reminder_endpoint():
    """Test if the /reminder endpoint responds"""
    
    # Test URL
    url = "wss://deepgram-twillio-server.onrender.com/reminder?event_name=Test&event_time=2:00%20PM&event_id=test123&advance_minutes=10"
    
    print(f"🔍 Testing reminder endpoint...")
    print(f"   URL: {url}")
    print()
    
    try:
        print("⏳ Attempting to connect...")
        async with websockets.connect(url, timeout=10) as ws:
            print("✅ Connection successful!")
            print("   The /reminder endpoint is working and accessible.")
            print()
            print("   This means:")
            print("   - Server is running")
            print("   - /reminder endpoint exists")
            print("   - Websocket connection works")
            print()
            print("   If you're still getting 'application error' in test calls,")
            print("   the issue might be with:")
            print("   - Twilio credentials")
            print("   - Deepgram API key")
            print("   - Other environment variables")
            
            # Try to receive a message (the server might send something)
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"\n📨 Received message from server: {message[:100]}...")
            except asyncio.TimeoutError:
                print("\n(No immediate response from server, which is normal)")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with status code: {e.status_code}")
        if e.status_code == 404:
            print("   The /reminder endpoint doesn't exist yet.")
            print("   → Make sure you deployed the latest code to Render")
        elif e.status_code == 500:
            print("   The server returned an error.")
            print("   → Check Render logs for the error details")
        else:
            print(f"   Unexpected status code")
    
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        print("   The server might not be responding correctly")
        print("   → Check Render logs for errors")
    
    except asyncio.TimeoutError:
        print("❌ Connection timeout!")
        print("   The server didn't respond within 10 seconds")
        print("   Possible reasons:")
        print("   - Server is down")
        print("   - Server is starting up (try again in a minute)")
        print("   - Network issues")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_reminder_endpoint())

