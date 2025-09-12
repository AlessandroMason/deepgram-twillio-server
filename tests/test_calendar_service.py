#!/usr/bin/env python3
"""
Test script for Google Calendar Service with OAuth2
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables")

from services.calendar_service import GoogleCalendarService

def test_calendar_service():
    """Test the Google Calendar service functionality"""
    print("🧪 Testing Google Calendar Service with OAuth2")
    print("=" * 60)
    
    # Check environment variables
    gmail_email = os.getenv("GMAIL_PASSWORD")
    print(f"Gmail credentials: {'✅ Set' if gmail_email else '❌ Not set'}")
    
    try:
        # Initialize service
        print("\n📅 Initializing Calendar Service...")
        calendar_service = GoogleCalendarService()
        
        # Get service status
        print("\n📊 Service Status:")
        status = calendar_service.get_service_status()
        print(json.dumps(status, indent=2))
        
        if not status["initialized"] and not os.path.exists("credentials.json"):
            print("\n✅ Service initialized in fallback mode (expected without credentials.json)")
            print("📋 Please follow the setup guide in docs/GOOGLE_CALENDAR_OAUTH_SETUP.md")
            return False
        
        # Test getting upcoming events
        print("\n📅 Testing Real Calendar Events:")
        events_text = calendar_service.get_events_for_agent()
        print(events_text)
        
        # Test scheduler status
        print("\n⏰ Testing Scheduler:")
        print("Waiting 3 seconds to see scheduler in action...")
        time.sleep(3)
        
        final_status = calendar_service.get_service_status()
        print(f"Scheduler running: {final_status['scheduler_running']}")
        
        # Stop service
        print("\n🛑 Stopping service...")
        calendar_service.stop()
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing calendar service: {e}")
        return False

def test_setup_status():
    """Test the setup status"""
    print("\n🔧 Testing Setup Status")
    print("=" * 30)
    
    has_credentials = os.path.exists("credentials.json")
    has_token = os.path.exists("token.json")
    
    print(f"Credentials file: {'✅ Found' if has_credentials else '❌ Missing'}")
    print(f"Token file: {'✅ Found' if has_token else '❌ Missing'}")
    
    if has_credentials and has_token:
        print("🎉 Setup appears complete!")
        return True
    elif has_credentials:
        print("🔐 Credentials found, need to complete OAuth2 authentication")
        return False
    else:
        print("📋 Need to download credentials.json from Google Cloud Console")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Google Calendar Service Tests")
    print("=" * 60)
    
    # Test 1: Setup status
    setup_ok = test_setup_status()
    
    # Test 2: Service functionality
    service_ok = test_calendar_service()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"Setup Status: {"⚠️  FALLBACK MODE" if not setup_ok else "✅ COMPLETE"}")
    print(f"Service Test: {"✅ PASSED (fallback mode)" if not setup_ok and service_ok else "✅ PASSED" if service_ok else "❌ FAILED"}")
    
    if setup_ok and service_ok:
        print("\n🎉 All tests passed! Calendar service is ready.")
        return 0
    elif not setup_ok:
        print("\n📋 Setup incomplete. Please follow the setup guide:")
        print("   docs/GOOGLE_CALENDAR_OAUTH_SETUP.md")
        return 1
    else:
        print("\n💥 Service test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
