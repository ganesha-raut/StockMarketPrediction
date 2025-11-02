"""
Quick script to train ML model for a single stock
Usage: python train_single_stock.py RELIANCE
"""
import sys
import io
# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import create_app, db
from models import Stock, HistoricalData, ModelTraining
from utils.ml_model import StockPredictionModel
from utils.stock_data import get_historical_data_yfinance
from datetime import datetime
import pandas as pd

app = create_app()

def train_stock(symbol):
    """Train model for a specific stock"""
    with app.app_context():
        stock = Stock.query.filter_by(symbol=symbol).first()
        
        if not stock:
            print(f"❌ Stock {symbol} not found in database")
            return False
        
        print(f"\n{'='*60}")
        print(f"Training model for: {stock.symbol} - {stock.name}")
        print(f"{'='*60}\n")
        
        try:
            # Check historical data
            data_count = HistoricalData.query.filter_by(stock_id=stock.id).count()
            print(f"📊 Current data points: {data_count}")
            
            if data_count < 100:
                print(f"⚠️  Need more data. Fetching from Yahoo Finance...")
                hist_data = get_historical_data_yfinance(stock.symbol, period="2y")
                
                if not hist_data:
                    print(f"❌ Failed to fetch data")
                    return False
                
                print(f"📥 Saving {len(hist_data)} records...")
                for record in hist_data:
                    existing = HistoricalData.query.filter_by(
                        stock_id=stock.id,
                        date=record['date']
                    ).first()
                    
                    if not existing:
                        hist = HistoricalData(
                            stock_id=stock.id,
                            date=record['date'],
                            open_price=record['open'],
                            high_price=record['high'],
                            low_price=record['low'],
                            close_price=record['close'],
                            volume=record['volume'],
                            dividend=record.get('dividend', 0.0)
                        )
                        db.session.add(hist)
                
                db.session.commit()
                print(f"✅ Data saved")
            
            # Get training data
            recent_data = HistoricalData.query.filter_by(
                stock_id=stock.id
            ).order_by(HistoricalData.date.desc()).limit(500).all()
            
            if len(recent_data) < 100:
                print(f"❌ Insufficient data: {len(recent_data)} records")
                return False
            
            print(f"🧠 Training with {len(recent_data)} data points...")
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': d.date,
                'open_price': d.open_price,
                'high_price': d.high_price,
                'low_price': d.low_price,
                'close_price': d.close_price,
                'volume': d.volume,
                'dividend': d.dividend
            } for d in reversed(recent_data)])
            
            # Train model
            model = StockPredictionModel(stock.symbol)
            result = model.train(df, sentiment_score=0.0)
            
            if result['success']:
                # Update stock
                stock.has_model = True
                stock.model_version = f"v{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                stock.last_trained = datetime.utcnow()
                db.session.commit()
                
                print(f"\n✅ SUCCESS!")
                print(f"   Accuracy: {result['accuracy']:.2f}%")
                print(f"   Model saved: models/{stock.symbol}_model.pkl")
                print(f"\n🎉 You can now make predictions for {stock.symbol}!")
                return True
            else:
                print(f"\n❌ Training failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python train_single_stock.py <SYMBOL>")
        print("Example: python train_single_stock.py RELIANCE")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    train_stock(symbol)
