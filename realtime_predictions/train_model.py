#!/usr/bin/env python3
"""
Train Model Script
Trains the behavior prediction model on the provided data
"""

import os
import sys
from datetime import datetime

# Add services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.predictor import RealtimeBehaviorPredictor

def main():
    """Train the behavior prediction model"""
    print("🚀 Training Human Behavior Prediction Model")
    print("=" * 50)
    
    # Initialize predictor
    predictor = RealtimeBehaviorPredictor()
    
    # Check if data file exists
    data_file = "data/firestore_data.csv"
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print("   Please ensure the data file is in the data/ directory")
        return
    
    # Train the model
    print(f"📊 Training model on {data_file}...")
    try:
        accuracy = predictor.train_model(data_file)
        print(f"\n✅ Model training completed!")
        print(f"   Accuracy: {accuracy:.3f}")
        print(f"   Model saved to: models/realtime_behavior_model.pkl")
        print(f"   Features: {len(predictor.feature_columns)}")
        print(f"   Categories: {len(predictor.action_categories)}")
        
        # Test the model
        print(f"\n🧪 Testing model...")
        recent_entries = predictor.get_recent_entries(data_file, days=30)
        
        if recent_entries:
            print(f"📅 Found {len(recent_entries)} recent entries")
            
            # Make a test prediction
            try:
                prediction = predictor.predict_next_entry(recent_entries[-5:])  # Use last 5 entries
                print(f"🎯 Test prediction:")
                print(f"   Predicted action: {prediction['predicted_action']}")
                print(f"   Confidence: {prediction['confidence']:.1%}")
            except Exception as e:
                print(f"⚠️ Test prediction failed: {e}")
        else:
            print("⚠️ No recent entries found for testing")
        
        print(f"\n🎉 Model is ready for deployment!")
        print(f"   Start the API server with: python api_server.py")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


