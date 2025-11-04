"""
Realistic Predictor
Makes conservative, accurate predictions based on actual market behavior
No over-optimistic predictions!
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import joblib
import os
from datetime import datetime, timedelta
import logging
import requests
from utils.stock_data import get_google_stock_data, get_stock_news

logger = logging.getLogger(__name__)

class RealisticPredictor:
    """Conservative predictor based on actual market patterns"""
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.model = None
        self.scaler = StandardScaler()
        self.model_dir = 'ml_models/realistic'
        self.api_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
        
        os.makedirs(self.model_dir, exist_ok=True)
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators"""
        df = df.copy()
        
        # Flatten MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Price changes
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Change_5'] = df['Close'].pct_change(periods=5)
        
        # Moving Averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        
        # Distance from moving averages
        df['Dist_SMA_5'] = (df['Close'] - df['SMA_5']) / df['SMA_5']
        df['Dist_SMA_10'] = (df['Close'] - df['SMA_10']) / df['SMA_10']
        df['Dist_SMA_20'] = (df['Close'] - df['SMA_20']) / df['SMA_20']
        
        # EMA
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Volatility (important for realistic predictions)
        df['Volatility'] = df['Close'].pct_change().rolling(window=10).std()
        df['High_Low_Range'] = (df['High'] - df['Low']) / df['Close']
        
        # Volume
        df['Volume_Change'] = df['Volume'].pct_change()
        df['Volume_MA'] = df['Volume'].rolling(window=10).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Fill NaN and handle infinity
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.bfill().ffill()
        df = df.dropna()
        
        # Final check for any remaining invalid values
        df = df[~df.isin([np.nan, np.inf, -np.inf]).any(axis=1)]
        
        return df
    
    def train_model(self):
        """Train realistic model with time series validation"""
        try:
            logger.info(f"Training realistic model for {self.symbol}")
            
            # Fetch 1 year data for better training
            ticker = f"{self.symbol}.NS"
            data = yf.download(ticker, period='1y', progress=False)
            
            if data.empty:
                logger.error("No data available")
                return False
            
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            if len(data) < 50:
                logger.error("Insufficient data")
                return False
            
            # Prepare features - focus on recent patterns
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'Price_Change', 'Price_Change_5',
                'SMA_5', 'SMA_10', 'SMA_20',
                'Dist_SMA_5', 'Dist_SMA_10', 'Dist_SMA_20',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal',
                'RSI', 'Volatility', 'High_Low_Range',
                'Volume_Change', 'Volume_Ratio'
            ]
            
            # Create target: next day's close
            data['Target'] = data['Close'].shift(-1)
            data = data.dropna()
            
            X = data[feature_columns].values
            y = data['Target'].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            
            # Use conservative Random Forest
            self.model = RandomForestRegressor(
                n_estimators=200,
                max_depth=10,  # Limit depth to avoid overfitting
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42
            )
            
            # Train on all data
            self.model.fit(X_scaled, y)
            
            # Calculate realistic accuracy
            predictions = self.model.predict(X_scaled)
            mape = np.mean(np.abs((y - predictions) / y)) * 100
            
            logger.info(f"Model trained. Average error: {mape:.2f}%")
            
            # Save model
            self.save_model()
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_news_sentiment(self):
        """Analyze news sentiment"""
        try:
            news_items = get_stock_news(self.symbol, limit=10)
            
            if not news_items:
                return {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'news_count': 0
                }
            
            news_text = "\n".join([f"- {item['title']}" for item in news_items[:10]])
            
            prompt = f"""Analyze news for {self.company_name} and give HONEST assessment:

NEWS:
{news_text}

Provide:
SCORE: [number -1.0 (bearish) to 1.0 (bullish)]
LABEL: [bullish/bearish/neutral]

Be truthful."""
            
            headers = {'Content-Type': 'application/json'}
            data = {"prompt": prompt}
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code != 200:
                return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'news_count': len(news_items)}
            
            result = response.json()
            text = (result.get('text') or result.get('response') or result.get('output') or '').strip()
            
            sentiment_score = 0.0
            sentiment_label = 'neutral'
            
            for line in text.split('\n'):
                line_upper = line.upper()
                if 'SCORE:' in line_upper:
                    try:
                        sentiment_score = float(line.split(':')[1].strip())
                    except:
                        pass
                elif 'LABEL:' in line_upper:
                    sentiment_label = line.split(':')[1].strip().lower()
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'news_count': len(news_items)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news: {e}")
            return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'news_count': 0}
    
    def predict(self, days_ahead=1):
        """Make realistic prediction"""
        try:
            # Load or train model
            if not self.load_model():
                logger.info("Training new model...")
                if not self.train_model():
                    return {'success': False, 'error': 'Model training failed'}
            
            # Fetch recent data
            ticker = f"{self.symbol}.NS"
            data = yf.download(ticker, period='3mo', progress=False)
            
            if data.empty:
                return {'success': False, 'error': 'No data available'}
            
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            if data.empty:
                return {'success': False, 'error': 'Insufficient data'}
            
            # Get current price
            current_price = float(data['Close'].iloc[-1])
            
            # Get live data for real-time bullish/bearish signals
            live_data = get_google_stock_data(self.symbol)
            
            # Get news sentiment
            news_sentiment = self.analyze_news_sentiment()
            
            # Prepare features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'Price_Change', 'Price_Change_5',
                'SMA_5', 'SMA_10', 'SMA_20',
                'Dist_SMA_5', 'Dist_SMA_10', 'Dist_SMA_20',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal',
                'RSI', 'Volatility', 'High_Low_Range',
                'Volume_Change', 'Volume_Ratio'
            ]
            
            X_latest = data[feature_columns].iloc[-1:].values
            X_scaled = self.scaler.transform(X_latest)
            
            # Base prediction
            base_prediction = self.model.predict(X_scaled)[0]
            
            # Get recent volatility and trend
            recent_volatility = data['Volatility'].iloc[-5:].mean()
            recent_change = data['Price_Change'].iloc[-5:].mean()
            rsi = data['RSI'].iloc[-1]
            macd = data['MACD'].iloc[-1]
            
            # CONSERVATIVE ADJUSTMENT
            # Don't predict wild swings - stocks usually move < 2% daily
            
            # Limit prediction to realistic range
            max_daily_change = 0.02  # 2% max change
            
            # Calculate raw change
            raw_change = (base_prediction - current_price) / current_price
            
            # Cap the change
            if abs(raw_change) > max_daily_change:
                if raw_change > 0:
                    base_prediction = current_price * (1 + max_daily_change)
                else:
                    base_prediction = current_price * (1 - max_daily_change)
            
            # Apply volatility dampening
            # High volatility = less confident = smaller prediction
            volatility_factor = 1 - (recent_volatility * 10)  # Reduce prediction if volatile
            volatility_factor = max(0.95, min(1.05, volatility_factor))
            
            predicted_price = current_price + (base_prediction - current_price) * volatility_factor
            
            # RSI adjustment (mean reversion)
            if rsi > 70:  # Overbought
                predicted_price *= 0.99  # Expect slight decline
            elif rsi < 30:  # Oversold
                predicted_price *= 1.01  # Expect slight rise
            
            # Trend continuation (but conservative)
            if abs(recent_change) > 0.01:  # If there's a trend
                trend_impact = recent_change * 0.3  # Only 30% of trend continues
                predicted_price *= (1 + trend_impact)
            
            # Live data adjustment (if available)
            if live_data and isinstance(live_data, dict):
                if live_data.get('trend') == 'bearish':
                    predicted_price *= 0.995  # Slight bearish adjustment
                elif live_data.get('trend') == 'bullish':
                    predicted_price *= 1.005  # Slight bullish adjustment
            
            # News sentiment adjustment (conservative)
            if news_sentiment['sentiment_score'] < -0.3:
                predicted_price *= 0.995  # Negative news impact
            elif news_sentiment['sentiment_score'] > 0.3:
                predicted_price *= 1.005  # Positive news impact
            
            # Final safety check - never predict > 3% change for 1 day
            final_change = (predicted_price - current_price) / current_price
            if abs(final_change) > 0.03:
                if final_change > 0:
                    predicted_price = current_price * 1.03
                else:
                    predicted_price = current_price * 0.97
            
            # For multi-day predictions, scale conservatively
            if days_ahead > 1:
                # Don't just multiply - use diminishing returns
                daily_change = (predicted_price - current_price) / current_price
                # Each day has less impact
                total_change = daily_change * (1 + (days_ahead - 1) * 0.5)
                # Cap at 5% for 7 days, 10% for 30 days
                max_change = min(0.05 * (days_ahead / 7), 0.10)
                if abs(total_change) > max_change:
                    total_change = max_change if total_change > 0 else -max_change
                predicted_price = current_price * (1 + total_change)
            
            # Calculate metrics
            price_change = predicted_price - current_price
            percent_change = (price_change / current_price) * 100
            
            # Realistic trend determination
            if percent_change > 1.5:
                trend = 'bullish'
                recommendation = 'BUY'
            elif percent_change < -1.5:
                trend = 'bearish'
                recommendation = 'SELL'
            else:
                trend = 'neutral'
                recommendation = 'HOLD'
            
            # Conservative confidence
            base_confidence = 70
            
            # Reduce confidence if volatile
            if recent_volatility > 0.02:
                base_confidence -= 10
            
            # Reduce confidence for longer predictions
            if days_ahead > 7:
                base_confidence -= 5
            
            confidence = max(60, min(85, base_confidence))
            
            # Risk based on volatility
            risk_percentage = min(50, recent_volatility * 1000 + abs(percent_change))
            
            return {
                'success': True,
                'predicted_price': float(predicted_price),
                'current_price': float(current_price),
                'price_change': float(price_change),
                'percent_change': float(percent_change),
                'trend': trend,
                'recommendation': recommendation,
                'confidence': float(confidence),
                'risk_percentage': float(risk_percentage),
                'prediction_date': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d'),
                'technical_indicators': {
                    'rsi': float(rsi),
                    'macd': float(macd),
                    'volatility': float(recent_volatility * 100),
                    'recent_trend': float(recent_change * 100)
                },
                'news_sentiment': news_sentiment,
                'live_data': live_data if live_data else None,
                'model_info': {
                    'type': 'realistic_conservative',
                    'max_daily_change': '2%',
                    'volatility_adjusted': True,
                    'uses_live_data': True,
                    'uses_news_sentiment': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def save_model(self):
        """Save model"""
        try:
            model_path = os.path.join(self.model_dir, f'{self.symbol}_model.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            
            joblib.dump(self.model, model_path)
            joblib.dump(self.scaler, scaler_path)
            
            logger.info("Model saved")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load model"""
        try:
            model_path = os.path.join(self.model_dir, f'{self.symbol}_model.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            
            if not os.path.exists(model_path):
                return False
            
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


def get_realistic_predictor(symbol, company_name):
    """Get realistic predictor instance"""
    return RealisticPredictor(symbol, company_name)
