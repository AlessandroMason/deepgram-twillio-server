#!/usr/bin/env python3
"""
Multi-Service Startup Script
Starts both the WebSocket server and the FastAPI prediction server
"""

import os
import sys
import signal
import subprocess
import time
from threading import Thread

# Track running processes
processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully shutdown all services"""
    print("\n🛑 Shutting down all services...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()
    sys.exit(0)

def run_websocket_server():
    """Run the main WebSocket server"""
    print("🌐 Starting WebSocket server (Twilio/Deepgram)...")
    proc = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(proc)
    proc.wait()

def run_prediction_api():
    """Run the realtime predictions FastAPI server"""
    print("🤖 Starting Behavior Prediction API...")
    
    # Get port for prediction API (main server uses PORT, we use PORT+1 or 8001)
    main_port = int(os.environ.get("PORT", 5000))
    api_port = int(os.environ.get("PREDICTION_API_PORT", main_port + 1))
    
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "realtime_predictions.api_server:app",
            "--host", "0.0.0.0",
            "--port", str(api_port)
        ],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(proc)
    proc.wait()

def main():
    """Start all services"""
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🚀 Starting All Services")
    print("=" * 60)
    
    main_port = int(os.environ.get("PORT", 5000))
    api_port = int(os.environ.get("PREDICTION_API_PORT", main_port + 1))
    
    print(f"📍 Main WebSocket Server: ws://0.0.0.0:{main_port}")
    print(f"📍 Prediction API: http://0.0.0.0:{api_port}")
    print("=" * 60)
    
    # Start services in separate threads
    ws_thread = Thread(target=run_websocket_server, daemon=True)
    api_thread = Thread(target=run_prediction_api, daemon=True)
    
    ws_thread.start()
    time.sleep(2)  # Give WebSocket server time to start
    api_thread.start()
    
    print("✅ All services started!")
    print("Press Ctrl+C to stop all services")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

