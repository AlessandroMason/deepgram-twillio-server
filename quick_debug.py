#!/usr/bin/env python3
"""
Quick debug script for Deepgram Voice Agent
Fast way to test diary loading and prompt generation
"""

import os
import sys
from services.optimized_diary_service import OptimizedDiaryService

def quick_test():
    """Quick test of diary service and prompt generation"""
    print("🚀 QUICK DEEPGRAM DEBUG")
    print("="*40)
    
    # Check environment
    if not os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH"):
        print("❌ FIREBASE_SERVICE_ACCOUNT_PATH not set")
        return
    
    try:
        # Test diary service
        print("🔄 Testing diary service...")
        service = OptimizedDiaryService()
        user_id = "qkr7puLMnfOvZP5T967rJNyqOsv1"
        
        # Get diary data
        diary_section = service.get_diary_prompt_section(user_id, days=4, max_entries=100, max_chars=8000)
        
        # Create full prompt
        full_prompt = f"""you are a friend and mentor in a phonecall with Alessandro, be masculine. direct. use coaching techniques to guide him but also bring up topics if you want and if you retain necessary. I attach some of his diary so you know him better

{diary_section}"""
        
        # Show results
        print(f"✅ Diary loaded: {len(diary_section)} characters")
        print(f"✅ Full prompt: {len(full_prompt)} characters")
        print(f"✅ Deepgram limit: 25,000 characters")
        print(f"✅ Usage: {(len(full_prompt)/25000)*100:.1f}%")
        
        if len(full_prompt) > 25000:
            print("⚠️  WARNING: Prompt too long!")
        elif len(full_prompt) > 20000:
            print("⚠️  WARNING: Prompt close to limit")
        else:
            print("✅ Prompt size is good")
        
        # Show sample of diary data
        print(f"\n📝 DIARY SAMPLE (first 800 chars):")
        print("-" * 40)
        print(diary_section[:800] + "..." if len(diary_section) > 800 else diary_section)
        print("-" * 40)
        
        # Show prompt sample
        print(f"\n📝 PROMPT SAMPLE (first 400 chars):")
        print("-" * 40)
        print(full_prompt[:400] + "..." if len(full_prompt) > 400 else full_prompt)
        print("-" * 40)
        
        # Show timezone info
        from datetime import datetime
        import pytz
        ny_tz = pytz.timezone('America/New_York')
        current_time_ny = datetime.now(ny_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"\n🕐 CURRENT NY TIME: {current_time_ny}")
        
        print("\n🎉 Quick test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()
