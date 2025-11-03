"""
Enhanced ML Model (Lite Version - No TensorFlow dependency)
Uses ensemble methods + Gemini AI sentiment + syntactic intelligence
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
import yfinance as yf
from datetime import datetime, timedelta
import ta
import warnings
warnings.filterwarnings('ignore')

# Handle gemini_ai import
try:
    from .gemini_ai import get_gemini
except ImportError:
    try:
        from gemini_ai import get_gemini
    except ImportError:
        def get_gemini():
            return None

class EnhancedStockPredictionModelLite:
    """Enhanced ML Model using Ensemble Methods (No TensorFlow)"""
    
    def __init__(self, stock_symbol):
        self.stock_symbol = stock_symbol
        self.ensemble_models = {}
        self.feature_scaler = StandardScaler()
        self.price_scaler = MinMaxScaler()
        self.feature_columns = []
        self.model_version = None
        # Try to get Gemini AI, but don't fail if not available
        try:
            self.gemini_ai = get_gemini()
        except:
            self.gemini_ai = None
        
    def fetch_news_sentiment(self, stock_symbol, days_back=7):
        """Fetch and analyze news sentiment"""
        try:
            sentiment_scores = []
            
            # Method 1: Gemini AI sentiment
            if self.gemini_ai:
                try:
                    news_prompt = f"""
                    Analyze recent market sentiment for {stock_symbol} stock over the last {days_back} days.
                    Consider company news, earnings, market trends, and sector performance.
                    Return a sentiment score between -1.0 (very negative) to 1.0 (very positive).
                    Return ONLY the numeric score.
                    """
                    
                    gemini_response = self.gemini_ai._generate_content(news_prompt)
                    if gemini_response:
                        import re
                        score = float(re.findall(r'-?\d+\.?\d*', gemini_response)[0])
                        sentiment_scores.append(max(-1.0, min(1.0, score)))
                except:
                    pass
            
            # Method 2: Technical sentiment
            try:
                ticker = yf.Ticker(f"{stock_symbol}.NS")
                hist = ticker.history(period=f"{days_back}d")
                
                if not hist.empty:
                    price_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                    volume_trend = hist['Volume'].tail(3).mean() / hist['Volume'].head(3).mean()
                    
                    rsi = ta.momentum.RSIIndicator(hist['Close']).rsi().iloc[-1]
                    rsi_sentiment = (rsi - 50) / 50
                    
                    tech_sentiment = (price_change * 2 + (volume_trend - 1) + rsi_sentiment) / 3
                    sentiment_scores.append(max(-1.0, min(1.0, tech_sentiment)))
            except:
                pass
            
            return np.mean(sentiment_scores) if sentiment_scores else 0.0
                
        except Exception as e:
            return 0.0
    
    def create_syntactic_features(self, df):
        """Create advanced syntactic intelligence features"""
        df = df.copy()
        
        # Fractal patterns
        df['fractal_high'] = df['High'].rolling(window=5).apply(
            lambda x: 1 if len(x) >= 5 and x.iloc[2] == max(x) else 0, raw=False
        )
        df['fractal_low'] = df['Low'].rolling(window=5).apply(
            lambda x: 1 if len(x) >= 5 and x.iloc[2] == min(x) else 0, raw=False
        )
        
        # Candlestick patterns
        df['doji'] = np.where(
            abs(df['Close'] - df['Open']) <= (df['High'] - df['Low']) * 0.1, 1, 0
        )
        df['hammer'] = np.where(
            (df['Close'] > df['Open']) & 
            ((df['Open'] - df['Low']) > 2 * (df['Close'] - df['Open'])) &
            ((df['High'] - df['Close']) < (df['Close'] - df['Open'])), 1, 0
        )
        
        # Price dynamics
        df['price_velocity'] = df['Close'].pct_change()
        df['price_acceleration'] = df['price_velocity'].diff()
        
        # VWAP
        df['vwap'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
        df['volume_price_trend'] = df['price_velocity'] * df['Volume']
        
        # Volatility
        df['volatility'] = df['Close'].rolling(window=20).std()
        df['volatility_ratio'] = df['volatility'] / df['volatility'].rolling(window=60).mean()
        
        # Trend strength
        try:
            df['trend_strength'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()
        except:
            df['trend_strength'] = 25.0
        
        df['market_regime'] = np.where(df['trend_strength'] > 25, 1, 0)
        
        # Fibonacci levels
        high_20 = df['High'].rolling(window=20).max()
        low_20 = df['Low'].rolling(window=20).min()
        df['fib_38.2'] = low_20 + 0.382 * (high_20 - low_20)
        df['fib_61.8'] = low_20 + 0.618 * (high_20 - low_20)
        df['dist_from_fib_38.2'] = (df['Close'] - df['fib_38.2']) / df['Close']
        df['dist_from_vwap'] = (df['Close'] - df['vwap']) / df['Close']
        
        # Moving averages
        df['sma_5'] = df['Close'].rolling(window=5).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['sma_200'] = df['Close'].rolling(window=200).mean()
        
        # Crossover signals
        df['golden_cross'] = np.where(
            (df['sma_50'] > df['sma_200']) & (df['sma_50'].shift(1) <= df['sma_200'].shift(1)), 1, 0
        )
        df['death_cross'] = np.where(
            (df['sma_50'] < df['sma_200']) & (df['sma_50'].shift(1) >= df['sma_200'].shift(1)), 1, 0
        )
        
        # Momentum divergence
        df['price_momentum'] = df['Close'] / df['Close'].shift(14) - 1
        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['momentum_divergence'] = df['price_momentum'] - (df['rsi'] - 50) / 50
        
        return df
    
    def prepare_enhanced_features(self, df):
        """Prepare comprehensive feature set"""
        df = df.copy()
        
        # Ensure OHLCV columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Create syntactic features
        df = self.create_syntactic_features(df)
        
        # Technical indicators
        df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        df['macd'] = ta.trend.MACD(df['Close']).macd()
        df['macd_signal'] = ta.trend.MACD(df['Close']).macd_signal()
        df['bb_high'] = ta.volatility.BollingerBands(df['Close']).bollinger_hband()
        df['bb_low'] = ta.volatility.BollingerBands(df['Close']).bollinger_lband()
        df['atr'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()
        
        # Additional indicators
        df['stoch_k'] = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close']).stoch()
        df['williams_r'] = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close']).williams_r()
        df['cci'] = ta.trend.CCIIndicator(df['High'], df['Low'], df['Close']).cci()
        
        # Sentiment
        sentiment_score = self.fetch_news_sentiment(self.stock_symbol)
        df['sentiment_score'] = sentiment_score
        
        # Lag features
        for i in [1, 2, 3, 5, 10, 20]:
            df[f'close_lag_{i}'] = df['Close'].shift(i)
            df[f'volume_lag_{i}'] = df['Volume'].shift(i)
            df[f'rsi_lag_{i}'] = df['rsi'].shift(i)
        
        # Rolling statistics
        for window in [5, 10, 20]:
            df[f'close_mean_{window}'] = df['Close'].rolling(window=window).mean()
            df[f'close_std_{window}'] = df['Close'].rolling(window=window).std()
            df[f'volume_mean_{window}'] = df['Volume'].rolling(window=window).mean()
        
        # Price ratios
        df['high_low_ratio'] = df['High'] / df['Low']
        df['close_open_ratio'] = df['Close'] / df['Open']
        
        # Clean data
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        
        return df
    
    def train(self, df, validation_split=0.2):
        """Train the enhanced prediction model"""
        try:
            print("🚀 Starting enhanced model training...")
            
            df = self.prepare_enhanced_features(df)
            
            if len(df) < 100:
                raise ValueError("Insufficient data for training. Need at least 100 data points.")
            
            print(f"📊 Prepared {len(df)} data points with {len(df.columns)} features")
            
            # Define features
            exclude_cols = ['Close', 'Date'] + [col for col in df.columns if 'date' in col.lower()]
            self.feature_columns = [col for col in df.columns if col not in exclude_cols]
            
            # Prepare data
            X = df[self.feature_columns].values
            y = df['Close'].values
            
            # Scale
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Split
            split_idx = int(len(X_scaled) * (1 - validation_split))
            X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train ensemble models
            print("🧠 Training ensemble models...")
            
            # Random Forest
            print("   Training Random Forest...")
            self.ensemble_models['rf'] = RandomForestRegressor(
                n_estimators=100, max_depth=15, min_samples_split=5, random_state=42, n_jobs=-1
            )
            self.ensemble_models['rf'].fit(X_train, y_train)
            
            # Gradient Boosting
            print("   Training Gradient Boosting...")
            self.ensemble_models['gb'] = GradientBoostingRegressor(
                n_estimators=100, max_depth=8, learning_rate=0.1, random_state=42
            )
            self.ensemble_models['gb'].fit(X_train, y_train)
            
            # AdaBoost
            print("   Training AdaBoost...")
            self.ensemble_models['ada'] = AdaBoostRegressor(
                n_estimators=50, learning_rate=0.1, random_state=42
            )
            self.ensemble_models['ada'].fit(X_train, y_train)
            
            # Ridge Regression
            print("   Training Ridge Regression...")
            self.ensemble_models['ridge'] = Ridge(alpha=1.0)
            self.ensemble_models['ridge'].fit(X_train, y_train)
            
            # Evaluate ensemble
            predictions = []
            for name, model in self.ensemble_models.items():
                pred = model.predict(X_val)
                predictions.append(pred)
            
            # Weighted average
            ensemble_pred = (
                predictions[0] * 0.35 +  # Random Forest
                predictions[1] * 0.35 +  # Gradient Boosting
                predictions[2] * 0.15 +  # AdaBoost
                predictions[3] * 0.15    # Ridge
            )
            
            # Metrics
            mae = mean_absolute_error(y_val, ensemble_pred)
            rmse = np.sqrt(mean_squared_error(y_val, ensemble_pred))
            r2 = r2_score(y_val, ensemble_pred)
            mape = np.mean(np.abs((y_val - ensemble_pred) / y_val)) * 100
            accuracy = max(0, 100 - mape)
            
            self.model_version = f"enhanced_lite_v{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            print(f"✅ Training completed!")
            print(f"📊 MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {r2:.4f}, Accuracy: {accuracy:.2f}%")
            
            return {
                'success': True,
                'mae': float(mae),
                'rmse': float(rmse),
                'r2_score': float(r2),
                'accuracy': float(accuracy),
                'model_version': self.model_version,
                'data_points': len(df),
                'features_count': len(self.feature_columns)
            }
            
        except Exception as e:
            print(f"❌ Error in training: {e}")
            return {'success': False, 'error': str(e)}
    
    def predict(self, recent_data, days_ahead=1):
        """Make enhanced prediction"""
        try:
            if not self.ensemble_models:
                raise ValueError("Model not trained yet")
            
            df = self.prepare_enhanced_features(recent_data)
            
            if len(df) < 1:
                raise ValueError(f"Insufficient data after feature engineering. Need at least 250 days of historical data. Currently have {len(recent_data)} days which resulted in {len(df)} usable data points.")
            
            # Get latest features
            latest_features = df[self.feature_columns].iloc[-1:].values
            X_scaled = self.feature_scaler.transform(latest_features)
            
            # Get predictions from all models
            predictions = {}
            for name, model in self.ensemble_models.items():
                predictions[name] = model.predict(X_scaled)[0]
            
            # Weighted ensemble (base prediction for 1 day)
            base_prediction = (
                predictions['rf'] * 0.35 +
                predictions['gb'] * 0.35 +
                predictions['ada'] * 0.15 +
                predictions['ridge'] * 0.15
            )
            
            # Adjust prediction based on days_ahead
            current_price = float(df['Close'].iloc[-1])
            
            # Calculate trend from recent price movement
            recent_prices = df['Close'].tail(30).values
            price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            
            # Calculate daily change rate from base prediction
            base_change = (base_prediction - current_price) / current_price
            
            # If base change is too small, use trend-based estimation
            if abs(base_change) < 0.001:  # Less than 0.1% change
                # Use recent trend as base
                base_change = price_trend / 30  # Daily trend rate
            
            # Apply time-based scaling with compound growth
            # Use compound interest formula: FV = PV * (1 + r)^t
            daily_rate = base_change
            
            # Calculate compound prediction
            if days_ahead <= 7:
                # Very short term: linear
                growth_factor = 1 + (daily_rate * days_ahead)
            elif days_ahead <= 30:
                # Short term: slight compounding
                growth_factor = (1 + daily_rate) ** (days_ahead * 0.9)
            elif days_ahead <= 90:
                # Medium term: moderate compounding with dampening
                growth_factor = (1 + daily_rate) ** (days_ahead * 0.7)
            elif days_ahead <= 180:
                # Medium-long term: dampened compounding
                growth_factor = (1 + daily_rate) ** (days_ahead * 0.5)
            elif days_ahead <= 365:
                # Long term: heavily dampened
                growth_factor = (1 + daily_rate) ** (days_ahead * 0.35)
            else:
                # Very long term: logarithmic dampening
                growth_factor = (1 + daily_rate) ** (days_ahead * 0.25)
            
            # Calculate final prediction
            final_prediction = current_price * growth_factor
            
            # Add volatility-based adjustment
            volatility = np.std(recent_prices) / np.mean(recent_prices)
            volatility_adjustment = 1 + (volatility * np.sqrt(days_ahead / 365) * 0.5)
            
            # Apply bounds based on volatility
            lower_bound = current_price * (1 - volatility * np.sqrt(days_ahead / 365) * 2)
            upper_bound = current_price * (1 + volatility * np.sqrt(days_ahead / 365) * 3)
            
            # Ensure prediction is within reasonable bounds
            final_prediction = max(lower_bound, min(upper_bound, final_prediction))
            final_prediction = max(current_price * 0.3, min(current_price * 3.0, final_prediction))
            
            # Calculate confidence (decreases with longer timeframes)
            pred_std = np.std(list(predictions.values()))
            avg_pred = np.mean(list(predictions.values()))
            base_confidence = max(40, min(95, 85 - (pred_std / avg_pred) * 100))
            
            # Reduce confidence for longer predictions
            if days_ahead <= 7:
                confidence = base_confidence
            elif days_ahead <= 30:
                confidence = base_confidence * 0.95
            elif days_ahead <= 90:
                confidence = base_confidence * 0.85
            elif days_ahead <= 180:
                confidence = base_confidence * 0.75
            elif days_ahead <= 365:
                confidence = base_confidence * 0.65
            else:
                confidence = base_confidence * 0.55
            
            confidence = max(40, min(95, confidence))
            
            # Analysis
            price_diff = final_prediction - current_price
            percent_change = (price_diff / current_price) * 100
            
            # Trend
            if percent_change > 2.0:
                trend, recommendation = 'strongly_bullish', 'STRONG_BUY'
            elif percent_change > 0.5:
                trend, recommendation = 'bullish', 'BUY'
            elif percent_change < -2.0:
                trend, recommendation = 'strongly_bearish', 'STRONG_SELL'
            elif percent_change < -0.5:
                trend, recommendation = 'bearish', 'SELL'
            else:
                trend, recommendation = 'neutral', 'HOLD'
            
            # Risk
            volatility = df['Close'].tail(20).std()
            risk_percentage = min(100, abs(percent_change) * 1.5 + (volatility / current_price) * 100)
            
            sentiment_score = df['sentiment_score'].iloc[-1]
            
            return {
                'success': True,
                'predicted_price': float(final_prediction),
                'current_price': current_price,
                'price_change': float(price_diff),
                'percent_change': float(percent_change),
                'confidence': float(confidence),
                'trend': trend,
                'recommendation': recommendation,
                'risk_percentage': float(risk_percentage),
                'sentiment_score': float(sentiment_score),
                'model_version': self.model_version,
                'individual_predictions': {k: float(v) for k, v in predictions.items()}
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def save_model(self, filepath):
        """Save model"""
        try:
            model_data = {
                'feature_scaler': self.feature_scaler,
                'feature_columns': self.feature_columns,
                'model_version': self.model_version,
                'stock_symbol': self.stock_symbol,
                'ensemble_models': self.ensemble_models
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            joblib.dump(model_data, filepath)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath):
        """Load model"""
        try:
            if not os.path.exists(filepath):
                return False
            
            model_data = joblib.load(filepath)
            self.feature_scaler = model_data['feature_scaler']
            self.feature_columns = model_data['feature_columns']
            self.model_version = model_data['model_version']
            self.stock_symbol = model_data['stock_symbol']
            self.ensemble_models = model_data['ensemble_models']
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

def get_enhanced_model_path(stock_symbol):
    """Get model path"""
    return f"models/{stock_symbol}_enhanced_lite.pkl"

def load_or_create_enhanced_model(stock_symbol):
    """Load or create model"""
    model = EnhancedStockPredictionModelLite(stock_symbol)
    model_path = get_enhanced_model_path(stock_symbol)
    
    if os.path.exists(model_path):
        if model.load_model(model_path):
            return model
    
    return model
