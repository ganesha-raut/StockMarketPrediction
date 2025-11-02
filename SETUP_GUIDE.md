# 🚀 Complete Setup Guide - AI Stock Market Prediction Platform

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [First Run](#first-run)
5. [Adding Stocks](#adding-stocks)
6. [Training Models](#training-models)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### Required Software
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **pip** (comes with Python)
- **Git** (optional) - [Download](https://git-scm.com/downloads)

### Required API Keys
- **Gemini AI API Key** - [Get it here](https://makersuite.google.com/app/apikey)
- **Gmail App Password** (for email notifications)

---

## 2. Installation Steps

### Step 1: Open Terminal/Command Prompt
```bash
# Navigate to project directory
cd "C:\Users\GANESH RAUT\Desktop\Prediction"
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

This will install all required packages. It may take 5-10 minutes.

---

## 3. Configuration

### Step 1: Create .env File
Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Step 2: Edit .env File
Open `.env` in a text editor and configure:

#### A. Flask Configuration
```env
SECRET_KEY=your-random-secret-key-here-change-this-to-something-secure
FLASK_ENV=development
DEBUG=True
```

Generate a secure secret key:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

#### B. Email Configuration (Gmail)

**Get Gmail App Password:**
1. Go to [Google Account](https://myaccount.google.com/)
2. Security → 2-Step Verification (enable if not enabled)
3. App Passwords → Generate
4. Select "Mail" and "Windows Computer"
5. Copy the 16-character password

**Update .env:**
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

#### C. Gemini AI Configuration

**Get API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

**Update .env:**
```env
GEMINI_API_KEY=your-gemini-api-key-here
```

#### D. App Settings
```env
APP_NAME=AI Stock Market Prediction
PRICE_UPDATE_INTERVAL=10
MODEL_RETRAIN_INTERVAL=86400
```

---

## 4. First Run

### Method 1: Using Quick Start Script (Recommended)
```bash
python run.py
```

This will:
- Check all requirements
- Initialize database
- Create default admin user
- Start the application

### Method 2: Manual Start
```bash
# Initialize database
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()

# Start application
python app.py
```

### Access the Application
Open your browser and go to:
```
http://localhost:5000
```

### Default Admin Login
```
Email: admin@stockai.com
Password: admin123
```

**⚠️ IMPORTANT: Change this password immediately!**

---

## 5. Adding Stocks

### Method 1: Admin Panel (Recommended for Testing)

1. **Login as Admin**
   - Go to http://localhost:5000/auth/login
   - Use admin credentials

2. **Navigate to Stocks**
   - Click "Stocks" in admin menu

3. **Add Stock**
   - Click "Add Stock" button
   - Enter:
     - Symbol: `TCS` (or any NSE stock)
     - Name: `Tata Consultancy Services`
     - Sector: `IT`
   - Click "Save"

4. **Download Historical Data**
   - Find the stock in list
   - Click "Download Data" button
   - Wait for download to complete (5 years of data)

5. **Train Model**
   - Click "Train Model" button
   - Wait for training (may take 2-5 minutes)
   - Check training status

### Method 2: Upload CSV

**CSV Format Required:**
```csv
Date,Open,High,Low,Close,Volume,Dividend
2019-01-01,1250.50,1275.00,1240.00,1270.00,5000000,0
2019-01-02,1270.00,1280.00,1265.00,1275.00,4500000,0
...
```

**Steps:**
1. Prepare CSV with at least 100 rows (preferably 5 years)
2. Admin Panel → Stocks → Select Stock
3. Click "Upload CSV"
4. Select file and upload
5. Click "Train Model"

### Recommended Stocks to Add
```
TCS - Tata Consultancy Services
RELIANCE - Reliance Industries
HDFCBANK - HDFC Bank
INFY - Infosys
ICICIBANK - ICICI Bank
WIPRO - Wipro
SBIN - State Bank of India
ITC - ITC Limited
BHARTIARTL - Bharti Airtel
HINDUNILVR - Hindustan Unilever
```

---

## 6. Training Models

### Training Process

**What Happens During Training:**
1. Data preprocessing (cleaning, normalization)
2. Feature engineering (30+ technical indicators)
3. Sentiment analysis (from news)
4. Model training (Linear Regression/LSTM)
5. Performance evaluation
6. Model saving

**Training Time:**
- Small dataset (100-500 rows): 30 seconds - 1 minute
- Medium dataset (500-1000 rows): 1-3 minutes
- Large dataset (1000+ rows): 3-5 minutes

**Performance Metrics:**
- **Accuracy**: 70-85% is good
- **MAE** (Mean Absolute Error): Lower is better
- **RMSE** (Root Mean Square Error): Lower is better

### Monitoring Training

**Check Training Status:**
1. Admin Panel → Stocks
2. Look for "Model Status" column
3. Green = Trained, Red = Not Trained

**View Training Logs:**
- Check console output
- Look for training metrics

---

## 7. Testing

### Test User Registration

1. **Logout** from admin account
2. **Go to Register** page
3. **Fill form:**
   - Username: `testuser`
   - Email: `your-test-email@gmail.com`
   - Password: `test123`
4. **Check email** for OTP
5. **Verify OTP**
6. **Login** with new credentials

### Test Stock Prediction

1. **Login as user**
2. **Go to Home** page
3. **View AI Suggestions** (should show 4 stocks)
4. **Click "Predict"** on any stock
5. **Select prediction type:**
   - Intraday (for same day)
   - Long-term (for next day)
6. **View results:**
   - Predicted price
   - Confidence score
   - Recommendation (BUY/SELL/HOLD)
   - Risk percentage
   - AI insights

### Test Watchlist

1. **Click star icon** on any stock
2. **Go to Watchlist** page
3. **Set notification:**
   - Target price
   - Email alerts ON
   - Drop threshold: 5%
4. **Save settings**

### Test Chatbot

1. **Click chatbot icon** (bottom right)
2. **Ask questions:**
   - "What is the price of TCS?"
   - "Should I buy RELIANCE?"
   - "Predict INFY for tomorrow"
3. **Check responses**

### Test Email Notifications

1. **Set up notification** for a stock
2. **Wait for trigger** (or manually trigger in admin)
3. **Check email** inbox
4. **Verify notification** received

---

## 8. Troubleshooting

### Issue: Packages Not Installing

**Solution:**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install packages one by one
pip install Flask
pip install Flask-SQLAlchemy
pip install pandas
# ... etc
```

### Issue: Email Not Sending

**Possible Causes:**
1. Wrong Gmail credentials
2. App password not generated
3. 2FA not enabled
4. Firewall blocking

**Solution:**
```bash
# Test email manually
python
>>> from flask_mail import Mail, Message
>>> from app import create_app
>>> app = create_app()
>>> mail = Mail(app)
>>> with app.app_context():
...     msg = Message('Test', recipients=['your-email@gmail.com'])
...     msg.body = 'Test email'
...     mail.send(msg)
```

### Issue: Gemini AI Not Working

**Possible Causes:**
1. Invalid API key
2. API quota exceeded
3. Network issues

**Solution:**
```bash
# Test API key
python
>>> import google.generativeai as genai
>>> genai.configure(api_key='your-key')
>>> model = genai.GenerativeModel('gemini-pro')
>>> response = model.generate_content('Hello')
>>> print(response.text)
```

### Issue: Stock Data Not Loading

**Possible Causes:**
1. Google Finance blocking requests
2. Network issues
3. Invalid stock symbol

**Solution:**
```bash
# Test data fetching
python
>>> from utils.stock_data import get_google_stock_data
>>> data = get_google_stock_data('TCS')
>>> print(data)
```

### Issue: Model Training Fails

**Possible Causes:**
1. Insufficient data (< 100 rows)
2. Missing columns in CSV
3. Invalid data format

**Solution:**
1. Check data has at least 100 rows
2. Verify CSV columns: Date, Open, High, Low, Close, Volume
3. Check for NaN values
4. Review error logs

### Issue: Port 5000 Already in Use

**Solution:**
```bash
# Windows - Kill process
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Or use different port
python app.py --port 8000
```

### Issue: Database Locked

**Solution:**
```bash
# Delete database and recreate
rm stock_prediction.db
python run.py
```

---

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All packages installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] Gmail app password generated
- [ ] Gemini API key obtained
- [ ] Database initialized (`python run.py`)
- [ ] Application running (http://localhost:5000)
- [ ] Admin login successful
- [ ] At least 1 stock added
- [ ] Historical data downloaded
- [ ] Model trained successfully
- [ ] User registration tested
- [ ] Prediction tested
- [ ] Email notification tested

---

## 📞 Need Help?

### Common Commands Reference

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt

# Start application
python run.py
# OR
python app.py

# Initialize database
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()

# Check Python version
python --version

# Check pip version
pip --version

# List installed packages
pip list

# Deactivate virtual environment
deactivate
```

---

## 🚀 Next Steps

After successful setup:

1. **Add more stocks** (10-20 recommended)
2. **Train all models**
3. **Create test user account**
4. **Test all features**
5. **Configure email notifications**
6. **Customize settings** in admin panel
7. **Monitor background tasks**
8. **Review logs** for errors

---

## ⚠️ Important Notes

1. **Never commit `.env` file** to version control
2. **Change admin password** immediately
3. **Use strong passwords** for all accounts
4. **Keep API keys secure**
5. **Backup database** regularly
6. **Monitor API usage** (Gemini has limits)
7. **Test email** before going live
8. **Review logs** regularly

---

**Happy Predicting! 📈**
