#!/usr/bin/env python3
"""
FastAPI Server for Real-time Behavior Prediction
Production-ready API server for behavior prediction and learning
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.predictor import RealtimeBehaviorPredictor

# Initialize FastAPI app
app = FastAPI(
    title="Human Behavior Prediction API",
    description="Real-time behavior prediction and learning API for journal entries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictor instance
predictor = None

# Pydantic models for request/response
class JournalEntry(BaseModel):
    timestamp: str = Field(..., description="ISO timestamp of the entry")
    action: str = Field(..., description="Action performed")
    description: Optional[str] = Field(None, description="Description of the activity")
    duration_minutes: Optional[int] = Field(0, description="Duration in minutes")

class PredictionRequest(BaseModel):
    recent_entries: List[JournalEntry] = Field(..., description="Recent journal entries for prediction")

class PredictionResponse(BaseModel):
    predicted_action: str = Field(..., description="Predicted next action")
    confidence: float = Field(..., description="Confidence score (0-1)")
    top_predictions: List[Dict[str, float]] = Field(..., description="Top predictions with probabilities")
    feature_importance: Dict[str, float] = Field(..., description="Feature importance scores")
    timestamp: str = Field(..., description="Prediction timestamp")

class LearningRequest(BaseModel):
    new_entry: JournalEntry = Field(..., description="New entry to learn from")
    recent_entries: List[JournalEntry] = Field(..., description="Recent entries for context")

class LearningResponse(BaseModel):
    success: bool = Field(..., description="Whether learning was successful")
    message: str = Field(..., description="Status message")

class StatusResponse(BaseModel):
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_accuracy: Optional[float] = Field(None, description="Model accuracy if available")
    feature_count: Optional[int] = Field(None, description="Number of features")
    categories: Optional[List[str]] = Field(None, description="Available action categories")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Current timestamp")

# Initialize predictor on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the predictor on startup"""
    global predictor
    print("🚀 Starting Human Behavior Prediction API...")
    
    predictor = RealtimeBehaviorPredictor()
    
    # Try to load existing model
    if not predictor.load_model():
        print("⚠️ No model found. API will run in degraded mode.")
        print("   Train a model using: python train_model.py")
        print("   Or use the /retrain endpoint to train with existing data")
    else:
        print("✅ Model loaded successfully!")
    
    print("🌐 API server ready!")
    print("   Health check: /health")
    print("   API docs: /docs")

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get model status and information"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    if predictor.model is None:
        return StatusResponse(
            model_loaded=False,
            message="Model not loaded. Train a model first."
        )
    
    return StatusResponse(
        model_loaded=True,
        model_accuracy=None,  # Would need to calculate this
        feature_count=len(predictor.feature_columns) if predictor.feature_columns else 0,
        categories=list(predictor.action_categories.keys()) if predictor.action_categories else []
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_next_entry(request: PredictionRequest):
    """Predict the next journal entry based on recent entries"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    if predictor.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Train a model first.")
    
    if not request.recent_entries:
        raise HTTPException(status_code=400, detail="No recent entries provided")
    
    try:
        # Convert Pydantic models to dictionaries
        recent_entries = [entry.dict() for entry in request.recent_entries]
        
        # Make prediction
        prediction = predictor.predict_next_entry(recent_entries)
        
        return PredictionResponse(
            predicted_action=prediction['predicted_action'],
            confidence=prediction['confidence'],
            top_predictions=[
                {"action": action, "probability": prob} 
                for action, prob in prediction['top_predictions']
            ],
            feature_importance=prediction['feature_importance'],
            timestamp=prediction['timestamp']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/learn", response_model=LearningResponse)
async def learn_from_entry(request: LearningRequest, background_tasks: BackgroundTasks):
    """Learn from a new journal entry"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    if predictor.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Train a model first.")
    
    try:
        # Convert Pydantic models to dictionaries
        new_entry = request.new_entry.dict()
        recent_entries = [entry.dict() for entry in request.recent_entries]
        
        # Learn from new entry
        predictor.learn_from_entry(new_entry, recent_entries)
        
        return LearningResponse(
            success=True,
            message=f"Successfully learned from entry: {new_entry['action']}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Learning failed: {str(e)}")

@app.get("/recent-entries")
async def get_recent_entries(days: int = 7):
    """Get recent entries from the data file"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        recent_entries = predictor.get_recent_entries('data/firestore_data.csv', days=days)
        return {
            "entries": recent_entries,
            "count": len(recent_entries),
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent entries: {str(e)}")

@app.post("/evaluate")
async def evaluate_model(test_days: int = 7):
    """Evaluate model performance on recent data"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    if predictor.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Train a model first.")
    
    try:
        results = predictor.evaluate_model('data/firestore_data.csv', test_days=test_days)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
    """Retrain the model with latest data"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Run training in background
        background_tasks.add_task(train_model_background)
        return {"message": "Model retraining started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

async def train_model_background():
    """Background task to retrain the model"""
    global predictor
    try:
        print("🔄 Retraining model in background...")
        accuracy = predictor.train_model('data/firestore_data.csv')
        print(f"✅ Model retrained successfully! Accuracy: {accuracy:.3f}")
    except Exception as e:
        print(f"❌ Background training failed: {e}")

# Example usage endpoints
@app.get("/example/prediction")
async def get_example_prediction():
    """Get an example prediction request"""
    example_entries = [
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
    
    return {
        "description": "Example prediction request",
        "request_body": {
            "recent_entries": example_entries
        },
        "usage": "POST this to /predict endpoint"
    }

@app.get("/example/learning")
async def get_example_learning():
    """Get an example learning request"""
    example_new_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "Workout",
        "description": "Morning exercise routine",
        "duration_minutes": 45
    }
    
    example_recent_entries = [
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "action": "Duties",
            "description": "Morning routine",
            "duration_minutes": 30
        }
    ]
    
    return {
        "description": "Example learning request",
        "request_body": {
            "new_entry": example_new_entry,
            "recent_entries": example_recent_entries
        },
        "usage": "POST this to /learn endpoint"
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Human Behavior Prediction API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting API server on {args.host}:{args.port}")
    print(f"📚 API documentation available at: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


