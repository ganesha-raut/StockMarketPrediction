# Fix Prediction Page - Complete Guide

## Step 1: Test All APIs

Run this to test all prediction page APIs:
```powershell
python test_prediction_page.py
```

## Step 2: Verify Data Exists

Check if stock and historical data exist:
```powershell
python -c "from app import create_app; from models import Stock, HistoricalData, db; app = create_app(); ctx = app.app_context(); ctx.push(); stock = Stock.query.filter_by(symbol='RELIANCE').first(); print(f'Stock: {stock.symbol if stock else None}'); print(f'Has Model: {stock.has_model if stock else False}'); data_count = HistoricalData.query.filter_by(stock_id=stock.id).count() if stock else 0; print(f'Historical Data: {data_count} records')"
```

Expected output:
```
Stock: RELIANCE
Has Model: True
Historical Data: 495 records
```

## Step 3: Restart Flask App

```powershell
python app.py
```

## Step 4: Test Prediction Page

1. Open browser: http://localhost:5000/user/prediction/RELIANCE
2. Check browser console (F12) for errors
3. Check Flask terminal for errors

## Expected Behavior

### Page Load:
- ✅ Stock symbol displays: RELIANCE
- ✅ Stock name loads: Reliance Industries
- ✅ Price displays (from historical data if market closed)
- ✅ Market status badge shows (Open/Closed)

### APIs Called:
1. `/user/api/stock/RELIANCE` - Stock data
2. `/user/api/market-status` - Market status
3. `/api/stock-news/RELIANCE` - Latest news
4. `/api/stock-chart-data/RELIANCE` - Chart data

### Prediction Form:
- ✅ Select "Intraday" or "Long Term"
- ✅ Fill required fields
- ✅ Click "Get AI Prediction"
- ✅ Shows prediction result

## Common Issues & Fixes

### Issue 1: "Failed to load stock data"
**Cause:** API endpoint not working
**Fix:** Check Flask console for actual error

### Issue 2: "Model not trained"
**Fix:** Run training:
```powershell
python train_single_stock.py RELIANCE
```

### Issue 3: "Market is closed"
**Expected:** This is normal after 3:30 PM IST
**Fix:** Use "Long Term" prediction instead

### Issue 4: No historical data
**Fix:** The training script should have saved it. Check:
```powershell
python -c "from app import create_app; from models import HistoricalData, Stock, db; app = create_app(); ctx = app.app_context(); ctx.push(); stock = Stock.query.filter_by(symbol='RELIANCE').first(); print(HistoricalData.query.filter_by(stock_id=stock.id).count())"
```

## Debug Mode

To see detailed errors, check:
1. **Browser Console** (F12 → Console tab)
2. **Flask Terminal** (where you ran `python app.py`)
3. **Network Tab** (F12 → Network tab) - Check API responses

## Quick Test Commands

### Test Stock API:
```powershell
curl http://localhost:5000/user/api/stock/RELIANCE -H "Cookie: session=YOUR_SESSION"
```

### Test Market Status:
```powershell
curl http://localhost:5000/user/api/market-status -H "Cookie: session=YOUR_SESSION"
```

## Success Criteria

✅ Page loads without errors
✅ Stock data displays
✅ Market status shows
✅ News section loads (even if empty)
✅ Chart displays
✅ Prediction form works
✅ Can make predictions (if model trained)

## If All Else Fails

1. Stop Flask (Ctrl+C)
2. Delete `instance/stock_prediction.db`
3. Run `python app.py` (will recreate DB)
4. Add stocks via admin panel
5. Train models: `python train_all_models.py`
6. Test prediction page again
