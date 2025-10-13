#!/usr/bin/env python3
"""
Start Server Script
Easy way to start the API server with proper configuration
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import pandas
        import numpy
        import sklearn
        import fastapi
        import uvicorn
        print("✅ All requirements are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing requirement: {e}")
        print("   Install with: pip install -r requirements.txt")
        return False

def check_model():
    """Check if model exists"""
    model_path = "models/realtime_behavior_model.pkl"
    if os.path.exists(model_path):
        print("✅ Model found")
        return True
    else:
        print("❌ Model not found")
        print("   Train the model first with: python train_model.py")
        return False

def check_data():
    """Check if data file exists"""
    data_path = "data/firestore_data.csv"
    if os.path.exists(data_path):
        print("✅ Data file found")
        return True
    else:
        print("❌ Data file not found")
        print("   Please ensure data/firestore_data.csv exists")
        return False

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(description="Start Human Behavior Prediction API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--skip-checks", action="store_true", help="Skip pre-flight checks")
    
    args = parser.parse_args()
    
    # Use PORT environment variable if available (for Render.com and other cloud platforms)
    port = args.port if args.port is not None else int(os.environ.get("PORT", 8000))
    
    print("🚀 Human Behavior Prediction API Server")
    print("=" * 50)
    
    if not args.skip_checks:
        print("🔍 Running pre-flight checks...")
        
        # Check requirements
        if not check_requirements():
            return 1
        
        # Check data
        if not check_data():
            return 1
        
        # Check model
        if not check_model():
            return 1
        
        print("✅ All checks passed!")
    
    print(f"\n🌐 Starting server on {args.host}:{port}")
    print(f"📚 API documentation: http://{args.host}:{port}/docs")
    print(f"🔍 Interactive docs: http://{args.host}:{port}/redoc")
    print(f"\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run(
            "api_server:app",
            host=args.host,
            port=port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


