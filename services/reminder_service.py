# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables")

import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Set, Optional
from twilio.rest import Client
from urllib.parse import quote

class ReminderService:
    """
    Service that monitors calendar events and makes automated reminder calls
    via Twilio 10 minutes before each event starts.
    """
    
    def __init__(self, 
                 calendar_service,
                 phone_number: str = None,
                 advance_minutes: int = 10,
                 check_interval_seconds: int = 30):
        """
        Initialize the reminder service
        
        Args:
            calendar_service: Instance of GoogleCalendarService to monitor
            phone_number: Phone number to call for reminders (default from env REMINDER_PHONE_NUMBER)
            advance_minutes: How many minutes before event to call (default: 10)
            check_interval_seconds: How often to check for upcoming events (default: 30)
        """
        # Get phone number from env or parameter
        self.phone_number = phone_number or os.getenv("REMINDER_PHONE_NUMBER", "+12162589844")
        self.advance_minutes = advance_minutes
        self.check_interval = check_interval_seconds
        self.calendar_service = calendar_service
        
        # Twilio configuration
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # Validate Twilio credentials
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
            raise ValueError(
                "Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
                "and TWILIO_PHONE_NUMBER environment variables."
            )
        
        # Initialize Twilio client
        self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        
        # Track which events we've already sent reminders for
        self.notified_events: Set[str] = set()
        
        # Thread control
        self.running = False
        self.monitor_thread = None
        
        print(f"📞 Reminder Service initialized")
        print(f"   Phone: {self.phone_number}")
        print(f"   Advance time: {self.advance_minutes} minutes")
        print(f"   Check interval: {self.check_interval} seconds")
        
        # Start monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start the background monitoring thread"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            print("🔔 Started event monitoring for reminders")
    
    def _monitoring_loop(self):
        """Background thread that checks for upcoming events"""
        while self.running:
            try:
                self._check_upcoming_events()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Sleep for 1 minute on error
    
    def _check_upcoming_events(self):
        """Check for events that need reminders"""
        now = datetime.now(timezone.utc)
        reminder_window_start = now + timedelta(minutes=self.advance_minutes)
        reminder_window_end = reminder_window_start + timedelta(seconds=self.check_interval * 2)
        
        # Get upcoming events from calendar service
        events = self.calendar_service.get_upcoming_events(days_ahead=1)
        
        for event in events:
            try:
                event_id = event.get("id", "")
                event_start = datetime.fromisoformat(event["start"].replace('Z', '+00:00'))
                
                # Check if event is in the reminder window and hasn't been notified yet
                if (reminder_window_start <= event_start <= reminder_window_end and 
                    event_id not in self.notified_events):
                    
                    print(f"🔔 Event '{event['summary']}' is {self.advance_minutes} minutes away - sending reminder!")
                    self._send_reminder_call(event)
                    self.notified_events.add(event_id)
                
                # Clean up old notified events (events that have passed)
                if event_start < now and event_id in self.notified_events:
                    self.notified_events.discard(event_id)
                    
            except Exception as e:
                print(f"⚠️  Error processing event for reminder: {e}")
                continue
    
    def _send_reminder_call(self, event: Dict):
        """
        Send a reminder call via Twilio that connects directly to Kayros AI
        Kayros announces the event in his greeting
        
        Args:
            event: Event dictionary with summary, start, end
        """
        try:
            event_name = event.get("summary", "Unnamed event")
            event_start = datetime.fromisoformat(event["start"].replace('Z', '+00:00'))
            event_id = event.get("id", "")
            
            # Format the time nicely
            formatted_time = event_start.strftime("%I:%M %p")
            
            # Connect directly to /twilio endpoint (same as regular calls)
            # This is the simplest approach - just use the working endpoint
            server_url = os.getenv("REMINDER_WEBSOCKET_URL", "wss://deepgram-twillio-server.onrender.com/twilio")
            
            # Simple TwiML - just connect to Kayros AI
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{server_url}" />
    </Connect>
