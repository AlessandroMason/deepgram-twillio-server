#!/usr/bin/env python3
"""
Test script for the reminder service - allows local testing of outbound calls
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables")

import os
import sys
import json
import time
from services.calendar_service import GoogleCalendarService
from services.reminder_service import ReminderService

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_calendar_service():
    """Test calendar service initialization and event fetching"""
    print_section("1️⃣  Testing Calendar Service")
    
    try:
        # Initialize with 5-minute refresh interval for testing
        calendar_service = GoogleCalendarService(refresh_interval_minutes=5)
        
        # Get status
        status = calendar_service.get_service_status()
        print("\n📊 Calendar Service Status:")
        print(json.dumps(status, indent=2))
        
        # Get events
        print("\n📅 Upcoming Events:")
        events_text = calendar_service.get_events_for_agent()
        print(events_text)
        
        return calendar_service
        
    except Exception as e:
        print(f"❌ Error testing calendar service: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_reminder_service(calendar_service):
    """Test reminder service initialization"""
    print_section("2️⃣  Testing Reminder Service")
    
    try:
        # Initialize reminder service
        reminder_service = ReminderService(
            calendar_service=calendar_service,
            phone_number="+12162589844",  # Your default number
            advance_minutes=10,
            check_interval_seconds=30
        )
        
        # Get status
        status = reminder_service.get_service_status()
        print("\n📊 Reminder Service Status:")
        print(json.dumps(status, indent=2))
        
        return reminder_service
        
    except Exception as e:
        print(f"❌ Error testing reminder service: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_test_call(reminder_service):
    """Send a test reminder call"""
    print_section("3️⃣  Sending Test Call")
    
    print(f"\n📞 Target phone number: {reminder_service.phone_number}")
    print(f"📞 From Twilio number: {reminder_service.twilio_phone_number}")
    print(f"\n💡 This test will:")
    print(f"   1. Call your phone and connect directly to Kayros")
    print(f"   2. Kayros will greet you with the event announcement")
    print(f"   3. You can talk to him normally - he has full context")
    print(f"   4. He knows about all your upcoming events too!")
    
    response = input("\n⚠️  This will make a real phone call. Continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Test call cancelled by user.")
        return False
    
    try:
        print("\n📞 Initiating test reminder call with Kayros AI connection...")
        call_sid = reminder_service.test_reminder_call()
        
        if call_sid:
            print(f"\n✅ Test call initiated successfully!")
            print(f"   Call SID: {call_sid}")
            print(f"   Phone should ring at: {reminder_service.phone_number}")
            print(f"\n💡 What will happen:")
            print(f"   1. Phone rings")
            print(f"   2. Kayros greets you: 'Hey Alessandro, Kayros here. Quick reminder: you have Test Event...'")
            print(f"   3. You can talk to him - he has full context (diary, calendar, all events)")
            print(f"   4. He knows this is a reminder and will be helpful and focused")
            return True
        else:
            print("❌ Failed to initiate test call")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test call: {e}")
        import traceback
        traceback.print_exc()
        return False

def monitor_upcoming_events(reminder_service, duration_seconds=60):
    """Monitor for upcoming events that need reminders"""
    print_section("4️⃣  Monitoring for Upcoming Events")
    
    print(f"\n🔔 Monitoring for events in the next {reminder_service.advance_minutes} minutes...")
    print(f"   Will check every {reminder_service.check_interval} seconds")
    print(f"   Monitoring for {duration_seconds} seconds total")
    print("\n💡 If you have any events starting soon, you'll receive a reminder call!")
    print("   Press Ctrl+C to stop monitoring early\n")
    
    try:
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            elapsed = int(time.time() - start_time)
            remaining = duration_seconds - elapsed
            print(f"⏱️  Monitoring... ({elapsed}s elapsed, {remaining}s remaining)", end='\r')
            time.sleep(1)
        
        print("\n\n✅ Monitoring complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring stopped by user")

def main():
    """Main test function"""
    print("🧪 Reminder Service Local Test Script")
    print("This script allows you to test the reminder calling feature locally")
    print("before deploying to production.")
    
    # Check required environment variables
    print_section("🔍 Checking Environment Variables")
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN", 
        "TWILIO_PHONE_NUMBER",
        "GMAIL_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "PASSWORD" in var or "TOKEN" in var or "SID" in var:
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file or environment")
        return 1
    
    # Test calendar service
    calendar_service = test_calendar_service()
    if not calendar_service:
        print("\n❌ Calendar service test failed")
        return 1
    
    # Test reminder service
    reminder_service = test_reminder_service(calendar_service)
    if not reminder_service:
        print("\n❌ Reminder service test failed")
        calendar_service.stop()
        return 1
    
    # Interactive menu
    while True:
        print_section("📋 Test Menu")
        print("\nWhat would you like to test?")
        print("  1. Send a test reminder call now")
        print("  2. Monitor for upcoming events (60 seconds)")
        print("  3. Check service status")
        print("  4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            send_test_call(reminder_service)
        elif choice == "2":
            monitor_upcoming_events(reminder_service, duration_seconds=60)
        elif choice == "3":
            print("\n📊 Calendar Service Status:")
            print(json.dumps(calendar_service.get_service_status(), indent=2))
            print("\n📊 Reminder Service Status:")
            print(json.dumps(reminder_service.get_service_status(), indent=2))
        elif choice == "4":
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
    
    # Cleanup
    print_section("🧹 Cleanup")
    print("Stopping services...")
    reminder_service.stop()
    calendar_service.stop()
    print("✅ All services stopped")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

