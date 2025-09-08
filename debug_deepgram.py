#!/usr/bin/env python3
"""
Debug script for Deepgram Voice Agent configuration
Shows exactly what settings and diary data are being applied
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from services.optimized_diary_service import OptimizedDiaryService
from constants import (
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

def print_section(title, content, max_width=80):
    """Print a formatted section"""
    print(f"\n{'='*max_width}")
    print(f" {title}")
    print(f"{'='*max_width}")
    print(content)
    print(f"{'='*max_width}")

def print_json_section(title, data, max_width=80):
    """Print a formatted JSON section"""
    print(f"\n{'='*max_width}")
    print(f" {title}")
    print(f"{'='*max_width}")
    print(json.dumps(data, indent=2))
    print(f"{'='*max_width}")

def analyze_prompt(prompt):
    """Analyze the prompt for debugging"""
    lines = prompt.split('\n')
    word_count = len(prompt.split())
    char_count = len(prompt)
    
    print(f"\n📊 PROMPT ANALYSIS:")
    print(f"  📝 Lines: {len(lines)}")
    print(f"  📝 Words: {word_count}")
    print(f"  📝 Characters: {char_count}")
    print(f"  📝 Deepgram Limit: 25,000 characters")
    print(f"  📝 Usage: {(char_count/25000)*100:.1f}% of limit")
    
    if char_count > 25000:
        print(f"  ⚠️  WARNING: Prompt exceeds Deepgram limit!")
    elif char_count > 20000:
        print(f"  ⚠️  WARNING: Prompt is close to Deepgram limit")
    else:
        print(f"  ✅ Prompt is within safe limits")

def debug_deepgram_config():
    """Debug the Deepgram configuration"""
    
    print("🔍 DEEPGRAM VOICE AGENT DEBUG")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Show Constants
    print_section("1. CONSTANTS FROM constants.py", f"""
INITIAL_PROMPT: {len(INITIAL_PROMPT)} characters
GREETING: {GREETING}
USER_ID: {USER_ID}
DIARY_DAYS: {DIARY_DAYS}
DIARY_MAX_ENTRIES: {DIARY_MAX_ENTRIES}
DIARY_MAX_CHARS: {DIARY_MAX_CHARS}
""")
    
    # 2. Load Complete Prompt
    print("\n🔄 Loading complete prompt with diary data...")
    try:
        complete_prompt = get_complete_prompt()
        print("✅ Complete prompt loaded successfully")
    except Exception as e:
        print(f"❌ Error loading complete prompt: {e}")
        return
    
    # 3. Show Diary Section
    diary_section = complete_prompt.replace(INITIAL_PROMPT, "").strip()
    print_section("2. DIARY SECTION", diary_section)
    
    # 4. Analyze Complete Prompt
    analyze_prompt(complete_prompt)
    
    # 5. Complete Configuration
    config_message = {
        "type": "Settings",
        "audio": {
            "input": {
                "encoding": "mulaw",
                "sample_rate": 8000,
            },
            "output": {
                "encoding": "mulaw",
                "sample_rate": 8000,
                "container": "none",
            },
        },
        "agent": {
            "speak": {
                "provider": {"type": "deepgram", "model": "aura-2-odysseus-en"}
            },
            "listen": {"provider": {"type": "deepgram", "model": "nova-3"}},
            "think": {
                "provider": {"type": "open_ai", "model": "gpt-4.1"},
                "prompt": complete_prompt,
            },
            "greeting": GREETING,
        },
    }
    
    print_json_section("3. COMPLETE CONFIGURATION", config_message)
    
    # 6. Summary
    print_section("4. SUMMARY", f"""
🎯 VOICE AGENT CONFIGURATION SUMMARY:

📡 Audio Settings:
  • Input: mulaw, 8000Hz
  • Output: mulaw, 8000Hz, no container

🤖 Agent Settings:
  • Speech: Deepgram Aura-2-Odysseus-EN
  • Listening: Deepgram Nova-3
  • Thinking: OpenAI GPT-4.1
  • Greeting: "{GREETING}"

📝 Prompt Configuration:
  • Complete prompt: {len(complete_prompt)} characters
  • Deepgram limit: 25,000 characters
  • Usage: {(len(complete_prompt)/25000)*100:.1f}%

🔄 Flow:
  1. Server starts → Pre-loads diary data
  2. Call comes in → Gets complete prompt with diary data
  3. Sends complete configuration to Deepgram immediately
  4. No updates needed - everything is ready from the start

⚡ Performance:
  • Diary data pre-loaded on startup
  • Cache TTL: 10 minutes
  • Instant access to cached data
  • Complete prompt sent immediately
  • No UpdatePrompt complexity

✅ Ready for voice calls!
""")

def test_diary_service():
    """Test the diary service separately"""
    print("\n🧪 TESTING DIARY SERVICE")
    print("="*50)
    
    try:
        service = OptimizedDiaryService()
        
        print("🔄 Fetching diary entries...")
        entries = service.get_diary_entries_optimized(USER_ID, days=DIARY_DAYS, max_entries=DIARY_MAX_ENTRIES)
        
        print(f"✅ Fetched {len(entries)} entries")
        
        if entries:
            print(f"📅 Date range: {entries[-1]['date']} to {entries[0]['date']}")
            print(f"📅 Days covered: {len(set(entry['date'] for entry in entries))}")
            
            # Show first few entries
            print("\n📝 First 3 entries:")
            for i, entry in enumerate(entries[:3], 1):
                print(f"  {i}. {entry['date']} {entry['time']} - {entry['action']} ({entry['duration']})")
                if entry['description']:
                    desc = entry['description'][:100] + "..." if len(entry['description']) > 100 else entry['description']
                    print(f"     {desc}")
        
        # Test formatting
        print("\n🔄 Testing prompt formatting...")
        formatted = service.format_entries_for_prompt(entries, max_chars=DIARY_MAX_CHARS)
        print(f"✅ Formatted prompt: {len(formatted)} characters")
        
    except Exception as e:
        print(f"❌ Error testing diary service: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main debug function"""
    print("🚀 DEEPGRAM VOICE AGENT DEBUG TOOL")
    print("="*60)
    
    # Check environment variables
    print("\n🔍 ENVIRONMENT CHECK:")
    deepgram_key = os.getenv("DEEPGRAM_API_KEY")
    firebase_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    
    if deepgram_key:
        print(f"✅ DEEPGRAM_API_KEY: {deepgram_key[:10]}...")
    else:
        print("❌ DEEPGRAM_API_KEY: Not set")
    
    if firebase_path:
        print(f"✅ FIREBASE_SERVICE_ACCOUNT_PATH: {firebase_path}")
    else:
        print("❌ FIREBASE_SERVICE_ACCOUNT_PATH: Not set")
    
    # Test diary service first
    test_diary_service()
    
    # Debug Deepgram configuration
    debug_deepgram_config()
    
    print("\n🎉 DEBUG COMPLETE!")
    print("\n💡 TIPS:")
    print("  • Check the prompt length - should be under 25,000 characters")
    print("  • Verify diary data is loading correctly")
    print("  • Make sure environment variables are set")
    print("  • Test with actual voice call")
    print("  • Modify prompts in constants.py")

if __name__ == "__main__":
    main()
