from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import atexit

def monitor_notifications(app):
    """Monitor stocks and send notifications"""
    with app.app_context():
        from models import db, NotificationSetting, Notification, Stock, Prediction
        from utils.stock_data import get_google_stock_data
        from utils.email_service import send_notification_email
        
        try:
            # Get all active notification settings
            settings = NotificationSetting.query.filter_by(email_enabled=True).all()
            
            for setting in settings:
                stock = setting.stock
                user = setting.user
                
                # Get live data
                live_data = get_google_stock_data(stock.symbol)
                if not live_data:
                    continue
                
                live_price = live_data['live_price']
                
                # Check target price
                if setting.target_price and live_price >= setting.target_price:
                    # Create notification
                    notif = Notification(
                        user_id=user.id,
                        stock_id=stock.id,
                        notification_type='TARGET',
                        title=f'{stock.symbol} reached target price',
                        message=f'{stock.name} has reached your target price of ₹{setting.target_price:,.2f}. Current price: ₹{live_price:,.2f}'
                    )
                    db.session.add(notif)
                    
                    # Send email
                    email_data = {
                        'stock_name': stock.name,
                        'symbol': stock.symbol,
                        'type': 'TARGET',
                        'live_price': live_price,
                        'predicted_price': setting.target_price,
                        'confidence': 100,
                        'change_percent': ((live_price - setting.target_price) / setting.target_price) * 100,
                        'trend': 'bullish' if live_price > setting.target_price else 'neutral',
                        'message': f'Your target price of ₹{setting.target_price:,.2f} has been reached!'
                    }
                    
                    if send_notification_email(user.email, email_data):
                        notif.email_sent = True
                
                # Check for large drops
                if setting.notify_on_drop:
                    change_percent = live_data['percent_change']
                    if change_percent < -setting.drop_threshold:
                        # Check if already notified today
                        today = datetime.now().date()
                        existing = Notification.query.filter(
                            Notification.user_id == user.id,
                            Notification.stock_id == stock.id,
                            Notification.notification_type == 'DROP',
                            db.func.date(Notification.created_at) == today
                        ).first()
                        
                        if not existing:
                            notif = Notification(
                                user_id=user.id,
                                stock_id=stock.id,
                                notification_type='DROP',
                                title=f'{stock.symbol} dropped significantly',
                                message=f'{stock.name} has dropped {abs(change_percent):.2f}% today. Current price: ₹{live_price:,.2f}'
                            )
                            db.session.add(notif)
                            
                            email_data = {
                                'stock_name': stock.name,
                                'symbol': stock.symbol,
                                'type': 'DROP',
                                'live_price': live_price,
                                'predicted_price': live_price * (1 + abs(change_percent)/100),
                                'confidence': 90,
                                'change_percent': change_percent,
                                'trend': 'bearish',
                                'message': f'Alert: Stock has dropped {abs(change_percent):.2f}% today!'
                            }
                            
                            if send_notification_email(user.email, email_data):
                                notif.email_sent = True
                
                # Check predictions
                if setting.notify_on_prediction and stock.has_model:
                    # Get latest prediction
                    latest_pred = Prediction.query.filter_by(
                        stock_id=stock.id
                    ).order_by(Prediction.created_at.desc()).first()
                    
                    if latest_pred and latest_pred.confidence > 60:
                        predicted_price = latest_pred.predicted_price
                        price_diff_percent = ((predicted_price - live_price) / live_price) * 100
                        
                        # Check if significant difference
                        if abs(price_diff_percent) > 3:
                            # Check if already notified for this prediction
                            existing = Notification.query.filter(
                                Notification.user_id == user.id,
                                Notification.stock_id == stock.id,
                                Notification.created_at > latest_pred.created_at
                            ).first()
                            
                            if not existing:
                                notif_type = 'BUY' if price_diff_percent > 0 else 'SELL'
                                
                                notif = Notification(
                                    user_id=user.id,
                                    stock_id=stock.id,
                                    notification_type=notif_type,
                                    title=f'{notif_type} signal for {stock.symbol}',
                                    message=f'AI predicts {stock.name} may {"rise" if price_diff_percent > 0 else "fall"} by {abs(price_diff_percent):.2f}%. Confidence: {latest_pred.confidence:.1f}%'
                                )
                                db.session.add(notif)
                                
                                email_data = {
                                    'stock_name': stock.name,
                                    'symbol': stock.symbol,
                                    'type': notif_type,
                                    'live_price': live_price,
                                    'predicted_price': predicted_price,
                                    'confidence': latest_pred.confidence,
                                    'change_percent': price_diff_percent,
                                    'trend': latest_pred.trend,
                                    'message': f'AI suggests {notif_type} - Expected change: {price_diff_percent:+.2f}%'
                                }
                                
                                if send_notification_email(user.email, email_data):
                                    notif.email_sent = True
            
            db.session.commit()
            print(f"[{datetime.now()}] Notification monitoring completed")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in notification monitoring: {e}")

