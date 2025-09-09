#!/usr/bin/env python3
"""
Quick debug script for Deepgram Voice Agent
Fast way to test diary loading and prompt generation
"""

import os
import sys
from ..services.optimized_diary_service import OptimizedDiaryService
from ..agents.constants import (
    INITIAL_PROMPT, 
    GREETING, 
    USER_ID, 
    DIARY_DAYS, 
    DIARY_MAX_ENTRIES, 
    DIARY_MAX_CHARS,
    FALLBACK_DIARY
)

def get_complete_prompt():
    """
    Get the complete prompt with diary data included immediately
    """
    try:
        # Get the optimized service
        service = OptimizedDiaryService()
        
        # Get formatted diary entries with limits
        diary_section = service.get_diary_prompt_section(
            USER_ID, 
            days=DIARY_DAYS, 
            max_entries=DIARY_MAX_ENTRIES, 
            max_chars=DIARY_MAX_CHARS
        )
        
        # Combine initial prompt with diary data
        complete_prompt = f"""{INITIAL_PROMPT}

{diary_section}"""
        
        return complete_prompt
        
    except Exception as e:
        print(f"Error fetching diary entries: {e}")
        # Fallback to static diary content if Firebase fails
        return f"""{INITIAL_PROMPT}

{FALLBACK_DIARY}"""

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
        print("🔄 Testing complete prompt generation...")
        complete_prompt = get_complete_prompt()
        
        # Show results
        print(f"✅ Complete prompt: {len(complete_prompt)} characters")
        print(f"✅ Deepgram limit: 25,000 characters")
        print(f"✅ Usage: {(len(complete_prompt)/25000)*100:.1f}%")
        
        if len(complete_prompt) > 25000:
            print("⚠️  WARNING: Prompt too long!")
        elif len(complete_prompt) > 20000:
            print("⚠️  WARNING: Prompt close to limit")
        else:
            print("✅ Prompt size is good")
        
        # Show sample of complete prompt
        print(f"\n📝 COMPLETE PROMPT SAMPLE (first 3000 chars):")
        print("-" * 40)
        print(complete_prompt[:3000] + "..." if len(complete_prompt) > 3000 else complete_prompt)
        print("-" * 40)
        
        # Show greeting
        print(f"\n👋 GREETING: {GREETING}")
        
        # Show timezone info
        from datetime import datetime
        import pytz
        ny_tz = pytz.timezone('America/New_York')
        current_time_ny = datetime.now(ny_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"\n🕐 CURRENT NY TIME: {current_time_ny}")
        
        print("\n🎉 Quick test complete!")
        print("\n💡 To modify prompts, edit agents/constants.py")
        print("💡 Complete prompt is sent immediately - no updates needed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()
