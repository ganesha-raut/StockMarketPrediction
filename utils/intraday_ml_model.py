"""
Advanced Intraday ML Model
Combines live stock data, historical patterns, and news sentiment for intraday predictions
Supports predictions from 1 day to 30 days
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime, timedelta
import logging
from utils.stock_data import get_google_stock_data, get_stock_news
from utils.gemini_ai import get_gemini
import requests
from config import Config

logger = logging.getLogger(__name__)

class IntradayMLModel:
    """
    Advanced ML model for intraday and short-term (up to 30 days) predictions
    Features:
    - Real-time live stock data integration
    - Historical price patterns and technical indicators
    - News sentiment analysis using Gemini AI
    - Multiple ML algorithms (Random Forest + Gradient Boosting)
    - Dynamic feature engineering
    """
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.model_rf = None
        self.model_gb = None
        self.scaler = StandardScaler()
        self.model_dir = 'ml_models/intraday'
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize Gemini AI for news analysis - Use REST API
        self.gemini = get_gemini()
        self.api_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
    
    def fetch_live_data(self):
        """Fetch real-time live stock data"""
        try:
            live_data = get_google_stock_data(self.symbol)
            if not live_data:
                logger.warning(f"Could not fetch live data for {self.symbol}")
                return None
            
            return {
                'current_price': live_data['live_price'],
                'open_price': live_data['opening_price'],
                'high_price': live_data['high'],
                'low_price': live_data['low'],
                'volume': live_data.get('volume', 0),
                'change_percent': live_data['percent_change'],
                'trend': live_data['trend']
            }
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            return None
    
    def fetch_historical_data(self, period='1y'):
        """Fetch historical data for training"""
        try:
            ticker = yf.Ticker(f"{self.symbol}.NS")
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.error(f"No historical data for {self.symbol}")
                return None
            
            return hist
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None
    
    def analyze_news_sentiment(self):
        """Analyze news sentiment using Gemini AI REST API"""
        try:
            news_items = get_stock_news(self.symbol, limit=10)
            
            if not news_items:
                return {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'news_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0
                }
            
            # Prepare news summary for AI analysis
            news_text = "\n".join([f"- {item['headline']}" for item in news_items[:5]])
            
            prompt = f"""
Analyze the sentiment of these news headlines for {self.company_name} ({self.symbol}):

{news_text}

Provide:
1. Overall sentiment score (-100 to +100, where -100 is very bearish, 0 is neutral, +100 is very bullish)
2. Sentiment label (bullish/bearish/neutral)
3. Count of positive, negative, and neutral news

