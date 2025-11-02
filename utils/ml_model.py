import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from datetime import datetime, timedelta
import ta  # Technical Analysis library

class StockPredictionModel:
    """ML Model for stock price prediction"""
    
    def __init__(self, stock_symbol):
        self.stock_symbol = stock_symbol
        self.model = None
        self.scaler = MinMaxScaler()
        self.feature_columns = []
        self.model_version = None
        
    def prepare_features(self, df):
        """Calculate technical indicators and prepare features"""
        df = df.copy()
        df = df.sort_values('date')
        
        # Ensure we have required columns
        required_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Calculate technical indicators
        
        # Moving Averages
        df['sma_5'] = df['close_price'].rolling(window=5).mean()
        df['sma_10'] = df['close_price'].rolling(window=10).mean()
        df['sma_20'] = df['close_price'].rolling(window=20).mean()
        df['sma_50'] = df['close_price'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close_price'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close_price'].ewm(span=26, adjust=False).mean()
        
        # RSI (Relative Strength Index)
        try:
            df['rsi'] = ta.momentum.RSIIndicator(df['close_price'], window=14).rsi()
        except:
            df['rsi'] = 50.0  # Neutral default
        
        # MACD
        try:
            macd = ta.trend.MACD(df['close_price'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
        except:
            df['macd'] = 0.0
            df['macd_signal'] = 0.0
            df['macd_diff'] = 0.0
        
        # Bollinger Bands
        try:
            bollinger = ta.volatility.BollingerBands(df['close_price'])
            df['bb_high'] = bollinger.bollinger_hband()
            df['bb_low'] = bollinger.bollinger_lband()
            df['bb_mid'] = bollinger.bollinger_mavg()
        except:
            df['bb_high'] = df['close_price']
            df['bb_low'] = df['close_price']
            df['bb_mid'] = df['close_price']
        
        # Price changes
        df['price_change'] = df['close_price'].pct_change()
        df['high_low_diff'] = df['high_price'] - df['low_price']
        df['open_close_diff'] = df['close_price'] - df['open_price']
        
        # Volume indicators
        df['volume_change'] = df['volume'].pct_change()
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        
        # Lag features
        for i in [1, 2, 3, 5, 7]:
            df[f'close_lag_{i}'] = df['close_price'].shift(i)
            df[f'volume_lag_{i}'] = df['volume'].shift(i)
        
        # Dividend rate (if available)
        if 'dividend' in df.columns:
            df['dividend_rate'] = df['dividend'] / df['close_price']
        else:
            df['dividend_rate'] = 0.0
        
        # Day of week and month (cyclical encoding)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['month'] = df['date'].dt.month
            df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Replace infinity values with NaN, then drop
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Drop NaN values
        df = df.dropna()
        
        return df
    
    def train(self, df, sentiment_score=0.0):
        """Train the prediction model"""
        try:
            # Prepare features
            df = self.prepare_features(df)
            
            if len(df) < 100:
                raise ValueError("Insufficient data for training. Need at least 100 data points.")
            
            # Add sentiment score as feature
            df['sentiment_score'] = sentiment_score
            
            # Define feature columns
            self.feature_columns = [
                'open_price', 'high_price', 'low_price', 'volume',
                'sma_5', 'sma_10', 'sma_20', 'sma_50',
                'ema_12', 'ema_26',
                'rsi', 'macd', 'macd_signal', 'macd_diff',
                'bb_high', 'bb_low', 'bb_mid',
                'price_change', 'high_low_diff', 'open_close_diff',
                'volume_change', 'volume_sma_20',
                'close_lag_1', 'close_lag_2', 'close_lag_3', 'close_lag_5', 'close_lag_7',
                'volume_lag_1', 'volume_lag_2', 'volume_lag_3', 'volume_lag_5', 'volume_lag_7',
                'dividend_rate', 'sentiment_score',
                'day_sin', 'day_cos', 'month_sin', 'month_cos'
            ]
            
            # Prepare X and y
            X = df[self.feature_columns].values
            y = df['close_price'].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, shuffle=False
            )
            
            # Train model
            self.model = LinearRegression()
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            # Calculate accuracy (inverse of MAPE)
            mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            accuracy = max(0, 100 - mape)
            
            self.model_version = f"v{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            return {
                'success': True,
                'mae': float(mae),
                'rmse': float(rmse),
                'r2_score': float(r2),
                'accuracy': float(accuracy),
                'model_version': self.model_version,
                'data_points': len(df)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict(self, recent_data, sentiment_score=0.0, days_ahead=1):
        """Make prediction for future price"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
            
            # Prepare features
            df = self.prepare_features(recent_data)
            
            if len(df) == 0:
                raise ValueError("No valid data after feature preparation")
            
            # Get latest data point
            latest = df.iloc[-1:].copy()
            latest['sentiment_score'] = sentiment_score
            
            # Prepare features
            X = latest[self.feature_columns].values
            X_scaled = self.scaler.transform(X)
            
            # Predict
            predicted_price = self.model.predict(X_scaled)[0]
            
            # Calculate confidence based on recent volatility
            recent_volatility = df['close_price'].tail(20).std()
            avg_price = df['close_price'].tail(20).mean()
            volatility_ratio = recent_volatility / avg_price
            
            # Confidence decreases with volatility
            base_confidence = 75.0
            confidence = max(40.0, min(95.0, base_confidence - (volatility_ratio * 100)))
            
            # Determine trend
            current_price = float(df['close_price'].iloc[-1])
            price_diff = predicted_price - current_price
            percent_change = (price_diff / current_price) * 100
            
            if percent_change > 1.0:
                trend = 'bullish'
                recommendation = 'BUY'
            elif percent_change < -1.0:
                trend = 'bearish'
                recommendation = 'SELL'
            else:
                trend = 'neutral'
                recommendation = 'HOLD'
            
            # Calculate risk percentage
            risk_percentage = min(100, abs(percent_change) * 2)
            
            return {
                'success': True,
                'predicted_price': float(predicted_price),
                'current_price': current_price,
                'price_change': float(price_diff),
                'percent_change': float(percent_change),
                'confidence': float(confidence),
                'trend': trend,
                'recommendation': recommendation,
                'risk_percentage': float(risk_percentage),
                'sentiment_score': sentiment_score,
                'model_version': self.model_version
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_model(self, filepath):
        """Save trained model to file"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'model_version': self.model_version,
                'stock_symbol': self.stock_symbol
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            joblib.dump(model_data, filepath)
            return True
            
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath):
        """Load trained model from file"""
        try:
            if not os.path.exists(filepath):
                return False
            
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.model_version = model_data['model_version']
            self.stock_symbol = model_data['stock_symbol']
            
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def update_with_actual(self, predicted_price, actual_price):
        """Update model learning based on actual vs predicted"""
        try:
            # Calculate prediction error
            error = abs(actual_price - predicted_price)
            error_percent = (error / actual_price) * 100
            
            # Log for continuous learning
            return {
                'error': float(error),
                'error_percent': float(error_percent),
                'predicted': float(predicted_price),
                'actual': float(actual_price)
            }
            
        except Exception as e:
            return None

def get_model_path(stock_symbol):
    """Get model file path for a stock"""
    return f"models/{stock_symbol}_model.pkl"

def load_or_create_model(stock_symbol):
    """Load existing model or create new one"""
    model = StockPredictionModel(stock_symbol)
    model_path = get_model_path(stock_symbol)
    
    if os.path.exists(model_path):
        if model.load_model(model_path):
            return model
    
    return model
