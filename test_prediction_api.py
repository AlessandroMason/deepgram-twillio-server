#!/usr/bin/env python3
"""
Quick test script for the Prediction API
"""

import requests
import json
from datetime import datetime, timedelta

# Change this to your API URL
# Local: http://localhost:8000
# Render: https://your-prediction-api.onrender.com
API_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_status():
    """Test the status endpoint"""
    print("\n🔍 Testing /status endpoint...")
    try:
        response = requests.get(f"{API_URL}/status")
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_prediction():
    """Test making a prediction"""
    print("\n🔍 Testing /predict endpoint...")
    
    # Sample data
    recent_entries = [
        {
            "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
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
            f"{API_URL}/predict",
            json={"recent_entries": recent_entries}
        )
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Predicted Action: {result['predicted_action']}")
            print(f"   Confidence: {result['confidence']:.2%}")
            print(f"   Top Predictions:")
            for pred in result['top_predictions']:
                print(f"      - {pred['action']}: {pred['probability']:.2%}")
        else:
            print(f"   Error: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_learning():
    """Test the learning endpoint"""
    print("\n🔍 Testing /learn endpoint...")
    
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "Workout",
        "description": "Morning exercise",
        "duration_minutes": 45
    }
    
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
            f"{API_URL}/learn",
            json={
                "new_entry": new_entry,
                "recent_entries": recent_entries
            }
        )
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Prediction API")
    print(f"   Target: {API_URL}")
    print("=" * 60)
    
    # Run tests
    results = {
        "Health Check": test_health(),
        "Status": test_status(),
        "Prediction": test_prediction(),
        "Learning": test_learning()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()

