# 🎯 Real-time Behavior Prediction API

A production-ready FastAPI server for real-time behavior prediction and learning from journal entries.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the Model

```bash
python train_model.py
```

### 3. Start the API Server

```bash
python start_server.py
```

Or directly:

```bash
python api_server.py
```

### 4. Access the API

- **API Server**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc

## 📁 Project Structure

```
realtime_predictions/
├── api_server.py          # FastAPI server
├── train_model.py         # Model training script
├── start_server.py        # Easy startup script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── models/               # Trained models
│   └── realtime_behavior_model.pkl
├── data/                 # Data files
│   └── firestore_data.csv
├── services/             # Core prediction logic
│   └── predictor.py
└── docs/                 # Documentation
    └── API_README.md
```

## 🔧 Configuration

### Environment Variables

- `MODEL_PATH`: Path to the trained model (default: models/realtime_behavior_model.pkl)
- `DATA_PATH`: Path to the data file (default: data/firestore_data.csv)

### Server Options

```bash
python start_server.py --help
```

Options:
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload for development
- `--skip-checks`: Skip pre-flight checks

## 📚 API Endpoints

### Health & Status

- `GET /` - Health check
- `GET /health` - Health status
- `GET /status` - Model status and information

### Predictions

- `POST /predict` - Predict next journal entry
- `POST /learn` - Learn from new entry
- `GET /recent-entries` - Get recent entries
- `POST /evaluate` - Evaluate model performance
- `POST /retrain` - Retrain model

### Examples

- `GET /example/prediction` - Example prediction request
- `GET /example/learning` - Example learning request

## 🧪 Testing the API

### Using curl

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Make Prediction
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "recent_entries": [
      {
        "timestamp": "2024-01-15T08:00:00.000Z",
        "action": "Sleep",
        "description": "Good night sleep",
        "duration_minutes": 480
      }
    ]
  }'
```

#### Learn from Entry
```bash
curl -X POST "http://localhost:8000/learn" \
  -H "Content-Type: application/json" \
  -d '{
    "new_entry": {
      "timestamp": "2024-01-15T10:30:00.000Z",
      "action": "Workout",
      "description": "Morning exercise",
      "duration_minutes": 45
    },
    "recent_entries": []
  }'
```

### Using Python

```python
import requests

# Make a prediction
response = requests.post("http://localhost:8000/predict", json={
    "recent_entries": [
        {
            "timestamp": "2024-01-15T08:00:00.000Z",
            "action": "Sleep",
            "description": "Good night sleep",
            "duration_minutes": 480
        }
    ]
})

prediction = response.json()
print(f"Predicted: {prediction['predicted_action']}")
print(f"Confidence: {prediction['confidence']:.1%}")
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "start_server.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
docker build -t behavior-prediction-api .
docker run -p 8000:8000 behavior-prediction-api
```

## ☁️ Cloud Deployment

### Heroku

1. Create a `Procfile`:
```
web: python start_server.py --host 0.0.0.0 --port $PORT
```

2. Deploy:
```bash
git add .
git commit -m "Deploy behavior prediction API"
git push heroku main
```

### AWS EC2

1. Install dependencies:
```bash
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt
```

2. Start server:
```bash
python3 start_server.py --host 0.0.0.0 --port 8000
```

3. Configure security group to allow port 8000

### Google Cloud Run

1. Create `Dockerfile` (see above)
2. Build and deploy:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/behavior-prediction-api
gcloud run deploy --image gcr.io/PROJECT_ID/behavior-prediction-api --platform managed
```

## 📊 Model Information

- **Algorithm**: Random Forest Classifier
- **Accuracy**: 97.7% on training data
- **Features**: 16 temporal and behavioral features
- **Categories**: 9 action categories
- **Temporal Weighting**: Recent entries have more influence

## 🔒 Security Considerations

- CORS enabled for all origins (configure for production)
- No authentication implemented
- Input validation via Pydantic models
- Error handling with proper HTTP status codes

## 📈 Performance

- **Prediction latency**: ~10-50ms per request
- **Memory usage**: ~100-200MB
- **Concurrent requests**: Limited by uvicorn workers
- **Model size**: ~2-5MB

## 🛠️ Development

### Adding New Features

1. Modify `services/predictor.py` for core logic
2. Update `api_server.py` for API endpoints
3. Add tests and documentation
4. Update this README

### Debugging

```bash
# Start with reload for development
python start_server.py --reload

# Skip checks for debugging
python start_server.py --skip-checks
```

## 📝 Data Format

### Journal Entry

```json
{
  "timestamp": "2024-01-15T08:00:00.000Z",
  "action": "Sleep",
  "description": "Good night sleep",
  "duration_minutes": 480
}
```

### Prediction Request

```json
{
  "recent_entries": [
    {
      "timestamp": "2024-01-15T08:00:00.000Z",
      "action": "Sleep",
      "description": "Good night sleep",
      "duration_minutes": 480
    }
  ]
}
```

### Prediction Response

```json
{
  "predicted_action": "Work",
  "confidence": 0.741,
  "top_predictions": [
    {"action": "Work", "probability": 0.741},
    {"action": "Other", "probability": 0.105}
  ],
  "feature_importance": {
    "action_category_encoded": 0.463,
    "hour": 0.086
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## 🎯 Use Cases

1. **Journaling Apps**: Integrate behavior prediction
2. **Productivity Tools**: Predict next activities
3. **Health Monitoring**: Track daily routines
4. **Research**: Analyze behavior patterns
5. **Personal Assistants**: Provide intelligent suggestions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- **Documentation**: Check the interactive docs at `/docs`
- **Issues**: Create an issue on GitHub
- **Examples**: See `/example/prediction` and `/example/learning` endpoints

