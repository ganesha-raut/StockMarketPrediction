"""
Stock Monitoring System
Continuously monitors stocks and sends email alerts for risks and opportunities
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from utils.enhanced_ml_model_lite import EnhancedStockPredictionModelLite
from utils.email_notifier import EmailNotifier
from app import db, create_app
from models import Stock, User, StockAlert, UserWatchlist
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stock_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StockMonitor:
    """Background stock monitoring and alert system"""
    
    def __init__(self, app):
        self.app = app
        self.email_notifier = EmailNotifier()
        self.monitoring = True
        self.check_interval = 3600  # Check every hour (3600 seconds)
        
    def load_enhanced_model(self, symbol):
        """Load enhanced model for a stock"""
        try:
            model_path = f"models/{symbol}_enhanced_lite.pkl"
            if not os.path.exists(model_path):
                logger.warning(f"Model not found for {symbol}")
                return None
            
            model = EnhancedStockPredictionModelLite(symbol)
            if model.load_model(model_path):
                return model
            return None
        except Exception as e:
            logger.error(f"Error loading model for {symbol}: {e}")
            return None
    
    def get_recent_data(self, symbol, days=300):
        """Fetch recent stock data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            ticker = f"{symbol}.NS"
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                return None
            
            data.reset_index(inplace=True)
            if 'Adj Close' in data.columns:
                data = data.drop('Adj Close', axis=1)
            data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def analyze_stock(self, symbol, prediction_days=30):
        """Analyze a stock and return prediction results"""
        try:
            # Load model
            model = self.load_enhanced_model(symbol)
            if not model:
                return None
            
            # Get data
            data = self.get_recent_data(symbol)
            if data is None or len(data) < 100:
                return None
            
            # Make prediction
            result = model.predict(data, days_ahead=prediction_days)
            
            if not result or 'predicted_price' not in result:
                return None
            
            return {
                'symbol': symbol,
                'current_price': result['current_price'],
                'predicted_price': result['predicted_price'],
                'percent_change': result['percent_change'],
                'confidence': result['confidence'],
                'trend': result['trend'],
                'recommendation': result['recommendation'],
                'risk_percentage': result.get('risk_percentage', 50),
                'prediction_days': prediction_days,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def check_alert_conditions(self, analysis):
        """Check if analysis meets alert conditions"""
        alerts = []
        
        # High Risk Alert (>30%)
        if analysis['risk_percentage'] > 30:
            alerts.append({
                'type': 'HIGH_RISK',
                'severity': 'critical' if analysis['risk_percentage'] > 50 else 'warning',
                'message': f"⚠️ High Risk Alert: {analysis['risk_percentage']:.1f}% risk detected",
                'recommendation': 'SELL' if analysis['risk_percentage'] > 50 else 'REDUCE_POSITION'
            })
        
        # Strong Bullish Alert
        if analysis['trend'] in ['strongly_bullish', 'bullish'] and analysis['percent_change'] > 5:
            alerts.append({
                'type': 'BULLISH_OPPORTUNITY',
                'severity': 'opportunity',
                'message': f"📈 Bullish Opportunity: Expected +{analysis['percent_change']:.2f}% gain",
                'recommendation': 'BUY'
            })
        
        # Strong Bearish Alert
        if analysis['trend'] in ['strongly_bearish', 'bearish'] and analysis['percent_change'] < -5:
            alerts.append({
                'type': 'BEARISH_WARNING',
                'severity': 'warning',
                'message': f"📉 Bearish Warning: Expected {analysis['percent_change']:.2f}% drop",
                'recommendation': 'SELL'
            })
        
        # High Confidence Prediction
        if analysis['confidence'] > 80 and abs(analysis['percent_change']) > 3:
            alerts.append({
                'type': 'HIGH_CONFIDENCE',
                'severity': 'info',
                'message': f"🎯 High Confidence: {analysis['confidence']:.1f}% confidence in prediction",
                'recommendation': analysis['recommendation']
            })
        
        return alerts
    
    def send_alert_email(self, user, stock_symbol, analysis, alert):
        """Send email alert to user"""
        try:
            subject = f"🚨 Stock Alert: {stock_symbol} - {alert['type'].replace('_', ' ').title()}"
            
            # Build email body
            body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background: #0d6efd; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .alert-box {{ 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 5px;
            background: {'#dc3545' if alert['severity'] == 'critical' else '#ffc107' if alert['severity'] == 'warning' else '#28a745' if alert['severity'] == 'opportunity' else '#17a2b8'};
            color: white;
        }}
        .stats {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .stat-row {{ display: flex; justify-content: space-between; margin: 10px 0; }}
        .recommendation {{ 
            font-size: 24px; 
            font-weight: bold; 
            text-align: center; 
            padding: 20px;
            background: {'#dc3545' if alert['recommendation'] == 'SELL' else '#28a745' if alert['recommendation'] == 'BUY' else '#ffc107'};
            color: white;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{ text-align: center; color: #6c757d; margin-top: 30px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Stock Alert: {stock_symbol}</h1>
        <p>{datetime.now().strftime('%d %B %Y, %I:%M %p')}</p>
    </div>
    
    <div class="content">
        <div class="alert-box">
            <h2>{alert['message']}</h2>
        </div>
        
        <div class="stats">
            <h3>📈 Analysis Details</h3>
            <div class="stat-row">
                <strong>Current Price:</strong>
                <span>₹{analysis['current_price']:,.2f}</span>
            </div>
            <div class="stat-row">
                <strong>Predicted Price ({analysis['prediction_days']} days):</strong>
                <span>₹{analysis['predicted_price']:,.2f}</span>
            </div>
            <div class="stat-row">
                <strong>Expected Change:</strong>
                <span style="color: {'green' if analysis['percent_change'] > 0 else 'red'}">
                    {analysis['percent_change']:+.2f}%
                </span>
            </div>
            <div class="stat-row">
                <strong>Confidence Level:</strong>
                <span>{analysis['confidence']:.1f}%</span>
            </div>
            <div class="stat-row">
                <strong>Risk Level:</strong>
                <span>{analysis['risk_percentage']:.1f}%</span>
            </div>
            <div class="stat-row">
                <strong>Trend:</strong>
                <span>{analysis['trend'].replace('_', ' ').title()}</span>
            </div>
        </div>
        
        <div class="recommendation">
            💡 RECOMMENDATION: {alert['recommendation']}
        </div>
        
        <p style="text-align: center; color: #6c757d;">
            <em>This alert was generated by AI analysis. Always do your own research before making investment decisions.</em>
        </p>
    </div>
    
    <div class="footer">
        <p>Stock AI Prediction System</p>
        <p>To manage your alerts, visit the Notifications page in your dashboard.</p>
    </div>
</body>
</html>
"""
            
            return self.email_notifier.send_email(
                to_email=user.email,
                subject=subject,
                body=body,
                is_html=True
            )
            
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {e}")
            return False
    
    def save_alert_to_db(self, user_id, stock_id, analysis, alert):
        """Save alert to database"""
        try:
            stock_alert = StockAlert(
                user_id=user_id,
                stock_id=stock_id,
                alert_type=alert['type'],
                severity=alert['severity'],
                message=alert['message'],
                current_price=analysis['current_price'],
                predicted_price=analysis['predicted_price'],
                percent_change=analysis['percent_change'],
                confidence=analysis['confidence'],
                risk_percentage=analysis['risk_percentage'],
                recommendation=alert['recommendation'],
                is_read=False,
                created_at=datetime.now()
            )
            db.session.add(stock_alert)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving alert to DB: {e}")
            db.session.rollback()
            return False
    
    def monitor_stock_for_user(self, user, stock):
        """Monitor a single stock for a user"""
        try:
            # Check if user has notifications enabled for this stock
            watchlist = UserWatchlist.query.filter_by(
                user_id=user.id,
                stock_id=stock.id
            ).first()
            
            if not watchlist or not watchlist.notifications_enabled:
                return
            
            logger.info(f"Monitoring {stock.symbol} for user {user.email}")
            
            # Analyze stock
            analysis = self.analyze_stock(stock.symbol, prediction_days=30)
            
            if not analysis:
                logger.warning(f"No analysis available for {stock.symbol}")
                return
            
            # Check alert conditions
            alerts = self.check_alert_conditions(analysis)
            
            if not alerts:
                logger.info(f"No alerts for {stock.symbol}")
                return
            
            # Process each alert
            for alert in alerts:
                logger.info(f"Alert for {stock.symbol}: {alert['type']}")
                
                # Save to database
                self.save_alert_to_db(user.id, stock.id, analysis, alert)
                
                # Send email if enabled
                if user.email_notifications:
                    self.send_alert_email(user, stock.symbol, analysis, alert)
                    logger.info(f"Email sent to {user.email} for {stock.symbol}")
            
        except Exception as e:
            logger.error(f"Error monitoring {stock.symbol} for {user.email}: {e}")
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        with self.app.app_context():
            try:
                logger.info("=" * 60)
                logger.info("Starting monitoring cycle")
                logger.info("=" * 60)
                
                # Get all users with email notifications enabled
                users = User.query.filter_by(email_notifications=True).all()
                
                if not users:
                    logger.info("No users with notifications enabled")
                    return
                
                logger.info(f"Monitoring for {len(users)} users")
                
                for user in users:
                    # Get user's watchlist
                    watchlist_items = UserWatchlist.query.filter_by(
                        user_id=user.id,
                        notifications_enabled=True
                    ).all()
                    
                    if not watchlist_items:
                        continue
                    
                    logger.info(f"User {user.email}: {len(watchlist_items)} stocks in watchlist")
                    
                    for item in watchlist_items:
                        stock = Stock.query.get(item.stock_id)
                        if stock and stock.has_model:
                            self.monitor_stock_for_user(user, stock)
                            time.sleep(2)  # Small delay between stocks
                
                logger.info("Monitoring cycle completed")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                import traceback
                traceback.print_exc()
    
    def start(self):
        """Start continuous monitoring"""
        logger.info("🚀 Stock Monitor Started")
        logger.info(f"Check interval: {self.check_interval} seconds ({self.check_interval/60:.0f} minutes)")
        
        while self.monitoring:
            try:
                self.run_monitoring_cycle()
                
                # Wait for next cycle
                logger.info(f"Waiting {self.check_interval/60:.0f} minutes until next check...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                self.monitoring = False
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        logger.info("Stock Monitor Stopped")

def main():
    """Main entry point"""
    # Create Flask app
    app = create_app('development')
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Start monitor
    monitor = StockMonitor(app)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        monitor.stop()

if __name__ == "__main__":
    main()
