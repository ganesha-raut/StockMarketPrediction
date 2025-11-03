"""
Train Aggressive Models for All Stocks
"""

from utils.aggressive_model import get_aggressive_model
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of stocks
STOCKS = [
    ('TCS', 'Tata Consultancy Services'),
    ('RELIANCE', 'Reliance Industries'),
    ('HDFCBANK', 'HDFC Bank'),
    ('INFY', 'Infosys'),
    ('ICICIBANK', 'ICICI Bank'),
    ('HINDUNILVR', 'Hindustan Unilever'),
    ('KOTAKBANK', 'Kotak Mahindra Bank'),
    ('SBIN', 'State Bank of India'),
    ('BHARTIARTL', 'Bharti Airtel'),
    ('WIPRO', 'Wipro'),
    ('LT', 'Larsen & Toubro'),
    ('AXISBANK', 'Axis Bank'),
    ('ITC', 'ITC Limited'),
    ('MARUTI', 'Maruti Suzuki'),
    ('TITAN', 'Titan Company')
]

def train_all():
    """Train models for all stocks"""
    
    print("\n" + "="*60)
    print("🚀 TRAINING AGGRESSIVE MODELS")
    print("="*60)
    
    success_count = 0
    failed_stocks = []
    
    for symbol, company_name in STOCKS:
        print(f"\n📊 Training: {company_name} ({symbol})")
        print("-" * 60)
        
        try:
            model = get_aggressive_model(symbol, company_name)
            
            # Train for 90 days (default)
            if model.train_model(days_ahead=90):
                print(f"   ✅ Success! Model saved for {symbol}")
                success_count += 1
            else:
                print(f"   ❌ Failed to train {symbol}")
                failed_stocks.append(symbol)
                
        except Exception as e:
            print(f"   ❌ Error training {symbol}: {e}")
            failed_stocks.append(symbol)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TRAINING SUMMARY")
    print("="*60)
    print(f"✅ Successful: {success_count}/{len(STOCKS)}")
    print(f"❌ Failed: {len(failed_stocks)}/{len(STOCKS)}")
    
    if failed_stocks:
        print(f"\nFailed stocks: {', '.join(failed_stocks)}")
    
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE!")
    print("="*60)
    print("\nModels saved in: models/")
    print("Ready for predictions!")

if __name__ == "__main__":
    train_all()
