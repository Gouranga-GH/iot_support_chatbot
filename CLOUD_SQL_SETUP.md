# Google Cloud SQL Setup Guide

## Step 1: Create Cloud SQL Instance

```bash
# Create a Cloud SQL instance
gcloud sql instances create iot-chatbot-db \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=your-root-password \
    --storage-type=SSD \
    --storage-size=10GB
```

## Step 2: Create Database and User

```bash
# Create the database
gcloud sql databases create iot_chatbot_db --instance=iot-chatbot-db

# Create a user for the application
gcloud sql users create iot-chatbot-user \
    --instance=iot-chatbot-db \
    --password=your-app-password
```

## Step 3: Get Connection Information

```bash
# Get the connection name
gcloud sql instances describe iot-chatbot-db --format="value(connectionName)"

# Get the public IP (if needed)
gcloud sql instances describe iot-chatbot-db --format="value(ipAddresses[0].ipAddress)"
```

## Step 4: Update CircleCI Environment Variables

In your CircleCI project settings, update these environment variables:

- `MYSQL_HOST`: Your Cloud SQL instance IP or connection name
- `MYSQL_USER`: `iot-chatbot-user`
- `MYSQL_PASSWORD`: `your-app-password`
- `MYSQL_DATABASE`: `iot_chatbot_db`
- `MYSQL_PORT`: `3306`

## Step 5: Configure Network Access

```bash
# Allow connections from GKE cluster
gcloud sql instances patch iot-chatbot-db \
    --authorized-networks=0.0.0.0/0
```

## Alternative: Use Cloud SQL Proxy (More Secure)

For better security, use Cloud SQL Proxy:

```bash
# Install Cloud SQL Proxy in your container
# Add to Dockerfile:
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /usr/local/bin/cloud_sql_proxy
RUN chmod +x /usr/local/bin/cloud_sql_proxy
```

Then update your connection to use the proxy. 