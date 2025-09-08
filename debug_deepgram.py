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

def get_diary_prompt_section():
    """
    Get diary entries from Firebase and format them for the prompt with limits
    """
    try:
        # User ID from the path provided
        user_id = "qkr7puLMnfOvZP5T967rJNyqOsv1"
        
        # Get the optimized service
        service = OptimizedDiaryService()
        
        # Get formatted diary entries with limits to prevent prompt from being too long
        # Limit to 4 days, 100 entries max, 8000 characters max
        diary_section = service.get_diary_prompt_section(
            user_id, 
            days=4, 
            max_entries=100, 
            max_chars=8000
        )
        
        return diary_section
        
    except Exception as e:
        print(f"❌ Error fetching diary entries: {e}")
        # Fallback to static diary content if Firebase fails
        return """12:45 - Reflecting [15 min]
writing a lit of the diary. Still debating if keeping it private or making it public, while i
write there is a difference vibe absed on if its going to get shown or not whatever i
should sleep a little now.
Also since this morning (at the start of the run) my right ball hurts, but i think it might
have to do with me practicing my kicking skills on the tree and having fucked up some
muscle or tendon in that area, not sure but since there is a clear trauma ill not worry
about it.
also looking at what i have done one year ago and send screens to BJ and Jasper about
the night. its cool to stay in touch that way.
13:00 - Sleep [15 min]
good nap, i found a place where i can actually nap on a table, its outside the view form
the door so they dont see me, but still see my laptop and stuff so will not come in.
great place to nap and recharge before the next leetcode streak. (that i start now i
guess)
14:00 - leetcode [1 h]
leetcoding session, finally solved a couple of medium problmes withouth help form
chat in a straightforeward manner, were both matrix problems and the ML practice i
have done this morning really helped, found a window problem and losing focus. ill
nap for 15 min and be back on the grind for a final 45 min then do my resume for
Saab, apply to interships, idk other work that feels lighter"""

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
    
    # 1. Initial Configuration
    initial_config = {
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
                "prompt": """you are a friend and mentor in a phonecall with Alessandro, be masculine. direct. use coaching techniques to guide him but also bring up topics if you want and if you retain necessary. I will provide you with his diary entries shortly.""",
            },
            "greeting": "Hi Ale! Kayros Ai here.",
        },
    }
    
    print_json_section("1. INITIAL CONFIGURATION", initial_config)
    
    # 2. Load Diary Data
    print("\n🔄 Loading diary data...")
    try:
        diary_content = get_diary_prompt_section()
        print("✅ Diary data loaded successfully")
    except Exception as e:
        print(f"❌ Error loading diary data: {e}")
        return
    
    # 3. Create Updated Prompt
    updated_prompt = f"""you are a friend and mentor in a phonecall with Alessandro, be masculine. direct. use coaching techniques to guide him but also bring up topics if you want and if you retain necessary. I attach some of his diary so you know him better

{diary_content}"""
    
    print_section("2. DIARY CONTENT", diary_content)
    
    # 4. Analyze Prompt
    analyze_prompt(updated_prompt)
    
    # 5. UpdatePrompt Message
    update_message = {
        "type": "UpdatePrompt",
        "prompt": updated_prompt
    }
    
    print_json_section("3. UPDATEPROMPT MESSAGE", update_message)
    
    # 6. Final Configuration (what the agent will have)
    final_config = {
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
                "prompt": updated_prompt,
            },
            "greeting": "Hi Ale! Kayros Ai here.",
        },
    }
    
    print_json_section("4. FINAL CONFIGURATION (After UpdatePrompt)", final_config)
    
    # 7. Summary
    print_section("5. SUMMARY", f"""
🎯 VOICE AGENT CONFIGURATION SUMMARY:

📡 Audio Settings:
  • Input: mulaw, 8000Hz
  • Output: mulaw, 8000Hz, no container

🤖 Agent Settings:
  • Speech: Deepgram Aura-2-Odysseus-EN
  • Listening: Deepgram Nova-3
  • Thinking: OpenAI GPT-4.1
  • Greeting: "Hi Ale! Kayros Ai here."

📝 Prompt Configuration:
  • Initial: Basic mentor prompt
  • Updated: Includes diary data from last 4 days
  • Character count: {len(updated_prompt)}
  • Deepgram limit: 25,000 characters
  • Usage: {(len(updated_prompt)/25000)*100:.1f}%

🔄 Flow:
  1. Call starts with basic prompt
  2. Diary data loads in background
  3. UpdatePrompt message sent with full context
  4. Agent now has complete context

✅ Ready for voice calls!
""")

def test_diary_service():
    """Test the diary service separately"""
    print("\n🧪 TESTING DIARY SERVICE")
    print("="*50)
    
    try:
        service = OptimizedDiaryService()
        user_id = "qkr7puLMnfOvZP5T967rJNyqOsv1"
        
        print("🔄 Fetching diary entries...")
        entries = service.get_diary_entries_optimized(user_id, days=4, max_entries=100)
        
        print(f"✅ Fetched {len(entries)} entries")
        
        if entries:
            print(f"�� Date range: {entries[-1]['date']} to {entries[0]['date']}")
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
        formatted = service.format_entries_for_prompt(entries, max_chars=8000)
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
    print("  • Test with actual voice call to see if UpdatePrompt works")

if __name__ == "__main__":
    main()
