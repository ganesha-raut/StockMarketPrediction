from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Email notifications enabled
    email_notifications = db.Column(db.Boolean, default=True)
    
    # Relationships
    watchlist = db.relationship('Watchlist', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    notification_settings = db.relationship('NotificationSetting', backref='user', lazy=True, cascade='all, delete-orphan')
    user_watchlist = db.relationship('UserWatchlist', backref='user', lazy=True, cascade='all, delete-orphan')
    stock_alerts = db.relationship('StockAlert', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class OTP(db.Model):
    """OTP model for email verification"""
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)  # 'registration', 'password_reset', 'email_change'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<OTP {self.email} - {self.purpose}>'

class Stock(db.Model):
    """Stock model for storing stock information"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    exchange = db.Column(db.String(20), default='NSE')
    sector = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    has_model = db.Column(db.Boolean, default=False)
    model_version = db.Column(db.String(50))
    last_trained = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    historical_data = db.relationship('HistoricalData', backref='stock', lazy=True, cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='stock', lazy=True, cascade='all, delete-orphan')
    news_sentiment = db.relationship('NewsSentiment', backref='stock', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'

class HistoricalData(db.Model):
    """Historical stock data"""
    __tablename__ = 'historical_data'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger)
    dividend = db.Column(db.Float, default=0.0)
    
    # Technical indicators
    sma_20 = db.Column(db.Float)
    sma_50 = db.Column(db.Float)
    ema_12 = db.Column(db.Float)
    ema_26 = db.Column(db.Float)
    rsi = db.Column(db.Float)
    macd = db.Column(db.Float)
    macd_signal = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('stock_id', 'date', name='_stock_date_uc'),)
    
    def __repr__(self):
        return f'<HistoricalData {self.stock_id} - {self.date}>'

class Prediction(db.Model):
    """ML model predictions"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    prediction_date = db.Column(db.Date, nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    actual_price = db.Column(db.Float)
    confidence = db.Column(db.Float)
    trend = db.Column(db.String(20))  # 'bullish', 'bearish', 'neutral'
    prediction_type = db.Column(db.String(20))  # 'intraday', 'long_term'
    
    # Additional metrics
    risk_percentage = db.Column(db.Float)
    sentiment_score = db.Column(db.Float)
    recommendation = db.Column(db.String(20))  # 'BUY', 'SELL', 'HOLD'
    
    model_version = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Prediction {self.stock_id} - {self.prediction_date}>'

class NewsSentiment(db.Model):
    """News sentiment analysis"""
    __tablename__ = 'news_sentiment'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    headline = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(200))
    url = db.Column(db.Text)
    sentiment = db.Column(db.String(20))  # 'positive', 'negative', 'neutral'
    sentiment_score = db.Column(db.Float)  # -1 to +1
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NewsSentiment {self.stock_id} - {self.sentiment}>'

class Watchlist(db.Model):
    """User watchlist"""
    __tablename__ = 'watchlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref='watchlist_items')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'stock_id', name='_user_stock_uc'),)
    
    def __repr__(self):
        return f'<Watchlist User:{self.user_id} Stock:{self.stock_id}>'

class NotificationSetting(db.Model):
    """User notification settings for stocks"""
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    target_price = db.Column(db.Float)
    email_enabled = db.Column(db.Boolean, default=True)
    notify_on_prediction = db.Column(db.Boolean, default=True)
    notify_on_drop = db.Column(db.Boolean, default=True)
    drop_threshold = db.Column(db.Float, default=5.0)  # percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stock = db.relationship('Stock', backref='notification_settings')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'stock_id', name='_user_stock_notif_uc'),)
    
    def __repr__(self):
        return f'<NotificationSetting User:{self.user_id} Stock:{self.stock_id}>'

class Notification(db.Model):
    """Notification history"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)  # 'BUY', 'SELL', 'DROP', 'TARGET'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    email_sent = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.notification_type} - {self.created_at}>'

class EmailConfig(db.Model):
    """Admin configurable email settings"""
    __tablename__ = 'email_config'
    
    id = db.Column(db.Integer, primary_key=True)
    mail_server = db.Column(db.String(200), nullable=False)
    mail_port = db.Column(db.Integer, nullable=False)
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_username = db.Column(db.String(200), nullable=False)
    mail_password = db.Column(db.String(200), nullable=False)
    mail_default_sender = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<EmailConfig {self.mail_server}>'

class ModelTraining(db.Model):
    """Model training history and logs"""
    __tablename__ = 'model_training'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    model_version = db.Column(db.String(50), nullable=False)
    training_start = db.Column(db.DateTime, nullable=False)
    training_end = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)  # 'running', 'completed', 'failed'
    accuracy = db.Column(db.Float)
    mae = db.Column(db.Float)  # Mean Absolute Error
    rmse = db.Column(db.Float)  # Root Mean Square Error
    data_points = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    stock = db.relationship('Stock', backref='training_history')
    
    def __repr__(self):
        return f'<ModelTraining {self.stock_id} - {self.model_version}>'

class MarketStatus(db.Model):
    """Market open/close status"""
    __tablename__ = 'market_status'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    is_open = db.Column(db.Boolean, nullable=False)
    open_time = db.Column(db.Time)
    close_time = db.Column(db.Time)
    holiday_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MarketStatus {self.date} - {"Open" if self.is_open else "Closed"}>'

class UserWatchlist(db.Model):
    """User watchlist with notification settings"""
    __tablename__ = 'user_watchlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    notifications_enabled = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = db.relationship('Stock', backref='user_watchlist')
    
    def __repr__(self):
        return f'<UserWatchlist user={self.user_id} stock={self.stock_id}>'

class StockAlert(db.Model):
    """Stock alerts generated by monitoring system"""
    __tablename__ = 'stock_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # HIGH_RISK, BULLISH_OPPORTUNITY, etc.
    severity = db.Column(db.String(20), nullable=False)  # critical, warning, info, opportunity
    message = db.Column(db.Text, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    percent_change = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    risk_percentage = db.Column(db.Float, nullable=False)
    recommendation = db.Column(db.String(20), nullable=False)  # BUY, SELL, HOLD, etc.
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = db.relationship('Stock', backref='alerts')
    
    def __repr__(self):
        return f'<StockAlert {self.alert_type} for {self.stock_id}>'