</Response>"""
            
            # Make the call
            call = self.twilio_client.calls.create(
                twiml=twiml,
                to=self.phone_number,
                from_=self.twilio_phone_number
            )
            
            print(f"✅ Reminder call initiated: SID={call.sid}")
            print(f"   Event: {event_name} at {formatted_time}")
            print(f"   Calling: {self.phone_number}")
            print(f"   Kayros will answer with his normal greeting")
            
            return call.sid
            
        except Exception as e:
            print(f"❌ Error sending reminder call: {e}")
            return None
    
    def test_reminder_call(self, test_message: str = None, use_twilio_endpoint=False):
        """
        Send a test reminder call immediately (for testing purposes)
        Connects to Kayros AI like a real reminder
        
        Args:
            test_message: Custom message to speak (optional)
            use_twilio_endpoint: If True, connect to /twilio instead of /reminder for testing
        """
        try:
            if use_twilio_endpoint:
                # TEST MODE: Connect directly to /twilio endpoint (bypasses reminder logic)
                print("🧪 TEST MODE: Connecting to /twilio endpoint directly")
                server_url = "wss://deepgram-twillio-server.onrender.com/twilio"
                
                twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{server_url}" />
    </Connect>
</Response>"""
                
                call = self.twilio_client.calls.create(
                    twiml=twiml,
                    to=self.phone_number,
                    from_=self.twilio_phone_number
                )
                
                print(f"✅ Test call initiated (connecting to /twilio)!")
                print(f"   Call SID: {call.sid}")
                print(f"   This tests if outbound calls work at all")
                print(f"   You should hear: 'Hi Alessandro! Kayros here.'")
                
                return call.sid
            else:
                # NORMAL MODE: Use reminder endpoint
                # Create a fake test event
                test_event = {
                    "id": "test-event-" + str(int(time.time())),
                    "summary": "Test Event",
                    "start": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                    "end": (datetime.now(timezone.utc) + timedelta(minutes=11)).isoformat()
                }
                
                # Use the real reminder call method
                call_sid = self._send_reminder_call(test_event)
                
                if call_sid:
                    print(f"✅ Test reminder call sent successfully!")
                    print(f"   This is a REAL reminder call that connects to Kayros AI")
                    print(f"   You can talk to the AI after the initial announcement")
                
                return call_sid
            
        except Exception as e:
            print(f"❌ Error sending test call: {e}")
            raise
    
    def get_service_status(self) -> Dict:
        """Get the current status of the reminder service"""
        return {
            "running": self.running and self.monitor_thread and self.monitor_thread.is_alive(),
            "phone_number": self.phone_number,
            "advance_minutes": self.advance_minutes,
            "check_interval_seconds": self.check_interval,
            "notified_events_count": len(self.notified_events),
            "twilio_configured": bool(self.twilio_client),
            "twilio_phone_number": self.twilio_phone_number
        }
    
    def stop(self):
        """Stop the reminder service"""
        print("🛑 Stopping Reminder Service...")
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        print("✅ Reminder Service stopped")


def main():
    """Test the reminder service"""
    try:
        print("🧪 Testing Reminder Service")
        print("=" * 60)
        
        # Import calendar service
        from calendar_service import GoogleCalendarService
        
        # Initialize calendar service
        print("\n1️⃣ Initializing Calendar Service...")
        calendar_service = GoogleCalendarService()
        
        # Initialize reminder service
        print("\n2️⃣ Initializing Reminder Service...")
        reminder_service = ReminderService(calendar_service)
        
        # Get status
        print("\n📊 Service Status:")
        import json
        status = reminder_service.get_service_status()
        print(json.dumps(status, indent=2))
        
        # Ask user if they want to send a test call
        print("\n" + "=" * 60)
        response = input("Would you like to send a test reminder call? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            print("\n3️⃣ Sending test reminder call...")
            call_sid = reminder_service.test_reminder_call()
            if call_sid:
                print(f"✅ Test call sent successfully!")
                print(f"   Call SID: {call_sid}")
                print(f"   Check your phone at {reminder_service.phone_number}")
        else:
            print("Skipping test call.")
        
        # Monitor for a bit
        print("\n4️⃣ Monitoring for upcoming events (30 seconds)...")
        time.sleep(30)
        
        # Stop service
        reminder_service.stop()
        calendar_service.stop()
        
    except Exception as e:
        print(f"❌ Error testing reminder service: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