Format:
SCORE: [number]
LABEL: [bullish/bearish/neutral]
POSITIVE: [count]
NEGATIVE: [count]
NEUTRAL: [count]
"""
            
            # Call REST API
            headers = {'Content-Type': 'application/json'}
            data = {
                "prompt": prompt
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'news_count': len(news_items),
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0
                }
            
            result = response.json()
            text = (result.get('text') or result.get('response') or result.get('output') or '').strip()
            
            # Parse response
            sentiment_score = 0.0
            sentiment_label = 'neutral'
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
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
            
            return {
                'sentiment_score': sentiment_score / 100.0,  # Normalize to -1 to +1
                'sentiment_label': sentiment_label,
                'news_count': len(news_items),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'news_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators for feature engineering"""
        try:
            # Moving Averages
            df['SMA_5'] = df['Close'].rolling(window=5).mean()
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # Exponential Moving Averages
            df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
            
            # Volatility
            df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Price momentum
            df['Momentum_5'] = df['Close'].pct_change(periods=5)
            df['Momentum_10'] = df['Close'].pct_change(periods=10)
            df['Momentum_20'] = df['Close'].pct_change(periods=20)
            
            # Rate of Change
            df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
            
            # Average True Range (ATR)
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
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def prepare_features(self, df, live_data=None, news_sentiment=None):
        """Prepare features for ML model"""
        try:
            # Calculate technical indicators
            df = self.calculate_technical_indicators(df)
            
            # Drop NaN values
            df = df.dropna()
            
            if df.empty:
                return None, None
            
            # Select features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width',
                'Volatility', 'Volume_Ratio',
                'Momentum_5', 'Momentum_10', 'Momentum_20',
                'ROC', 'ATR', 'Stochastic'
            ]
            
            X = df[feature_columns].values
            y = df['Close'].values
            
            # Add live data features if available
            if live_data:
                # This will be used for prediction, not training
                pass
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return None, None
    
    def train_model(self, force_retrain=False):
        """Train the ML models"""
        try:
            model_path_rf = os.path.join(self.model_dir, f'{self.symbol}_rf.pkl')
            model_path_gb = os.path.join(self.model_dir, f'{self.symbol}_gb.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            
            # Check if model exists and is recent (less than 7 days old)
            if not force_retrain and os.path.exists(model_path_rf):
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path_rf))
                if model_age.days < 7:
                    logger.info(f"Loading existing model for {self.symbol}")
                    self.model_rf = joblib.load(model_path_rf)
                    self.model_gb = joblib.load(model_path_gb)
                    self.scaler = joblib.load(scaler_path)
                    return True
            
            # Fetch historical data
            logger.info(f"Training new model for {self.symbol}")
            hist_data = self.fetch_historical_data(period='2y')
            
            if hist_data is None or hist_data.empty:
                logger.error(f"No data available for training {self.symbol}")
                return False
            
            # Prepare features
            X, y = self.prepare_features(hist_data)
            
            if X is None or len(X) < 100:
                logger.error(f"Insufficient data for training {self.symbol}")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest
            self.model_rf = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
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
            
            # Evaluate models
            rf_score = self.model_rf.score(X_test_scaled, y_test)
            gb_score = self.model_gb.score(X_test_scaled, y_test)
            
            logger.info(f"Model trained - RF Score: {rf_score:.4f}, GB Score: {gb_score:.4f}")
            
            # Save models
            joblib.dump(self.model_rf, model_path_rf)
            joblib.dump(self.model_gb, model_path_gb)
            joblib.dump(self.scaler, scaler_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict(self, days_ahead=1):
        """
        Make prediction for specified number of days ahead (1-30 days)
        Combines ML predictions with live data and news sentiment
        """
        try:
            # Ensure model is trained
            if self.model_rf is None or self.model_gb is None:
                if not self.train_model():
                    return None
            
            # Fetch live data
            live_data = self.fetch_live_data()
            
            # Fetch news sentiment
            news_sentiment = self.analyze_news_sentiment()
            
            # Fetch recent historical data for prediction
            hist_data = self.fetch_historical_data(period='6mo')
            
            if hist_data is None or hist_data.empty:
                logger.error(f"No historical data for prediction")
                return None
            
            # Calculate technical indicators
            hist_data = self.calculate_technical_indicators(hist_data)
            hist_data = hist_data.dropna()
            
            if hist_data.empty:
                return None
            
            # Get latest features
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
            
            # Get predictions from both models
            pred_rf = self.model_rf.predict(X_scaled)[0]
            pred_gb = self.model_gb.predict(X_scaled)[0]
            
            # Ensemble prediction (weighted average)
            base_prediction = (pred_rf * 0.6 + pred_gb * 0.4)
            
            # Get current price
            current_price = live_data['current_price'] if live_data else hist_data['Close'].iloc[-1]
            
            # Adjust prediction based on days ahead
            # For intraday (1 day), use base prediction with minor adjustments
            # For longer periods, apply momentum and trend analysis
            
            if days_ahead == 1:
                # Intraday prediction - HEAVILY weight live data and current market conditions
                if live_data:
                    # Strong factor based on current intraday trend
                    trend_factor = 1.0
                    if live_data['trend'] == 'bullish':
                        trend_factor = 1.01  # 1% bullish adjustment
                    elif live_data['trend'] == 'bearish':
                        trend_factor = 0.99  # 1% bearish adjustment
                    
                    # If live price is significantly different from last close, adjust more
                    last_close = hist_data['Close'].iloc[-1]
                    live_change = (live_data['current_price'] - last_close) / last_close
                    
                    # Apply live momentum (if price is falling, predict lower)
                    if abs(live_change) > 0.02:  # More than 2% change
                        trend_factor *= (1 + live_change * 0.5)  # 50% of live momentum
                    
                    base_prediction *= trend_factor
                
                # Apply news sentiment (stronger for intraday)
                sentiment_adjustment = news_sentiment['sentiment_score'] * 0.015  # Max 1.5% adjustment
                predicted_price = base_prediction * (1 + sentiment_adjustment)
                
                # CRITICAL: Check RSI and MACD for overbought/oversold
                rsi = hist_data['RSI'].iloc[-1]
                macd_hist = hist_data['MACD_Hist'].iloc[-1]
                
                # If RSI > 70 (overbought), reduce prediction
                if rsi > 70:
                    predicted_price *= 0.98  # 2% reduction for overbought
                # If RSI < 30 (oversold), increase prediction
                elif rsi < 30:
                    predicted_price *= 1.02  # 2% increase for oversold
                
                # If MACD histogram is negative (bearish), reduce prediction
                if macd_hist < 0:
                    predicted_price *= 0.99  # 1% reduction for bearish MACD
                
            else:
                # Multi-day prediction (2-30 days)
                # Calculate expected daily return based on historical momentum
                daily_returns = hist_data['Close'].pct_change().dropna()
                avg_daily_return = daily_returns.mean()
                volatility = daily_returns.std()
                
                # Apply momentum for multi-day predictions
                momentum_factor = 1 + (avg_daily_return * days_ahead)
                
                # Apply news sentiment (stronger effect for longer periods)
                sentiment_factor = 1 + (news_sentiment['sentiment_score'] * 0.02 * (days_ahead / 30))
                
                # Combine factors
                predicted_price = base_prediction * momentum_factor * sentiment_factor
                
                # Add volatility-based uncertainty
                volatility_adjustment = volatility * np.sqrt(days_ahead)
                predicted_price = predicted_price * (1 + np.random.uniform(-volatility_adjustment, volatility_adjustment) * 0.5)
            
            # Calculate metrics
            price_change = predicted_price - current_price
            percent_change = (price_change / current_price) * 100
            
            # Calculate confidence based on multiple factors
            base_confidence = 85
            
            # Reduce confidence for longer predictions
            time_penalty = (days_ahead / 30) * 15
            
            # Adjust based on volatility
            volatility_penalty = hist_data['Volatility'].iloc[-1] * 100 * 10
            
            # Adjust based on news sentiment strength
            if abs(news_sentiment['sentiment_score']) > 0.5:
                confidence_boost = 5
            else:
                confidence_boost = 0
            
            confidence = max(min(base_confidence - time_penalty - volatility_penalty + confidence_boost, 95), 50)
            
            # Determine trend and recommendation with better thresholds
            # Also consider technical indicators for final decision
            rsi_current = hist_data['RSI'].iloc[-1]
            macd_current = hist_data['MACD_Hist'].iloc[-1]
            
            # Base trend from price change
            if percent_change > 2:
                trend = 'bullish'
                recommendation = 'STRONG BUY'
            elif percent_change > 0.5:
                trend = 'bullish'
                recommendation = 'BUY'
            elif percent_change < -2:
                trend = 'bearish'
                recommendation = 'STRONG SELL'
            elif percent_change < -0.5:
                trend = 'bearish'
                recommendation = 'SELL'
            else:
                trend = 'neutral'
                recommendation = 'HOLD'
            
            # Override if technical indicators strongly disagree
            # If RSI is overbought (>70) and MACD is negative, don't recommend BUY
            if rsi_current > 70 and macd_current < 0 and recommendation in ['BUY', 'STRONG BUY']:
                recommendation = 'HOLD'
                trend = 'neutral'
            
            # If RSI is oversold (<30) and MACD is positive, don't recommend SELL
            if rsi_current < 30 and macd_current > 0 and recommendation in ['SELL', 'STRONG SELL']:
                recommendation = 'HOLD'
                trend = 'neutral'
            
            # If live data shows strong bearish trend, override bullish prediction
            if live_data and live_data['trend'] == 'bearish' and live_data['change_percent'] < -1:
                if recommendation in ['BUY', 'STRONG BUY']:
                    recommendation = 'HOLD'
                    trend = 'neutral'
            
            # Calculate risk percentage
            risk_percentage = 100 - confidence
            
            return {
                'success': True,
                'predicted_price': round(predicted_price, 2),
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(percent_change, 2),
                'confidence': round(confidence, 1),
                'trend': trend,
                'recommendation': recommendation,
                'risk_percentage': round(risk_percentage, 1),
                'days_ahead': days_ahead,
                'prediction_type': 'intraday' if days_ahead == 1 else 'short_term',
                
                # Additional details
                'live_data': live_data,
                'news_sentiment': news_sentiment,
                'technical_indicators': {
                    'rsi': round(hist_data['RSI'].iloc[-1], 2),
                    'macd': round(hist_data['MACD'].iloc[-1], 2),
                    'volatility': round(hist_data['Volatility'].iloc[-1] * 100, 2),
                    'volume_ratio': round(hist_data['Volume_Ratio'].iloc[-1], 2)
                },
                'model_predictions': {
                    'random_forest': round(pred_rf, 2),
                    'gradient_boosting': round(pred_gb, 2),
                    'ensemble': round(base_prediction, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


# Global instance cache
_intraday_models = {}

def get_intraday_model(symbol, company_name):
    """Get or create intraday model instance"""
    key = f"{symbol}_{company_name}"
    if key not in _intraday_models:
        _intraday_models[key] = IntradayMLModel(symbol, company_name)
    return _intraday_models[key]
