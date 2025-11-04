"""
Advanced ML Predictor
Uses enhanced news analysis + live data + technical indicators
Replaces old models with comprehensive feature set
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
from utils.stock_data import get_google_stock_data
from utils.enhanced_news_analyzer import get_enhanced_news_analyzer

logger = logging.getLogger(__name__)

class AdvancedMLPredictor:
    """Advanced predictor with comprehensive feature set"""
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.model_rf = None
        self.model_gb = None
        self.scaler = StandardScaler()
        self.model_dir = 'ml_models/advanced'
        
        os.makedirs(self.model_dir, exist_ok=True)
    
    def calculate_technical_indicators(self, df):
        """Calculate comprehensive technical indicators"""
        df = df.copy()
        
        # Flatten MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Price changes
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Change_5'] = df['Close'].pct_change(periods=5)
        df['Price_Change_10'] = df['Close'].pct_change(periods=10)
        
        # Moving Averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Distance from MAs
        df['Dist_SMA_5'] = (df['Close'] - df['SMA_5']) / df['SMA_5']
        df['Dist_SMA_10'] = (df['Close'] - df['SMA_10']) / df['SMA_10']
        df['Dist_SMA_20'] = (df['Close'] - df['SMA_20']) / df['SMA_20']
        
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
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Volatility
        df['Volatility'] = df['Close'].pct_change().rolling(window=10).std()
        df['Volatility_20'] = df['Close'].pct_change().rolling(window=20).std()
        df['High_Low_Range'] = (df['High'] - df['Low']) / df['Close']
        
        # Volume
        df['Volume_Change'] = df['Volume'].pct_change()
        df['Volume_MA'] = df['Volume'].rolling(window=10).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
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
        
        # Fill NaN and handle infinity
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.bfill().ffill()
        df = df.dropna()
        
        # Final check
        df = df[~df.isin([np.nan, np.inf, -np.inf]).any(axis=1)]
        
        return df
    
    def train_model(self):
        """Train advanced model"""
        try:
            logger.info(f"Training advanced model for {self.symbol}")
            
            # Fetch 1 year data
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
            
            # Prepare features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'Price_Change', 'Price_Change_5', 'Price_Change_10',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'Dist_SMA_5', 'Dist_SMA_10', 'Dist_SMA_20',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width',
                'Volatility', 'Volatility_20', 'High_Low_Range',
                'Volume_Change', 'Volume_Ratio',
                'Momentum_5', 'Momentum_10', 'ROC', 'ATR'
            ]
            
            # Create target
            data['Target'] = data['Close'].shift(-1)
            data = data.dropna()
            
            X = data[feature_columns].values
            y = data['Target'].values
            
            # Scale
            X_scaled = self.scaler.fit_transform(X)
            
            # Train models
            self.model_rf = RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42
            )
            
            self.model_gb = GradientBoostingRegressor(
                n_estimators=150,
                max_depth=8,
                learning_rate=0.1,
                random_state=42
            )
            
            self.model_rf.fit(X_scaled, y)
            self.model_gb.fit(X_scaled, y)
            
            # Save
            self.save_model()
            
            logger.info(f"Advanced model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict(self, days_ahead=1):
        """Make prediction with all features"""
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
            
            # Get live data
            live_data = get_google_stock_data(self.symbol)
            
            # Get enhanced news analysis
            news_analyzer = get_enhanced_news_analyzer(self.symbol, self.company_name)
            news_analysis = news_analyzer.analyze_all_news(limit=15)
            
            # Prepare features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'Price_Change', 'Price_Change_5', 'Price_Change_10',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'Dist_SMA_5', 'Dist_SMA_10', 'Dist_SMA_20',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width',
                'Volatility', 'Volatility_20', 'High_Low_Range',
                'Volume_Change', 'Volume_Ratio',
                'Momentum_5', 'Momentum_10', 'ROC', 'ATR'
            ]
            
            X_latest = data[feature_columns].iloc[-1:].values
            X_scaled = self.scaler.transform(X_latest)
            
            # Get predictions from both models
            pred_rf = self.model_rf.predict(X_scaled)[0]
            pred_gb = self.model_gb.predict(X_scaled)[0]
            
            # Ensemble prediction
            base_prediction = (pred_rf * 0.6 + pred_gb * 0.4)
            
            # Get indicators
            rsi = data['RSI'].iloc[-1]
            macd = data['MACD'].iloc[-1]
            volatility = data['Volatility'].iloc[-1]
            recent_change = data['Price_Change'].iloc[-5:].mean()
            
            # Start with base prediction
            predicted_price = base_prediction
            
            # Apply conservative limits
            max_daily_change = 0.025  # 2.5% max
            raw_change = (predicted_price - current_price) / current_price
            
            if abs(raw_change) > max_daily_change:
                if raw_change > 0:
                    predicted_price = current_price * (1 + max_daily_change)
                else:
                    predicted_price = current_price * (1 - max_daily_change)
            
            # RSI adjustment
            if rsi > 70:
                predicted_price *= 0.99
            elif rsi < 30:
                predicted_price *= 1.01
            
            # MACD adjustment
            if macd < 0:
                predicted_price *= 0.99
            elif macd > 0:
                predicted_price *= 1.01
            
            # Live data adjustment
            if live_data and isinstance(live_data, dict):
                if live_data.get('trend') == 'bearish':
                    predicted_price *= 0.995
                elif live_data.get('trend') == 'bullish':
                    predicted_price *= 1.005
            
            # NEWS SENTIMENT ADJUSTMENT (Enhanced)
            if news_analysis['success']:
                news_score = news_analysis['overall_score']
                
                # Strong news impact
                if news_score < -0.5:  # Very negative
                    predicted_price *= 0.98
                elif news_score < -0.2:  # Negative
                    predicted_price *= 0.99
                elif news_score > 0.5:  # Very positive
                    predicted_price *= 1.02
                elif news_score > 0.2:  # Positive
                    predicted_price *= 1.01
                
                # Adjust based on news count
                if news_analysis['negative_count'] > news_analysis['positive_count'] * 2:
                    predicted_price *= 0.995  # Overwhelmingly negative
                elif news_analysis['positive_count'] > news_analysis['negative_count'] * 2:
                    predicted_price *= 1.005  # Overwhelmingly positive
            
            # Final safety cap
            final_change = (predicted_price - current_price) / current_price
            if abs(final_change) > 0.03:
                if final_change > 0:
                    predicted_price = current_price * 1.03
                else:
                    predicted_price = current_price * 0.97
            
            # Multi-day scaling
            if days_ahead > 1:
                daily_change = (predicted_price - current_price) / current_price
                total_change = daily_change * (1 + (days_ahead - 1) * 0.5)
                max_change = min(0.05 * (days_ahead / 7), 0.10)
                if abs(total_change) > max_change:
                    total_change = max_change if total_change > 0 else -max_change
                predicted_price = current_price * (1 + total_change)
            
            # Calculate metrics
            price_change = predicted_price - current_price
            percent_change = (price_change / current_price) * 100
            
            # Determine trend
            if percent_change > 1.5:
                trend = 'bullish'
                recommendation = 'BUY'
            elif percent_change < -1.5:
                trend = 'bearish'
                recommendation = 'SELL'
            else:
                trend = 'neutral'
                recommendation = 'HOLD'
            
            # Calculate confidence
            base_confidence = 75
            
            if volatility > 0.02:
                base_confidence -= 10
            
            if days_ahead > 7:
                base_confidence -= 5
            
            # Boost confidence if news agrees with prediction
            if news_analysis['success']:
                if (trend == 'bullish' and news_analysis['overall_sentiment'] == 'positive') or \
                   (trend == 'bearish' and news_analysis['overall_sentiment'] == 'negative'):
                    base_confidence += 5
            
            confidence = max(65, min(90, base_confidence))
            
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
                    'recent_trend': float(recent_change * 100)
                },
                'news_analysis': news_analysis,
                'live_data': live_data if live_data else None,
                'model_info': {
                    'type': 'advanced_ml_ensemble',
                    'models': 'Random Forest + Gradient Boosting',
                    'features': len(feature_columns),
                    'uses_live_data': True,
                    'uses_enhanced_news': True,
                    'news_categorization': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def save_model(self):
        """Save models"""
        try:
            rf_path = os.path.join(self.model_dir, f'{self.symbol}_rf.pkl')
            gb_path = os.path.join(self.model_dir, f'{self.symbol}_gb.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            
            joblib.dump(self.model_rf, rf_path)
            joblib.dump(self.model_gb, gb_path)
            joblib.dump(self.scaler, scaler_path)
            
            logger.info("Models saved")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_model(self):
        """Load models"""
        try:
            rf_path = os.path.join(self.model_dir, f'{self.symbol}_rf.pkl')
            gb_path = os.path.join(self.model_dir, f'{self.symbol}_gb.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            
            if not os.path.exists(rf_path):
                return False
            
            self.model_rf = joblib.load(rf_path)
            self.model_gb = joblib.load(gb_path)
            self.scaler = joblib.load(scaler_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False


def get_advanced_predictor(symbol, company_name):
    """Get advanced predictor instance"""
    return AdvancedMLPredictor(symbol, company_name)
