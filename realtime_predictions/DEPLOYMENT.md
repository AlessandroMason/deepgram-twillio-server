# 🚀 Deployment Guide

This guide covers different ways to deploy the Real-time Behavior Prediction API.

## 📋 Prerequisites

- Python 3.9+
- pip package manager
- Data file: `data/firestore_data.csv`
- Trained model: `models/realtime_behavior_model.pkl`

## 🏠 Local Development

### 1. Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Train the model
python train_model.py

# Start the server
python start_server.py
```

### 2. Development Mode

```bash
# Start with auto-reload
python start_server.py --reload

# Skip pre-flight checks
python start_server.py --skip-checks
```

## 🐳 Docker Deployment

### 1. Build and Run

```bash
# Build the image
docker build -t behavior-prediction-api .

# Run the container
docker run -p 8000:8000 behavior-prediction-api
```

### 2. Docker Compose

```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ☁️ Cloud Deployment

### Heroku

1. **Create Heroku App**
```bash
heroku create your-app-name
```

2. **Create Procfile**
```
web: python start_server.py --host 0.0.0.0 --port $PORT
```

3. **Deploy**
```bash
git add .
git commit -m "Deploy behavior prediction API"
git push heroku main
```

4. **View Logs**
```bash
heroku logs --tail
```

### AWS EC2

1. **Launch EC2 Instance**
   - Ubuntu 20.04 LTS
   - t3.micro or larger
   - Security group: Allow port 8000

2. **Connect and Setup**
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3-pip python3-venv -y

# Clone your repository
git clone https://github.com/your-username/your-repo.git
cd your-repo/realtime_predictions

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Train model
python train_model.py

# Start server
python start_server.py --host 0.0.0.0 --port 8000
```

3. **Run as Service**
```bash
# Create systemd service
sudo nano /etc/systemd/system/behavior-prediction.service
```

Service file content:
```ini
[Unit]
Description=Behavior Prediction API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/your-repo/realtime_predictions
Environment=PATH=/home/ubuntu/your-repo/realtime_predictions/venv/bin
ExecStart=/home/ubuntu/your-repo/realtime_predictions/venv/bin/python start_server.py --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable behavior-prediction
sudo systemctl start behavior-prediction
sudo systemctl status behavior-prediction
```

### Google Cloud Run

1. **Create Dockerfile** (already included)

2. **Build and Deploy**
```bash
# Set project ID
export PROJECT_ID=your-project-id

# Build image
gcloud builds submit --tag gcr.io/$PROJECT_ID/behavior-prediction-api

# Deploy to Cloud Run
gcloud run deploy behavior-prediction-api \
  --image gcr.io/$PROJECT_ID/behavior-prediction-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000
```

### DigitalOcean App Platform

1. **Create App Spec**
```yaml
name: behavior-prediction-api
services:
- name: api
  source_dir: /realtime_predictions
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python start_server.py --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8000
  routes:
  - path: /
  envs:
  - key: PORT
    value: "8000"
```

2. **Deploy**
```bash
doctl apps create --spec app.yaml
```

## 🔧 Configuration

### Environment Variables

```bash
# Model and data paths
export MODEL_PATH=models/realtime_behavior_model.pkl
export DATA_PATH=data/firestore_data.csv

# Server configuration
export HOST=0.0.0.0
export PORT=8000
```

### Production Settings

```bash
# Start with production settings
python start_server.py --host 0.0.0.0 --port 8000

# Or use gunicorn for production
pip install gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📊 Monitoring

### Health Checks

```bash
# Check API health
curl http://your-server:8000/health

# Check model status
curl http://your-server:8000/status
```

### Logs

```bash
# Docker logs
docker logs behavior-prediction-api

# Docker Compose logs
docker-compose logs -f

# Systemd logs
sudo journalctl -u behavior-prediction -f
```

## 🔒 Security

### Production Security Checklist

- [ ] Change CORS origins from `*` to specific domains
- [ ] Add API key authentication
- [ ] Enable HTTPS/TLS
- [ ] Set up rate limiting
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets
- [ ] Regular security updates

### Example Security Configuration

```python
# In api_server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🚨 Troubleshooting

### Common Issues

1. **Model not found**
   ```bash
   # Train the model first
   python train_model.py
   ```

2. **Port already in use**
   ```bash
   # Use different port
   python start_server.py --port 8001
   ```

3. **Permission denied**
   ```bash
   # Make scripts executable
   chmod +x *.py
   ```

4. **Dependencies missing**
   ```bash
   # Install requirements
   pip install -r requirements.txt
   ```

### Debug Mode

```bash
# Start with debug logging
python start_server.py --reload --skip-checks
```

## 📈 Scaling

### Horizontal Scaling

1. **Load Balancer**
   - Use nginx or HAProxy
   - Distribute traffic across multiple instances

2. **Container Orchestration**
   - Kubernetes
   - Docker Swarm
   - AWS ECS

3. **Database Integration**
   - Store predictions in database
   - Cache frequently used data
   - Use Redis for session storage

### Performance Optimization

1. **Model Optimization**
   - Use smaller model for faster inference
   - Implement model quantization
   - Cache predictions

2. **API Optimization**
   - Add response caching
   - Implement async processing
   - Use connection pooling

## 📞 Support

- **Documentation**: Check `/docs` endpoint
- **Health Check**: `/health` endpoint
- **Status**: `/status` endpoint
- **Examples**: `/example/prediction` and `/example/learning`

## 🎯 Next Steps

1. **Add Authentication**: Implement API key or JWT authentication
2. **Database Integration**: Store predictions and learnings
3. **Monitoring**: Add Prometheus metrics
4. **Alerting**: Set up alerts for failures
5. **CI/CD**: Automate deployment pipeline


