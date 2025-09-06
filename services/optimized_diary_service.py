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
            standard_base64 = encrypted_string.replace("-", "+").replace("_", "/")
            
            # Add padding if needed
            while len(standard_base64) % 4:
                standard_base64 += "="
            
            # Decode the base64 string
            encrypted_buffer = base64.b64decode(standard_base64)
            
            # Create decipher using AES-256-ECB (no IV needed for ECB mode)
            decipher = AES.new(key, AES.MODE_ECB)
            
            # Decrypt the data
            decrypted = decipher.decrypt(encrypted_buffer)
            
            # Remove padding and convert to string
            decrypted_str = decrypted.decode('utf-8').rstrip('\x00')
            
            return decrypted_str
            
        except Exception as e:
            print(f"Decryption error: {e}")
            if "bad decrypt" in str(e).lower():
                return "[Invalid decryption - wrong password or corrupted data]"
            return "[Decryption failed]"
    
    def _convert_firestore_value(self, value):
        """
        Convert Firestore values to Python strings
        """
        if value is None:
            return ""
        
        # Handle Firestore timestamp objects
        if hasattr(value, 'timestamp'):
            # Convert to datetime string
            dt = datetime.fromtimestamp(value.timestamp())
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        elif hasattr(value, 'strftime'):
            # Already a datetime object
            return value.strftime("%Y-%m-%d %H:%M:%S.%f")
        elif isinstance(value, str):
            return value
        else:
            return str(value)
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cache is still valid
        """
        return time.time() - self.last_fetch_time < self.cache_ttl
    
    def _get_cache_key(self, user_id: str, days: int) -> str:
        """
        Generate cache key for user and days
        """
        return f"{user_id}_{days}_{datetime.now().strftime('%Y%m%d%H')}"
    
    def _parse_time_string(self, time_str: str) -> Optional[datetime]:
        """
        Parse time string with multiple format support
        """
        if not time_str:
            return None
        
        # List of possible time formats to try
        time_formats = [
            "%Y-%m-%d %H:%M:%S.%f",  # 2024-07-26 07:30:00.000
            "%Y-%m-%d %H:%M:%S",     # 2024-07-26 07:30:00
            "%Y-%m-%d %H:%M",        # 2024-07-26 07:30
            "%H:%M:%S.%f",           # 07:30:00.000
            "%H:%M:%S",              # 07:30:00
            "%H:%M",                 # 07:30
        ]
        
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        # If none of the formats work, try to extract just the time part
        if ' ' in time_str:
            time_part = time_str.split(' ')[1]
            for fmt in time_formats[3:]:  # Try time-only formats
                try:
                    return datetime.strptime(time_part, fmt)
                except ValueError:
                    continue
        
        return None
    
    def get_diary_entries_optimized(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Optimized method to fetch diary entries with caching
        
        Args:
            user_id: The user ID in Firebase
            days: Number of days to fetch (default 7)
            
        Returns:
            List of formatted diary entries
        """
        cache_key = self._get_cache_key(user_id, days)
        
        # Check cache first
        if cache_key in self.cache and self._is_cache_valid():
            print(f"🔄 Using cached data for {user_id}")
            return self.cache[cache_key]
        
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
                            lasttime_str = self._convert_firestore_value(time_data.get('lasstime', ''))
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
                            
                            # Extract the required fields
                            entry = {
                                'date': doc_date.strftime("%Y-%m-%d"),
                                'time': time_str,
                                'lasttime': lasttime_str,
                                'action': action,
                                'description': description,
                                'time_id': time_id
                            }
                            
                            # Calculate duration
                            duration = self._calculate_duration(entry['time'], entry['lasttime'])
                            entry['duration'] = duration
                            
                            print(f"  ⏱️  Duration: {duration}")
                            
                            entries.append(entry)
                    else:
                        print(f"⏭️  Skipping date outside range: {date_str}")
                        
                except ValueError as e:
                    print(f"❌ Skipping document with invalid date format: {date_str} - {e}")
                    continue
        
        # Sort entries by date and time
        entries.sort(key=lambda x: (x['date'], x['time']))
        
        print(f"📊 Total entries collected: {len(entries)}")
        
        # Update cache
        self.cache[cache_key] = entries
        self.last_fetch_time = time.time()
        
        return entries
    
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
            
            if not time_dt or not lasttime_dt:
                print(f"❌ Could not parse time strings: '{time_str}' or '{lasttime_str}'")
                return "Unknown duration"
            
            # Calculate difference
            duration = lasttime_dt - time_dt
            
            # Handle negative durations (lasttime before time)
            if duration.total_seconds() < 0:
                print(f"⚠️  Negative duration detected: {time_str} -> {lasttime_str}")
                return "Invalid duration"
            
            # Convert to minutes
            total_minutes = int(duration.total_seconds() / 60)
            
            if total_minutes < 60:
                return f"{total_minutes} min"
            else:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                if minutes == 0:
                    return f"{hours} h"
                else:
                    return f"{hours} h {minutes} min"
                    
        except Exception as e:
            print(f"❌ Error calculating duration: {e}")
            print(f"  Time: '{time_str}'")
            print(f"  LastTime: '{lasttime_str}'")
            return "Unknown duration"
    
    def format_entries_for_prompt(self, entries: List[Dict[str, Any]]) -> str:
        """
        Format diary entries for use in the agent prompt
        """
        if not entries:
            return "No diary entries found for the last 7 days."
        
        formatted_entries = []
        current_date = None
        
        for entry in entries:
            # Add date header if it's a new date
            if entry['date'] != current_date:
                if current_date is not None:
                    formatted_entries.append("")
                
                # Format date nicely
                date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%b %d, %Y")
                formatted_entries.append(f"{formatted_date}")
                current_date = entry['date']
            
            # Format time and duration
            time_str = str(entry['time'])
            if ' ' in time_str:
                time_str = time_str.split(' ')[1][:5]
            else:
                time_str = time_str[:5]
            
            duration_str = entry['duration']
            action = entry['action']
            description = entry['description']
            
            # Create formatted entry
            formatted_entry = f"{time_str} - {action} [{duration_str}]"
            if description:
                formatted_entry += f"\n{description}"
            
            formatted_entries.append(formatted_entry)
        
        return "\n".join(formatted_entries)
    
    def get_diary_prompt_section(self, user_id: str, days: int = 7) -> str:
        """
        Get formatted diary entries ready for the agent prompt with caching
        """
        entries = self.get_diary_entries_optimized(user_id, days)
        formatted_entries = self.format_entries_for_prompt(entries)
        
        if formatted_entries == "No diary entries found for the last 7 days.":
            return formatted_entries
        
        return f"Here are Alessandro's diary entries from the last {days} days:\n\n{formatted_entries}"
    
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
        
        # Get formatted diary entries
        prompt_section = service.get_diary_prompt_section(user_id)
        
        print("=== DIARY ENTRIES FOR AGENT PROMPT ===")
        print(prompt_section)
        print("=" * 50)
        
        # Test caching
        print("\n=== TESTING CACHE ===")
        start_time = time.time()
        entries = service.get_diary_entries_optimized(user_id)
        first_fetch_time = time.time() - start_time
        
        start_time = time.time()
        entries = service.get_diary_entries_optimized(user_id)
        second_fetch_time = time.time() - start_time
        
        print(f"First fetch: {first_fetch_time:.2f}s")
        print(f"Second fetch (cached): {second_fetch_time:.2f}s")
        print(f"Speed improvement: {first_fetch_time/second_fetch_time:.1f}x faster")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set the FIREBASE_SERVICE_ACCOUNT_PATH environment variable")

if __name__ == "__main__":
    main()
