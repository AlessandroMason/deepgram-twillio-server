#!/usr/bin/env python3
"""
Online Learning API Server
API server with true online learning - learns from each new entry incrementally
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add parent directory to path to find services
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import from services subdirectory
try:
    from services.online_predictor import OnlineBehaviorPredictor
except ImportError:
    # If running from parent directory, try alternative import
    sys.path.insert(0, os.path.join(current_dir, '..'))
    from realtime_predictions.services.online_predictor import OnlineBehaviorPredictor

# Initialize FastAPI app
app = FastAPI(
    title="Online Learning Behavior Prediction API",
    description="Real-time online learning API - learns from each entry incrementally without retraining",
    version="2.0.0",
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

# Pydantic models
class JournalEntry(BaseModel):
    timestamp: str = Field(..., description="ISO timestamp of the entry")
    action: str = Field(..., description="Action performed")
    description: Optional[str] = Field(None, description="Description of the activity")
    duration_minutes: Optional[int] = Field(0, description="Duration in minutes")

class LearnRequest(BaseModel):
    entry: JournalEntry = Field(..., description="New entry to learn from")

class PredictRequest(BaseModel):
    recent_entries: Optional[List[JournalEntry]] = Field(None, description="Recent entries for context (optional)")

class BulkLearnRequest(BaseModel):
    entries: List[JournalEntry] = Field(..., description="Multiple entries to learn from sequentially")

class PredictionResponse(BaseModel):
    predicted_action: str
    confidence: float
    top_predictions: List[Dict[str, float]]
    timestamp: str
    total_learned: int
    predictions_made: int

class LearnResponse(BaseModel):
    success: bool
    message: str
    total_learned: int

class StatsResponse(BaseModel):
    model_trained: bool
    total_entries_learned: int
    predictions_made: int
    memory_size: int
    max_memory_size: int
    action_categories: List[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# Initialize predictor on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the online learning predictor"""
    global predictor
    print("🚀 Starting Online Learning Behavior Prediction API...")
    print("="*50)
    
    predictor = OnlineBehaviorPredictor()
    
    print("🎯 Online Learning Mode: ENABLED")
    print("   • Learns from each new entry")
    print("   • No retraining needed")
    print("   • Sequential learning")
    print("="*50)
    print("🌐 API server ready!")

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

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get model statistics"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    stats = predictor.get_stats()
    return StatsResponse(**stats)

@app.post("/learn", response_model=LearnResponse)
async def learn_from_entry(request: LearnRequest):
    """
    Learn from a new journal entry (online learning)
    The model learns immediately without retraining
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Convert Pydantic model to dictionary
        entry = request.entry.dict()
        
        # Learn from the entry
        success = predictor.learn_from_entry(entry)
        
        if success:
            # Auto-save after learning
            predictor.save_model()
            
            return LearnResponse(
                success=True,
                message=f"Successfully learned from entry: {entry['action']}",
                total_learned=predictor.total_entries_learned
            )
        else:
            raise HTTPException(status_code=500, detail="Learning failed")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Learning failed: {str(e)}")

@app.post("/learn/bulk", response_model=LearnResponse)
async def bulk_learn(request: BulkLearnRequest):
    """
    Learn from multiple entries sequentially
    Useful for initializing the model with historical data
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Convert Pydantic models to dictionaries
        entries = [entry.dict() for entry in request.entries]
        
        # Bulk learn
        learned_count = predictor.bulk_learn(entries)
        
        # Auto-save after bulk learning
        predictor.save_model()
        
        return LearnResponse(
            success=True,
            message=f"Successfully learned from {learned_count} entries",
            total_learned=predictor.total_entries_learned
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk learning failed: {str(e)}")

@app.post("/predict", response_model=PredictionResponse)
async def predict_next_entry(request: PredictRequest):
    """
    Predict the next journal entry
    Uses recent entries for context or model memory if not provided
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    if not predictor.model_trained:
        raise HTTPException(
            status_code=503, 
            detail="Model not trained yet. Feed some data first using /learn endpoint"
        )
    
    try:
        # Convert Pydantic models to dictionaries if provided
        recent_entries = None
        if request.recent_entries:
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
            timestamp=prediction['timestamp'],
            total_learned=prediction['total_learned'],
            predictions_made=prediction['predictions_made']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/reset")
async def reset_model():
    """Reset the model to empty state"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    predictor.reset()
    return {"message": "Model reset to empty state", "success": True}

@app.post("/save")
async def save_model():
    """Manually save the model"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        predictor.save_model()
        return {"message": "Model saved successfully", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")

# Example endpoints
@app.get("/example/learn")
async def get_learn_example():
    """Get an example learning request"""
    example_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "Workout",
        "description": "Morning exercise routine",
        "duration_minutes": 45
    }
    
    return {
        "description": "Example learning request",
        "endpoint": "POST /learn",
        "request_body": {
            "entry": example_entry
        },
        "usage": "Send this to /learn to teach the model about a new activity"
    }

@app.get("/example/predict")
async def get_predict_example():
    """Get an example prediction request"""
    example_entries = [
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "action": "Sleep",
            "description": "Good night sleep",
            "duration_minutes": 480
        },
        {
            "timestamp": datetime.now().isoformat(),
            "action": "Duties",
            "description": "Morning routine",
            "duration_minutes": 30
        }
    ]
    
    return {
        "description": "Example prediction request",
        "endpoint": "POST /predict",
        "request_body": {
            "recent_entries": example_entries
        },
        "note": "recent_entries is optional - will use model memory if not provided"
    }

@app.get("/example/bulk-learn")
async def get_bulk_learn_example():
    """Get an example bulk learning request"""
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
        }
    ]
    
    return {
        "description": "Example bulk learning request",
        "endpoint": "POST /learn/bulk",
        "request_body": {
            "entries": example_entries
        },
        "usage": "Send historical data to initialize the model"
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Online Learning Behavior Prediction API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Online Learning API on {args.host}:{args.port}")
    print(f"📚 API documentation: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "online_api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
