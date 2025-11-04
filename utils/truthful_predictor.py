"""
Truthful Predictor
Gives honest bullish/bearish predictions based on:
- Live market data
- Historical data analysis
- News sentiment
- Technical indicators
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

class TruthfulPredictor:
    """Honest predictor that gives truthful bullish/bearish signals"""
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.model_rf = None
        self.model_gb = None
        self.scaler = StandardScaler()
        self.model_dir = 'ml_models/truthful'
        self.api_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
        
        os.makedirs(self.model_dir, exist_ok=True)
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators"""
        df = df.copy()
        
        # Flatten MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Moving Averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # EMA
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
        
        # Volatility
        df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
        
        # Volume
        df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
        
        # Momentum
        df['Momentum_5'] = df['Close'].pct_change(periods=5)
        df['Momentum_10'] = df['Close'].pct_change(periods=10)
        
        # ROC
        df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Handle SMA_50
        if df['SMA_50'].isna().all():
            df['SMA_50'] = df['SMA_20']
        
        # Fill NaN
        df = df.bfill().ffill()
        df = df.dropna()
        
        return df
    
    def analyze_news_sentiment(self):
        """Analyze news sentiment"""
        try:
            news_items = get_stock_news(self.symbol, limit=15)
            
            if not news_items:
                return {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'news_count': 0,
                    'trend_analysis': 'No news available'
                }
            
            news_text = "\n".join([f"- {item['title']}" for item in news_items[:15]])
            
            prompt = f"""Analyze news for {self.company_name} ({self.symbol}) and give HONEST assessment:

NEWS:
{news_text}

Provide:
SCORE: [number -1.0 (very bearish) to 1.0 (very bullish)]
LABEL: [bullish/bearish/neutral]
TREND: [One honest sentence about trend]

Be truthful - if news is bad, say bearish. If good, say bullish."""
            
            headers = {'Content-Type': 'application/json'}
            data = {"prompt": prompt}
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code != 200:
                return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'news_count': len(news_items), 'trend_analysis': 'Unable to analyze'}
            
            result = response.json()
            text = (result.get('text') or result.get('response') or result.get('output') or '').strip()
            
            sentiment_score = 0.0
            sentiment_label = 'neutral'
            trend_analysis = ''
            
            for line in text.split('\n'):
                line_upper = line.upper()
                if 'SCORE:' in line_upper:
                    try:
                        sentiment_score = float(line.split(':')[1].strip())
                    except:
                        pass
                elif 'LABEL:' in line_upper:
                    sentiment_label = line.split(':')[1].strip().lower()
                elif 'TREND:' in line_upper:
                    trend_analysis = line.split(':', 1)[1].strip()
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'news_count': len(news_items),
                'trend_analysis': trend_analysis or 'Mixed sentiment'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news: {e}")
            return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'news_count': 0, 'trend_analysis': 'Error analyzing news'}
    
    def train_model(self):
        """Train model"""
        try:
            logger.info(f"Training truthful model for {self.symbol}")
            
            # Fetch 2 years data
            ticker = f"{self.symbol}.NS"
            data = yf.download(ticker, period='2y', progress=False)
            
            if data.empty:
                return False
            
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            if len(data) < 100:
                return False
            
            # Prepare features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower',
                'Volatility', 'Volume_Ratio', 'Momentum_5', 'Momentum_10',
                'ROC', 'ATR'
            ]
            
            X = data[feature_columns].values
            y = data['Close'].values
            
            # Scale
            X_scaled = self.scaler.fit_transform(X)
            
            # Train models
            self.model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model_gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
            
            self.model_rf.fit(X_scaled, y)
            self.model_gb.fit(X_scaled, y)
            
            # Save
            self.save_model()
            
            logger.info(f"Model trained successfully for {self.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False
    
    def predict(self, days_ahead=1):
        """Make truthful prediction"""
        try:
            # Load or train model
            if not self.load_model():
                if not self.train_model():
                    return {'success': False, 'error': 'Model training failed'}
            
            # Fetch live data
            live_data = get_google_stock_data(self.symbol)
            
            # Fetch historical data
            period = '1mo' if days_ahead <= 7 else '6mo'
            ticker = f"{self.symbol}.NS"
            hist_data = yf.download(ticker, period=period, progress=False)
            
            if hist_data.empty:
                return {'success': False, 'error': 'No historical data'}
            
            # Calculate indicators
            hist_data = self.calculate_technical_indicators(hist_data)
            
            if hist_data.empty:
                return {'success': False, 'error': 'Insufficient data'}
            
            # Get news sentiment
            news_sentiment = self.analyze_news_sentiment()
            
            # Prepare features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower',
                'Volatility', 'Volume_Ratio', 'Momentum_5', 'Momentum_10',
                'ROC', 'ATR'
            ]
            
            X_latest = hist_data[feature_columns].iloc[-1:].values
            X_scaled = self.scaler.transform(X_latest)
            
            # Get predictions
            pred_rf = self.model_rf.predict(X_scaled)[0]
            pred_gb = self.model_gb.predict(X_scaled)[0]
            
            # Base prediction
            base_prediction = (pred_rf * 0.6 + pred_gb * 0.4)
            
            # Get current price
            if live_data and 'current_price' in live_data:
                current_price = live_data['current_price']
            else:
                current_price = hist_data['Close'].iloc[-1]
            
            # Get indicators
            rsi = hist_data['RSI'].iloc[-1]
            macd = hist_data['MACD'].iloc[-1]
            macd_hist = hist_data['MACD_Hist'].iloc[-1]
            volatility = hist_data['Volatility'].iloc[-1]
            
            # TRUTHFUL ADJUSTMENT based on ALL signals
            predicted_price = base_prediction
            
            # 1. Live data adjustment (if bearish, reduce prediction)
            if live_data and isinstance(live_data, dict):
                if live_data.get('trend') == 'bearish':
                    predicted_price *= 0.98  # Reduce by 2%
                elif live_data.get('trend') == 'bullish':
                    predicted_price *= 1.01  # Increase by 1%
                
                # Live momentum
                if 'current_price' in live_data:
                    last_close = hist_data['Close'].iloc[-1]
                    live_change = (live_data['current_price'] - last_close) / last_close
                    
                    if abs(live_change) > 0.02:
                        # Apply 50% of live momentum
                        predicted_price *= (1 + live_change * 0.5)
            
            # 2. News sentiment (honest impact)
            news_impact = news_sentiment['sentiment_score'] * 0.02  # Max 2% impact
            predicted_price *= (1 + news_impact)
            
            # 3. RSI (overbought/oversold)
            if rsi > 70:
                predicted_price *= 0.97  # Overbought - likely to fall
            elif rsi < 30:
                predicted_price *= 1.03  # Oversold - likely to rise
            
            # 4. MACD (trend strength)
            if macd < 0 and macd_hist < 0:
                predicted_price *= 0.98  # Strong bearish signal
            elif macd > 0 and macd_hist > 0:
                predicted_price *= 1.02  # Strong bullish signal
            
            # Calculate change
            price_change = predicted_price - current_price
            percent_change = (price_change / current_price) * 100
            
            # TRUTHFUL TREND DETERMINATION
            # Don't just look at prediction - look at ALL signals
            bearish_signals = 0
            bullish_signals = 0
            
            # Check RSI
            if rsi > 70:
                bearish_signals += 2  # Strong signal
            elif rsi < 30:
                bullish_signals += 2
            
            # Check MACD
            if macd < 0:
                bearish_signals += 1
            else:
                bullish_signals += 1
            
            # Check live trend
            if live_data and live_data.get('trend') == 'bearish':
                bearish_signals += 2
            elif live_data and live_data.get('trend') == 'bullish':
                bullish_signals += 1
            
            # Check news
            if news_sentiment['sentiment_score'] < -0.3:
                bearish_signals += 2
            elif news_sentiment['sentiment_score'] > 0.3:
                bullish_signals += 2
            
            # Check price prediction
            if percent_change < -1:
                bearish_signals += 1
            elif percent_change > 1:
                bullish_signals += 1
            
            # HONEST VERDICT
            if bearish_signals > bullish_signals + 2:
                trend = 'bearish'
                if percent_change < -2:
                    recommendation = 'STRONG SELL'
                else:
                    recommendation = 'SELL'
            elif bullish_signals > bearish_signals + 2:
                trend = 'bullish'
                if percent_change > 2:
                    recommendation = 'STRONG BUY'
                else:
                    recommendation = 'BUY'
            else:
                trend = 'neutral'
                recommendation = 'HOLD'
            
            # Calculate confidence
            signal_difference = abs(bearish_signals - bullish_signals)
            base_confidence = 70 + (signal_difference * 3)
            base_confidence = min(95, max(60, base_confidence))
            
            # Adjust for volatility
            if volatility > 0.03:
                base_confidence -= 10
            
            confidence = base_confidence
            
            # Risk
            risk_percentage = min(50, volatility * 1000 + abs(percent_change))
            
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
                    'volatility': float(volatility * 100),
                    'volume_ratio': float(hist_data['Volume_Ratio'].iloc[-1])
                },
                'news_sentiment': news_sentiment,
                'signal_analysis': {
                    'bearish_signals': bearish_signals,
                    'bullish_signals': bullish_signals,
                    'verdict': 'BEARISH' if bearish_signals > bullish_signals else 'BULLISH' if bullish_signals > bearish_signals else 'NEUTRAL'
                },
                'live_data': live_data if live_data else None
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def save_model(self):
        """Save model"""
        try:
            model_rf_path = os.path.join(self.model_dir, f'{self.symbol}_rf.pkl')
            model_gb_path = os.path.join(self.model_dir, f'{self.symbol}_gb.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            
            joblib.dump(self.model_rf, model_rf_path)
            joblib.dump(self.model_gb, model_gb_path)
            joblib.dump(self.scaler, scaler_path)
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load model"""
        try:
            model_rf_path = os.path.join(self.model_dir, f'{self.symbol}_rf.pkl')
            model_gb_path = os.path.join(self.model_dir, f'{self.symbol}_gb.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            
            if not os.path.exists(model_rf_path):
                return False
            
            self.model_rf = joblib.load(model_rf_path)
            self.model_gb = joblib.load(model_gb_path)
            self.scaler = joblib.load(scaler_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


def get_truthful_predictor(symbol, company_name):
    """Get truthful predictor instance"""
    return TruthfulPredictor(symbol, company_name)
