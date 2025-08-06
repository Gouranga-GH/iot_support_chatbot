# IoT Support Chatbot - Setup Guide

This guide will help you set up and run the IoT Support Chatbot properly.

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Environment File
Create a `.env` file in the root directory with at least:
```bash
GROQ_API_KEY=your_chatgroq_api_key_here
```

### Step 3: Test Database Connection
```bash
python test_db.py
```

This will test all database operations and confirm everything is working.

## 🔧 Full Setup (Production Mode)

### Step 1: Environment Configuration
Copy `env_template.txt` to `.env` and fill in your values:

```bash
# Copy template
cp env_template.txt .env

# Edit the .env file with your actual values
```

Required environment variables:
- `GROQ_API_KEY`: Your ChatGroq API key (get from https://console.groq.com/)
- `MYSQL_HOST`: MySQL database host
- `MYSQL_USER`: MySQL username
- `MYSQL_PASSWORD`: MySQL password
- `MYSQL_DATABASE`: Database name

### Step 2: Database Setup
If you want to use the full version with database:

1. Install MySQL
2. Create database: `CREATE DATABASE iot_chatbot_db;`
3. Update `.env` with your MySQL credentials

### Step 3: Test Database Connection
```bash
python test_db.py
```

This will test all database operations and confirm everything is working.

### Step 4: Run Application
```bash
python app.py
```

## 🎯 Running Options

### Option 1: Streamlit (Development)
```bash
streamlit run main.py
```
- Runs on port 8501
- Full Streamlit interface
- Good for development

### Option 2: Flask (Production)
```bash
python app.py
```
- Runs on port 5000
- Requires database setup
- Production ready

## 🔑 Getting ChatGroq API Key

1. Go to https://console.groq.com/
2. Sign up for a free account
3. Create an API key
4. Add it to your `.env` file:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

## 🐛 Troubleshooting

### Issue: "ChatGroq API key not found"
**Solution**: Add your GROQ_API_KEY to the `.env` file

### Issue: "Database connection failed"
**Solution**: 
1. Run `python test_db.py` to diagnose database issues
2. Check your MySQL credentials in `.env`
3. Ensure MySQL is running and accessible

### Issue: "Module not found"
**Solution**: Install dependencies with `pip install -r requirements.txt`

### Issue: "Port already in use"
**Solution**: Change port in the app file or kill existing process

### Issue: "Data not being saved to database"
**Solution**: 
1. Run `python test_db.py` to verify database connectivity
2. Check the console logs for database operation messages
3. Ensure MySQL is running and accessible

## 📝 Test the Chatbot

1. Open your browser to `http://localhost:5000`
2. Register with your email and phone
3. Start chatting!

### Sample Questions to Test:
- "What IoT products do you support?"
- "Tell me about the Smart Home Hub"
- "How does the Security Camera System work?"
- "What are the features of the Smart Thermostat?"

## 🔄 Switching Between Modes

### Development Mode (Streamlit)
```bash
streamlit run main.py
```

### Production Mode (Flask)
```bash
python app.py
```

## 📊 Status Check

Visit `http://localhost:5000/api/status` to check:
- Database connection status
- RAG chain availability
- Document processor status

## 🎯 Next Steps

1. **Set up your GROQ API key** for full AI capabilities
2. **Test database connectivity** with `python test_db.py`
3. **Configure database** (optional) for production use
4. **Deploy to production** using the deployment files

## 💡 Tips

- The chatbot works best with a GROQ API key
- Both Streamlit and Flask versions use the same backend logic
- Check console logs for detailed operation tracking
- Use `test_db.py` to verify database functionality before running the full app 