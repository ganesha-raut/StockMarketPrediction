# 🚀 AI Stock Market Prediction Platform

A comprehensive full-stack web application for AI-powered stock market prediction with real-time data, machine learning models, and automated notifications.

## 📋 Features

### User Panel
- **🔐 Authentication System**
  - Email registration with OTP verification
  - Secure login with password hashing
  - Password reset functionality
  - Remember me option

- **📊 Live Market Data**
  - Real-time stock prices from Google Finance
  - Market status indicator (Open/Closed)
  - Live price updates every 10 seconds
  - Day high/low, volume, market cap

- **🤖 AI-Powered Predictions**
  - Machine learning models (LSTM/Linear Regression)
  - Technical indicators (RSI, MACD, Bollinger Bands)
  - Sentiment analysis from news
  - Confidence scores and risk assessment
  - Intraday and long-term predictions

- **⭐ Watchlist Management**
  - Add/remove stocks to watchlist
  - Live price updates for watched stocks
  - Quick access to predictions

- **🔔 Smart Notifications**
  - Email alerts for price targets
  - Buy/Sell signals based on AI predictions
  - Large drop alerts (configurable threshold)
  - Notification history

- **💬 AI Chatbot**
  - Powered by Gemini AI
  - Stock-specific queries
  - Market insights and advice
  - Natural language interaction

- **📈 Stock Analysis**
  - Interactive candlestick charts
  - Historical data visualization
  - News sentiment analysis
  - Technical indicators

### Admin Panel
- **👥 User Management**
  - View all registered users
  - Activate/deactivate accounts
  - User statistics

- **📊 Stock Management**
  - Add new stocks manually
  - Upload historical data (CSV)
  - Download data from Yahoo Finance
  - Train ML models

- **🧠 Model Training**
  - Automated model training
  - Performance metrics (MAE, RMSE, Accuracy)
  - Model versioning
  - Training history

- **📧 Email Configuration**
  - Configurable SMTP settings
  - Test email functionality
  - Update email credentials

## 🛠️ Tech Stack

### Backend
- **Framework:** Flask (Python)
- **Database:** SQLite (easily upgradable to PostgreSQL/MySQL)
- **ORM:** SQLAlchemy
- **Authentication:** Flask-Login, Bcrypt
- **Email:** Flask-Mail (SMTP)
- **Scheduler:** APScheduler

### Machine Learning
- **Libraries:** scikit-learn, TensorFlow/Keras, pandas, numpy
- **Models:** Linear Regression, LSTM (configurable)
- **Features:** Technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands)
- **Analysis:** TA-Lib for technical analysis

### AI Integration
- **Gemini AI:** Stock suggestions, chatbot, sentiment analysis
- **News Scraping:** BeautifulSoup for Google Finance

### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap 5:** Responsive design
- **jQuery:** AJAX requests
- **Chart.js:** Data visualization
- **Font Awesome:** Icons

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
cd Desktop/Prediction
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-this
FLASK_ENV=development
DEBUG=True

# Database
DATABASE_URI=sqlite:///stock_prediction.db

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Gemini AI API
GEMINI_API_KEY=your-gemini-api-key-here

# App Settings
APP_NAME=AI Stock Market Prediction
PRICE_UPDATE_INTERVAL=10
MODEL_RETRAIN_INTERVAL=86400
```

### Step 5: Initialize Database
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Step 6: Run the Application
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## 🔑 Default Admin Credentials
- **Email:** admin@stockai.com
- **Password:** admin123

**⚠️ Important:** Change these credentials immediately after first login!

## 📧 Email Setup (Gmail)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"
3. Use the generated password in `.env` file

## 🤖 Gemini AI Setup

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env` file as `GEMINI_API_KEY`

## 📊 Adding Stocks

### Method 1: Admin Panel
1. Login as admin
2. Go to Stocks Management
3. Click "Add Stock"
4. Enter symbol (e.g., TCS, RELIANCE) and name

### Method 2: Upload CSV
1. Prepare CSV with columns: Date, Open, High, Low, Close, Volume
2. Upload via Admin Panel
3. Click "Train Model"

### Method 3: Auto-Download
1. Click "Download Data" in Admin Panel
2. System fetches 5 years of data from Yahoo Finance
3. Click "Train Model"

## 🧠 Model Training

The ML model uses:
- **Historical price data** (5 years recommended)
- **Technical indicators** (RSI, MACD, SMA, EMA, Bollinger Bands)
- **Volume analysis**
- **News sentiment** (from Gemini AI)
- **Dividend data**

