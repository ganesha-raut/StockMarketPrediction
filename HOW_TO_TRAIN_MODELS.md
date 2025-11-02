# How to Train ML Models for Stock Prediction

## Why Do You Need to Train Models?

The AI Stock Prediction system uses Machine Learning models to predict stock prices. Before you can make predictions, you need to train these models with historical data.

## Quick Start - Train All Stocks

### Option 1: Train All Stocks at Once (Recommended)

Run this command in your terminal:

```bash
cd "C:\Users\GANESH RAUT\Desktop\Prediction"
.\venv\Scripts\python.exe train_all_models.py
```

This will:
- ✅ Fetch historical data for all stocks
- ✅ Train ML models for each stock
- ✅ Save models to disk
- ✅ Update database with model status

**Time Required:** 5-10 minutes for 10 stocks

---

### Option 2: Train Single Stock (For Testing)

Train just one stock to test:

```bash
.\venv\Scripts\python.exe train_single_stock.py RELIANCE
```

Replace `RELIANCE` with any stock symbol (TCS, INFY, HDFCBANK, etc.)

---

## Step-by-Step Process

### 1. **Check Current Status**

First, let's see which stocks need training:

```bash
.\venv\Scripts\python.exe -c "from app import create_app, db; from models import Stock; app = create_app(); app.app_context().push(); stocks = Stock.query.all(); print('\nStock Training Status:\n' + '='*50); [print(f'{s.symbol:15} - Model: {'✅ Trained' if s.has_model else '❌ Not Trained'}') for s in stocks]"
```

### 2. **Train Models**

Run the training script:

```bash
.\venv\Scripts\python.exe train_all_models.py
```

**What happens during training:**

1. 📥 **Fetch Data** - Downloads 2 years of historical stock data
2. 💾 **Save to Database** - Stores data for future use
3. 🧠 **Train Model** - Uses LSTM neural network to learn patterns
4. 📊 **Test Accuracy** - Validates model performance
5. ✅ **Save Model** - Saves trained model to `models/` folder

### 3. **Verify Training**

Check if models are trained:

```bash
.\venv\Scripts\python.exe -c "from app import create_app, db; from models import Stock; app = create_app(); app.app_context().push(); trained = Stock.query.filter_by(has_model=True).count(); total = Stock.query.count(); print(f'\n✅ Trained Models: {trained}/{total}')"
```

---

## Troubleshooting

### Error: "Insufficient historical data"

**Solution:** The script will automatically fetch data from Yahoo Finance. Just wait for it to complete.

### Error: "Failed to fetch historical data"

**Possible causes:**
1. No internet connection
2. Yahoo Finance API is down
3. Stock symbol is incorrect

**Solution:** 
- Check internet connection
- Try again later
- Verify stock symbol is correct

### Error: "Training failed"

**Solution:**
1. Check if you have enough disk space (need ~100MB)
2. Make sure `models/` folder exists
3. Try training one stock at a time

---

## Understanding the Output

When training completes, you'll see:

```
✅ Model trained successfully!
   Accuracy: 85.32%
   Model Version: v20251101-172530
```

**Accuracy Levels:**
- 🟢 **80-100%** - Excellent (High confidence predictions)
- 🟡 **60-80%** - Good (Moderate confidence)
- 🔴 **Below 60%** - Poor (May need more data)

---

## After Training

Once models are trained, you can:

1. ✅ **Make Predictions** - Go to any stock's prediction page
2. ✅ **Intraday Trading** - Get today's closing price prediction
3. ✅ **Long Term** - Predict prices for next 7-30 days
4. ✅ **Investment Calculator** - Calculate potential profit/loss

---

## Re-training Models

Models should be retrained periodically to stay accurate:

**Recommended Schedule:**
- 📅 **Weekly** - For active trading
- 📅 **Monthly** - For long-term investing

**To retrain:**
```bash
.\venv\Scripts\python.exe train_all_models.py
```

This will update existing models with latest data.

---

## Quick Commands Reference

```bash
# Train all stocks
.\venv\Scripts\python.exe train_all_models.py

# Train single stock
.\venv\Scripts\python.exe train_single_stock.py RELIANCE

# Check training status
.\venv\Scripts\python.exe -c "from app import *; from models import *; app = create_app(); app.app_context().push(); print(f'Trained: {Stock.query.filter_by(has_model=True).count()}/{Stock.query.count()}')"

# List all stocks
.\venv\Scripts\python.exe -c "from app import *; from models import *; app = create_app(); app.app_context().push(); [print(s.symbol) for s in Stock.query.all()]"
```

---

## Need Help?

If you encounter any issues:

1. Check the error message carefully
2. Make sure the Flask app is NOT running during training
3. Ensure you have internet connection
4. Try training one stock at a time first

---

## What's Next?

After training models:

1. 🚀 **Start the app:** `.\venv\Scripts\python.exe app.py`
2. 🌐 **Open browser:** http://localhost:5000
3. 📊 **Go to any stock's prediction page**
4. 🎯 **Click "Get AI Prediction"**
5. 💰 **Enter investment amount (for intraday)**
6. ✨ **Get predictions!**

---

**Happy Trading! 📈💰**
