"""Test chart data availability"""
from app import create_app
from models import Stock, HistoricalData, db
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    symbol = 'RELIANCE'
    
    print(f"\n{'='*60}")
    print(f"Testing Chart Data for {symbol}")
    print(f"{'='*60}\n")
    
    # Check stock exists
    stock = Stock.query.filter_by(symbol=symbol).first()
    if not stock:
        print(f"❌ Stock {symbol} not found in database!")
        exit(1)
    
    print(f"✓ Stock found: {stock.name} (ID: {stock.id})")
    
    # Check historical data
    total_data = HistoricalData.query.filter_by(stock_id=stock.id).count()
    print(f"✓ Total historical records: {total_data}")
    
    # Check last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    recent_data = HistoricalData.query.filter(
        HistoricalData.stock_id == stock.id,
        HistoricalData.date >= start_date,
        HistoricalData.date <= end_date
    ).order_by(HistoricalData.date.asc()).all()
    
    print(f"✓ Last 30 days records: {len(recent_data)}")
    
    if recent_data:
        print(f"\nSample data (first 3 records):")
        for data in recent_data[:3]:
            print(f"  {data.date}: O={data.open_price:.2f}, H={data.high_price:.2f}, L={data.low_price:.2f}, C={data.close_price:.2f}")
        
        print(f"\nDate range:")
        print(f"  First: {recent_data[0].date}")
        print(f"  Last: {recent_data[-1].date}")
    else:
        print(f"\n❌ No data found for last 30 days!")
        print(f"   Start date: {start_date}")
        print(f"   End date: {end_date}")
        
        # Check what dates we have
        all_dates = HistoricalData.query.filter_by(
            stock_id=stock.id
        ).order_by(HistoricalData.date.desc()).limit(5).all()
        
        if all_dates:
            print(f"\n   Latest dates in database:")
            for d in all_dates:
                print(f"     - {d.date}")
    
    print(f"\n{'='*60}")
    print("Test Complete")
    print(f"{'='*60}\n")
