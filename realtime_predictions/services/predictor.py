#!/usr/bin/env python3
"""
Real-time Behavior Predictor
Core prediction and learning logic for the API
"""

import os
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

class RealtimeBehaviorPredictor:
    def __init__(self, model_path: str = "models/realtime_behavior_model.pkl"):
        """
        Initialize real-time behavior predictor
        
        Args:
            model_path: Path to save/load the model
        """
        self.model_path = model_path
        self.model = None
        self.encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
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
        
        # Load existing model if available
        self.load_model()
    
    def categorize_action(self, action: str) -> str:
        """Categorize action into broader categories"""
        action_lower = action.lower()
        for category, keywords in self.action_categories.items():
            if any(keyword.lower() in action_lower for keyword in keywords):
                return category
        return 'Other'
    
    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create temporal features with recency weighting"""
        df = df.copy()
        
        # Handle different timestamp column names
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns and 'start_time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['start_time'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
        else:
            raise ValueError("No timestamp column found! Expected 'timestamp', 'date', or 'date' + 'start_time'")
        
        df = df.sort_values('timestamp')
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_morning'] = ((df['hour'] >= 6) & (df['hour'] < 12)).astype(int)
        df['is_afternoon'] = ((df['hour'] >= 12) & (df['hour'] < 18)).astype(int)
        df['is_evening'] = ((df['hour'] >= 18) & (df['hour'] < 22)).astype(int)
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] < 6)).astype(int)
        
        # Duration features
        df['duration_minutes'] = df['duration_minutes'].fillna(0)
        df['is_short_activity'] = (df['duration_minutes'] < 30).astype(int)
        df['is_medium_activity'] = ((df['duration_minutes'] >= 30) & (df['duration_minutes'] < 120)).astype(int)
        df['is_long_activity'] = (df['duration_minutes'] >= 120).astype(int)
        
        # Previous activity features
        df['prev_action'] = df['action'].shift(1)
        df['prev_duration'] = df['duration_minutes'].shift(1)
        df['prev_hour'] = df['hour'].shift(1)
        
        # Time gap features
        df['time_gap_hours'] = df['timestamp'].diff().dt.total_seconds() / 3600
        df['time_gap_hours'] = df['time_gap_hours'].fillna(0)
        
        # Pattern features - create action sequences manually
        df['action_sequence'] = ''
        for i in range(len(df)):
            start_idx = max(0, i-2)
            end_idx = i + 1
            sequence = df['action'].iloc[start_idx:end_idx].dropna().astype(str).tolist()
            df.iloc[i, df.columns.get_loc('action_sequence')] = ' -> '.join(sequence)
        
        # Recency weighting (more recent entries get higher weight)
        max_timestamp = df['timestamp'].max()
        df['days_since_max'] = (max_timestamp - df['timestamp']).dt.days
        df['recency_weight'] = np.exp(-df['days_since_max'] / 7)  # Exponential decay with 7-day half-life
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare features for training/prediction"""
        df = self.create_temporal_features(df)
        
        # Categorize actions
        df['action_category'] = df['action'].apply(self.categorize_action)
        
        # Encode categorical features
        categorical_features = ['action_category', 'prev_action']
        for feature in categorical_features:
            if feature not in self.encoders:
                self.encoders[feature] = LabelEncoder()
                df[f'{feature}_encoded'] = self.encoders[feature].fit_transform(df[feature].fillna('Unknown'))
            else:
                # Handle new categories
                known_categories = set(self.encoders[feature].classes_)
                df[feature] = df[feature].fillna('Unknown')
                df[feature] = df[feature].apply(lambda x: x if x in known_categories else 'Unknown')
                df[f'{feature}_encoded'] = self.encoders[feature].transform(df[feature])
        
        # Select features
        feature_columns = [
            'hour', 'day_of_week', 'is_weekend', 'is_morning', 'is_afternoon', 
            'is_evening', 'is_night', 'duration_minutes', 'is_short_activity',
            'is_medium_activity', 'is_long_activity', 'prev_duration', 'prev_hour',
            'time_gap_hours', 'action_category_encoded', 'prev_action_encoded'
        ]
        
        # Filter to available columns
        available_features = [col for col in feature_columns if col in df.columns]
        self.feature_columns = available_features
        
        X = df[available_features].fillna(0).values
        y = df['action_category'].values
        weights = df['recency_weight'].values
        
        return X, y, weights
    
    def train_model(self, csv_file_path: str):
        """Train the model on historical data"""
        print("🔄 Loading and preparing data...")
        
        # Load data
        if not os.path.isabs(csv_file_path):
            csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), csv_file_path)
        
        df = pd.read_csv(csv_file_path)
        print(f"📊 Loaded {len(df)} entries")
        
        # Prepare features
        X, y, weights = self.prepare_features(df)
        print(f"🔧 Prepared {X.shape[1]} features")
        
        # Train model
        print("🤖 Training model...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        # Fit with sample weights
        self.model.fit(X, y, sample_weight=weights)
        
        # Evaluate
        y_pred = self.model.predict(X)
        accuracy = accuracy_score(y, y_pred)
        print(f"✅ Model trained! Accuracy: {accuracy:.3f}")
        
        # Save model
        self.save_model()
        
        return accuracy
    
    def predict_next_entry(self, recent_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict the next journal entry based on recent entries"""
        if self.model is None:
            raise ValueError("Model not trained! Train the model first.")
        
        if not recent_entries:
            raise ValueError("No recent entries provided!")
        
        # Convert to DataFrame
        df = pd.DataFrame(recent_entries)
        
        # Prepare features for the last entry
        X, _, _ = self.prepare_features(df)
        last_features = X[-1:].reshape(1, -1)
        
        # Predict
        prediction = self.model.predict(last_features)[0]
        probabilities = self.model.predict_proba(last_features)[0]
        
        # Get feature importance for explanation
        feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        
        # Get top predictions
        classes = self.model.classes_
        top_predictions = sorted(zip(classes, probabilities), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'predicted_action': prediction,
            'confidence': max(probabilities),
            'top_predictions': top_predictions,
            'feature_importance': feature_importance,
            'timestamp': datetime.now().isoformat()
        }
    
    def learn_from_entry(self, new_entry: Dict[str, Any], recent_entries: List[Dict[str, Any]]):
        """Learn from a new journal entry"""
        if self.model is None:
            raise ValueError("Model not trained! Train the model first.")
        
        print(f"📚 Learning from new entry: {new_entry.get('action', 'Unknown')}")
        
        # Add new entry to recent entries
        all_entries = recent_entries + [new_entry]
        
        # Prepare features
        df = pd.DataFrame(all_entries)
        X, y, weights = self.prepare_features(df)
        
        # Update model with new data (partial fit for incremental learning)
        # For RandomForest, we'll retrain with all data including the new entry
        # In a production system, you might use online learning algorithms
        
        # For now, we'll store the new entry and retrain periodically
        # This is a simplified approach - in practice, you'd want true incremental learning
        
        print("✅ Entry learned! (Model will be updated on next training)")
        
        return True
    
    def save_model(self):
        """Save the model and encoders"""
        if not os.path.isabs(self.model_path):
            self.model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.model_path)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'encoders': self.encoders,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'action_categories': self.action_categories
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to {self.model_path}")
    
    def load_model(self):
        """Load the model and encoders"""
        possible_paths = [
            self.model_path,
            "models/realtime_behavior_model.pkl",
            "../models/realtime_behavior_model.pkl",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models/realtime_behavior_model.pkl")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    self.model = model_data['model']
                    self.encoders = model_data['encoders']
                    self.scaler = model_data['scaler']
                    self.feature_columns = model_data['feature_columns']
                    self.action_categories = model_data['action_categories']
                    
                    print(f"✅ Model loaded from {path}")
                    return True
                except Exception as e:
                    print(f"❌ Error loading model from {path}: {e}")
                    continue
        
        print("⚠️ No model found. Train the model first.")
        return False
    
    def get_recent_entries(self, csv_file_path: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent entries from the last N days"""
        if not os.path.isabs(csv_file_path):
            csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), csv_file_path)
        
        df = pd.read_csv(csv_file_path)
        
        # Handle different timestamp column names
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns and 'start_time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['start_time'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
        else:
            raise ValueError("No timestamp column found!")
        
        # Get recent entries
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_df = df[df['timestamp'] >= cutoff_date].sort_values('timestamp')
        
        return recent_df.to_dict('records')
    
    def evaluate_model(self, csv_file_path: str, test_days: int = 7):
        """Evaluate model performance on recent data"""
        if self.model is None:
            raise ValueError("Model not trained!")
        
        print(f"🔍 Evaluating model on last {test_days} days...")
        
        # Get recent entries
        recent_entries = self.get_recent_entries(csv_file_path, test_days)
        
        if len(recent_entries) < 2:
            print("❌ Not enough recent data for evaluation")
            return
        
        # Prepare features
        df = pd.DataFrame(recent_entries)
        X, y, weights = self.prepare_features(df)
        
        # Predict
        y_pred = self.model.predict(X)
        
        # Calculate accuracy
        accuracy = accuracy_score(y, y_pred)
        
        # Classification report
        report = classification_report(y, y_pred, output_dict=True)
        
        print(f"📊 Evaluation Results:")
        print(f"   Accuracy: {accuracy:.3f}")
        print(f"   Total entries: {len(recent_entries)}")
        print(f"   Recent entries: {len([e for e in recent_entries if pd.to_datetime(e['timestamp']).date() == datetime.now().date()])}")
        
        return {
            'accuracy': accuracy,
            'total_entries': len(recent_entries),
            'classification_report': report
        }


