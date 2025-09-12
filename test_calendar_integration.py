#!/usr/bin/env python3
"""
Quick test script for Google Calendar integration
Run this anytime to verify everything is working
"""

import sys
import os
sys.path.append('.')
from dotenv import load_dotenv

def test_environment():
    """Test environment variables"""
    print('🔧 Testing Environment Variables')
    print('=' * 40)
    
    load_dotenv()
    required_vars = [
        'GMAIL_PASSWORD',
        'GOOGLE_CALENDAR_CREDENTIALS_FILE', 
        'GOOGLE_TOKEN_FILE',
        'OPENAI_API_KEY',
        'FIREBASE_SERVICE_ACCOUNT_PATH'
    ]
    
    all_good = True
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "❌ Missing"
        print(f'  {var}: {status}')
        if not value:
            all_good = False
    
    return all_good

def test_calendar_service():
    """Test calendar service"""
    print('\n📅 Testing Calendar Service')
    print('=' * 40)
    
    try:
        from services.calendar_service import GoogleCalendarService
        import json
        
        calendar_service = GoogleCalendarService()
        status = calendar_service.get_service_status()
        
        print(f'  Initialized: {"✅ Yes" if status["initialized"] else "❌ No"}')
        print(f'  Auth Method: {status["authentication_method"]}')
        print(f'  Cached Events: {status["cached_events_count"]}')
        print(f'  Scheduler Running: {"✅ Yes" if status["scheduler_running"] else "❌ No"}')
        
        # Test getting events
        events_text = calendar_service.get_events_for_agent()
        if events_text and events_text != "No upcoming calendar events.":
            print(f'  Events: ✅ {len(events_text)} characters')
            print(f'  Sample: {events_text[:100]}...')
        else:
            print('  Events: ⚠️  No events found')
        
        calendar_service.stop()
        return status["initialized"]
        
    except Exception as e:
        print(f'  ❌ Error: {e}')
        return False

def test_ai_integration():
    """Test AI agent integration"""
    print('\n🤖 Testing AI Agent Integration')
    print('=' * 40)
    
    try:
        from server import get_calendar_service, get_complete_prompt
        
        calendar_svc = get_calendar_service()
        if not calendar_svc:
            print('  ❌ Calendar service not available')
            return False
        
        # Test prompt integration
        prompt = get_complete_prompt(use_personal=True)
        if 'Calendar:' in prompt:
            print('  ✅ Calendar events included in AI prompt')
            
            # Extract calendar line
            lines = prompt.split('\n')
            for line in lines:
                if 'Calendar:' in line:
                    print(f'  📅 Calendar data: {line[:100]}...')
                    break
        else:
            print('  ❌ Calendar events NOT found in AI prompt')
            return False
        
        calendar_svc.stop()
        return True
        
    except Exception as e:
        print(f'  ❌ Error: {e}')
        return False

def test_files():
    """Test required files"""
    print('\n📁 Testing Required Files')
    print('=' * 40)
    
    import glob
    required_patterns = [
        'new_path/client_secret_*.json',
        'new_path/token.json',
        'new_path/ring-database-firebase-adminsdk-*.json'
    ]
    
    all_good = True
    for pattern in required_patterns:
        files = glob.glob(pattern)
        if files:
            print(f'  ✅ {pattern}: Found {len(files)} file(s)')
        else:
            print(f'  ❌ {pattern}: Missing')
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print('🧪 Google Calendar Integration Test Suite')
    print('=' * 50)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Required Files", test_files),
        ("Calendar Service", test_calendar_service),
        ("AI Integration", test_ai_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f'  ❌ {test_name} failed with error: {e}')
            results.append((test_name, False))
    
    # Summary
    print('\n📊 Test Summary')
    print('=' * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f'  {test_name}: {status}')
        if result:
            passed += 1
    
    print(f'\n🎯 Overall: {passed}/{len(results)} tests passed')
    
    if passed == len(results):
        print('🎉 All tests passed! Your calendar integration is working perfectly!')
        return 0
    else:
        print('⚠️  Some tests failed. Check the output above for details.')
        return 1

if __name__ == "__main__":
    sys.exit(main())
