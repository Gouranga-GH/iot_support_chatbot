# IoT Support Chatbot - Setup Guide

This guide will help you set up and run the IoT Support Chatbot with Google Cloud SQL.

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Google Cloud SQL
Follow the [CLOUD_SQL_SETUP.md](CLOUD_SQL_SETUP.md) guide to create your Cloud SQL instance.

### Step 3: Configure Environment Variables
Create a `.env` file with your Cloud SQL details:
```bash
# Copy the template
cp env_template.txt .env
```

Update the `.env` file with your Cloud SQL credentials:
```env
# Cloud SQL Connection Details
MYSQL_HOST=your_cloud_sql_public_ip
MYSQL_USER=iot-chatbot-user
MYSQL_PASSWORD=your_cloud_sql_password
MYSQL_DATABASE=iot_chatbot_db
MYSQL_PORT=3306

# API Keys
GROQ_API_KEY=your_groq_api_key

# Application Settings
DEBUG=True
FEEDBACK_INTERVAL=3
```

### Step 4: Test Database Connection
```bash
python test_db.py
```

This will test all database operations and confirm everything is working.

## 🔧 Full Setup (Production Mode)

### Step 1: Google Cloud SQL Setup
1. Create Cloud SQL instance (see [CLOUD_SQL_SETUP.md](CLOUD_SQL_SETUP.md))
2. Create database and user
3. Configure network access
4. Get connection details

### Step 2: Configure CircleCI Environment Variables
In your CircleCI project settings, add these environment variables:
- `GROQ_API_KEY`
- `MYSQL_HOST` (your Cloud SQL public IP)
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `MYSQL_PORT`
- `DEBUG`
- `FEEDBACK_INTERVAL`

### Step 3: Test Database Connection
```bash
python test_db.py
```

This will test all database operations and confirm everything is working.

### Step 4: Run Application
```bash
python app.py
```

## 💻 Running Options

### Option 1: Streamlit (Development)
```bash
streamlit run main.py
```
- Runs on port 8501
- Good for development

### Option 2: Flask (Production)
```bash
python app.py
```
- Runs on port 5000
- Requires Cloud SQL setup
- Production-ready

## 🔧 Troubleshooting

### Issue: "Database connection failed"
**Solution**: 
1. Run `python test_db.py` to diagnose database issues
2. Check your Cloud SQL configuration
3. Verify network access is configured

### Issue: "Module not found"
**Solution**: Run `pip install -r requirements.txt`

### Issue: "Port already in use"
**Solution**: Change port in the app file or kill existing process

### Issue: "Data not being saved to database"
**Solution**: 
1. Run `python test_db.py` to verify database connectivity
2. Check the console logs for database operation messages
3. Ensure Cloud SQL is running and accessible

### Issue: "Can't connect to MySQL server"
**Solution**:
1. Check your Cloud SQL public IP in `.env` file
2. Verify network access is configured in Cloud SQL
3. Ensure the instance is running

## 📝 Test the Chatbot

1. **Set up your GROQ API key** for full AI capabilities
2. **Configure Cloud SQL** following the setup guide
3. **Test database connectivity** with `python test_db.py`
4. **Deploy to production** using the deployment files

## 💡 Tips

- Both Streamlit and Flask versions use the same backend logic
- Check console logs for detailed operation tracking
- Use `test_db.py` to verify database functionality before running the full app
- Cloud SQL is required for production deployment
- Local testing requires proper network access configuration

## 🚀 Deployment

For production deployment, follow the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) which includes:
- Docker containerization
- Google Kubernetes Engine (GKE) deployment
- CircleCI CI/CD pipeline
- Environment variable management 