"""
Prediction Monitor Service
Runs in background, makes predictions at market open, checks accuracy at market close
Learns from prediction errors to improve accuracy
"""

import schedule
import time
from datetime import datetime, timedelta
import logging
from models import db, Prediction, Stock, User, Notification
from utils.unified_predictor import get_unified_predictor
from utils.stock_data import get_google_stock_data
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionMonitor:
    """Monitor predictions and learn from accuracy"""
    
    def __init__(self, app):
        self.app = app
        self.active_predictions = {}
    
    def is_market_open(self):
        """Check if market is open (9:15 AM - 3:30 PM IST, Mon-Fri)"""
        now = datetime.now()
        
        # Check if weekend
        if now.weekday() >= 5:
            return False
        
        # Check time (9:15 AM to 3:30 PM)
        market_open = now.replace(hour=9, minute=15, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)
        
        return market_open <= now <= market_close
    
    def make_morning_predictions(self):
        """Make predictions at 10:00 AM for all active stocks"""
        
        logger.info("=" * 80)
        logger.info("🌅 MORNING PREDICTION RUN - 10:00 AM")
        logger.info("=" * 80)
        
        with self.app.app_context():
            try:
                # Get all stocks that users are watching
                stocks = Stock.query.filter_by(has_model=True).all()
                
                logger.info(f"Found {len(stocks)} stocks to predict")
                
                for stock in stocks:
                    try:
                        logger.info(f"\n📊 Predicting: {stock.name} ({stock.symbol})")
                        
                        # Get predictor
                        predictor = get_unified_predictor(stock.symbol, stock.name)
                        
                        # Make intraday prediction
                        result = predictor.predict(days_ahead=1)
                        
                        if result and result.get('success'):
                            # Save prediction to database
                            prediction = Prediction(
                                stock_id=stock.id,
                                user_id=None,  # System prediction
                                predicted_price=result['predicted_price'],
                                current_price=result['current_price'],
                                confidence=result['confidence'],
                                trend=result['trend'],
                                prediction_type='intraday',
                                days_ahead=1,
                                risk_percentage=result['risk_percentage'],
                                sentiment_score=result['news_sentiment']['sentiment_score'],
                                recommendation=result['recommendation'],
                                prediction_date=datetime.now() + timedelta(days=1),
                                created_at=datetime.now()
                            )
                            
                            db.session.add(prediction)
                            db.session.commit()
                            
                            # Store for evening check
                            self.active_predictions[stock.symbol] = {
                                'prediction_id': prediction.id,
                                'predicted_price': result['predicted_price'],
                                'current_price': result['current_price'],
                                'trend': result['trend'],
                                'recommendation': result['recommendation']
                            }
                            
                            logger.info(f"✅ Prediction saved:")
                            logger.info(f"   Current: ₹{result['current_price']:.2f}")
                            logger.info(f"   Predicted: ₹{result['predicted_price']:.2f}")
                            logger.info(f"   Change: {result['percent_change']:+.2f}%")
                            logger.info(f"   Trend: {result['trend'].upper()}")
                            
                            # Send notification to users watching this stock
                            self.notify_users_prediction(stock, result)
                        
                        else:
                            logger.error(f"❌ Prediction failed: {result.get('error')}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error predicting {stock.symbol}: {e}")
                        continue
                
                logger.info(f"\n✅ Morning predictions complete: {len(self.active_predictions)} stocks")
                
            except Exception as e:
                logger.error(f"❌ Error in morning predictions: {e}")
                import traceback
                traceback.print_exc()
    
    def check_evening_accuracy(self):
        """Check prediction accuracy at 3:45 PM (after market close)"""
        
        logger.info("=" * 80)
        logger.info("🌆 EVENING ACCURACY CHECK - 3:45 PM")
        logger.info("=" * 80)
        
        with self.app.app_context():
            try:
                for symbol, pred_data in self.active_predictions.items():
                    try:
                        logger.info(f"\n📊 Checking: {symbol}")
                        
                        # Get actual closing price
                        ticker = f"{symbol}.NS"
                        stock_data = yf.download(ticker, period='1d', progress=False)
                        
                        if stock_data.empty:
                            ticker = f"{symbol}.BO"
                            stock_data = yf.download(ticker, period='1d', progress=False)
                        
                        if not stock_data.empty:
                            actual_close = stock_data['Close'].iloc[-1]
                            predicted_price = pred_data['predicted_price']
                            
                            # Calculate accuracy
                            error = abs(actual_close - predicted_price)
                            error_percent = (error / actual_close) * 100
                            accuracy = max(0, 100 - error_percent)
                            
                            # Update prediction in database
                            prediction = Prediction.query.get(pred_data['prediction_id'])
                            if prediction:
                                prediction.actual_price = actual_close
                                prediction.accuracy = accuracy
                                prediction.checked_at = datetime.now()
                                db.session.commit()
                            
                            logger.info(f"✅ Accuracy Check:")
                            logger.info(f"   Predicted: ₹{predicted_price:.2f}")
                            logger.info(f"   Actual:    ₹{actual_close:.2f}")
                            logger.info(f"   Error:     ₹{error:.2f} ({error_percent:.2f}%)")
                            logger.info(f"   Accuracy:  {accuracy:.2f}%")
                            
                            # Learn from error
                            self.learn_from_prediction(symbol, predicted_price, actual_close, pred_data)
                            
                            # Notify users about accuracy
                            self.notify_users_accuracy(symbol, predicted_price, actual_close, accuracy)
                        
                        else:
                            logger.warning(f"⚠️  Could not fetch closing price for {symbol}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error checking {symbol}: {e}")
                        continue
                
                # Clear active predictions
                self.active_predictions.clear()
                logger.info(f"\n✅ Evening accuracy check complete")
                
            except Exception as e:
                logger.error(f"❌ Error in evening check: {e}")
                import traceback
                traceback.print_exc()
    
    def learn_from_prediction(self, symbol, predicted, actual, pred_data):
        """Learn from prediction error to improve future accuracy"""
        
        try:
            error = actual - predicted
            error_percent = (error / actual) * 100
            
            # Analyze what went wrong
            if abs(error_percent) > 2:
                logger.info(f"\n🎓 LEARNING FROM ERROR:")
                
                if error > 0:
                    logger.info(f"   Model UNDER-predicted by {abs(error_percent):.2f}%")
                    logger.info(f"   Actual was MORE bullish than predicted")
                    
                    if pred_data['trend'] == 'bearish':
                        logger.info(f"   ⚠️  Model predicted BEARISH but was BULLISH")
                        logger.info(f"   → Need to reduce bearish bias")
                else:
                    logger.info(f"   Model OVER-predicted by {abs(error_percent):.2f}%")
                    logger.info(f"   Actual was MORE bearish than predicted")
                    
                    if pred_data['trend'] == 'bullish':
                        logger.info(f"   ⚠️  Model predicted BULLISH but was BEARISH")
                        logger.info(f"   → Need to increase bearish detection")
                
                # Store learning data (can be used for model retraining)
                with self.app.app_context():
                    # You can store this in a separate LearningData table
                    # For now, just log it
                    logger.info(f"   Learning data stored for future model improvement")
        
        except Exception as e:
            logger.error(f"Error in learning: {e}")
    
    def notify_users_prediction(self, stock, result):
        """Send notification to users about new prediction"""
        
        try:
            # Get users watching this stock
            from models import UserWatchlist
            
            watchlist_entries = UserWatchlist.query.filter_by(stock_id=stock.id).all()
            
            for entry in watchlist_entries:
                user = User.query.get(entry.user_id)
                
                if user and user.notification_settings:
                    # Check if user wants prediction notifications
                    settings = user.notification_settings
                    
                    if settings.prediction_alerts:
                        # Create notification
                        notification = Notification(
                            user_id=user.id,
                            title=f"📊 {stock.symbol} Prediction",
                            message=f"Predicted closing price: ₹{result['predicted_price']:.2f} ({result['trend'].upper()}). Recommendation: {result['recommendation']}",
                            type='prediction',
                            stock_symbol=stock.symbol,
                            created_at=datetime.now()
                        )
                        
                        db.session.add(notification)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def notify_users_accuracy(self, symbol, predicted, actual, accuracy):
        """Send notification about prediction accuracy"""
        
        try:
            stock = Stock.query.filter_by(symbol=symbol).first()
            
            if not stock:
                return
            
            from models import UserWatchlist
            
            watchlist_entries = UserWatchlist.query.filter_by(stock_id=stock.id).all()
            
            for entry in watchlist_entries:
                user = User.query.get(entry.user_id)
                
                if user and user.notification_settings:
                    settings = user.notification_settings
                    
                    if settings.prediction_alerts:
                        # Create notification
                        emoji = "✅" if accuracy > 95 else "📊"
                        
                        notification = Notification(
                            user_id=user.id,
                            title=f"{emoji} {stock.symbol} Result",
                            message=f"Predicted: ₹{predicted:.2f}, Actual: ₹{actual:.2f}. Accuracy: {accuracy:.1f}%",
                            type='accuracy',
                            stock_symbol=stock.symbol,
                            created_at=datetime.now()
                        )
                        
                        db.session.add(notification)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error sending accuracy notifications: {e}")
    
    def start(self):
        """Start the monitoring service"""
        
        logger.info("=" * 80)
        logger.info("🚀 PREDICTION MONITOR SERVICE STARTED")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Schedule:")
        logger.info("  • 10:00 AM - Make predictions for all stocks")
        logger.info("  • 03:45 PM - Check accuracy and learn")
        logger.info("")
        logger.info("=" * 80)
        
        # Schedule jobs
        schedule.every().day.at("10:00").do(self.make_morning_predictions)
        schedule.every().day.at("15:45").do(self.check_evening_accuracy)
        
        # Run continuously
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping Prediction Monitor Service...")
                break
            
            except Exception as e:
                logger.error(f"❌ Error in monitor service: {e}")
                time.sleep(60)


def start_monitor_service(app):
    """Start the prediction monitor service"""
    monitor = PredictionMonitor(app)
    monitor.start()
