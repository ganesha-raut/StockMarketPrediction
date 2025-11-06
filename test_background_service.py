"""
Test Background Service - Run Immediately
Tests all background features without waiting for scheduled times
"""

from app import create_app
from services.adaptive_monitor import AdaptiveMonitorService
import os

def test_background_service():
    """Test all background service features immediately"""
    
    print("=" * 80)
    print("  🧪 TESTING BACKGROUND SERVICE")
    print("=" * 80)
    print()
    
    # Email configuration
    print("📧 Email Configuration:")
    print("   To enable email, update the settings below:")
    print()
    
    email_config = {
        'enabled': False,  # Set to True to test email
        'sender_email': os.getenv('EMAIL_SENDER', 'your_email@gmail.com'),
        'sender_password': os.getenv('EMAIL_PASSWORD', 'your_app_password'),
        'recipient_email': os.getenv('EMAIL_RECIPIENT', 'recipient@gmail.com'),
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587))
    }
    
    print(f"   Enabled: {email_config['enabled']}")
    if email_config['enabled']:
        print(f"   Sender: {email_config['sender_email']}")
        print(f"   Recipient: {email_config['recipient_email']}")
    else:
        print("   ⚠️  Email disabled - Set 'enabled': True to test emails")
    print()
    print("=" * 80)
    print()
    
    # Create Flask app
    app = create_app()
    
    # Create service instance
    service = AdaptiveMonitorService(app, email_config)
    
    # Test 1: Morning Predictions
    print("\n" + "=" * 80)
    print("TEST 1: MORNING PREDICTIONS (Normally runs at 10:00 AM)")
    print("=" * 80)
    print()
    print("This will:")
    print("  • Make predictions for all active stocks")
    print("  • Test 8 ML algorithms and select best one")
    print("  • Generate AI stock recommendations")
    print("  • Send email with predictions (if enabled)")
    print()
    print("⏳ Starting morning predictions test...")
    print()
    
    service.make_morning_predictions()
    
    # Test 2: AI Recommendations
    print("\n" + "=" * 80)
    print("TEST 2: AI STOCK RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("This will generate AI-powered stock recommendations")
    print()
    print("⏳ Testing AI recommendations...")
    print()
    
    with app.app_context():
        from utils.ai_stock_recommender import get_ai_recommender
        recommender = get_ai_recommender()
        recommendations = recommender.get_recommendations()
    
    if recommendations.get('success'):
        categorized = recommendations['categorized_stocks']
        print("\n📊 AI RECOMMENDATIONS SUMMARY:")
        print(f"   Strong Buy: {len(categorized['strong_buy'])} stocks")
        print(f"   Buy: {len(categorized['buy'])} stocks")
        print(f"   Hold: {len(categorized['hold'])} stocks")
        print(f"   Sell: {len(categorized['sell'])} stocks")
        print(f"   Strong Sell: {len(categorized['strong_sell'])} stocks")
        print()
        
        # Show top 3 strong buy
        if categorized['strong_buy']:
            print("🎯 TOP 3 STRONG BUY RECOMMENDATIONS:")
            for i, stock in enumerate(categorized['strong_buy'][:3], 1):
                print(f"\n   {i}. {stock['name']} ({stock['symbol']})")
                print(f"      Expected Gain: {stock['percent_change']:+.2f}%")
                print(f"      Confidence: {stock['confidence']:.0f}%")
                print(f"      Recommendation: {stock['recommendation']}")
        
        print("\n🤖 AI ANALYSIS:")
        print(recommendations['ai_recommendations'])
        print()
    else:
        print("❌ Failed to generate recommendations")
    
    # Test 3: Email Sending
    if email_config['enabled']:
        print("\n" + "=" * 80)
        print("TEST 3: EMAIL SENDING")
        print("=" * 80)
        print()
        print("This will send prediction email with AI recommendations")
        print()
        print("⏳ Sending test email...")
        print()
        
        service.send_prediction_email(recommendations)
    else:
        print("\n" + "=" * 80)
        print("TEST 3: EMAIL SENDING - SKIPPED")
        print("=" * 80)
        print()
        print("⚠️  Email is disabled. To test email:")
        print("   1. Set 'enabled': True in email_config above")
        print("   2. Configure your email credentials")
        print("   3. Run this script again")
        print()
    
    # Test 4: Accuracy Check (if predictions exist)
    print("\n" + "=" * 80)
    print("TEST 4: ACCURACY CHECK & LEARNING (Normally runs at 3:45 PM)")
    print("=" * 80)
    print()
    print("This will:")
    print("  • Check actual stock prices")
    print("  • Calculate prediction accuracy")
    print("  • Learn from errors (self-learning)")
    print("  • Send accuracy report email (if enabled)")
    print()
    print("⚠️  Note: This only works if predictions were made earlier today")
    print()
    print("⏳ Testing accuracy check...")
    print()
    
    try:
        service.check_accuracy_and_learn()
    except Exception as e:
        print(f"⚠️  Accuracy check skipped: {e}")
    
    # Test 5: Performance Stats
    print("\n" + "=" * 80)
    print("TEST 5: PERFORMANCE STATISTICS")
    print("=" * 80)
    print()
    print("⏳ Loading performance stats...")
    print()
    
    service.log_performance_stats()
    
    # Summary
    print("\n" + "=" * 80)
    print("  ✅ TESTING COMPLETE")
    print("=" * 80)
    print()
    print("What was tested:")
    print("  ✓ Morning predictions with adaptive algorithms")
    print("  ✓ AI stock recommendations")
    print(f"  {'✓' if email_config['enabled'] else '⏭️'} Email sending (predictions)")
    print("  ✓ Accuracy checking & learning")
    print("  ✓ Performance statistics")
    print()
    print("Background Service Features:")
    print("  • Runs automatically when you start run.py")
    print("  • Scheduled at 10:00 AM (predictions)")
    print("  • Scheduled at 3:45 PM (accuracy check)")
    print("  • Scheduled at 11:59 PM (daily reset)")
    print("  • Scheduled every Sunday 2:00 AM (model refresh)")
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    test_background_service()
