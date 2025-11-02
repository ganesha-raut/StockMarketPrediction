"""Test the stock API endpoint"""
from app import create_app
from models import db, Stock, HistoricalData
from utils.stock_data import check_market_status, get_google_stock_data

app = create_app()

with app.app_context():
    symbol = 'RELIANCE'
    
    print(f"\n{'='*60}")
    print(f"Testing API for {symbol}")
    print(f"{'='*60}\n")
    
    # Check stock exists
    stock = Stock.query.filter_by(symbol=symbol).first()
    print(f"1. Stock exists: {stock is not None}")
    if stock:
        print(f"   Stock ID: {stock.id}")
        print(f"   Stock Name: {stock.name}")
        print(f"   Has Model: {stock.has_model}")
    
    # Check market status
    print(f"\n2. Checking market status...")
    market_status = check_market_status()
    print(f"   Market Open: {market_status.get('is_open')}")
    print(f"   Status: {market_status.get('status')}")
    
    # Check historical data
    print(f"\n3. Checking historical data...")
    latest_data = HistoricalData.query.filter_by(
        stock_id=stock.id
    ).order_by(HistoricalData.date.desc()).first()
    
    if latest_data:
        print(f"   Latest Date: {latest_data.date}")
        print(f"   Close Price: ₹{latest_data.close_price:,.2f}")
        print(f"   Volume: {latest_data.volume:,}")
    else:
        print(f"   No historical data found!")
    
    # Try to get live data
    print(f"\n4. Trying to fetch live data...")
    try:
        live_data = get_google_stock_data(symbol)
        if live_data:
            print(f"   ✓ Live data fetched successfully")
            print(f"   Name: {live_data.get('name')}")
            print(f"   Price: {live_data.get('live_price')}")
        else:
            print(f"   ✗ Live data fetch returned None")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print(f"\n{'='*60}")
    print("Test complete!")
    print(f"{'='*60}\n")
