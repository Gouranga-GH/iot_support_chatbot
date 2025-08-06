# IoT Support Chatbot - Deployment Guide

This guide provides step-by-step instructions for deploying the IoT Support Chatbot to Google Cloud Platform (GCP) using Google Kubernetes Engine (GKE) and CircleCI.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CircleCI      │    │   Google Cloud  │    │   Cloud SQL     │
│   CI/CD         │───▶│   Kubernetes    │───▶│   MySQL         │
│   Pipeline      │    │   Engine (GKE)  │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### 1. Google Cloud Platform Setup
- Google Cloud account with billing enabled
- Google Cloud CLI installed (optional, web console works too)
- Project with required APIs enabled

### 2. Required GCP APIs
Enable these APIs in your Google Cloud Console:
- Kubernetes Engine API
- Container Registry API
- Compute Engine API
- Cloud Build API
- Cloud Storage API
- IAM API

### 3. CircleCI Setup
- CircleCI account connected to your GitHub repository
- Project configured in CircleCI

## 🚀 Step-by-Step Deployment

### Step 1: Google Cloud SQL Setup

Follow the [CLOUD_SQL_SETUP.md](CLOUD_SQL_SETUP.md) guide to:
1. Create Cloud SQL MySQL instance
2. Create database and user
3. Configure network access
4. Get connection details

### Step 2: Configure CircleCI Environment Variables

In your CircleCI project settings, add these environment variables:

#### GCP Configuration
```
GCLOUD_SERVICE_KEY=[Base64 encoded service account key]
GOOGLE_PROJECT_ID=[Your GCP project ID]
GKE_CLUSTER=[Your GKE cluster name]
GOOGLE_COMPUTE_REGION=[Your region, e.g., us-central1]
```

#### Application Configuration
```
GROQ_API_KEY=[Your Groq API key]
MYSQL_HOST=[Cloud SQL public IP]
MYSQL_USER=[Cloud SQL username]
MYSQL_PASSWORD=[Cloud SQL password]
MYSQL_DATABASE=[Database name]
MYSQL_PORT=3306
DEBUG=true
FEEDBACK_INTERVAL=3
```

### Step 3: Create GCP Service Account

1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Create a new service account with these roles:
   - Kubernetes Engine Admin
   - Storage Admin
   - Cloud Build Service Account
   - Container Registry Service Agent

3. Download the JSON key and encode it to base64:
   ```bash
   # On Windows:
   certutil -encode gcp-key.json gcp-key.txt
   
   # On Linux/Mac:
   base64 -i gcp-key.json
   ```

4. Add the base64 encoded key to CircleCI as `GCLOUD_SERVICE_KEY`

### Step 4: Create GKE Cluster

1. Go to Google Cloud Console → Kubernetes Engine
2. Click "Create Cluster"
3. Configure:
   - **Name**: `iot-chatbot-cluster`
   - **Region**: `us-central1`
   - **Zone**: Any zone in us-central1
   - **Machine type**: `e2-medium` (2 vCPU, 4 GB RAM)
   - **Node count**: 1-3 nodes

### Step 5: Push Code to GitHub

```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 6: Monitor CircleCI Build

1. Go to your CircleCI project
2. Monitor the build process:
   - **Build Docker Image**: Creates and pushes container image
   - **Deploy to GKE**: Deploys application to Kubernetes

### Step 7: Access Your Application

1. Get the LoadBalancer IP:
   ```bash
   kubectl get service iot-support-service
   ```

2. Access your application at: `http://[LOAD_BALANCER_IP]`

## 🔧 Configuration Files

### Dockerfile
```dockerfile
FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential curl default-mysql-client
COPY . .
RUN pip install --no-cache-dir -e .
EXPOSE 5000
CMD ["sh", "-c", "python debug_env.py && python app.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iot-support-chatbot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: iot-support-chatbot
  template:
    metadata:
      labels:
        app: iot-support-chatbot
    spec:
      containers:
      - name: iot-support-chatbot
        image: us-central1-docker.pkg.dev/[PROJECT_ID]/iot-support-repo/iot-support-chatbot:latest
        ports:
        - containerPort: 5000
        env:
        - name: GROQ_API_KEY
          value: "${GROQ_API_KEY}"
        - name: MYSQL_HOST
          value: "${MYSQL_HOST}"
        - name: MYSQL_USER
          value: "${MYSQL_USER}"
        - name: MYSQL_PASSWORD
          value: "${MYSQL_PASSWORD}"
        - name: MYSQL_DATABASE
          value: "${MYSQL_DATABASE}"
        - name: MYSQL_PORT
          value: "${MYSQL_PORT}"
        - name: DEBUG
          value: "${DEBUG}"
        - name: FEEDBACK_INTERVAL
          value: "${FEEDBACK_INTERVAL}"
```

