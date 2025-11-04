"""
Unified Stock Predictor
Handles both intraday (1 day) and long-term (2-30 days) predictions
Uses live data for intraday, historical data for long-term
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
import logging
import requests
from utils.stock_data import get_google_stock_data, get_stock_news
from utils.gemini_ai import get_gemini
from config import Config

logger = logging.getLogger(__name__)

class UnifiedPredictor:
    """Unified predictor for 1-30 days stock predictions"""
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.model_rf = None
        self.model_gb = None
        self.scaler = StandardScaler()
        self.model_dir = 'ml_models/unified'
        self.api_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
        
        os.makedirs(self.model_dir, exist_ok=True)
    
    def fetch_live_data(self):
        """Fetch live stock data from Google Finance"""
        try:
            return get_google_stock_data(self.symbol)
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            return None
    
    def fetch_historical_data(self, period='1y'):
        """Fetch historical data from yfinance"""
        try:
            ticker = f"{self.symbol}.NS"
            data = yf.download(ticker, period=period, progress=False)
            
            if data.empty:
                ticker = f"{self.symbol}.BO"
                data = yf.download(ticker, period=period, progress=False)
            
            return data if not data.empty else None
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Calculate all technical indicators"""
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Flatten MultiIndex columns if present (from yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            # Get the first level (column names like 'Close', 'High', etc.)
            df.columns = df.columns.get_level_values(0)
        
        # Remove any duplicate column names that might exist
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Ensure we have the required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}. Available columns: {df.columns.tolist()}")
        
        # Moving Averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        bb_middle = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Middle'] = bb_middle
        df['BB_Upper'] = bb_middle + (bb_std * 2)
        df['BB_Lower'] = bb_middle - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Volatility
        df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
        
        # Volume indicators
        df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
        
        # Momentum
        df['Momentum_5'] = df['Close'].pct_change(periods=5)
        df['Momentum_10'] = df['Close'].pct_change(periods=10)
        df['Momentum_20'] = df['Close'].pct_change(periods=20)
        
        # Rate of Change
        df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        
        # Average True Range
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Stochastic Oscillator
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['Stochastic'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
        
        return df
    
    def analyze_news_sentiment(self):
        """Analyze news sentiment and understand market trends using AI"""
        try:
            news_items = get_stock_news(self.symbol, limit=15)
            
            if not news_items:
                return {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'news_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'trend_analysis': 'No news available',
                    'key_factors': []
                }
            
            # Get latest news with details
            news_text = "\n".join([f"- {item['title']}" for item in news_items[:15]])
            
            prompt = f"""Analyze the latest news for {self.company_name} ({self.symbol}) and understand the market trend:

LATEST NEWS:
{news_text}

Provide detailed analysis:
1. SCORE: [number between -1.0 (very bearish) to 1.0 (very bullish)]
2. LABEL: [bullish/bearish/neutral]
3. POSITIVE: [count of positive news]
4. NEGATIVE: [count of negative news]
5. NEUTRAL: [count of neutral news]
6. TREND: [One sentence about the overall market trend based on news]
7. KEY_FACTORS: [List 2-3 key factors affecting the stock, separated by |]

Example format:
SCORE: 0.6
LABEL: bullish
POSITIVE: 8
NEGATIVE: 2
NEUTRAL: 5
TREND: Strong positive momentum driven by earnings growth and sector tailwinds
KEY_FACTORS: Q3 earnings beat expectations | New product launch | Sector upgrade by analysts
"""
            
            headers = {'Content-Type': 'application/json'}
            data = {"prompt": prompt}
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code != 200:
                return {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'news_count': len(news_items),
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'trend_analysis': 'API error - unable to analyze',
                    'key_factors': [],
                    'latest_news': [item['title'] for item in news_items[:5]]
                }
            
            result = response.json()
            text = (result.get('text') or result.get('response') or result.get('output') or '').strip()
            
            # Parse response
            sentiment_score = 0.0
            sentiment_label = 'neutral'
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            trend_analysis = ''
            key_factors = []
            
            for line in text.split('\n'):
                line_upper = line.upper()
                if 'SCORE:' in line_upper:
                    try:
                        sentiment_score = float(line.split(':')[1].strip())
                    except:
                        pass
                elif 'LABEL:' in line_upper:
                    sentiment_label = line.split(':')[1].strip().lower()
                elif 'POSITIVE:' in line_upper:
                    try:
                        positive_count = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'NEGATIVE:' in line_upper:
                    try:
                        negative_count = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'NEUTRAL:' in line_upper:
                    try:
                        neutral_count = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'TREND:' in line_upper:
                    trend_analysis = line.split(':', 1)[1].strip()
                elif 'KEY_FACTORS:' in line_upper:
                    factors_text = line.split(':', 1)[1].strip()
                    key_factors = [f.strip() for f in factors_text.split('|') if f.strip()]
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'news_count': len(news_items),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'trend_analysis': trend_analysis or 'Market sentiment is mixed',
                'key_factors': key_factors or ['No specific factors identified'],
                'latest_news': [item['title'] for item in news_items[:5]]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'news_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'trend_analysis': 'Unable to analyze news',
                'key_factors': [],
                'latest_news': []
            }
    
    def train_model(self):
        """Train ML models"""
        try:
            logger.info(f"Training unified model for {self.symbol}")
            
            # Fetch historical data
            hist_data = self.fetch_historical_data(period='2y')
            
            if hist_data is None or hist_data.empty:
                logger.error("No historical data available")
                return False
            
            # Calculate indicators
            hist_data = self.calculate_technical_indicators(hist_data)
            hist_data = hist_data.dropna()
            
            if len(hist_data) < 100:
                logger.error("Insufficient data for training")
                return False
            
            # Prepare features and target
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width',
                'Volatility', 'Volume_Ratio',
                'Momentum_5', 'Momentum_10', 'Momentum_20',
                'ROC', 'ATR', 'Stochastic'
            ]
            
            X = hist_data[feature_columns].values
            y = hist_data['Close'].values
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest
            self.model_rf = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            self.model_rf.fit(X_train_scaled, y_train)
            
            # Train Gradient Boosting
            self.model_gb = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.model_gb.fit(X_train_scaled, y_train)
            
            # Save models
            model_path = os.path.join(self.model_dir, f'{self.symbol}_unified.pkl')
            joblib.dump({
                'model_rf': self.model_rf,
                'model_gb': self.model_gb,
                'scaler': self.scaler
            }, model_path)
            
            logger.info(f"Model trained and saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_model(self):
        """Load trained model"""
        try:
            model_path = os.path.join(self.model_dir, f'{self.symbol}_unified.pkl')
            
            if os.path.exists(model_path):
                data = joblib.load(model_path)
                self.model_rf = data['model_rf']
                self.model_gb = data['model_gb']
                self.scaler = data['scaler']
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, days_ahead=1):
        """
        Make prediction for specified days ahead
        days_ahead: 1 for intraday, 2-30 for long-term
        """
        try:
            # Load or train model
            if not self.load_model():
                if not self.train_model():
                    return {'success': False, 'error': 'Model training failed'}
            
            # Fetch live data (for current price)
            live_data = self.fetch_live_data()
            
            # Fetch historical data
            period = '1mo' if days_ahead == 1 else '6mo'
            hist_data = self.fetch_historical_data(period=period)
            
            if hist_data is None or hist_data.empty:
                return {'success': False, 'error': 'No historical data'}
            
            # Calculate indicators
            logger.info(f"Data before indicators: {len(hist_data)} rows")
            hist_data = self.calculate_technical_indicators(hist_data)
            logger.info(f"Data after indicators: {len(hist_data)} rows")
            
            # Fill NaN values for indicators that need more historical data
            # For SMA_50, if we don't have enough data, use SMA_20 as proxy
            if 'SMA_50' in hist_data.columns and hist_data['SMA_50'].isna().all():
                hist_data['SMA_50'] = hist_data['SMA_20']
            
            # Use forward/backward fill for remaining NaN
            hist_data = hist_data.bfill().ffill()
            
            # Drop any remaining NaN rows (should be minimal now)
            hist_data = hist_data.dropna()
            
            if hist_data.empty or len(hist_data) < 10:
                logger.error(f"Columns with NaN: {hist_data.columns[hist_data.isna().any()].tolist()}")
                return {'success': False, 'error': f'Insufficient data after indicators. Need at least 10 rows, got {len(hist_data)}'}
            
            # Get news sentiment
            news_sentiment = self.analyze_news_sentiment()
            
            # Prepare features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width',
                'Volatility', 'Volume_Ratio',
                'Momentum_5', 'Momentum_10', 'Momentum_20',
                'ROC', 'ATR', 'Stochastic'
            ]
            
            X_latest = hist_data[feature_columns].iloc[-1:].values
            X_scaled = self.scaler.transform(X_latest)
            
            # Get predictions
            pred_rf = self.model_rf.predict(X_scaled)[0]
            pred_gb = self.model_gb.predict(X_scaled)[0]
            
            # Ensemble prediction
            base_prediction = (pred_rf * 0.6 + pred_gb * 0.4)
            
            # Get current price
            if live_data and 'current_price' in live_data:
                current_price = live_data['current_price']
            else:
                current_price = hist_data['Close'].iloc[-1]
            
            # Get technical indicators
            rsi = hist_data['RSI'].iloc[-1]
            macd_hist = hist_data['MACD_Hist'].iloc[-1]
            volatility = hist_data['Volatility'].iloc[-1]
            
            # Adjust prediction based on days ahead
            if days_ahead == 1:
                # INTRADAY - Heavy weight on live data
                predicted_price = self._predict_intraday(
                    base_prediction, current_price, live_data, 
                    news_sentiment, rsi, macd_hist, hist_data
                )
            else:
                # LONG-TERM - Use momentum and trends
                predicted_price = self._predict_longterm(
                    base_prediction, current_price, days_ahead,
                    news_sentiment, rsi, macd_hist, hist_data
                )
            
            # Calculate metrics
            price_change = predicted_price - current_price
            percent_change = (price_change / current_price) * 100
            
            # Determine trend and recommendation
            trend, recommendation = self._determine_trend(
                percent_change, rsi, macd_hist, live_data
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                days_ahead, volatility, news_sentiment, rsi
            )
            
            return {
                'success': True,
                'predicted_price': round(predicted_price, 2),
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(percent_change, 2),
                'confidence': round(confidence, 1),
                'trend': trend,
                'recommendation': recommendation,
                'risk_percentage': round(100 - confidence, 1),
                'days_ahead': days_ahead,
                'prediction_type': 'intraday' if days_ahead == 1 else 'longterm',
                'prediction_date': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d'),
                'live_data': live_data,
                'news_sentiment': news_sentiment,
                'technical_indicators': {
                    'rsi': round(rsi, 2),
                    'macd': round(macd_hist, 2),
                    'volatility': round(volatility * 100, 2),
                    'volume_ratio': round(hist_data['Volume_Ratio'].iloc[-1], 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _predict_intraday(self, base_pred, current_price, live_data, news, rsi, macd, hist_data):
        """Intraday prediction with heavy live data weight"""
        
        predicted_price = base_pred
        
        if live_data and isinstance(live_data, dict):
            # Apply live trend (1% adjustment)
            if live_data.get('trend') == 'bullish':
                predicted_price *= 1.01
            elif live_data.get('trend') == 'bearish':
                predicted_price *= 0.99
            
            # Apply live momentum if significant
            if 'current_price' in live_data:
                last_close = hist_data['Close'].iloc[-1]
                live_change = (live_data['current_price'] - last_close) / last_close
                
                if abs(live_change) > 0.02:
                    predicted_price *= (1 + live_change * 0.5)
        
        # Apply news sentiment (1.5% max)
        predicted_price *= (1 + news['sentiment_score'] * 0.015)
        
        # Apply RSI adjustment
        if rsi > 70:
            predicted_price *= 0.98  # Overbought
        elif rsi < 30:
            predicted_price *= 1.02  # Oversold
        
        # Apply MACD adjustment
        if macd < 0:
            predicted_price *= 0.99  # Bearish
        
        return predicted_price
    
    def _predict_longterm(self, base_pred, current_price, days, news, rsi, macd, hist_data):
        """Long-term prediction with momentum and trends"""
        
        # Calculate daily returns and momentum
        daily_returns = hist_data['Close'].pct_change().dropna()
        avg_daily_return = daily_returns.mean()
        volatility = daily_returns.std()
        
        # Apply momentum
        momentum_factor = 1 + (avg_daily_return * days)
        predicted_price = base_pred * momentum_factor
        
        # Apply news sentiment (stronger for longer periods)
        sentiment_factor = 1 + (news['sentiment_score'] * 0.02 * (days / 30))
        predicted_price *= sentiment_factor
        
        # Add volatility-based uncertainty
        volatility_adjustment = volatility * np.sqrt(days)
        predicted_price *= (1 + np.random.uniform(-volatility_adjustment, volatility_adjustment) * 0.3)
        
        return predicted_price
    
    def _determine_trend(self, percent_change, rsi, macd, live_data):
        """Determine trend and recommendation"""
        
        # Base trend
        if percent_change > 2:
            trend, recommendation = 'bullish', 'STRONG BUY'
        elif percent_change > 0.5:
            trend, recommendation = 'bullish', 'BUY'
        elif percent_change < -2:
            trend, recommendation = 'bearish', 'STRONG SELL'
        elif percent_change < -0.5:
            trend, recommendation = 'bearish', 'SELL'
        else:
            trend, recommendation = 'neutral', 'HOLD'
        
        # Override if indicators disagree
        if rsi > 70 and macd < 0 and recommendation in ['BUY', 'STRONG BUY']:
            recommendation = 'HOLD'
            trend = 'neutral'
        
        if rsi < 30 and macd > 0 and recommendation in ['SELL', 'STRONG SELL']:
            recommendation = 'HOLD'
            trend = 'neutral'
        
        # Override if live data strongly disagrees
        if live_data and isinstance(live_data, dict):
            if live_data.get('trend') == 'bearish' and live_data.get('change_percent', 0) < -1:
                if recommendation in ['BUY', 'STRONG BUY']:
                    recommendation = 'HOLD'
                    trend = 'neutral'
        
        return trend, recommendation
    
    def _calculate_confidence(self, days, volatility, news, rsi):
        """Calculate prediction confidence"""
        
        base_confidence = 85
        
        # Time penalty
        time_penalty = (days / 30) * 15
        
        # Volatility penalty
        volatility_penalty = volatility * 100 * 10
        
        # News boost
        news_boost = 5 if abs(news['sentiment_score']) > 0.5 else 0
        
        confidence = base_confidence - time_penalty - volatility_penalty + news_boost
        
        return max(min(confidence, 95), 50)


# Global cache
_unified_predictors = {}

def get_unified_predictor(symbol, company_name):
    """Get or create unified predictor instance"""
    key = f"{symbol}_{company_name}"
    if key not in _unified_predictors:
        _unified_predictors[key] = UnifiedPredictor(symbol, company_name)
    return _unified_predictors[key]
