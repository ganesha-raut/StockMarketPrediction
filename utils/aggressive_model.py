"""
Aggressive Stock Prediction Model
Trains and saves models for better predictions
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AggressiveStockModel:
    """Aggressive model for bullish predictions with 20-50% returns"""
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = f"models/{symbol}_aggressive.pkl"
        
    def fetch_training_data(self, years=5):
        """Fetch historical data for training"""
        try:
            ticker = f"{self.symbol}.NS"
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years*365)
            
            # Fetch data
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.error(f"No data for {self.symbol}")
                return None
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None
    
    def create_features(self, df):
        """Create aggressive features for high returns"""
        
        # Price features
        df['Returns'] = df['Close'].pct_change()
        df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Moving averages
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_10'] = df['Close'].rolling(window=10).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_50'] = df['Close'].rolling(window=50).mean()
        df['MA_200'] = df['Close'].rolling(window=200).mean()
        
        # Momentum indicators
        df['Momentum_7'] = df['Close'].pct_change(7)
        df['Momentum_14'] = df['Close'].pct_change(14)
        df['Momentum_30'] = df['Close'].pct_change(30)
        
        # Volatility
        df['Volatility_10'] = df['Returns'].rolling(window=10).std()
        df['Volatility_20'] = df['Returns'].rolling(window=20).std()
        df['Volatility_30'] = df['Returns'].rolling(window=30).std()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Volume features
        df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA_20']
        
        # Trend strength
        df['Trend_7'] = (df['Close'] - df['Close'].shift(7)) / df['Close'].shift(7) * 100
        df['Trend_30'] = (df['Close'] - df['Close'].shift(30)) / df['Close'].shift(30) * 100
        df['Trend_90'] = (df['Close'] - df['Close'].shift(90)) / df['Close'].shift(90) * 100
        
        # Price position
        df['Price_vs_MA20'] = (df['Close'] - df['MA_20']) / df['MA_20'] * 100
        df['Price_vs_MA50'] = (df['Close'] - df['MA_50']) / df['MA_50'] * 100
        df['Price_vs_MA200'] = (df['Close'] - df['MA_200']) / df['MA_200'] * 100
        
        return df
    
    def prepare_training_data(self, df, days_ahead=90):
        """Prepare X and y for training"""
        
        # Create features
        df = self.create_features(df)
        
        # Target: Future price (aggressive - aim for high returns)
        df['Target'] = df['Close'].shift(-days_ahead)
        
        # Drop NaN
        df = df.dropna()
        
        # Feature columns
        feature_cols = [
            'Returns', 'Log_Returns',
            'MA_5', 'MA_10', 'MA_20', 'MA_50', 'MA_200',
            'Momentum_7', 'Momentum_14', 'Momentum_30',
            'Volatility_10', 'Volatility_20', 'Volatility_30',
            'RSI', 'MACD', 'Signal_Line',
            'BB_Width', 'Volume_Ratio',
            'Trend_7', 'Trend_30', 'Trend_90',
            'Price_vs_MA20', 'Price_vs_MA50', 'Price_vs_MA200'
        ]
        
        X = df[feature_cols].values
        y = df['Target'].values
        
        return X, y, df['Close'].iloc[-1]
    
    def train_model(self, days_ahead=90):
        """Train aggressive model"""
        
        logger.info(f"Training aggressive model for {self.symbol}")
        
        # Fetch data
        df = self.fetch_training_data()
        if df is None:
            return False
        
        # Prepare data
        X, y, current_price = self.prepare_training_data(df, days_ahead)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train ensemble model (aggressive)
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42
        )
        
        gb_model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.1,
            random_state=42
        )
        
        # Train both
        rf_model.fit(X_scaled, y)
        gb_model.fit(X_scaled, y)
        
        # Store both models
        self.model = {
            'rf': rf_model,
            'gb': gb_model,
            'scaler': self.scaler,
            'current_price': current_price,
            'trained_date': datetime.now(),
            'days_ahead': days_ahead,
            'symbol': self.symbol
        }
        
        # Save model
        self.save_model()
        
        logger.info(f"Model trained successfully for {self.symbol}")
        return True
    
    def save_model(self):
        """Save trained model"""
        os.makedirs('models', exist_ok=True)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        logger.info(f"Model saved: {self.model_path}")
    
    def load_model(self):
        """Load trained model"""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model not found: {self.model_path}")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            self.scaler = self.model['scaler']
            logger.info(f"Model loaded: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, days_ahead=90):
        """Make aggressive prediction"""
        
        # Try to load existing model
        if not self.load_model():
            # Train new model if not exists
            logger.info(f"Training new model for {self.symbol}")
            if not self.train_model(days_ahead):
                return None
        
        # Check if model is too old (retrain if > 7 days)
        trained_date = self.model.get('trained_date')
        if trained_date and (datetime.now() - trained_date).days > 7:
            logger.info(f"Model is old, retraining for {self.symbol}")
            self.train_model(days_ahead)
        
        # Fetch recent data
        df = self.fetch_training_data(years=1)
        if df is None:
            return None
        
        # Create features
        df = self.create_features(df)
        df = df.dropna()
        
        # Get latest features
        feature_cols = [
            'Returns', 'Log_Returns',
            'MA_5', 'MA_10', 'MA_20', 'MA_50', 'MA_200',
            'Momentum_7', 'Momentum_14', 'Momentum_30',
            'Volatility_10', 'Volatility_20', 'Volatility_30',
            'RSI', 'MACD', 'Signal_Line',
            'BB_Width', 'Volume_Ratio',
            'Trend_7', 'Trend_30', 'Trend_90',
            'Price_vs_MA20', 'Price_vs_MA50', 'Price_vs_MA200'
        ]
        
        X_latest = df[feature_cols].iloc[-1:].values
        X_scaled = self.scaler.transform(X_latest)
        
        # Predict with both models
        rf_pred = self.model['rf'].predict(X_scaled)[0]
        gb_pred = self.model['gb'].predict(X_scaled)[0]
        
        # Ensemble prediction (weighted average)
        base_prediction = (rf_pred * 0.6 + gb_pred * 0.4)
        
        # Apply AGGRESSIVE BULLISH multiplier based on days
        current_price = df['Close'].iloc[-1]
        
        # Base change from model
        price_change = base_prediction - current_price
        percent_change_base = (price_change / current_price) * 100
        
        # AGGRESSIVE BULLISH TARGETS
        if days_ahead <= 7:
            target_return = 8.0  # Target 8% for 7 days
        elif days_ahead <= 30:
            target_return = 15.0  # Target 15% for 30 days
        elif days_ahead <= 90:
            target_return = 25.0  # Target 25% for 90 days
        else:
            target_return = 40.0  # Target 40% for 365 days
        
        # If model predicts negative or low returns, override with bullish target
        if percent_change_base < target_return * 0.5:
            # Use aggressive target
            aggressive_prediction = current_price * (1 + target_return / 100)
            aggressive_change = aggressive_prediction - current_price
        else:
            # Model is already bullish, amplify it
            multiplier = 1.5
            aggressive_change = price_change * multiplier
            aggressive_prediction = current_price + aggressive_change
        
        # Calculate metrics
        percent_change = (aggressive_prediction - current_price) / current_price * 100
        
        # Calculate confidence
        volatility = df['Volatility_20'].iloc[-1]
        confidence = 85 - (volatility * 1000) - (days_ahead / 365 * 15)
        confidence = max(min(confidence, 95), 50)
        
        return {
            'current_price': float(current_price),
            'predicted_price': float(aggressive_prediction),
            'price_change': float(aggressive_change),
            'percent_change': float(percent_change),
            'confidence': float(confidence),
            'model_age_days': (datetime.now() - self.model['trained_date']).days,
            'rsi': float(df['RSI'].iloc[-1]),
            'momentum_30': float(df['Momentum_30'].iloc[-1] * 100),
            'volatility': float(volatility * 100)
        }


def get_aggressive_model(symbol, company_name):
    """Get or create aggressive model instance"""
    return AggressiveStockModel(symbol, company_name)
