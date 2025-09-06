#!/usr/bin/env python3
"""
Debug script to investigate date loading issues
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.optimized_diary_service import OptimizedDiaryService

def debug_date_loading():
    """
    Debug date loading issues
    """
    print("�� Debugging Date Loading Issues")
    print("=" * 50)
    
    # Check if Firebase service account path is set
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if not service_account_path:
        print("❌ FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set")
        print("Please set it to the path of your Firebase service account JSON file")
        print("Example: export FIREBASE_SERVICE_ACCOUNT_PATH='/path/to/service-account.json'")
        return
    
    try:
        # Initialize the service
        service = OptimizedDiaryService(service_account_path, password="123456")
        user_id = "qkr7puLMnfOvZP5T967rJNyqOsv1"
        
        print(f"🔄 Testing with user: {user_id}")
        
        # Get entries for different time periods
        print("\n=== TESTING DIFFERENT TIME PERIODS ===")
        
        for days in [3, 7, 14, 30]:
            print(f"\n--- Testing {days} days ---")
            entries = service.get_diary_entries_optimized(user_id, days=days)
            print(f"📊 Found {len(entries)} entries for {days} days")
            
            if entries:
                # Show date range
                dates = [entry['date'] for entry in entries]
                unique_dates = sorted(set(dates))
                print(f"📅 Date range: {unique_dates[0]} to {unique_dates[-1]}")
                print(f"📅 Unique dates: {len(unique_dates)}")
                
                # Show first few entries
                print("📝 First 3 entries:")
                for i, entry in enumerate(entries[:3]):
                    print(f"  {i+1}. {entry['date']} {entry['time']} - {entry['action']} [{entry['duration']}]")
        
        # Test specific date range
        print("\n=== TESTING SPECIFIC DATE RANGE ===")
        from datetime import datetime, timedelta
        
        # Test last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Testing range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        entries_30 = service.get_diary_entries_optimized(user_id, days=30)
        print(f"📊 Found {len(entries_30)} entries for 30 days")
        
        if entries_30:
            dates = [entry['date'] for entry in entries_30]
            unique_dates = sorted(set(dates))
            print(f"📅 Actual date range: {unique_dates[0]} to {unique_dates[-1]}")
            print(f"📅 All dates: {unique_dates}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_date_loading()
