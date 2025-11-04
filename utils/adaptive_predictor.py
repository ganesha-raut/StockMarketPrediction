"""
Adaptive Self-Learning Predictor
Automatically tests multiple algorithms and selects the best one
Learns from prediction accuracy and improves over time
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib
import os
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AdaptivePredictor:
    """Self-learning predictor that adapts based on accuracy"""
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.model_dir = 'ml_models/adaptive'
        self.history_dir = 'ml_models/adaptive/history'
        self.scaler = StandardScaler()
        
        # Available algorithms to test
        self.algorithms = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'adaboost': AdaBoostRegressor(n_estimators=100, random_state=42),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=1.0),
            'elastic_net': ElasticNet(alpha=1.0, random_state=42),
            'svr': SVR(kernel='rbf', C=1.0),
            'neural_network': MLPRegressor(hidden_layers=(100, 50), max_iter=500, random_state=42)
        }
        
        # Current best model
        self.best_model = None
        self.best_algorithm = None
        self.best_accuracy = 0.0
        
        # Performance tracking
        self.performance_history = []
        
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        
        # Load existing model and history
        self.load_model()
        self.load_performance_history()
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators"""
        df = df.copy()
        
        # Flatten MultiIndex columns if present
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
        
        # Handle SMA_50 if insufficient data
        if df['SMA_50'].isna().all():
            df['SMA_50'] = df['SMA_20']
        
        # Fill NaN
        df = df.bfill().ffill()
        df = df.dropna()
        
        return df
    
    def test_all_algorithms(self, X_train, y_train):
        """Test all algorithms and find the best one"""
        logger.info(f"Testing {len(self.algorithms)} algorithms for {self.symbol}")
        
        results = {}
        
        for name, model in self.algorithms.items():
            try:
                # Cross-validation score
                scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
                mse = -scores.mean()
                accuracy = 1 / (1 + mse)  # Convert MSE to accuracy score
                
                results[name] = {
                    'accuracy': accuracy,
                    'mse': mse,
                    'model': model
                }
                
                logger.info(f"  {name}: Accuracy={accuracy:.4f}, MSE={mse:.4f}")
                
            except Exception as e:
                logger.error(f"  {name}: Failed - {e}")
                results[name] = {
                    'accuracy': 0.0,
                    'mse': float('inf'),
                    'model': None
                }
        
        # Find best algorithm
        best_name = max(results, key=lambda x: results[x]['accuracy'])
        best_result = results[best_name]
        
        logger.info(f"Best algorithm: {best_name} (Accuracy: {best_result['accuracy']:.4f})")
        
        return best_name, best_result, results
    
    def train_adaptive_model(self):
        """Train model by testing all algorithms and selecting the best"""
        try:
            logger.info(f"Starting adaptive training for {self.symbol}")
            
            # Fetch historical data
            ticker = f"{self.symbol}.NS"
            data = yf.download(ticker, period='2y', progress=False)
            
            if data.empty:
                logger.error("No historical data available")
                return False
            
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            if len(data) < 100:
                logger.error("Insufficient data after indicators")
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
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Test all algorithms
            best_name, best_result, all_results = self.test_all_algorithms(X_scaled, y)
            
            # Train best model on full data
            best_model = best_result['model']
            best_model.fit(X_scaled, y)
            
            # Update current best
            self.best_model = best_model
            self.best_algorithm = best_name
            self.best_accuracy = best_result['accuracy']
            
            # Save model
            self.save_model()
            
            # Save algorithm test results
            self.save_algorithm_results(all_results)
            
            logger.info(f"Adaptive training complete. Best: {best_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in adaptive training: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def learn_from_prediction(self, predicted_price, actual_price, prediction_date):
        """Learn from prediction accuracy and retrain if needed"""
        try:
            # Calculate accuracy
            error = abs(predicted_price - actual_price)
            percent_error = (error / actual_price) * 100
            accuracy = max(0, 100 - percent_error)
            
            # Record performance
            performance = {
                'date': prediction_date.strftime('%Y-%m-%d'),
                'predicted': float(predicted_price),
                'actual': float(actual_price),
                'error': float(error),
                'percent_error': float(percent_error),
                'accuracy': float(accuracy),
                'algorithm': self.best_algorithm,
                'timestamp': datetime.now().isoformat()
            }
            
            self.performance_history.append(performance)
            self.save_performance_history()
            
            logger.info(f"Learning: Predicted={predicted_price:.2f}, Actual={actual_price:.2f}, Accuracy={accuracy:.2f}%")
            
            # Calculate recent accuracy (last 10 predictions)
            recent_history = self.performance_history[-10:]
            recent_accuracy = np.mean([p['accuracy'] for p in recent_history])
            
            # Retrain if accuracy drops below threshold
            if len(self.performance_history) >= 10 and recent_accuracy < 70:
                logger.warning(f"Recent accuracy ({recent_accuracy:.2f}%) below threshold. Retraining...")
                self.train_adaptive_model()
            
            # Periodic retraining (every 30 predictions)
            if len(self.performance_history) % 30 == 0:
                logger.info("Periodic retraining triggered")
                self.train_adaptive_model()
            
            return accuracy
            
        except Exception as e:
            logger.error(f"Error learning from prediction: {e}")
            return 0.0
    
    def predict(self, days_ahead=1):
        """Make prediction using best model"""
        try:
            # Load model if not loaded
            if self.best_model is None:
                if not self.load_model():
                    logger.info("No model found. Training new model...")
                    if not self.train_adaptive_model():
                        return None
            
            # Fetch recent data
            ticker = f"{self.symbol}.NS"
            period = '1mo' if days_ahead == 1 else '6mo'
            data = yf.download(ticker, period=period, progress=False)
            
            if data.empty:
                return None
            
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            
            if data.empty:
                return None
            
            # Prepare features
            feature_columns = [
                'Open', 'High', 'Low', 'Volume',
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'RSI', 'BB_Middle', 'BB_Upper', 'BB_Lower',
                'Volatility', 'Volume_Ratio', 'Momentum_5', 'Momentum_10',
                'ROC', 'ATR'
            ]
            
            X_latest = data[feature_columns].iloc[-1:].values
            X_scaled = self.scaler.transform(X_latest)
            
            # Predict
            predicted_price = self.best_model.predict(X_scaled)[0]
            current_price = data['Close'].iloc[-1]
            
            return {
                'predicted_price': float(predicted_price),
                'current_price': float(current_price),
                'algorithm': self.best_algorithm,
                'model_accuracy': float(self.best_accuracy),
                'prediction_date': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def save_model(self):
        """Save best model and metadata"""
        try:
            model_path = os.path.join(self.model_dir, f'{self.symbol}_model.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            meta_path = os.path.join(self.model_dir, f'{self.symbol}_meta.json')
            
            joblib.dump(self.best_model, model_path)
            joblib.dump(self.scaler, scaler_path)
            
            metadata = {
                'algorithm': self.best_algorithm,
                'accuracy': float(self.best_accuracy),
                'last_updated': datetime.now().isoformat(),
                'symbol': self.symbol,
                'company_name': self.company_name
            }
            
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Model saved: {self.best_algorithm}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load saved model"""
        try:
            model_path = os.path.join(self.model_dir, f'{self.symbol}_model.pkl')
            scaler_path = os.path.join(self.model_dir, f'{self.symbol}_scaler.pkl')
            meta_path = os.path.join(self.model_dir, f'{self.symbol}_meta.json')
            
            if not os.path.exists(model_path):
                return False
            
            self.best_model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
                self.best_algorithm = metadata['algorithm']
                self.best_accuracy = metadata['accuracy']
            
            logger.info(f"Model loaded: {self.best_algorithm} (Accuracy: {self.best_accuracy:.4f})")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def save_performance_history(self):
        """Save performance history"""
        try:
            history_path = os.path.join(self.history_dir, f'{self.symbol}_history.json')
            
            with open(history_path, 'w') as f:
                json.dump(self.performance_history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def load_performance_history(self):
        """Load performance history"""
        try:
            history_path = os.path.join(self.history_dir, f'{self.symbol}_history.json')
            
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    self.performance_history = json.load(f)
                logger.info(f"Loaded {len(self.performance_history)} historical predictions")
                
        except Exception as e:
            logger.error(f"Error loading history: {e}")
    
    def save_algorithm_results(self, results):
        """Save algorithm comparison results"""
        try:
            results_path = os.path.join(self.history_dir, f'{self.symbol}_algorithms.json')
            
            # Convert to serializable format
            serializable_results = {}
            for name, result in results.items():
                serializable_results[name] = {
                    'accuracy': float(result['accuracy']),
                    'mse': float(result['mse'])
                }
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'results': serializable_results,
                'best_algorithm': self.best_algorithm
            }
            
            with open(results_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving algorithm results: {e}")
    
    def get_performance_stats(self):
        """Get performance statistics"""
        if not self.performance_history:
            return None
        
        accuracies = [p['accuracy'] for p in self.performance_history]
        errors = [p['percent_error'] for p in self.performance_history]
        
        return {
            'total_predictions': len(self.performance_history),
            'average_accuracy': np.mean(accuracies),
            'best_accuracy': np.max(accuracies),
            'worst_accuracy': np.min(accuracies),
            'average_error': np.mean(errors),
            'current_algorithm': self.best_algorithm,
            'recent_accuracy': np.mean(accuracies[-10:]) if len(accuracies) >= 10 else np.mean(accuracies)
        }


def get_adaptive_predictor(symbol, company_name):
    """Get or create adaptive predictor instance"""
    return AdaptivePredictor(symbol, company_name)
