#!/usr/bin/env python3
"""
Demo: Online Learning Behavior Prediction
Shows how the model learns and predicts incrementally
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))
from services.online_predictor import OnlineBehaviorPredictor

def main():
    print("🎯 Online Learning Behavior Prediction Demo")
    print("="*60)
    
    # Create a new empty predictor
    predictor = OnlineBehaviorPredictor()
    predictor.reset()  # Start fresh
    
    print("\n📊 Starting with EMPTY model")
    print(f"   Entries learned: {predictor.total_entries_learned}")
    print(f"   Model trained: {predictor.model_trained}")
    
    # Create sample journal entries
    sample_entries = [
        {
            "timestamp": (datetime.now() - timedelta(hours=10)).isoformat(),
            "action": "Sleep",
            "description": "Good night sleep",
            "duration_minutes": 480
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "action": "Duties",
            "description": "Morning routine",
            "duration_minutes": 30
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "action": "Homework",
            "description": "Working on assignments",
            "duration_minutes": 60
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "action": "Workout",
            "description": "Exercise",
            "duration_minutes": 45
        }
    ]
    
    # Learn from entries sequentially
    print("\n📚 Learning from entries sequentially...")
    print("-"*60)
    
    for i, entry in enumerate(sample_entries, 1):
        print(f"\n#{i}. Learning from: {entry['action']} ({entry['duration_minutes']} min)")
        success = predictor.learn_from_entry(entry)
        
        if success:
            print(f"   ✅ Learned! Total entries: {predictor.total_entries_learned}")
            
            # Try to predict after learning each entry
            if predictor.model_trained:
                try:
                    prediction = predictor.predict_next_entry()
                    print(f"   🔮 Prediction: {prediction['predicted_action']} ({prediction['confidence']:.1%} confidence)")
                except Exception as e:
                    print(f"   ⚠️ Prediction not ready yet: {e}")
        else:
            print(f"   ❌ Learning failed")
    
    # Make final prediction
    print("\n"+"="*60)
    print("🔮 Final Prediction (after learning from all entries):")
    print("-"*60)
    
    try:
        prediction = predictor.predict_next_entry()
        print(f"\n✅ Predicted next action: {prediction['predicted_action']}")
        print(f"   Confidence: {prediction['confidence']:.1%}")
        print(f"\n📊 Top 3 Predictions:")
        for i, (action, prob) in enumerate(prediction['top_predictions'], 1):
            print(f"   {i}. {action}: {prob:.1%}")
        
        print(f"\n📈 Model Statistics:")
        print(f"   Total entries learned: {prediction['total_learned']}")
        print(f"   Predictions made: {prediction['predictions_made']}")
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
    
    # Test adding one more entry and predicting again
    print("\n"+"="*60)
    print("📚 Adding one more entry: Duties (eating)")
    print("-"*60)
    
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "Duties",
        "description": "Eating lunch",
        "duration_minutes": 20
    }
    
    predictor.learn_from_entry(new_entry)
    
    # Predict again
    prediction = predictor.predict_next_entry()
    print(f"🔮 New prediction: {prediction['predicted_action']} ({prediction['confidence']:.1%} confidence)")
    
    # Save the model
    print("\n"+"="*60)
    print("💾 Saving model...")
    predictor.save_model()
    
    # Show final stats
    stats = predictor.get_stats()
    print("\n📊 Final Model Statistics:")
    print(f"   Model trained: {stats['model_trained']}")
    print(f"   Entries learned: {stats['total_entries_learned']}")
    print(f"   Predictions made: {stats['predictions_made']}")
    print(f"   Memory size: {stats['memory_size']}/{stats['max_memory_size']}")
    print(f"   Categories: {', '.join(stats['action_categories'])}")
    
    print("\n🎉 Demo completed!")
    print("\n💡 Key Features:")
    print("   ✓ Starts with EMPTY model")
    print("   ✓ Learns from EACH entry incrementally")
    print("   ✓ NO retraining needed")
    print("   ✓ Predicts after learning")
    print("   ✓ Saves state for later use")
    
    print("\n🚀 To use the API:")
    print("   python online_api_server.py")
    print("   Then POST to /learn to feed data")
    print("   Then POST to /predict to get predictions")

if __name__ == "__main__":
    main()
