#!/usr/bin/env python3
"""
Online Learning Behavior Predictor
Learns incrementally from each new entry without full retraining
"""

import os
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from collections import deque
import warnings
warnings.filterwarnings('ignore')

class OnlineBehaviorPredictor:
    def __init__(self, model_path: str = "models/online_behavior_model.pkl", memory_size: int = 1000):
        """
        Initialize online learning behavior predictor
        
        Args:
            model_path: Path to save/load the model
            memory_size: Number of recent entries to keep in memory
        """
        self.model_path = model_path
        self.memory_size = memory_size
        
        # Online learning model (supports partial_fit)
        self.model = MultinomialNB()
        self.model_trained = False
        
        # Encoders and scalers
        self.action_encoder = LabelEncoder()
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        # Feature columns
        self.feature_columns = []
        
        # Memory buffer for recent entries
        self.memory = deque(maxlen=memory_size)
        
        # Action categories
        self.action_categories = {
            'Sleep': ['Sleep', 'nap', 'sleeping', 'rest'],
            'Work': ['Work', 'work', 'job', 'office', 'meeting'],
            'Study': ['Homework', 'study', 'School', 'class', 'learning', 'research'],
            'Exercise': ['Workout', 'exercise', 'gym', 'running', 'fitness'],
            'Social': ['Friends and family', 'social', 'friends', 'family', 'hanging out'],
            'Personal': ['Duties', 'personal', 'chores', 'shower', 'eating', 'cooking'],
            'Entertainment': ['Waste', 'entertainment', 'gaming', 'watching', 'fun'],
            'Mindfulness': ['Meditate REAL', 'meditation', 'mindfulness', 'reflection'],
            'Career': ['internship 2026', 'career', 'job search', 'networking', 'resume']
        }
        
        # All possible classes (for partial_fit)
        self.all_classes = list(self.action_categories.keys()) + ['Other']
        
        # Statistics
        self.total_entries_learned = 0
        self.predictions_made = 0
        
        # Try to load existing model
        self.load_model()
    
    def categorize_action(self, action: str) -> str:
        """Categorize action into broader categories"""
        action_lower = action.lower()
        for category, keywords in self.action_categories.items():
            if any(keyword.lower() in action_lower for keyword in keywords):
                return category
        return 'Other'
    
    def extract_features(self, entries: List[Dict[str, Any]]) -> Tuple[np.ndarray, Optional[str]]:
        """
        Extract features from entries
        Returns: (features, target_action) or (features, None) for prediction
        """
        if not entries:
            raise ValueError("No entries provided")
        
        # Convert to DataFrame
        df = pd.DataFrame(entries)
        
        # Handle timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns and 'start_time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['start_time'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
        else:
            df['timestamp'] = pd.to_datetime('now')
        
        df = df.sort_values('timestamp')
        
        # Get the last entry for feature extraction
        last_entry = df.iloc[-1]
        
        # Extract temporal features
        hour = last_entry['timestamp'].hour
        day_of_week = last_entry['timestamp'].dayofweek
        is_weekend = 1 if day_of_week in [5, 6] else 0
        is_morning = 1 if 6 <= hour < 12 else 0
        is_afternoon = 1 if 12 <= hour < 18 else 0
        is_evening = 1 if 18 <= hour < 22 else 0
        is_night = 1 if hour >= 22 or hour < 6 else 0
        
        # Duration features
        duration = last_entry.get('duration_minutes', 0)
        duration = 0 if pd.isna(duration) else duration
        is_short = 1 if duration < 30 else 0
        is_medium = 1 if 30 <= duration < 120 else 0
        is_long = 1 if duration >= 120 else 0
        
        # Previous action features
        if len(df) > 1:
            prev_entry = df.iloc[-2]
            prev_action = self.categorize_action(prev_entry.get('action', 'Unknown'))
            prev_duration = prev_entry.get('duration_minutes', 0)
            prev_duration = 0 if pd.isna(prev_duration) else prev_duration
            prev_hour = prev_entry['timestamp'].hour
            
            # Time gap
            time_gap = (last_entry['timestamp'] - prev_entry['timestamp']).total_seconds() / 3600
        else:
            prev_action = 'Unknown'
            prev_duration = 0
            prev_hour = 0
            time_gap = 0
        
        # Encode previous action
        if prev_action not in self.all_classes:
            prev_action = 'Other'
        
        # One-hot encode previous action
        prev_action_encoded = [1 if cat == prev_action else 0 for cat in self.all_classes]
        
        # Combine all features
        features = [
            hour, day_of_week, is_weekend, is_morning, is_afternoon,
            is_evening, is_night, duration, is_short, is_medium, is_long,
            prev_duration, prev_hour, time_gap
        ] + prev_action_encoded
        
        # Get target action if this is for training
        target_action = None
        if 'action' in last_entry:
            target_action = self.categorize_action(last_entry['action'])
        
        return np.array(features).reshape(1, -1), target_action
    
    def learn_from_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Learn from a single new entry (online learning)
        
        Args:
            entry: New journal entry with timestamp, action, duration
        
        Returns:
            True if learning successful
        """
        try:
            # Add to memory
            self.memory.append(entry)
            
            # Need at least 1 entry to extract features
            if len(self.memory) < 1:
                print("⚠️ Need at least 1 entry to start learning")
                return False
            
            # Extract features from recent entries
            recent_entries = list(self.memory)[-10:]  # Use last 10 entries for context
            features, target_action = self.extract_features(recent_entries)
            
            if target_action is None:
                print("⚠️ No action found in entry")
                return False
            
            # Scale features
            if self.total_entries_learned == 0:
                # First time - fit the scaler
                self.scaler.fit(features)
            
            features_scaled = self.scaler.transform(features)
            
            # Ensure features are non-negative for MultinomialNB
            features_scaled = np.abs(features_scaled)
            
            # Partial fit (online learning)
            self.model.partial_fit(features_scaled, [target_action], classes=self.all_classes)
            self.model_trained = True
            
            self.total_entries_learned += 1
            
            print(f"📚 Learned from entry #{self.total_entries_learned}: {target_action}")
            
            return True
            
        except Exception as e:
            print(f"❌ Learning failed: {e}")
            return False
    
    def predict_next_entry(self, recent_entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Predict the next journal entry
        
        Args:
            recent_entries: Recent entries for context (optional, will use memory if not provided)
        
        Returns:
            Prediction with action, confidence, and top predictions
        """
        if not self.model_trained:
            raise ValueError("Model not trained yet! Feed some data first using learn_from_entry()")
        
        # Use memory if no recent entries provided
        if recent_entries is None:
            if len(self.memory) == 0:
                raise ValueError("No entries in memory to base prediction on")
            recent_entries = list(self.memory)[-10:]
        
        # Extract features
        features, _ = self.extract_features(recent_entries)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        features_scaled = np.abs(features_scaled)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Get top predictions
        classes = self.model.classes_
        top_predictions = sorted(zip(classes, probabilities), key=lambda x: x[1], reverse=True)[:3]
        
        self.predictions_made += 1
        
        return {
            'predicted_action': prediction,
            'confidence': max(probabilities),
            'top_predictions': top_predictions,
            'timestamp': datetime.now().isoformat(),
            'total_learned': self.total_entries_learned,
            'predictions_made': self.predictions_made
        }
    
    def bulk_learn(self, entries: List[Dict[str, Any]]) -> int:
        """
        Learn from multiple entries sequentially
        
        Args:
            entries: List of journal entries
        
        Returns:
            Number of entries successfully learned
        """
        learned_count = 0
        
        # Sort by timestamp
        df = pd.DataFrame(entries)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns and 'start_time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['start_time'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
        
        df = df.sort_values('timestamp')
        sorted_entries = df.to_dict('records')
        
        print(f"📚 Learning from {len(sorted_entries)} entries sequentially...")
        
        for i, entry in enumerate(sorted_entries, 1):
            if self.learn_from_entry(entry):
                learned_count += 1
            
            # Progress indicator
            if i % 100 == 0:
                print(f"   Processed {i}/{len(sorted_entries)} entries...")
        
        print(f"✅ Bulk learning completed! Learned from {learned_count}/{len(sorted_entries)} entries")
        
        return learned_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            'model_trained': self.model_trained,
            'total_entries_learned': self.total_entries_learned,
            'predictions_made': self.predictions_made,
            'memory_size': len(self.memory),
            'max_memory_size': self.memory_size,
            'action_categories': self.all_classes
        }
    
    def save_model(self):
        """Save the model, memory, and state"""
        if not os.path.isabs(self.model_path):
            self.model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.model_path)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'model_trained': self.model_trained,
            'action_encoder': self.action_encoder,
            'scaler': self.scaler,
            'memory': list(self.memory),
            'action_categories': self.action_categories,
            'all_classes': self.all_classes,
            'total_entries_learned': self.total_entries_learned,
            'predictions_made': self.predictions_made
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to {self.model_path}")
    
    def load_model(self):
        """Load the model and state"""
        possible_paths = [
            self.model_path,
            "models/online_behavior_model.pkl",
            "../models/online_behavior_model.pkl",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models/online_behavior_model.pkl")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    self.model = model_data['model']
                    self.model_trained = model_data['model_trained']
                    self.action_encoder = model_data['action_encoder']
                    self.scaler = model_data['scaler']
                    self.memory = deque(model_data['memory'], maxlen=self.memory_size)
                    self.action_categories = model_data['action_categories']
                    self.all_classes = model_data['all_classes']
                    self.total_entries_learned = model_data['total_entries_learned']
                    self.predictions_made = model_data['predictions_made']
                    
                    print(f"✅ Model loaded from {path}")
                    print(f"   Entries learned: {self.total_entries_learned}")
                    print(f"   Predictions made: {self.predictions_made}")
                    return True
                except Exception as e:
                    print(f"❌ Error loading model from {path}: {e}")
                    continue
        
        print("⚠️ No saved model found. Starting with empty model.")
        return False
    
    def reset(self):
        """Reset the model to empty state"""
        self.model = MultinomialNB()
        self.model_trained = False
        self.memory.clear()
        self.total_entries_learned = 0
        self.predictions_made = 0
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        print("🔄 Model reset to empty state")
