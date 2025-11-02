"""
Quick script to train ML models for all stocks
Run this script to train prediction models for all active stocks
"""
import sys
import io
# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import create_app, db
from models import Stock, HistoricalData, ModelTraining
from utils.ml_model import StockPredictionModel
from utils.stock_data import get_historical_data_yfinance, get_stock_news
from utils.gemini_ai import get_gemini
from datetime import datetime
import pandas as pd

app = create_app()

def train_stock_model(stock):
    """Train model for a single stock"""
    print(f"\n{'='*60}")
    print(f"Training model for: {stock.symbol} - {stock.name}")
    print(f"{'='*60}")
    
    try:
        # Check if historical data exists
        data_count = HistoricalData.query.filter_by(stock_id=stock.id).count()
        
        if data_count < 100:
            print(f"⚠️  Insufficient data ({data_count} records). Fetching from yfinance...")
            
            # Fetch historical data
            hist_data = get_historical_data_yfinance(stock.symbol, period="2y")
            
            if not hist_data:
                print(f"❌ Failed to fetch historical data for {stock.symbol}")
                return False
            
            # Save to database
            print(f"📥 Saving {len(hist_data)} historical records...")
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
            print(f"✅ Historical data saved")
        
        # Get recent data for training
        recent_data = HistoricalData.query.filter_by(
            stock_id=stock.id
        ).order_by(HistoricalData.date.desc()).limit(500).all()
        
        if len(recent_data) < 100:
            print(f"❌ Still insufficient data: {len(recent_data)} records")
            return False
        
        print(f"📊 Using {len(recent_data)} records for training")
        
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
        
        # Get sentiment score
        sentiment_score = 0.0
        print("🤖 Analyzing news sentiment...")
        gemini = get_gemini()
        if gemini:
            news = get_stock_news(stock.symbol, limit=10)
            if news:
                analyzed = gemini.analyze_news_batch(news)
                sentiment_scores = [item.get('sentiment_score', 0.0) for item in analyzed]
                sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
                print(f"   Sentiment Score: {sentiment_score:.2f}")
        
        # Create training record
        training = ModelTraining(
            stock_id=stock.id,
            model_version=f"v{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            training_start=datetime.utcnow(),
            status='running',
            data_points=len(df)
        )
        db.session.add(training)
        db.session.commit()
        
        # Train model
        print("🧠 Training ML model...")
        model = StockPredictionModel(stock.symbol)
        result = model.train(df, sentiment_score)
        
        if result['success']:
            # Update training record
            training.training_end = datetime.utcnow()
            training.accuracy = result['accuracy']
            training.status = 'completed'
            
            # Update stock
            stock.has_model = True
            stock.model_version = training.model_version
            stock.last_trained = datetime.utcnow()
            
            db.session.commit()
            
            print(f"✅ Model trained successfully!")
            print(f"   Accuracy: {result['accuracy']:.2f}%")
            print(f"   Model Version: {training.model_version}")
            return True
        else:
            training.status = 'failed'
            training.error_message = result.get('error', 'Unknown error')
            db.session.commit()
            print(f"❌ Training failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error training {stock.symbol}: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Train models for all active stocks"""
    with app.app_context():
        print("\n" + "="*60)
        print("AI STOCK PREDICTION - MODEL TRAINING")
        print("="*60)
        
        stocks = Stock.query.filter_by(is_active=True).all()
        print(f"\nFound {len(stocks)} active stocks")
        
        trained = 0
        failed = 0
        
        for i, stock in enumerate(stocks, 1):
            print(f"\n[{i}/{len(stocks)}] Processing {stock.symbol}...")
            
            if train_stock_model(stock):
                trained += 1
            else:
                failed += 1
        
        print("\n" + "="*60)
        print("TRAINING SUMMARY")
        print("="*60)
        print(f"✅ Successfully trained: {trained}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {len(stocks)}")
        print("="*60)
        
        if trained > 0:
            print("\n🎉 Models are ready! You can now make predictions.")
        else:
            print("\n⚠️  No models were trained. Check errors above.")

if __name__ == '__main__':
    main()
