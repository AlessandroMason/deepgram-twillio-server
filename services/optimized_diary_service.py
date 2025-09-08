import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import os
import hashlib
import base64
from Crypto.Cipher import AES
from typing import List, Dict, Any, Optional
import json
import time
from functools import lru_cache
from collections import defaultdict
import pytz

class OptimizedDiaryService:
    def __init__(self, service_account_path: str = None, password: str = "123456"):
        """
        Initialize optimized Firebase diary service with caching and decryption
        
        Args:
            service_account_path: Path to Firebase service account JSON file
            password: Password for decrypting descriptions
        """
        if service_account_path is None:
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        if not service_account_path:
            raise ValueError("Firebase service account path not provided. Set FIREBASE_SERVICE_ACCOUNT_PATH environment variable or pass service_account_path parameter.")
        
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.password = password
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.last_fetch_time = 0
        self.ny_tz = pytz.timezone('America/New_York')
        
    def deterministic_decryption(self, encrypted_string: str) -> str:
        """
        Decrypt encrypted string using AES-256-ECB with deterministic key generation
        
        Args:
            encrypted_string: Base64url encoded encrypted string
            
        Returns:
            Decrypted string or error message
        """
        try:
            if not encrypted_string or not isinstance(encrypted_string, str):
                return "[Invalid encrypted content]"
            
            # Create a key from the password using SHA-256
            key = hashlib.sha256(self.password.encode()).digest()
            
            # Convert base64url to standard base64
            standard_base64 = encrypted_string.replace('-', '+').replace('_', '/')
            
            # Add padding if needed
            while len(standard_base64) % 4:
                standard_base64 += '='
            
            # Decode the base64 string
            encrypted_buffer = base64.b64decode(standard_base64)
            
            # Create decipher using AES-256-ECB (no IV needed for ECB mode)
            decipher = AES.new(key, AES.MODE_ECB)
            
            # Decrypt the data
            decrypted = decipher.decrypt(encrypted_buffer)
            
            # Remove padding
            padding_length = decrypted[-1]
            decrypted = decrypted[:-padding_length]
            
            return decrypted.decode('utf8')
            
        except Exception as e:
            print(f"Decryption error: {e}")
            if "bad decrypt" in str(e).lower():
                return "[Invalid decryption - wrong password or corrupted data]"
            return "[Decryption failed]"
    
    def _get_cache_key(self, user_id: str, days: int) -> str:
        """Generate cache key for user and days"""
        return f"{user_id}_{days}"
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid based on TTL"""
        return time.time() - self.last_fetch_time < self.cache_ttl
    
    def _convert_firestore_value(self, value) -> str:
        """
        Convert Firestore value to string, handling different data types
        """
        if value is None:
            return ""
        
        # Handle DatetimeWithNanoseconds
        if hasattr(value, 'timestamp'):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        
        # Handle float timestamps
        if isinstance(value, float):
            try:
                return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
            except:
                return str(value)
        
        # Handle other types
        return str(value)
    
    def _convert_to_ny_time(self, time_str: str, date_str: str) -> str:
        """
        Convert time string to NY timezone
        """
        try:
            # Parse the time string
            time_dt = self._parse_time_string(time_str)
            if not time_dt:
                return time_str
            
            # If time doesn't have date, use the provided date
            if time_dt.date() == datetime(1900, 1, 1).date():
                date_dt = datetime.strptime(date_str, "%Y-%m-%d")
                time_dt = time_dt.replace(year=date_dt.year, month=date_dt.month, day=date_dt.day)
            
            # Convert to NY timezone
            if time_dt.tzinfo is None:
                time_dt = pytz.utc.localize(time_dt)
            
            ny_time = time_dt.astimezone(self.ny_tz)
            return ny_time.strftime("%H:%M:%S")
            
        except Exception as e:
            print(f"Error converting time to NY timezone: {e}")
            return time_str
    
    def get_diary_entries_optimized(self, user_id: str, days: int = 4, max_entries: int = 100) -> List[Dict[str, Any]]:
        """
        Optimized method to fetch diary entries with caching and limits
        
        Args:
            user_id: The user ID in Firebase
            days: Number of days to fetch (default 4)
            max_entries: Maximum number of entries to return (default 100)
            
        Returns:
            List of formatted diary entries (most recent day first, then by time within each day)
        """
        cache_key = self._get_cache_key(user_id, days)
        
        # Check cache first
        if cache_key in self.cache and self._is_cache_valid():
            print(f"🔄 Using cached data for {user_id}")
            cached_entries = self.cache[cache_key]
            return cached_entries[:max_entries]
        
        print(f"🔄 Fetching fresh data for {user_id} (last {days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        entries = []
        
        # Get all date documents in the range
        date_ref = self.db.collection('time').document(user_id).collection('date')
        
        # Use batch processing for better performance
        batch_size = 50
        date_docs = list(date_ref.stream())
        
        print(f"📊 Total date documents found: {len(date_docs)}")
        
        for i in range(0, len(date_docs), batch_size):
            batch_docs = date_docs[i:i + batch_size]
            
            for date_doc in batch_docs:
                date_str = date_doc.id
                
                try:
                    # Parse date
                    if ' ' in date_str and '.' in date_str:
                        doc_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        doc_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    print(f"📅 Processing date: {date_str} -> {doc_date.strftime('%Y-%m-%d')}")
                    
                    # Check if date is within our range
                    if start_date.date() <= doc_date.date() <= end_date.date():
                        print(f"✅ Date {date_str} is within range")
                        
                        # Get all SpecificTimes for this date
                        specific_times_ref = date_ref.document(date_str).collection('SpecificTimes')
                        specific_times = list(specific_times_ref.stream())
                        
                        print(f"📊 Found {len(specific_times)} specific times for {date_str}")
                        
                        for time_doc in specific_times:
                            time_data = time_doc.to_dict()
                            time_id = time_doc.id
                            
                            # Convert Firestore values to strings
                            time_str = self._convert_firestore_value(time_data.get('time', ''))
                            lasttime_str = self._convert_firestore_value(time_data.get('lasttime', ''))
                            action = self._convert_firestore_value(time_data.get('action', ''))
                            description = self._convert_firestore_value(time_data.get('description', ''))
                            
                            print(f"  ⏰ Time: {time_str}")
                            print(f"  ⏰ LastTime: {lasttime_str}")
                            print(f"  🎯 Action: {action}")
                            
                            # Decrypt description if it's encrypted
                            if description and not description.startswith('[') and len(description) > 10:
                                try:
                                    decrypted_desc = self.deterministic_decryption(description)
                                    if not decrypted_desc.startswith('['):  # Only use if decryption succeeded
                                        description = decrypted_desc
                                        print(f"  🔓 Decrypted description: {description[:50]}...")
                                except:
                                    pass  # Keep original if decryption fails
                            
                            # Convert times to NY timezone
                            date_str_formatted = doc_date.strftime("%Y-%m-%d")
                            ny_time = self._convert_to_ny_time(time_str, date_str_formatted)
                            ny_lasttime = self._convert_to_ny_time(lasttime_str, date_str_formatted)
                            
                            # Extract the required fields
                            entry = {
                                'date': date_str_formatted,
                                'time': ny_time,
                                'lasttime': ny_lasttime,
                                'action': action,
                                'description': description,
                                'time_id': time_id
                            }
                            
                            # Calculate duration
                            duration = self._calculate_duration(ny_time, ny_lasttime)
                            entry['duration'] = duration
                            
                            print(f"  ⏱️  Duration: {duration}")
                            
                            entries.append(entry)
                    else:
                        print(f"⏭️  Skipping date outside range: {date_str}")
                        
                except ValueError as e:
                    print(f"❌ Skipping document with invalid date format: {date_str} - {e}")
                    continue
        
        # Group entries by date
        entries_by_date = defaultdict(list)
        for entry in entries:
            entries_by_date[entry['date']].append(entry)
        
        # Sort dates in descending order (most recent first)
        sorted_dates = sorted(entries_by_date.keys(), reverse=True)
        
        # Sort entries within each date by time (most recent first)
        sorted_entries = []
        for date in sorted_dates:
            day_entries = entries_by_date[date]
            # Sort by time within the day (most recent first)
            day_entries.sort(key=lambda x: x['time'], reverse=True)
            sorted_entries.extend(day_entries)
        
        # Apply final limit
        sorted_entries = sorted_entries[:max_entries]
        
        print(f"📊 Total entries collected: {len(sorted_entries)}")
        if sorted_entries:
            print(f"📅 Date range: {sorted_entries[-1]['date']} to {sorted_entries[0]['date']}")
            print(f"📊 Showing most recent {len(sorted_entries)} entries")
            print(f"📅 Days covered: {len(set(entry['date'] for entry in sorted_entries))}")
        
        # Update cache
        self.cache[cache_key] = sorted_entries
        self.last_fetch_time = time.time()
        
        return sorted_entries
    
    def _calculate_duration(self, time_str: str, lasttime_str: str) -> str:
        """
        Calculate duration between time and lasttime with improved parsing
        """
        try:
            if not time_str or not lasttime_str:
                return "Unknown duration"
            
            # Parse time strings using improved parser
            time_dt = self._parse_time_string(time_str)
            lasttime_dt = self._parse_time_string(lasttime_str)
            
            if time_dt and lasttime_dt:
                duration = time_dt - lasttime_dt
                total_seconds = int(duration.total_seconds())
                
                if total_seconds < 0:
                    return "Invalid duration (negative)"
                
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                if hours > 0:
                    return f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    return f"{minutes}m {seconds}s"
                else:
                    return f"{seconds}s"
            else:
                return "Unknown duration"
                
        except Exception as e:
            print(f"Duration calculation error: {e}")
            return "Unknown duration"
    
    def _parse_time_string(self, time_str: str) -> Optional[datetime]:
        """
        Parse time string with multiple format support
        """
        if not time_str:
            return None
        
        # List of time formats to try
        time_formats = [
            "%Y-%m-%d %H:%M:%S.%f",  # 2024-07-26 07:30:00.000
            "%Y-%m-%d %H:%M:%S",     # 2024-07-26 07:30:00
            "%Y-%m-%d %H:%M",        # 2024-07-26 07:30
            "%H:%M:%S.%f",           # 07:30:00.000
            "%H:%M:%S",              # 07:30:00
            "%H:%M"                  # 07:30
        ]
        
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        print(f"Could not parse time string: {time_str}")
        return None
    
    def format_entries_for_prompt(self, entries: List[Dict[str, Any]], max_chars: int = 8000) -> str:
        """
        Format entries for the agent prompt with character limit and day grouping
        
        Args:
            entries: List of diary entries
            max_chars: Maximum characters for the formatted string
            
        Returns:
            Formatted string for the agent prompt
        """
        if not entries:
            return "No diary entries found for the last 4 days."
        
        formatted_entries = []
        current_chars = 0
        current_date = None
        
        for entry in entries:
            # Add day header if date changed
            if current_date != entry['date']:
                if current_date is not None:
                    formatted_entries.append("")  # Empty line between days
                
                current_date = entry['date']
                day_header = f"DATE: {current_date}"
                formatted_entries.append(day_header)
                current_chars += len(day_header) + 1  # +1 for newline
            
            # Format the entry
            formatted_entry = f"TIME: {entry['time']} | DURATION: {entry['duration']}"
            
            if entry['action']:
                formatted_entry += f" | ACTION: {entry['action']}"
            
            if entry['description']:
                # Truncate description if too long
                description = entry['description']
                if len(description) > 200:
                    description = description[:200] + "..."
                formatted_entry += f" | DESCRIPTION: {description}"
            
            # Check if adding this entry would exceed the character limit
            entry_chars = len(formatted_entry) + 2  # +2 for newlines
            if current_chars + entry_chars > max_chars:
                print(f"🛑 Reached character limit ({max_chars}), stopping at {len(formatted_entries)} entries")
                break
            
            formatted_entries.append(formatted_entry)
            current_chars += entry_chars
        
        result = "\n".join(formatted_entries)
        print(f"📊 Formatted {len(formatted_entries)} entries ({current_chars} characters)")
        
        return result
    
    def get_diary_prompt_section(self, user_id: str, days: int = 4, max_entries: int = 100, max_chars: int = 8000) -> str:
        """
        Get formatted diary entries ready for the agent prompt with limits
        
        Args:
            user_id: The user ID in Firebase
            days: Number of days to fetch (default 4)
            max_entries: Maximum number of entries to return (default 100)
            max_chars: Maximum characters for the formatted string (default 8000)
        """
        entries = self.get_diary_entries_optimized(user_id, days, max_entries)
        formatted_entries = self.format_entries_for_prompt(entries, max_chars)
        
        if formatted_entries == "No diary entries found for the last 4 days.":
            return formatted_entries
        
        # Get current time in NY timezone
        current_time_ny = datetime.now(self.ny_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return f"CURRENT TIME (NY): {current_time_ny}\n\nDIARY ENTRIES (last {days} days, most recent first, all times in NY timezone):\n\n{formatted_entries}"
    
    def clear_cache(self):
        """
        Clear the cache to force fresh data on next request
        """
        self.cache.clear()
        self.last_fetch_time = 0
        print("Cache cleared")

def main():
    """
    Example usage of the OptimizedDiaryService
    """
    user_id = "qkr7puLMnfOvZP5T967rJNyqOsv1"
    
    try:
        # Initialize the service
        service = OptimizedDiaryService()
        
        # Get formatted diary entries with limits
        prompt_section = service.get_diary_prompt_section(user_id, days=4, max_entries=100, max_chars=8000)
        
        print("=== DIARY ENTRIES FOR AGENT PROMPT ===")
        print(prompt_section)
        print("=" * 50)
        print(f"Character count: {len(prompt_section)}")
        
        # Test caching
        print("\n=== TESTING CACHE ===")
        start_time = time.time()
        entries = service.get_diary_entries_optimized(user_id, days=4, max_entries=100)
        first_fetch_time = time.time() - start_time
        
        start_time = time.time()
        entries = service.get_diary_entries_optimized(user_id, days=4, max_entries=100)
        second_fetch_time = time.time() - start_time
        
        print(f"First fetch: {first_fetch_time:.2f}s")
        print(f"Second fetch (cached): {second_fetch_time:.2f}s")
        print(f"Speed improvement: {first_fetch_time/second_fetch_time:.1f}x faster")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set the FIREBASE_SERVICE_ACCOUNT_PATH environment variable")

if __name__ == "__main__":
    main()
