# IoT Support Chatbot - Deployment Guide

This guide provides step-by-step instructions for deploying the IoT Support Chatbot to Google Cloud Platform (GCP) using Kubernetes and CircleCI.

## 📋 Prerequisites

### 1. Google Cloud Platform Setup
- GCP account with billing enabled
- Google Cloud SDK installed
- Required APIs enabled (see FULL_DOCUMENTATION.md in sample folder)

### 2. CircleCI Setup
- CircleCI account connected to your GitHub repository
- Environment variables configured in CircleCI

### 3. Local Development
- Docker installed
- Python 3.8+ installed
- MySQL database (optional for local testing)

## 🚀 Deployment Steps

### Step 1: GCP Project Setup

1. **Create GCP Project** (if not exists):
   ```bash
   gcloud projects create YOUR_PROJECT_ID
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Required APIs**:
   ```bash
   gcloud services enable container.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable iam.googleapis.com
   ```

3. **Create GKE Cluster**:
   ```bash
   gcloud container clusters create iot-support-cluster \
     --region=us-central1 \
     --num-nodes=1 \
     --machine-type=e2-medium
   ```

4. **Create Artifact Registry**:
   ```bash
   gcloud artifacts repositories create iot-support-repo \
     --repository-format=docker \
     --location=us-central1
   ```

### Step 2: Service Account Setup

1. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create iot-support-sa \
     --display-name="IoT Support Chatbot Service Account"
   ```

2. **Assign Roles**:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:iot-support-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/container.admin"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:iot-support-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:iot-support-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/artifactregistry.admin"
   ```

3. **Create and Download Key**:
   ```bash
   gcloud iam service-accounts keys create gcp-key.json \
     --iam-account=iot-support-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Convert to Base64** (for CircleCI):
   ```bash
   base64 -i gcp-key.json
   ```

### Step 3: CircleCI Configuration

1. **Add Environment Variables** to CircleCI:
   - `GCLOUD_SERVICE_KEY`: Base64 encoded service account key
   - `GOOGLE_PROJECT_ID`: Your GCP project ID
   - `GKE_CLUSTER`: `iot-support-cluster`
   - `GOOGLE_COMPUTE_REGION`: `us-central1`
   - `GROQ_API_KEY`: Your ChatGroq API key

2. **Push Code** to GitHub repository

3. **Monitor Deployment** in CircleCI dashboard

### Step 4: Kubernetes Secrets

1. **Create Kubernetes Secret** for API keys:
   ```bash
   kubectl create secret generic iot-support-secrets \
     --from-literal=GROQ_API_KEY=your_groq_api_key \
     --from-literal=MYSQL_HOST=your_mysql_host \
     --from-literal=MYSQL_USER=your_mysql_user \
     --from-literal=MYSQL_PASSWORD=your_mysql_password \
     --from-literal=MYSQL_DATABASE=your_mysql_database
   ```

### Step 5: Verify Deployment

1. **Check Pod Status**:
   ```bash
   kubectl get pods
   ```

2. **Check Service**:
   ```bash
   kubectl get services
   ```

3. **Get External IP**:
   ```bash
   kubectl get service iot-support-service
   ```

## 🔧 Configuration Files

### Dockerfile
- Multi-stage build for optimization
- Python 3.10 base image
- Installs system dependencies
- Copies application code
- Exposes port 5000

### kubernetes-deployment.yaml
- Deployment with 1 replica
- LoadBalancer service
- Environment variables from secrets
- Health checks and resource limits

### .circleci/config.yml
- Automated CI/CD pipeline
- Docker image build and push
- Kubernetes deployment
- Environment-specific configurations

## 🐛 Troubleshooting

### Issue: "Image pull failed"
**Solution**: Check Artifact Registry permissions and image name

### Issue: "Pod not starting"
**Solution**: Check logs with `kubectl logs <pod-name>`

### Issue: "Service not accessible"
**Solution**: Verify LoadBalancer configuration and firewall rules

### Issue: "Database connection failed"
**Solution**: Check MySQL credentials in Kubernetes secrets

### Issue: "API key not found"
**Solution**: Verify GROQ_API_KEY in Kubernetes secrets

## 📊 Monitoring

### Application Logs
```bash
kubectl logs -f deployment/iot-support-chatbot
```

### Service Status
```bash
kubectl get services iot-support-service
```

### Pod Status
```bash
kubectl get pods -l app=iot-support-chatbot
```

## 🔄 Updates and Rollbacks

### Update Application
1. Push new code to GitHub
2. CircleCI automatically builds and deploys
3. Monitor deployment status

### Rollback
```bash
kubectl rollout undo deployment/iot-support-chatbot
```

## 💡 Best Practices

1. **Use Environment Variables** for configuration
2. **Implement Health Checks** for reliability
3. **Set Resource Limits** to prevent resource exhaustion
4. **Use Secrets** for sensitive data
5. **Monitor Logs** regularly
6. **Test Locally** before deploying

## 📝 Next Steps

1. **Set up monitoring** (Prometheus/Grafana)
2. **Configure SSL/TLS** certificates
3. **Implement auto-scaling** based on load
4. **Set up backup** for database
5. **Configure alerts** for critical issues

## 🔗 Useful Commands

```bash
# Get cluster info
kubectl cluster-info

# View all resources
kubectl get all

# Describe deployment
kubectl describe deployment iot-support-chatbot

# Port forward for local testing
kubectl port-forward service/iot-support-service 8080:80

# View logs
kubectl logs -f deployment/iot-support-chatbot

# Scale deployment
kubectl scale deployment iot-support-chatbot --replicas=3
```

## 📚 Additional Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [CircleCI Documentation](https://circleci.com/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

**Note**: Replace `YOUR_PROJECT_ID` with your actual GCP project ID throughout this guide. 