def update_predictions(app):
    """Update predictions with actual prices"""
    with app.app_context():
        from models import db, Prediction, Stock
        from utils.stock_data import get_google_stock_data
        
        try:
            # Get predictions from yesterday that don't have actual price
            yesterday = (datetime.now() - timedelta(days=1)).date()
            
            predictions = Prediction.query.filter(
                Prediction.prediction_date == yesterday,
                Prediction.actual_price.is_(None)
            ).all()
            
            for pred in predictions:
                stock = pred.stock
                live_data = get_google_stock_data(stock.symbol)
                
                if live_data:
                    pred.actual_price = live_data['closing_price']
            
            db.session.commit()
            print(f"[{datetime.now()}] Updated {len(predictions)} predictions with actual prices")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating predictions: {e}")

def retrain_models(app):
    """Periodically retrain models with new data"""
    with app.app_context():
        from models import db, Stock
        from utils.stock_data import get_historical_data_yfinance
        from utils.ml_model import StockPredictionModel, get_model_path
        import pandas as pd
        
        try:
            # Get stocks that need retraining (older than 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            
            stocks = Stock.query.filter(
                Stock.has_model == True,
                Stock.last_trained < week_ago
            ).all()
            
            for stock in stocks:
                print(f"Retraining model for {stock.symbol}...")
                
                # Download latest data
                df = get_historical_data_yfinance(stock.symbol, period='5y')
                
                if df is not None and len(df) >= 100:
                    model = StockPredictionModel(stock.symbol)
                    result = model.train(df)
                    
                    if result['success']:
                        model_path = get_model_path(stock.symbol)
                        model.save_model(model_path)
                        
                        stock.model_version = result['model_version']
                        stock.last_trained = datetime.utcnow()
                        
                        print(f"Model retrained for {stock.symbol} - Accuracy: {result['accuracy']:.2f}%")
            
            db.session.commit()
            print(f"[{datetime.now()}] Model retraining completed")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error retraining models: {e}")

def start_scheduler(app):
    """Start background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Monitor notifications every 5 minutes
    scheduler.add_job(
        func=lambda: monitor_notifications(app),
        trigger=IntervalTrigger(minutes=5),
        id='monitor_notifications',
        name='Monitor stock notifications',
        replace_existing=True
    )
    
    # Update predictions daily at 4 PM (after market close)
    scheduler.add_job(
        func=lambda: update_predictions(app),
        trigger='cron',
        hour=16,
        minute=0,
        id='update_predictions',
        name='Update predictions with actual prices',
        replace_existing=True
    )
    
    # Retrain models weekly on Sunday at 2 AM
    scheduler.add_job(
        func=lambda: retrain_models(app),
        trigger='cron',
        day_of_week='sun',
        hour=2,
        minute=0,
        id='retrain_models',
        name='Retrain ML models',
        replace_existing=True
    )
    
    scheduler.start()
    print("Background scheduler started")
    
    # Shut down scheduler on exit
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler
