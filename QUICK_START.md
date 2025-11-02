# ⚡ Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (2 min)
```bash
cd "C:\Users\GANESH RAUT\Desktop\Prediction"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure (1 min)
```bash
# Copy example config
copy .env.example .env

# Edit .env and add:
# - Your Gmail credentials (for email)
# - Gemini API key (for AI features)
```

### Step 3: Run (1 min)
```bash
python run.py
```

### Step 4: Access (1 min)
Open browser: **http://localhost:5000**

**Admin Login:**
- Email: `admin@stockai.com`
- Password: `admin123`

---

## 📝 Essential Configuration

### Gmail Setup (Required for Email)
1. Enable 2FA on Gmail
2. Generate App Password: [Google Account](https://myaccount.google.com/) → Security → App Passwords
3. Add to `.env`:
```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
```

### Gemini AI Setup (Required for AI Features)
1. Get API Key: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env`:
```env
GEMINI_API_KEY=your-api-key-here
```

---

## 🎯 First Actions

### 1. Add a Stock
**Admin Panel → Stocks → Add Stock**
- Symbol: `TCS`
- Name: `Tata Consultancy Services`
- Sector: `IT`

### 2. Get Data
**Click "Download Data"** → Fetches 5 years of historical data

### 3. Train Model
**Click "Train Model"** → Trains AI model (2-5 min)

### 4. Test Prediction
**User Panel → Home → Click "Predict" on TCS**

---

## 🔧 Troubleshooting

### Port Already in Use?
```bash
# Use different port
python app.py --port 8000
```

### Packages Not Installing?
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Email Not Working?
- Check Gmail App Password (not regular password)
- Verify 2FA is enabled
- Test with admin panel email test

### Gemini AI Not Working?
- Verify API key is correct
- Check API quota limits
- Test key at [AI Studio](https://makersuite.google.com/)

---

## 📚 Full Documentation

- **Complete Setup:** See `SETUP_GUIDE.md`
- **Full Documentation:** See `README.md`
- **API Reference:** Check route files in `routes/`

---

## ✅ Success Checklist

- [ ] Application running at http://localhost:5000
- [ ] Admin login successful
- [ ] Email configured (test in admin panel)
- [ ] Gemini AI configured (test chatbot)
- [ ] At least 1 stock added
- [ ] Model trained successfully
- [ ] User registration works
- [ ] Prediction works
- [ ] Watchlist works
- [ ] Notifications work

---

## 🆘 Need Help?

**Common Issues:**
1. **Can't install packages** → Upgrade pip: `python -m pip install --upgrade pip`
2. **Database error** → Delete `stock_prediction.db` and restart
3. **Email not sending** → Check Gmail app password
4. **AI not working** → Verify Gemini API key
5. **Port in use** → Change port or kill process

**Still stuck?** Check `SETUP_GUIDE.md` for detailed troubleshooting.

---

## 🎉 You're Ready!

Your AI Stock Market Prediction Platform is now running!

**Next Steps:**
1. Change admin password
2. Add more stocks (10-20 recommended)
3. Create user account
4. Test all features
5. Configure notifications
6. Enjoy predicting! 📈

---

**Made with ❤️ for smart investors**
