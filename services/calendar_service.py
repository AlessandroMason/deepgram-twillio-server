# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables")

import os
import json
import threading
import time
import imaplib
import email
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import pytz

# Google Calendar API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

class GoogleCalendarService:
    """
    Google Calendar service that fetches real calendar events using OAuth2 refresh tokens.
    Falls back to Gmail IMAP for authentication testing.
    """
    
    def __init__(self, gmail_email: str = "axm2022@case.edu", gmail_password: str = None, refresh_interval_minutes: int = None):
        """
        Initialize Google Calendar service with OAuth2 refresh token
        
        Args:
            gmail_email: Gmail email address
            gmail_password: Gmail app password (if None, will use GMAIL_PASSWORD env var)
            refresh_interval_minutes: How often to refresh calendar (default: None for midnight-only refresh,
                                     or specify minutes like 5, 10, 15 for periodic refresh)
        """
        if gmail_password is None:
            gmail_password = os.getenv("GMAIL_PASSWORD")
        
        if not gmail_password:
            raise ValueError("Gmail password not provided. Set GMAIL_PASSWORD environment variable or pass gmail_password parameter.")
        
        self.gmail_email = gmail_email
        self.gmail_password = gmail_password
        self.cached_events = []
        self.last_refresh = None
        self.refresh_thread = None
        self.running = False
        self.refresh_interval_minutes = refresh_interval_minutes or int(os.getenv("CALENDAR_REFRESH_MINUTES", "0"))
        
        # OAuth2 setup
        # Use /tmp for files on Render (writable), fallback to local paths
        # Render sets RENDER_SERVICE_ID, so check for that
        is_render = os.getenv("RENDER_SERVICE_ID") is not None or os.getenv("RENDER") is not None
        default_creds_path = "/tmp/credentials.json" if is_render else "credentials.json"
        default_token_path = "/tmp/token.json" if is_render else "token.json"
        
        self.credentials_file = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE", default_creds_path)
        self.token_file = os.getenv("GOOGLE_TOKEN_FILE", default_token_path)
        self.service = None
        
        # Initialize the service
        self._initialize_service()
        
        # Start the midnight refresh scheduler
        self._start_midnight_scheduler()
    
    def _initialize_service(self):
        """Initialize Google Calendar API service with OAuth2 refresh token"""
        try:
            print("📅 Initializing Google Calendar service with OAuth2 refresh token...")
            
            # Try to initialize Google Calendar API
            self.service = self._build_calendar_from_token()
            
            if self.service:
                print("✅ Google Calendar API service initialized with refresh token")
            else:
                print("⚠️  Google Calendar API not available, using Gmail IMAP fallback")
                self._test_gmail_connection()
                
        except Exception as e:
            print(f"❌ Error initializing calendar service: {e}")
            print("📋 Using Gmail IMAP fallback for authentication testing")
            self._test_gmail_connection()
    
    def _build_calendar_from_token(self):
        """Build Google Calendar service from refresh token"""
        # Check if token is in environment variable (for Render deployment)
        token_json_env = os.getenv("GOOGLE_TOKEN_JSON")
        
        if token_json_env:
            print("📋 Using token from GOOGLE_TOKEN_JSON environment variable")
            try:
                data = json.loads(token_json_env)
                # Write to temp file so it can be updated when refreshed
                with open(self.token_file, 'w') as f:
                    json.dump(data, f)
                print(f"✅ Token written to {self.token_file}")
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing GOOGLE_TOKEN_JSON: {e}")
                return None
            except Exception as e:
                print(f"❌ Error writing token file: {e}")
                return None
        elif not os.path.exists(self.token_file):
            print(f"❌ Token file not found: {self.token_file}")
            print("📋 Please run setup_oauth2_token.py to generate refresh token")
            print("📋 Or set GOOGLE_TOKEN_JSON environment variable with token contents")
            return None
        
        try:
            # Load credentials from token file
            with open(self.token_file) as f:
                data = json.load(f)
            
            creds = Credentials.from_authorized_user_info(data, SCOPES)
            
            # Check if credentials are valid, refresh if needed
            if not creds.valid:
                if creds.refresh_token:
                    print("🔄 Refreshing access token...")
                    creds.refresh(Request())  # Auto-mints a new access token
                    
                    # Persist updated access token
                    with open(self.token_file, "w") as f:
                        f.write(creds.to_json())
                    print("✅ Access token refreshed and saved")
                else:
                    print("❌ No refresh token present")
                    print("📋 Please re-run setup_oauth2_token.py with access_type=offline&prompt=consent")
                    return None
            
            # Build the calendar service
            service = build("calendar", "v3", credentials=creds)
            print("✅ Google Calendar service built successfully")
            return service
            
        except Exception as e:
            print(f"❌ Error building calendar service: {e}")
            return None
    
    def _test_gmail_connection(self):
        """Test Gmail IMAP connection as fallback"""
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.gmail_email, self.gmail_password)
            mail.select('inbox')
            mail.close()
            mail.logout()
            print("✅ Gmail IMAP connection successful (fallback)")
            return True
        except Exception as e:
            print(f"⚠️  Gmail IMAP connection failed: {e}")
            return False
    
    def _start_midnight_scheduler(self):
        """Start the refresh scheduler (either periodic or midnight-only)"""
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            self.running = True
            if self.refresh_interval_minutes > 0:
                self.refresh_thread = threading.Thread(target=self._periodic_refresh_loop, daemon=True)
                self.refresh_thread.start()
                print(f"🔄 Started periodic refresh scheduler (every {self.refresh_interval_minutes} minutes)")
            else:
                self.refresh_thread = threading.Thread(target=self._midnight_refresh_loop, daemon=True)
                self.refresh_thread.start()
                print("🕛 Started midnight refresh scheduler")
    
    def _midnight_refresh_loop(self):
        """Background thread that refreshes calendar events at midnight"""
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                # Calculate next midnight
                next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                sleep_seconds = (next_midnight - now).total_seconds()
                
                print(f"⏰ Next calendar refresh scheduled for: {next_midnight}")
                time.sleep(sleep_seconds)
                
                if self.running:
                    print("🔄 Refreshing calendar events at midnight...")
                    self.refresh_events()
                    
            except Exception as e:
                print(f"❌ Error in midnight refresh loop: {e}")
                time.sleep(3600)  # Sleep for 1 hour on error
    
    def _periodic_refresh_loop(self):
        """Background thread that refreshes calendar events periodically"""
        # Do an initial refresh immediately
        self.refresh_events()
        
        while self.running:
            try:
                sleep_seconds = self.refresh_interval_minutes * 60
                print(f"⏰ Next calendar refresh in {self.refresh_interval_minutes} minutes")
                time.sleep(sleep_seconds)
                
                if self.running:
                    print(f"🔄 Refreshing calendar events (periodic: {self.refresh_interval_minutes}min interval)...")
                    self.refresh_events()
                    
            except Exception as e:
                print(f"❌ Error in periodic refresh loop: {e}")
                time.sleep(300)  # Sleep for 5 minutes on error
    
    def refresh_events(self):
        """Refresh cached calendar events from Google Calendar API"""
        if not self.service:
            print("❌ Google Calendar service not initialized. Using mock events.")
            self._use_mock_events()
            return
            
        try:
            print("🔄 Refreshing calendar events from Google Calendar API...")
            now = datetime.now(timezone.utc).isoformat()  # UTC timezone-aware
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            
            # Process and format events
            formatted_events = []
            for event in events:
                try:
                    # Get event details
                    summary = event.get("summary", "No Title")
                    start = event.get("start", {})
                    end = event.get("end", {})
                    
                    # Handle different date formats
                    start_time_str = start.get("dateTime", start.get("date"))
                    end_time_str = end.get("dateTime", end.get("date"))
                    
                    if not start_time_str or not end_time_str:
                        continue
                    
                    # Parse dates
                    if "T" in start_time_str:  # DateTime format
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    else:  # Date format (all-day events)
                        start_time = datetime.fromisoformat(start_time_str + "T00:00:00+00:00")
                        end_time = datetime.fromisoformat(end_time_str + "T23:59:59+00:00")
                    
                    formatted_events.append({
                        "id": event.get("id", ""),
                        "summary": summary,
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                    })
                    
                except Exception as e:
                    print(f"⚠️  Error processing event: {e}")
                    continue
            
            self.cached_events = formatted_events
            self.last_refresh = datetime.now()
            print(f"✅ Refreshed {len(self.cached_events)} real calendar events from Google Calendar")
            
        except HttpError as error:
            print(f"❌ Error refreshing calendar events: {error}")
            self._use_mock_events()
        except Exception as e:
            print(f"❌ An unexpected error occurred during refresh: {e}")
            self._use_mock_events()
    
    def _use_mock_events(self):
        """Fallback to mock events when real calendar is not available"""
        print("📋 Using mock calendar events as fallback")
        mock_events = self._get_mock_events()
        self.cached_events = mock_events
        self.last_refresh = datetime.now()
        print(f"✅ Refreshed {len(self.cached_events)} mock calendar events")
    
    def _get_mock_events(self):
        """Get mock calendar events for testing"""
        now = datetime.now(timezone.utc)
        mock_events = [
            {
                "id": "1",
                "summary": "Team Meeting",
                "start": (now + timedelta(hours=2)).isoformat(),
                "end": (now + timedelta(hours=3)).isoformat(),
            },
            {
                "id": "2", 
                "summary": "Project Deadline",
                "start": (now + timedelta(days=1)).isoformat(),
                "end": (now + timedelta(days=1, hours=1)).isoformat(),
            },
            {
                "id": "3",
                "summary": "Doctor Appointment",
                "start": (now + timedelta(days=2, hours=10)).isoformat(),
                "end": (now + timedelta(days=2, hours=11)).isoformat(),
            }
        ]
        return mock_events
    
    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming calendar events
        
        Args:
            days_ahead: Number of days to look ahead (default: 7)
            
        Returns:
            List of upcoming events
        """
        if not self.cached_events:
            self.refresh_events()
        
        now = datetime.now(timezone.utc)
        cutoff_date = now + timedelta(days=days_ahead)
        
        upcoming_events = []
        for event in self.cached_events:
            try:
                event_start = datetime.fromisoformat(event["start"].replace('Z', '+00:00'))
                if now <= event_start <= cutoff_date:
                    upcoming_events.append(event)
            except Exception as e:
                print(f"⚠️  Error parsing event date: {e}")
                continue
        
        # Sort by start time
        upcoming_events.sort(key=lambda x: x["start"])
        return upcoming_events
    
    def get_events_for_agent(self) -> str:
        """
        Get formatted calendar events for the AI agent - simplified format
        
        Returns:
            Formatted string with only: event name, start time, duration
        """
        events = self.get_upcoming_events()
        
        if not events:
            return "No upcoming calendar events."
        
        formatted_events = []
        for event in events:
            try:
                start_time = datetime.fromisoformat(event["start"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event["end"].replace('Z', '+00:00'))
                duration = end_time - start_time
                
                # Format start time as simple time
                formatted_time = start_time.strftime("%I:%M %p")
                
                # Calculate duration in hours and minutes
                total_minutes = int(duration.total_seconds() / 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                if hours > 0 and minutes > 0:
                    duration_str = f"{hours}h {minutes}m"
                elif hours > 0:
                    duration_str = f"{hours}h"
                else:
                    duration_str = f"{minutes}m"
                
                # Simple format: Name - Time (Duration)
                event_info = f"{event['summary']} - {formatted_time} ({duration_str})"
                formatted_events.append(event_info)
            except Exception as e:
                print(f"⚠️  Error formatting event: {e}")
                continue
        
        return "Calendar: " + ", ".join(formatted_events)
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of the calendar service
        
        Returns:
            Dictionary with service status information
        """
        refresh_mode = "periodic" if self.refresh_interval_minutes > 0 else "midnight-only"
        return {
            "initialized": self.service is not None,
            "cached_events_count": len(self.cached_events),
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "scheduler_running": self.running and self.refresh_thread and self.refresh_thread.is_alive(),
            "refresh_mode": refresh_mode,
            "refresh_interval_minutes": self.refresh_interval_minutes if self.refresh_interval_minutes > 0 else None,
            "gmail_email": self.gmail_email,
            "authentication_method": "Google Calendar API (OAuth2 Refresh Token)" if self.service else "Gmail IMAP (fallback)",
            "credentials_file": self.credentials_file,
            "token_file": self.token_file
        }
    
    def stop(self):
        """Stop the calendar service and cleanup resources"""
        print("🛑 Stopping Google Calendar service...")
        self.running = False
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=5)
        print("✅ Google Calendar service stopped")

def main():
    """Test the Google Calendar service"""
    try:
        print("🧪 Testing Google Calendar Service with OAuth2 Refresh Token")
        print("=" * 60)
        
        # Initialize service
        calendar_service = GoogleCalendarService()
        
        # Get service status
        print("\n📊 Service Status:")
        status = calendar_service.get_service_status()
        print(json.dumps(status, indent=2))
        
        # Get upcoming events
        print("\n📅 Testing Calendar Events:")
        events_text = calendar_service.get_events_for_agent()
        print(events_text)
        
        # Wait a bit to see the scheduler in action
        print("\n⏰ Waiting 3 seconds to see scheduler status...")
        time.sleep(3)
        
        # Final status
        final_status = calendar_service.get_service_status()
        print(f"\nFinal Status: {json.dumps(final_status, indent=2)}")
        
        # Stop service
        calendar_service.stop()
        
    except Exception as e:
        print(f"❌ Error testing calendar service: {e}")

if __name__ == "__main__":
    main()