### CircleCI Configuration
```yaml
version: 2.1
executors:
  docker-executor:
    docker:
      - image: cimg/base:2024.01
    working_directory: ~/repo

jobs:
  build_docker_image:
    executor: docker-executor
    steps:
      - checkout
      - setup_remote_docker
      - run:
          name: Install Google Cloud SDK
          command: |
            echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
            curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
            sudo apt-get update && sudo apt-get install google-cloud-cli -y
      - run:
          name: Authenticate with google cloud
          command: |
              echo "$GCLOUD_SERVICE_KEY" | base64 --decode > gcp-key.json
              gcloud auth activate-service-account --key-file=gcp-key.json
              gcloud auth configure-docker us-central1-docker.pkg.dev || gcloud auth configure-docker
      - run:
          name: Build and Push Image
          command: |
              docker build -t us-central1-docker.pkg.dev/$GOOGLE_PROJECT_ID/iot-support-repo/iot-support-chatbot:latest .
              docker push us-central1-docker.pkg.dev/$GOOGLE_PROJECT_ID/iot-support-repo/iot-support-chatbot:latest

  deploy_to_gke:
    executor: docker-executor
    steps:
      - checkout
      - setup_remote_docker
      - run:
          name: Install Google Cloud SDK and kubectl
          command: |
            echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
            curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
            sudo apt-get update && sudo apt-get install google-cloud-cli kubectl google-cloud-cli-gke-gcloud-auth-plugin -y
            echo 'export USE_GKE_GCLOUD_AUTH_PLUGIN=True' >> $BASH_ENV
      - run:
          name: Authenticate with google cloud
          command: |
              echo "$GCLOUD_SERVICE_KEY" | base64 --decode > gcp-key.json
              gcloud auth activate-service-account --key-file=gcp-key.json
              gcloud auth configure-docker us-central1-docker.pkg.dev || gcloud auth configure-docker
      - run:
          name: Configure GKE
          command: |
              gcloud container clusters get-credentials $GKE_CLUSTER --region $GOOGLE_COMPUTE_REGION --project $GOOGLE_PROJECT_ID
      - run:
          name: Substitute environment variables
          command: |
              envsubst < kubernetes-deployment.yaml > kubernetes-deployment-substituted.yaml
      - run:
          name: Deploy to GKE
          command: |
              kubectl apply -f kubernetes-deployment-substituted.yaml --validate=false
              kubectl rollout restart deployment iot-support-chatbot

workflows:
  version: 2
  deploy_pipeline:
    jobs:
      - build_docker_image
      - deploy_to_gke:
          requires:
            - build_docker_image
```

## 🔍 Troubleshooting

### Build Failures

#### Issue: "docker: command not found"
**Solution**: The CircleCI configuration uses `cimg/base:2024.01` which includes Docker.

#### Issue: "kubectl: command not found"
**Solution**: The configuration installs kubectl explicitly.

#### Issue: "gke-gcloud-auth-plugin not found"
**Solution**: The configuration installs the GKE auth plugin.

### Deployment Failures

#### Issue: "Can't connect to MySQL server"
**Solution**:
1. Verify Cloud SQL instance is running
2. Check network access configuration
3. Verify environment variables are set correctly

#### Issue: "Image pull failed"
**Solution**:
1. Check if the Docker image was built successfully
2. Verify the image repository path
3. Check authentication with Container Registry

### Application Issues

#### Issue: "Environment variables not found"
**Solution**:
1. Check CircleCI environment variables are set
2. Verify `envsubst` is working correctly
3. Check the substituted Kubernetes deployment file

#### Issue: "Application crashes on startup"
**Solution**:
1. Check application logs: `kubectl logs <pod-name>`
2. Verify database connection
3. Check environment variable loading

## 📊 Monitoring

### Check Application Status
```bash
# Get pod status
kubectl get pods

# Check application logs
kubectl logs <pod-name>

# Get service information
kubectl get services
```

### Check Database Connection
```bash
# Test database connectivity from pod
kubectl exec <pod-name> -- python -c "
import os
print('MYSQL_HOST:', os.getenv('MYSQL_HOST'))
print('MYSQL_USER:', os.getenv('MYSQL_USER'))
print('MYSQL_DATABASE:', os.getenv('MYSQL_DATABASE'))
"
```

## 🧹 Cleanup

### Remove Application
```bash
kubectl delete deployment iot-support-chatbot
kubectl delete service iot-support-service
```

### Remove Cloud SQL Instance
1. Go to Google Cloud Console → SQL
2. Select your instance
3. Click "Delete"

### Remove GKE Cluster
1. Go to Google Cloud Console → Kubernetes Engine
2. Select your cluster
3. Click "Delete"

## 💰 Cost Optimization

### Estimated Monthly Costs
- **GKE Cluster**: $50-100/month (depending on node count)
- **Cloud SQL**: $25-50/month (db-f1-micro instance)
- **Container Registry**: $5-10/month (storage)
- **Load Balancer**: $20-30/month

### Cost Reduction Tips
1. Use `db-f1-micro` for Cloud SQL (smallest instance)
2. Reduce GKE node count to 1 for testing
3. Delete resources when not in use
4. Use preemptible nodes for non-production workloads

## 🎯 Next Steps

1. **Monitor the application** for performance and errors
2. **Set up logging** with Google Cloud Logging
3. **Configure monitoring** with Google Cloud Monitoring
4. **Set up alerts** for critical issues
5. **Implement auto-scaling** based on traffic
6. **Add SSL/TLS** for production security 