# Email Setup Guide for Background Service

## Quick Setup

### Option 1: Configure in .env file (Recommended)

Add these lines to your `.env` file:

```env
# Email Configuration for Background Service
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_RECIPIENT=recipient@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Option 2: Configure in test_background_service.py

Edit `test_background_service.py` and update:

```python
email_config = {
    'enabled': True,  # Change to True
    'sender_email': 'your_email@gmail.com',  # Your Gmail
    'sender_password': 'your_app_password',  # Gmail App Password
    'recipient_email': 'recipient@gmail.com',  # Where to send
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}
```

## How to Get Gmail App Password

1. **Go to Google Account Settings**
   - Visit: https://myaccount.google.com/

2. **Enable 2-Step Verification**
   - Go to Security → 2-Step Verification
   - Follow the steps to enable it

3. **Generate App Password**
   - Go to Security → App passwords
   - Select "Mail" and "Windows Computer"
   - Click "Generate"
   - Copy the 16-character password

4. **Use the App Password**
   - Use this password (not your regular Gmail password)
   - Paste it in EMAIL_PASSWORD field

## Testing Email

### Test Immediately:
```bash
python test_background_service.py
```

This will:
- Make predictions for all stocks
- Generate AI recommendations
- Send email with predictions
- Test accuracy checking
- Send accuracy report email

### What Emails You'll Receive:

#### 1. Morning Prediction Email (10:00 AM)
- All stock predictions
- AI recommended stocks (Strong Buy/Sell)
- Expected gains/losses
- Confidence scores
- AI analysis

#### 2. Evening Accuracy Email (3:45 PM)
- Prediction accuracy for each stock
- Actual vs Predicted prices
- Overall accuracy percentage
- Learning insights
- Retraining recommendations

## Troubleshooting

### "Authentication failed"
- Make sure you're using App Password, not regular password
- Enable 2-Step Verification first

### "SMTP connection failed"
- Check your internet connection
- Verify SMTP server and port are correct
- For Gmail: smtp.gmail.com:587

### "Less secure app access"
- Gmail no longer supports this
- You MUST use App Password instead

## Email Schedule

When running with `python run.py`:
- **10:00 AM** - Prediction email with AI recommendations
- **3:45 PM** - Accuracy report email
- **Daily** - Automatic learning and retraining

## Disable Email

To run without email:
```python
email_config = {
    'enabled': False,  # Set to False
    # ... rest of config
}
```

The system will work normally but won't send emails.