Training process:
1. Feature engineering (30+ features)
2. Data normalization
3. Train/test split (80/20)
4. Model training
5. Performance evaluation
6. Model saving

## 🔄 Background Tasks

### Notification Monitoring (Every 5 minutes)
- Checks price targets
- Monitors for large drops
- Sends AI prediction alerts
- Email notifications

### Prediction Updates (Daily at 4 PM)
- Updates predictions with actual prices
- Calculates prediction accuracy
- Continuous learning

### Model Retraining (Weekly - Sunday 2 AM)
- Downloads latest data
- Retrains models
- Updates model versions

## 📁 Project Structure

```
Prediction/
├── app.py                 # Main application
├── config.py             # Configuration
├── models.py             # Database models
├── requirements.txt      # Dependencies
├── .env                  # Environment variables
│
├── routes/               # API routes
│   ├── auth.py          # Authentication
│   ├── user.py          # User panel
│   ├── admin.py         # Admin panel
│   └── api.py           # API endpoints
│
├── utils/                # Utility modules
│   ├── stock_data.py    # Stock data fetching
│   ├── ml_model.py      # ML prediction model
│   ├── gemini_ai.py     # Gemini AI integration
│   ├── email_service.py # Email notifications
│   └── scheduler.py     # Background tasks
│
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── user/
│   └── admin/
│
├── static/               # Static files (CSS, JS, images)
├── uploads/              # Uploaded CSV files
├── models/               # Trained ML models
└── data/                 # Historical data
```

## 🔒 Security Features

- Password hashing with bcrypt
- OTP-based email verification
- Session management
- CSRF protection
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection
- Secure password reset

## 🚀 Deployment

### Production Checklist
1. Change `SECRET_KEY` to a strong random value
2. Set `DEBUG=False`
3. Use production database (PostgreSQL/MySQL)
4. Configure proper SMTP server
5. Set up HTTPS/SSL
6. Use production WSGI server (Gunicorn/uWSGI)
7. Configure reverse proxy (Nginx/Apache)
8. Set up monitoring and logging

### Example Production Command
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 📈 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/verify-otp` - Verify OTP
- `POST /auth/forgot-password` - Password reset

### User Panel
- `GET /user/home` - Dashboard
- `GET /user/api/all-stocks` - Get all stocks
- `GET /user/api/ai-suggestions` - AI suggestions
- `POST /user/api/watchlist/add` - Add to watchlist
- `GET /user/api/notifications` - Get notifications

### Predictions
- `POST /api/predict/<symbol>` - Make prediction
- `GET /api/stock/<symbol>/news` - Get stock news
- `GET /api/stock/<symbol>/chart-data` - Chart data
- `POST /api/chatbot` - Chat with AI

### Admin
- `GET /admin/api/stats` - Dashboard stats
- `POST /admin/api/stock/add` - Add stock
- `POST /admin/api/stock/train-model` - Train model
- `POST /admin/api/email-config/update` - Update email

## 🐛 Troubleshooting

### Email Not Sending
- Check SMTP credentials
- Verify app password (not regular password)
- Check firewall/antivirus settings
- Test with admin panel email test

### Model Training Fails
- Ensure sufficient data (100+ points)
- Check CSV format
- Verify all required columns present
- Check error logs

### Live Data Not Loading
- Check internet connection
- Google Finance may block requests (use VPN)
- Try different user agents
- Check rate limiting

### Gemini AI Not Working
- Verify API key is correct
- Check API quota/limits
- Ensure internet connectivity
- Review Gemini AI status page

## 📝 License

This project is for educational purposes. Please ensure compliance with:
- Stock exchange data usage policies
- API terms of service (Google Finance, Gemini AI)
- Financial regulations in your jurisdiction

## ⚠️ Disclaimer

**This application is for educational and informational purposes only. It should NOT be considered as financial advice. Stock market investments carry risks. Always do your own research and consult with financial advisors before making investment decisions.**

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check documentation
- Review troubleshooting section

## 🎯 Future Enhancements

- [ ] Multi-exchange support (BSE, NYSE, NASDAQ)
- [ ] Portfolio management
- [ ] Paper trading simulation
- [ ] Mobile app (React Native)
- [ ] Advanced charting (TradingView integration)
- [ ] Social features (share predictions)
- [ ] Backtesting functionality
- [ ] More ML models (LSTM, GRU, Transformer)
- [ ] Real-time WebSocket updates
- [ ] Multi-language support

---

**Made with ❤️ for smart investors**
#   S t o c k M a r k e t _ p r e d i c t i o n  
 #   S t o c k M a r k e t _ p r e d i c t i o n  
 