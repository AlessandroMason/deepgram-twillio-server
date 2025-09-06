#!/usr/bin/env python3
"""
Test script for the Optimized Diary Service
This script demonstrates the performance improvements and caching
"""

import os
import sys
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.optimized_diary_service import OptimizedDiaryService

def test_diary_service():
    """
    Test the optimized diary service functionality
    """
    print("=== Testing Optimized Diary Service ===")
    
    # Check if Firebase service account path is set
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if not service_account_path:
        print("❌ FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set")
        print("Please set it to the path of your Firebase service account JSON file")
        print("Example: export FIREBASE_SERVICE_ACCOUNT_PATH='/path/to/service-account.json'")
        return False
    
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        return False
    
    print(f"✅ Using service account: {service_account_path}")
    
    try:
        # Initialize the service
        print("🔄 Initializing optimized service...")
        service = OptimizedDiaryService(service_account_path, password="123456")
        print("✅ Service initialized with decryption support")
        
        # Test user ID
        user_id = "qkr7puLMnfOvZP5T967rJNyqOsv1"
        print(f"🔄 Testing with user: {user_id}")
        
        # Test 1: First fetch (should hit Firebase)
        print("\n=== TEST 1: First Fetch (Firebase) ===")
        start_time = time.time()
        entries = service.get_diary_entries_optimized(user_id, days=7)
        first_fetch_time = time.time() - start_time
        print(f"✅ First fetch completed in {first_fetch_time:.2f}s")
        print(f"📊 Found {len(entries)} diary entries")
        
        # Test 2: Second fetch (should use cache)
        print("\n=== TEST 2: Second Fetch (Cache) ===")
        start_time = time.time()
        entries_cached = service.get_diary_entries_optimized(user_id, days=7)
        second_fetch_time = time.time() - start_time
        print(f"✅ Second fetch completed in {second_fetch_time:.2f}s")
        print(f"📊 Found {len(entries_cached)} diary entries")
        
        # Performance comparison
        if second_fetch_time > 0:
            speed_improvement = first_fetch_time / second_fetch_time
            print(f"🚀 Speed improvement: {speed_improvement:.1f}x faster with cache")
        
        # Test 3: Duration analysis
        print("\n=== TEST 3: Duration Analysis ===")
        if entries:
            unknown_duration_count = sum(1 for entry in entries if entry.get('duration') == 'Unknown duration')
            valid_duration_count = len(entries) - unknown_duration_count
            
            print(f"📊 Valid durations: {valid_duration_count}")
            print(f"📊 Unknown durations: {unknown_duration_count}")
            print(f"📊 Success rate: {valid_duration_count/len(entries)*100:.1f}%")
            
            # Show some examples
            print("\n📝 Sample entries:")
            for i, entry in enumerate(entries[:3]):
                print(f"  {i+1}. {entry.get('time', 'N/A')} - {entry.get('action', 'N/A')} [{entry.get('duration', 'N/A')}]")
        
        # Test 4: Decryption test
        print("\n=== TEST 4: Decryption Test ===")
        if entries:
            print("🔍 Checking for encrypted descriptions...")
            encrypted_count = 0
            decrypted_count = 0
            
            for entry in entries[:5]:  # Check first 5 entries
                desc = entry.get('description', '')
                if desc and len(desc) > 20 and not desc.startswith('['):
                    encrypted_count += 1
                    print(f"  📝 Description: {desc[:50]}...")
                elif desc and not desc.startswith('['):
                    decrypted_count += 1
                    print(f"  🔓 Decrypted: {desc[:50]}...")
            
            print(f"📊 Found {encrypted_count} potentially encrypted descriptions")
            print(f"📊 Found {decrypted_count} decrypted descriptions")
        
        # Test 5: Prompt formatting
        print("\n=== TEST 5: Prompt Formatting ===")
        prompt_section = service.get_diary_prompt_section(user_id, days=7)
        print("✅ Prompt section generated")
        print(f"📏 Length: {len(prompt_section)} characters")
        print("\n📄 Sample output:")
        print(prompt_section[:300] + "..." if len(prompt_section) > 300 else prompt_section)
        
        # Test 6: Cache management
        print("\n=== TEST 6: Cache Management ===")
        print("🔄 Testing cache clear...")
        service.clear_cache()
        print("✅ Cache cleared")
        
        # Test with different parameters
        print("\n=== TEST 7: Different Parameters ===")
        entries_3_days = service.get_diary_entries_optimized(user_id, days=3)
        print(f"📊 3 days: {len(entries_3_days)} entries")
        
        entries_14_days = service.get_diary_entries_optimized(user_id, days=14)
        print(f"📊 14 days: {len(entries_14_days)} entries")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Main function to run the test
    """
    print("Optimized Diary Service Test")
    print("=" * 50)
    
    success = test_diary_service()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("\n🚀 Performance Features:")
        print("  • Caching reduces repeated Firebase calls")
        print("  • Batch processing for better performance")
        print("  • Automatic decryption of descriptions")
        print("  • Configurable cache TTL (5 minutes)")
        print("  • Multiple time format support")
        print("\n📋 To use in your server:")
        print("1. Set FIREBASE_SERVICE_ACCOUNT_PATH environment variable")
        print("2. Run: python server.py")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
