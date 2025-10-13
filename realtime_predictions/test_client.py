#!/usr/bin/env python3
"""
Test Client for Real-time Behavior Prediction API
Demonstrates how to use the API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Status: {response.json()['status']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Is it running?")
        return False
    return True

def test_status():
    """Test status endpoint"""
    print("\n📊 Testing status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            status = response.json()
            print("✅ Status retrieved!")
            print(f"   Model loaded: {status['model_loaded']}")
            print(f"   Features: {status['feature_count']}")
            print(f"   Categories: {status['categories']}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_prediction():
    """Test prediction endpoint"""
    print("\n🔮 Testing prediction endpoint...")
    
    # Sample recent entries
    recent_entries = [
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "action": "Sleep",
            "description": "Good night sleep",
            "duration_minutes": 480
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "action": "Duties",
            "description": "Morning routine",
            "duration_minutes": 30
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "action": "Homework",
            "description": "Working on assignments",
            "duration_minutes": 60
        }
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json={"recent_entries": recent_entries}
        )
        
        if response.status_code == 200:
            prediction = response.json()
            print("✅ Prediction successful!")
            print(f"   Predicted action: {prediction['predicted_action']}")
            print(f"   Confidence: {prediction['confidence']:.1%}")
            print(f"   Top predictions:")
            for pred in prediction['top_predictions']:
                print(f"     - {pred['action']}: {pred['probability']:.1%}")
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_learning():
    """Test learning endpoint"""
    print("\n📚 Testing learning endpoint...")
    
    # New entry to learn from
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "Workout",
        "description": "Morning exercise routine",
        "duration_minutes": 45
    }
    
    # Recent entries for context
    recent_entries = [
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "action": "Duties",
            "description": "Morning routine",
            "duration_minutes": 30
        }
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/learn",
            json={
                "new_entry": new_entry,
                "recent_entries": recent_entries
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Learning successful!")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Learning failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_recent_entries():
    """Test recent entries endpoint"""
    print("\n📅 Testing recent entries endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/recent-entries?days=7")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Recent entries retrieved!")
            print(f"   Count: {data['count']} entries")
            print(f"   Days: {data['days']}")
            
            if data['entries']:
                print("   Recent entries:")
                for i, entry in enumerate(data['entries'][-3:], 1):  # Show last 3
                    timestamp = entry.get('timestamp', 'Unknown')
                    action = entry.get('action', 'Unknown')
                    print(f"     {i}. {timestamp} | {action}")
        else:
            print(f"❌ Recent entries failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_examples():
    """Test example endpoints"""
    print("\n📖 Testing example endpoints...")
    
    try:
        # Test prediction example
        response = requests.get(f"{BASE_URL}/example/prediction")
        if response.status_code == 200:
            print("✅ Prediction example retrieved!")
        
        # Test learning example
        response = requests.get(f"{BASE_URL}/example/learning")
        if response.status_code == 200:
            print("✅ Learning example retrieved!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all API tests"""
    print("🧪 Real-time Behavior Prediction API Test Client")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("\n❌ Server is not running. Start it with:")
        print("   python start_server.py")
        print("   or")
        print("   python api_server.py")
        return
    
    # Run all tests
    test_status()
    test_prediction()
    test_learning()
    test_recent_entries()
    test_examples()
    
    print("\n🎉 All tests completed!")
    print("\n💡 API Documentation:")
    print(f"   📚 Swagger UI: {BASE_URL}/docs")
    print(f"   🔍 ReDoc: {BASE_URL}/redoc")

if __name__ == "__main__":
    main()


