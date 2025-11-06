"""
Adaptive Prediction Monitor Service
Runs continuously, makes predictions at 10 AM, learns from accuracy at market close
Automatically tests and selects best algorithms
"""

import schedule
import time
from datetime import datetime, timedelta
import logging
import pandas as pd
from models import db, Stock, Prediction
from utils.adaptive_predictor import get_adaptive_predictor
from utils.stock_data import get_google_stock_data, check_market_status
from utils.unified_predictor import get_unified_predictor
from utils.advanced_ml_predictor import get_advanced_predictor
from utils.ai_stock_recommender import get_ai_recommender
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import glob
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdaptiveMonitorService:
    """Background service for adaptive predictions and learning"""
    
    def __init__(self, app, email_config=None):
        self.app = app
        self.predictions_made_today = set()
        self.accuracy_checked_today = set()
        self.email_config = email_config or {}
        self.learning_history = []
        self.model_retrain_needed = False
        self.last_model_cleanup = None
    
    def make_morning_predictions(self):
        """Make predictions at 10:00 AM for all active stocks"""
        logger.info("=" * 80)
        logger.info("🌅 MORNING PREDICTION SESSION STARTED")
        logger.info("=" * 80)
        
        with self.app.app_context():
            try:
                # Get all active stocks
                stocks = Stock.query.filter_by(is_active=True).all()
                
                if not stocks:
                    logger.warning("No active stocks found")
                    return
                
                logger.info(f"Found {len(stocks)} active stocks")
                
                success_count = 0
                fail_count = 0
                
                for stock in stocks:
                    try:
                        # Skip if already predicted today
                        today = datetime.now().date()
                        if stock.symbol in self.predictions_made_today:
                            logger.info(f"⏭️  {stock.symbol}: Already predicted today")
                            continue
                        
                        logger.info(f"\n📊 Processing {stock.symbol} ({stock.name})")
                        
                        # Get adaptive predictor
                        predictor = get_adaptive_predictor(stock.symbol, stock.name)
                        
                        # Make prediction
                        result = predictor.predict(days_ahead=1)
                        
                        if not result:
                            logger.error(f"❌ {stock.symbol}: Prediction failed")
                            fail_count += 1
                            continue
                        
                        # Get unified predictor for full analysis
                        unified = get_unified_predictor(stock.symbol, stock.name)
                        full_result = unified.predict(days_ahead=1)
                        
                        if not full_result or not full_result.get('success'):
                            logger.error(f"❌ {stock.symbol}: Full analysis failed")
                            fail_count += 1
                            continue
                        
                        # Save prediction to database
                        prediction = Prediction(
                            stock_id=stock.id,
                            prediction_date=today,
                            target_date=(today + timedelta(days=1)),
                            predicted_price=result['predicted_price'],
                            current_price=result['current_price'],
                            confidence=result['model_accuracy'] * 100,
                            trend=full_result['trend'],
                            prediction_type='intraday_adaptive',
                            risk_percentage=full_result['risk_percentage'],
                            sentiment_score=full_result['news_sentiment']['sentiment_score'],
                            recommendation=full_result['recommendation'],
                            model_version=f"adaptive_{result['algorithm']}",
                            algorithm_used=result['algorithm']
                        )
                        
                        db.session.add(prediction)
                        db.session.commit()
                        
                        # Mark as predicted
                        self.predictions_made_today.add(stock.symbol)
                        
                        logger.info(f"✅ {stock.symbol}: Prediction saved")
                        logger.info(f"   Current: ₹{result['current_price']:.2f}")
                        logger.info(f"   Predicted: ₹{result['predicted_price']:.2f}")
                        logger.info(f"   Algorithm: {result['algorithm']}")
                        logger.info(f"   Trend: {full_result['trend'].upper()}")
                        
                        success_count += 1
                        
                        # Small delay between stocks
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"❌ {stock.symbol}: Error - {e}")
                        fail_count += 1
                        continue
                
                logger.info("\n" + "=" * 80)
                logger.info(f"📊 MORNING SESSION COMPLETE")
                logger.info(f"   Success: {success_count}")
                logger.info(f"   Failed: {fail_count}")
                logger.info("=" * 80)
                
                # Generate AI recommendations
                logger.info("\n🤖 Generating AI stock recommendations...")
                recommender = get_ai_recommender()
                recommendations = recommender.get_recommendations()
                
                if recommendations.get('success'):
                    categorized = recommendations['categorized_stocks']
                    logger.info(f"   Strong Buy: {len(categorized['strong_buy'])} stocks")
                    logger.info(f"   Strong Sell: {len(categorized['strong_sell'])} stocks")
                    
                    # Send email with predictions and recommendations
                    self.send_prediction_email(recommendations)
                else:
                    logger.warning("   No recommendations generated")
                
            except Exception as e:
                logger.error(f"Error in morning predictions: {e}")
                import traceback
                traceback.print_exc()
    
    def check_accuracy_and_learn(self):
        """Check prediction accuracy at market close and learn"""
        logger.info("=" * 80)
        logger.info("🌆 EVENING ACCURACY CHECK & LEARNING SESSION")
        logger.info("=" * 80)
        
        with self.app.app_context():
            try:
                today = datetime.now().date()
                
                # Get today's predictions
                predictions = Prediction.query.filter(
                    Prediction.prediction_date == today,
                    Prediction.prediction_type == 'intraday_adaptive'
                ).all()
                
                if not predictions:
                    logger.warning("No predictions to check today")
                    return
                
                logger.info(f"Found {len(predictions)} predictions to verify")
                
                success_count = 0
                learn_count = 0
                
                for prediction in predictions:
                    try:
                        stock = prediction.stock
                        
                        # Skip if already checked
                        if stock.symbol in self.accuracy_checked_today:
                            logger.info(f"⏭️  {stock.symbol}: Already checked today")
                            continue
                        
                        logger.info(f"\n📊 Checking {stock.symbol}")
                        
                        # Fetch actual closing price
                        ticker = f"{stock.symbol}.NS"
                        data = yf.download(ticker, period='2d', progress=False)
                        
                        if data.empty:
                            logger.error(f"❌ {stock.symbol}: No data available")
                            continue
                        
                        # Flatten MultiIndex
                        if isinstance(data.columns, pd.MultiIndex):
                            data.columns = data.columns.get_level_values(0)
                        
                        actual_price = float(data['Close'].iloc[-1])
                        
                        # Get adaptive predictor
                        predictor = get_adaptive_predictor(stock.symbol, stock.name)
                        
                        # Learn from prediction
                        accuracy = predictor.learn_from_prediction(
                            prediction.predicted_price,
                            actual_price,
                            prediction.prediction_date
                        )
                        
                        # Update prediction record
                        prediction.actual_price = actual_price
                        prediction.accuracy_percentage = accuracy
                        prediction.checked_at = datetime.now()
                        
                        db.session.commit()
                        
                        # Mark as checked
                        self.accuracy_checked_today.add(stock.symbol)
                        
                        # Calculate error
                        error = abs(prediction.predicted_price - actual_price)
                        percent_error = (error / actual_price) * 100
                        
                        logger.info(f"✅ {stock.symbol}: Accuracy checked")
                        logger.info(f"   Predicted: ₹{prediction.predicted_price:.2f}")
                        logger.info(f"   Actual: ₹{actual_price:.2f}")
                        logger.info(f"   Error: ₹{error:.2f} ({percent_error:.2f}%)")
                        logger.info(f"   Accuracy: {accuracy:.2f}%")
                        logger.info(f"   Algorithm: {prediction.algorithm_used}")
                        
                        success_count += 1
                        learn_count += 1
                        
                        # Small delay
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"❌ {stock.symbol}: Error - {e}")
                        continue
                
                logger.info("\n" + "=" * 80)
                logger.info(f"📊 EVENING SESSION COMPLETE")
                logger.info(f"   Checked: {success_count}")
                logger.info(f"   Learned: {learn_count}")
                logger.info("=" * 80)
                
                # Calculate overall accuracy
                total_accuracy = 0
                accuracy_count = 0
                
                for prediction in predictions:
                    if prediction.accuracy_percentage:
                        total_accuracy += prediction.accuracy_percentage
                        accuracy_count += 1
                
                avg_accuracy = total_accuracy / accuracy_count if accuracy_count > 0 else 0
                
                logger.info(f"\n📊 Overall Accuracy: {avg_accuracy:.2f}%")
                
                # Self-learning insights
                self.analyze_learning_insights(predictions, avg_accuracy)
                
                # Get performance stats
                self.log_performance_stats()
                
                # Send accuracy email
                self.send_accuracy_email(predictions, avg_accuracy)
                
            except Exception as e:
                logger.error(f"Error in accuracy check: {e}")
                import traceback
                traceback.print_exc()
    
    def log_performance_stats(self):
        """Log overall performance statistics"""
        try:
            with self.app.app_context():
                stocks = Stock.query.filter_by(is_active=True).all()
                
                logger.info("\n" + "=" * 80)
                logger.info("📈 PERFORMANCE STATISTICS")
                logger.info("=" * 80)
                
                for stock in stocks[:5]:  # Top 5 stocks
                    predictor = get_adaptive_predictor(stock.symbol, stock.name)
                    stats = predictor.get_performance_stats()
                    
                    if stats:
                        logger.info(f"\n{stock.symbol} ({stock.name}):")
                        logger.info(f"  Total Predictions: {stats['total_predictions']}")
                        logger.info(f"  Average Accuracy: {stats['average_accuracy']:.2f}%")
                        logger.info(f"  Recent Accuracy: {stats['recent_accuracy']:.2f}%")
                        logger.info(f"  Current Algorithm: {stats['current_algorithm']}")
                
                logger.info("\n" + "=" * 80)
                
        except Exception as e:
            logger.error(f"Error logging stats: {e}")
    
    def send_email(self, subject, body, is_html=False):
        """Send email notification"""
        try:
            if not self.email_config.get('enabled', False):
                logger.info("📧 Email disabled, skipping...")
                return False
            
            sender = self.email_config.get('sender_email')
            password = self.email_config.get('sender_password')
            recipient = self.email_config.get('recipient_email')
            smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.email_config.get('smtp_port', 587)
            
            if not all([sender, password, recipient]):
                logger.warning("📧 Email configuration incomplete")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    def send_prediction_email(self, recommendations):
        """Send email with predictions and AI recommendations"""
        try:
            subject = f"📊 Stock Predictions & AI Recommendations - {datetime.now().strftime('%Y-%m-%d %I:%M %p')}"
            
            categorized = recommendations['categorized_stocks']
            
            body = f"""<html><head><style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px; }}
                .stock {{ border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .bullish {{ background: #e8f5e9; }}
                .bearish {{ background: #ffebee; }}
                .strong {{ font-weight: bold; border: 2px solid; }}
                .prediction-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                .prediction-table th {{ background: #2196F3; color: white; padding: 10px; text-align: left; }}
                .prediction-table td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                .up {{ color: green; font-weight: bold; }}
                .down {{ color: red; font-weight: bold; }}
            </style></head><body>
            <div class="header">
                <h1>📊 Daily Stock Predictions</h1>
                <p>{datetime.now().strftime('%A, %B %d, %Y - %I:%M %p')}</p>
            </div>
            <div class="section">
                <h2>📈 ALL STOCK PREDICTIONS</h2>
                <table class="prediction-table">
                    <tr>
                        <th>Stock</th>
                        <th>Current Price</th>
                        <th>Predicted Price</th>
                        <th>Change</th>
                        <th>Trend</th>
                        <th>Algorithm</th>
                    </tr>"""
            
            # Get today's predictions from database
            today = datetime.now().date()
            predictions = Prediction.query.filter_by(prediction_date=today).all()
            
            for pred in predictions:
                change = pred.predicted_price - pred.current_price
                change_pct = (change / pred.current_price) * 100
                change_class = 'up' if change > 0 else 'down'
                trend_emoji = '📈' if pred.trend == 'bullish' else '📉'
                
                body += f"""
                    <tr>
                        <td><strong>{pred.stock.symbol}</strong><br><small>{pred.stock.name}</small></td>
                        <td>₹{pred.current_price:.2f}</td>
                        <td>₹{pred.predicted_price:.2f}</td>
                        <td class="{change_class}">{change:+.2f} ({change_pct:+.2f}%)</td>
                        <td>{trend_emoji} {pred.trend.upper()}</td>
                        <td>{pred.algorithm_used or 'N/A'}</td>
                    </tr>"""
            
            body += """
                </table>
            </div>
            <div class="section">
                <h2>🎯 AI RECOMMENDED STOCKS</h2>"""
            
            # Strong Buy
            if categorized['strong_buy']:
                body += "<h3>📈 STRONG BUY (Top Picks)</h3>"
                for stock in categorized['strong_buy'][:5]:
                    body += f"""<div class="stock bullish strong">
                        <strong>{stock['name']} ({stock['symbol']})</strong><br>
                        Expected Gain: <strong style="color: green;">{stock['percent_change']:+.2f}%</strong><br>
                        Confidence: {stock['confidence']:.0f}%<br>
                        Recommendation: <strong>{stock['recommendation']}</strong>
                    </div>"""
            
            # Strong Sell
            if categorized['strong_sell']:
                body += "<h3>📉 STRONG SELL (Avoid These)</h3>"
                for stock in categorized['strong_sell'][:5]:
                    body += f"""<div class="stock bearish strong">
                        <strong>{stock['name']} ({stock['symbol']})</strong><br>
                        Expected Loss: <strong style="color: red;">{stock['percent_change']:+.2f}%</strong><br>
                        Confidence: {stock['confidence']:.0f}%<br>
                        Recommendation: <strong>{stock['recommendation']}</strong>
                    </div>"""
            
            # AI Analysis
            body += f"""<h3>🤖 AI ANALYSIS</h3>
                <div class="stock"><pre style="white-space: pre-wrap;">{recommendations['ai_recommendations']}</pre></div>
            </div>
            <div class="section" style="background: #f5f5f5; padding: 20px;">
                <p><strong>Note:</strong> Accuracy will be checked at 3:30 PM. You'll receive another email with results.</p>
            </div></body></html>"""
            
            self.send_email(subject, body, is_html=True)
            
        except Exception as e:
            logger.error(f"Error sending prediction email: {e}")
    
    def send_accuracy_email(self, predictions, avg_accuracy):
        """Send email with accuracy report"""
        try:
            subject = f"📊 Accuracy Report - {datetime.now().strftime('%Y-%m-%d')} - {avg_accuracy:.1f}%"
            
            body = f"""<html><head><style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background: #2196F3; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px; }}
                .stock {{ border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .good {{ background: #e8f5e9; }}
                .bad {{ background: #ffebee; }}
                .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style></head><body>
            <div class="header">
                <h1>📊 Daily Accuracy Report</h1>
                <p>{datetime.now().strftime('%A, %B %d, %Y - 3:30 PM')}</p>
                <h2>Average Accuracy: {avg_accuracy:.2f}%</h2>
            </div>
            <div class="section">
                <div class="summary">
                    <h3>📈 Summary</h3>
                    <p><strong>Total Predictions:</strong> {len(predictions)}</p>
                    <p><strong>Average Accuracy:</strong> {avg_accuracy:.2f}%</p>
                    <p><strong>High Accuracy (&gt;95%):</strong> {len([p for p in predictions if p.accuracy_percentage and p.accuracy_percentage > 95])}</p>
                    <p><strong>Low Accuracy (&lt;80%):</strong> {len([p for p in predictions if p.accuracy_percentage and p.accuracy_percentage < 80])}</p>
                </div>
                <h2>📋 Individual Stock Accuracy</h2>"""
            
            # Sort by accuracy
            sorted_predictions = sorted([p for p in predictions if p.accuracy_percentage], 
                                      key=lambda x: x.accuracy_percentage, reverse=True)
            
            for pred in sorted_predictions[:10]:  # Top 10
                accuracy_class = 'good' if pred.accuracy_percentage > 90 else 'bad' if pred.accuracy_percentage < 80 else ''
                body += f"""<div class="stock {accuracy_class}">
                    <strong>{pred.stock.name} ({pred.stock.symbol})</strong><br>
                    Predicted: ₹{pred.predicted_price:.2f}<br>
                    Actual: ₹{pred.actual_price:.2f}<br>
                    <strong>Accuracy: {pred.accuracy_percentage:.2f}%</strong><br>
                    Algorithm: {pred.algorithm_used or 'N/A'}
                </div>"""
            
            body += f"""</div>
            <div class="section">
                <h2>🧠 Learning Insights</h2>
                <div class="summary">
                    <p><strong>Model Performance:</strong> {'Excellent' if avg_accuracy > 90 else 'Good' if avg_accuracy > 80 else 'Needs Improvement'}</p>
                    <p><strong>Retraining Needed:</strong> {'Yes - Accuracy below 70%' if avg_accuracy < 70 else 'No - Performance acceptable'}</p>
                    <p><strong>Next Steps:</strong> {'Models will be retrained tomorrow' if avg_accuracy < 70 else 'Continue monitoring'}</p>
                </div>
            </div>
            <div class="section" style="background: #f5f5f5; padding: 20px;">
                <p><strong>Note:</strong> The system learns from these errors and will improve predictions over time.</p>
            </div></body></html>"""
            
            self.send_email(subject, body, is_html=True)
            
        except Exception as e:
            logger.error(f"Error sending accuracy email: {e}")
    
    def analyze_learning_insights(self, predictions, avg_accuracy):
        """Analyze learning insights from predictions"""
        try:
            logger.info("\n🧠 SELF-LEARNING ANALYSIS")
            logger.info("=" * 80)
            
            high_error = [p for p in predictions if p.accuracy_percentage and p.accuracy_percentage < 80]
            trend_errors = [p for p in predictions if p.actual_price and 
                          ((p.trend == 'bullish' and p.actual_price < p.current_price) or
                           (p.trend == 'bearish' and p.actual_price > p.current_price))]
            
            logger.info(f"Total Predictions: {len(predictions)}")
            logger.info(f"Average Accuracy: {avg_accuracy:.2f}%")
            logger.info(f"High Error Stocks: {len(high_error)}")
            logger.info(f"Trend Prediction Errors: {len(trend_errors)}")
            
            # Learning insights
            insights = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'avg_accuracy': avg_accuracy,
                'total_predictions': len(predictions),
                'high_error_count': len(high_error),
                'trend_error_count': len(trend_errors),
                'needs_retraining': avg_accuracy < 70 or len(high_error) > len(predictions) * 0.3
            }
            
            self.learning_history.append(insights)
            
            if insights['needs_retraining']:
                logger.warning("⚠️  ACCURACY BELOW THRESHOLD - RETRAINING RECOMMENDED")
                logger.info("   Models will be retrained in next prediction cycle")
            else:
                logger.info("✅ Accuracy acceptable - No retraining needed")
            
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error analyzing learning insights: {e}")
    
    def delete_old_models(self):
        """Delete old ML models to free space and force retraining"""
        try:
            logger.info("\n🗑️  DELETING OLD MODELS")
            logger.info("=" * 80)
            
            model_dirs = [
                'ml_models/adaptive',
                'ml_models/advanced',
                'ml_models/unified',
                'ml_models/realistic',
                'ml_models/intraday'
            ]
            
            deleted_count = 0
            
            for model_dir in model_dirs:
                if os.path.exists(model_dir):
                    # Get all model files
                    model_files = glob.glob(os.path.join(model_dir, '*.pkl')) + \
                                 glob.glob(os.path.join(model_dir, '*.joblib')) + \
                                 glob.glob(os.path.join(model_dir, '*.h5'))
                    
                    for model_file in model_files:
                        try:
                            os.remove(model_file)
                            deleted_count += 1
                            logger.info(f"   ✅ Deleted: {os.path.basename(model_file)}")
                        except Exception as e:
                            logger.error(f"   ❌ Failed to delete {model_file}: {e}")
            
            logger.info(f"\n📊 Total models deleted: {deleted_count}")
            logger.info("=" * 80)
            
            self.last_model_cleanup = datetime.now()
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old models: {e}")
            return 0
    
    def retrain_all_models(self):
        """Retrain all models from scratch"""
        try:
            logger.info("\n🔄 RETRAINING ALL MODELS")
            logger.info("=" * 80)
            
            with self.app.app_context():
                stocks = Stock.query.filter_by(is_active=True).all()
                
                if not stocks:
                    logger.warning("No active stocks to retrain")
                    return False
                
                success_count = 0
                fail_count = 0
                
                for stock in stocks:
                    try:
                        logger.info(f"\n📊 Retraining model for {stock.symbol}...")
                        
                        # Get predictor (will train new model since old one deleted)
                        predictor = get_advanced_predictor()
                        
                        # Force retrain by making a prediction
                        # This will trigger model creation if not exists
                        result = predictor.predict(stock.symbol, days=1)
                        
                        if result and result.get('success'):
                            logger.info(f"   ✅ {stock.symbol} model retrained")
                            success_count += 1
                        else:
                            logger.warning(f"   ⚠️  {stock.symbol} retrain failed")
                            fail_count += 1
                        
                        # Small delay to avoid overload
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"   ❌ {stock.symbol} error: {e}")
                        fail_count += 1
                        continue
                
                logger.info("\n" + "=" * 80)
                logger.info(f"🎯 RETRAINING COMPLETE")
                logger.info(f"   Success: {success_count}")
                logger.info(f"   Failed: {fail_count}")
                logger.info("=" * 80)
                
                self.model_retrain_needed = False
                return success_count > 0
                
        except Exception as e:
            logger.error(f"Error retraining models: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_and_retrain_if_needed(self):
        """Check if retraining is needed based on accuracy"""
        try:
            # Check learning history
            if not self.learning_history:
                return False
            
            recent_history = self.learning_history[-5:]  # Last 5 days
            avg_accuracy = sum(h['avg_accuracy'] for h in recent_history) / len(recent_history)
            
            logger.info(f"\n📊 Recent Average Accuracy: {avg_accuracy:.2f}%")
            
            # Retrain if accuracy is low
            if avg_accuracy < 70:
                logger.warning("⚠️  ACCURACY BELOW 70% - RETRAINING NEEDED")
                self.model_retrain_needed = True
                return True
            
            # Periodic retraining (every 7 days)
            if self.last_model_cleanup:
                days_since_cleanup = (datetime.now() - self.last_model_cleanup).days
                if days_since_cleanup >= 7:
                    logger.info("📅 7 days since last cleanup - Scheduled retraining")
                    self.model_retrain_needed = True
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking retrain need: {e}")
            return False
    
    def weekly_model_refresh(self):
        """Weekly model refresh - delete old models and retrain"""
        logger.info("\n" + "=" * 80)
        logger.info("🔄 WEEKLY MODEL REFRESH STARTED")
        logger.info("=" * 80)
        
        try:
            # Delete old models
            deleted = self.delete_old_models()
            
            if deleted > 0:
                logger.info("\n⏳ Waiting 5 seconds before retraining...")
                time.sleep(5)
                
                # Retrain all models
                success = self.retrain_all_models()
                
                if success:
                    logger.info("\n✅ WEEKLY REFRESH COMPLETE")
                else:
                    logger.warning("\n⚠️  WEEKLY REFRESH INCOMPLETE")
            else:
                logger.warning("\nNo models to refresh")
            
        except Exception as e:
            logger.error(f"Error in weekly refresh: {e}")
            import traceback
            traceback.print_exc()
    
    def reset_daily_tracking(self):
        """Reset daily tracking at midnight"""
        logger.info("🔄 Resetting daily tracking")
        self.predictions_made_today.clear()
        self.accuracy_checked_today.clear()
        
        # Check if retraining needed
        if self.check_and_retrain_if_needed():
            logger.info("\n🔄 Triggering model retraining...")
            self.delete_old_models()
            time.sleep(5)
            self.retrain_all_models()
    
    def start(self):
        """Start the monitoring service"""
        logger.info("=" * 80)
        logger.info("🚀 ADAPTIVE MONITOR SERVICE STARTING")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Schedule:")
        logger.info("  • 10:00 AM - Make predictions (adaptive algorithms)")
        logger.info("  • 03:45 PM - Check accuracy and learn")
        logger.info("  • 11:59 PM - Reset daily tracking + Auto-retrain check")
        logger.info("  • Every Sunday 2:00 AM - Weekly model refresh")
        logger.info("")
        logger.info("Features:")
        logger.info("  ✅ Tests 8 different ML algorithms")
        logger.info("  ✅ Automatically selects best algorithm")
        logger.info("  ✅ AI stock recommendations")
        logger.info("  ✅ Email notifications with predictions")
        logger.info("  ✅ Learns from prediction errors")
        logger.info("  ✅ Email accuracy reports")
        logger.info("  ✅ Deletes old models automatically")
        logger.info("  ✅ Retrains when accuracy drops below 70%")
        logger.info("  ✅ Weekly model refresh (every Sunday)")
        logger.info("  ✅ Saves performance history")
        logger.info("")
        logger.info("=" * 80)
        
        # Schedule jobs
        schedule.every().day.at("10:00").do(self.make_morning_predictions)
        schedule.every().day.at("15:45").do(self.check_accuracy_and_learn)
        schedule.every().day.at("23:59").do(self.reset_daily_tracking)
        schedule.every().sunday.at("02:00").do(self.weekly_model_refresh)
        
        # Run continuously
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Service stopped by user")
        except Exception as e:
            logger.error(f"Service error: {e}")
            import traceback
            traceback.print_exc()


def start_adaptive_monitor(app, email_config=None):
    """Start the adaptive monitor service"""
    service = AdaptiveMonitorService(app, email_config)
    service.start()
