# Testing Instructions - Background Self-Training Service

## ✅ What Was Done

The self-training service has been integrated into `run.py`. Now when you start your application, the background service automatically runs in a separate thread.

### Modified Files:
- **`run.py`** - Added background service integration
  - Imports threading module
  - Added `start_background_training()` function
  - Service starts automatically before Flask app

### New Files Created:
- **`test_background_service.py`** - Test script to run immediately
- **`EMAIL_SETUP_GUIDE.md`** - Email configuration guide

## 🚀 How to Test RIGHT NOW

### Method 1: Test Immediately (Without Waiting for Schedule)

```bash
python test_background_service.py
```

This will run all background tasks immediately:
1. ✅ Make predictions for all stocks
2. ✅ Test 8 ML algorithms
3. ✅ Generate AI stock recommendations
4. ✅ Send prediction email (if enabled)
5. ✅ Check accuracy and learn
6. ✅ Send accuracy report email (if enabled)

### Method 2: Run Normal Application (With Scheduled Times)

```bash
python run.py
```

The background service will:
- Start automatically in background
- Run predictions at **10:00 AM**
- Check accuracy at **3:45 PM**
- Reset daily at **11:59 PM**
- Refresh models every **Sunday 2:00 AM**

## 📧 Email Testing

### To Enable Email:

**Option A: Edit test_background_service.py**
```python
email_config = {
    'enabled': True,  # Change this to True
    'sender_email': 'your_email@gmail.com',
    'sender_password': 'your_gmail_app_password',
    'recipient_email': 'where_to_send@gmail.com',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}
```

**Option B: Add to .env file**
```env
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@gmail.com
```

### Get Gmail App Password:
1. Go to https://myaccount.google.com/
2. Security → 2-Step Verification (enable it)
3. Security → App passwords → Generate
4. Use the 16-character password

See `EMAIL_SETUP_GUIDE.md` for detailed instructions.

## 🧪 What to Test

### 1. Predictions
- [ ] Predictions are made for all active stocks
- [ ] 8 algorithms are tested
- [ ] Best algorithm is selected
- [ ] Predictions saved to database

### 2. AI Recommendations
- [ ] Strong Buy stocks identified
- [ ] Strong Sell stocks identified
- [ ] AI analysis generated
- [ ] Confidence scores calculated

### 3. Email Sending
- [ ] Prediction email received
- [ ] Email contains stock predictions
- [ ] Email contains AI recommendations
- [ ] Email formatting is correct

### 4. Accuracy & Learning
- [ ] Actual prices fetched
- [ ] Accuracy calculated
- [ ] Model learns from errors
- [ ] Accuracy email sent

### 5. Background Service
- [ ] Service starts automatically with run.py
- [ ] Runs in background thread
- [ ] Doesn't block Flask app
- [ ] Scheduled tasks work

## 📊 Expected Output

### Console Output:
```
============================================================
  🤖 Starting Self-Training Background Service
============================================================

Background Service Features:
  • Automatic daily predictions at 10:00 AM
  • Tests 8 ML algorithms and selects best one
  • AI-powered stock recommendations
  • Accuracy checking at 3:45 PM
  • Self-learning from prediction errors
  • Auto-retraining when accuracy drops
  • Weekly model refresh

📧 Email Notifications: Enabled/Disabled
============================================================

✓ Background training service started successfully
```

### Email Content:
1. **Prediction Email** - Stock predictions + AI recommendations
2. **Accuracy Email** - Accuracy report + learning insights

## 🔍 Verify It's Working

### Check 1: Console Logs
Look for these messages when running `python run.py`:
```
✓ Background training service started successfully
🚀 ADAPTIVE MONITOR SERVICE STARTING
```

### Check 2: Database
Check if predictions are saved:
```python
from app import create_app, db
from models import Prediction
from datetime import datetime

app = create_app()
with app.app_context():
    today = datetime.now().date()
    predictions = Prediction.query.filter_by(prediction_date=today).all()
    print(f"Predictions today: {len(predictions)}")
```

### Check 3: Email Inbox
- Check for prediction email
- Check for accuracy email

## 🎯 Quick Test Commands

```bash
# Test immediately (all features)
python test_background_service.py

# Run with background service
python run.py

# Run only adaptive monitor (separate process)
python run_adaptive_monitor.py
```

## 📝 Notes

- **Background service runs in daemon thread** - stops when main app stops
- **Email is optional** - system works without it
- **Predictions saved to database** - can view in web interface
- **Self-learning happens automatically** - models improve over time
- **Auto-retraining** - when accuracy drops below 70%

## 🆘 Troubleshooting

### Service not starting:
- Check if `services/adaptive_monitor.py` exists
- Check for import errors in console

### No predictions:
- Check if stocks are marked as `is_active=True`
- Check database connection
- Look for errors in console

### Email not sending:
- Verify email config is correct
- Check if `enabled: True`
- Use Gmail App Password (not regular password)
- Check internet connection

### Accuracy check fails:
- Predictions must exist from earlier today
- Stock market must be closed
- Check if yfinance can fetch data

## 🎉 Success Indicators

✅ Background service starts when running `python run.py`
✅ Predictions are made and saved to database
✅ AI recommendations are generated
✅ Emails are sent (if enabled)
✅ Accuracy is checked and models learn
✅ Performance stats are logged
✅ System runs continuously in background

---

**Ready to test?** Run: `python test_background_service.py`
