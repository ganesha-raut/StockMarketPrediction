"""
Test Prediction Script
Tests the aggressive model predictions with real data
"""

from utils.aggressive_model import get_aggressive_model
from utils.hybrid_predictor import get_hybrid_predictor
import yfinance as yf
from datetime import datetime

def test_single_stock(symbol, company_name, days_ahead=90):
    """Test prediction for a single stock"""
    
    print("\n" + "="*70)
    print(f"📊 TESTING: {company_name} ({symbol})")
    print("="*70)
    
    # Get current price
    try:
        ticker = f"{symbol}.NS"
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        current_price = hist['Close'].iloc[-1]
        
        print(f"\n💰 Current Price: ₹{current_price:,.2f}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"⏰ Prediction Period: {days_ahead} days")
        
    except Exception as e:
        print(f"❌ Error fetching current price: {e}")
        return
    
    print("\n" + "-"*70)
    print("🤖 TESTING AGGRESSIVE MODEL")
    print("-"*70)
    
    # Test aggressive model
    try:
        model = get_aggressive_model(symbol, company_name)
        result = model.predict(days_ahead)
        
        if result:
            print(f"\n✅ Model Prediction Successful!")
            print(f"\n📈 Predicted Price: ₹{result['predicted_price']:,.2f}")
            print(f"📊 Price Change: ₹{result['price_change']:,.2f}")
            print(f"📈 Percent Change: {result['percent_change']:+.2f}%")
            print(f"🎯 Confidence: {result['confidence']:.1f}%")
            print(f"📊 RSI: {result['rsi']:.1f}")
            print(f"🚀 Momentum (30d): {result['momentum_30']:.2f}%")
            print(f"📉 Volatility: {result['volatility']:.2f}%")
            print(f"🕐 Model Age: {result['model_age_days']} days")
            
            # Investment analysis
            print(f"\n💰 INVESTMENT ANALYSIS:")
            print(f"   Expected Return: {result['percent_change']:.2f}%")
            
            if result['percent_change'] >= 30:
                print(f"   Rating: ⭐⭐⭐⭐⭐ EXCELLENT")
                print(f"   Signal: 🟢 STRONG BUY")
            elif result['percent_change'] >= 20:
                print(f"   Rating: ⭐⭐⭐⭐ VERY GOOD")
                print(f"   Signal: 🟢 BUY")
            elif result['percent_change'] >= 10:
                print(f"   Rating: ⭐⭐⭐ GOOD")
                print(f"   Signal: 🟡 CONSIDER BUYING")
            elif result['percent_change'] >= 5:
                print(f"   Rating: ⭐⭐ FAIR")
                print(f"   Signal: 🟡 HOLD")
            else:
                print(f"   Rating: ⭐ POOR")
                print(f"   Signal: 🔴 NOT RECOMMENDED")
            
            # Calculate potential profit
            print(f"\n💵 PROFIT CALCULATION (₹10,000 investment):")
            investment = 10000
            shares = investment / current_price
            future_value = shares * result['predicted_price']
            profit = future_value - investment
            
            print(f"   Shares: {shares:.2f}")
            print(f"   Future Value: ₹{future_value:,.2f}")
            print(f"   Profit: ₹{profit:,.2f}")
            
        else:
            print("❌ Model prediction failed")
            
    except Exception as e:
        print(f"❌ Error in model prediction: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-"*70)
    print("🧠 TESTING HYBRID PREDICTOR")
    print("-"*70)
    
    # Test hybrid predictor
    try:
        predictor = get_hybrid_predictor(symbol, company_name)
        result = predictor.hybrid_predict(days_ahead)
        
        if result and result.get('success'):
            print(f"\n✅ Hybrid Prediction Successful!")
            print(f"\n📈 Final Price: ₹{result['predicted_price']:,.2f}")
            print(f"📊 Change: ₹{result['price_change']:,.2f} ({result['percent_change']:+.2f}%)")
            print(f"🎯 Confidence: {result['confidence']:.1f}%")
            print(f"📊 Recommendation: {result['recommendation']}")
            print(f"📈 Trend: {result['trend']}")
            
            if 'ml_prediction' in result:
                ml = result['ml_prediction']
                print(f"\n🤖 ML Component:")
                print(f"   Price: ₹{ml['price']:,.2f}")
                print(f"   Confidence: {ml['confidence']:.1f}%")
                if 'expected_return' in ml:
                    print(f"   Expected Return: {ml['expected_return']:.2f}%")
            
            if 'ai_prediction' in result:
                ai = result['ai_prediction']
                print(f"\n🧠 AI Component:")
                print(f"   Adjusted Price: ₹{ai['adjusted_price']:,.2f}")
                print(f"   Adjustment: {ai['adjustment_percent']:+.2f}%")
                print(f"   News Score: {ai['news_score']:.0f}/100")
                print(f"   Growth Score: {ai['growth_score']:.0f}/100")
                if 'summary' in ai:
                    print(f"   Summary: {ai['summary']}")
            
            if 'dividend_analysis' in result and result['dividend_analysis'].get('has_dividends'):
                div = result['dividend_analysis']
                print(f"\n💰 Dividend Component:")
                print(f"   Yield: {div['dividend_yield']:.2f}%")
                if 'expected_dividends_period' in div:
                    print(f"   Expected Dividends: ₹{div['expected_dividends_period']:.2f}")
                if 'dividend_return_percent' in div:
                    print(f"   Return: {div['dividend_return_percent']:.2f}%")
        else:
            print(f"❌ Hybrid prediction failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in hybrid prediction: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)


def test_multiple_stocks():
    """Test predictions for multiple stocks"""
    
    stocks = [
        ('TCS', 'Tata Consultancy Services'),
        ('RELIANCE', 'Reliance Industries'),
        ('HDFCBANK', 'HDFC Bank'),
        ('INFY', 'Infosys')
    ]
    
    print("\n" + "="*70)
    print("🚀 TESTING MULTIPLE STOCKS")
    print("="*70)
    
    for symbol, company_name in stocks:
        test_single_stock(symbol, company_name, days_ahead=90)
        print("\n")


def quick_test():
    """Quick test for TCS only"""
    
    print("\n" + "="*70)
    print("⚡ QUICK TEST - TCS")
    print("="*70)
    
    test_single_stock('TCS', 'Tata Consultancy Services', days_ahead=90)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quick':
            quick_test()
        elif sys.argv[1] == 'multiple':
            test_multiple_stocks()
        else:
            # Test specific stock
            symbol = sys.argv[1]
            company_name = sys.argv[2] if len(sys.argv) > 2 else symbol
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
            test_single_stock(symbol, company_name, days)
    else:
        # Default: quick test
        quick_test()
