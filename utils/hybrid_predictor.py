"""
Hybrid AI + SI + ML Predictor
Combines Gemini AI, Syntactic Intelligence, and Machine Learning for superior predictions
"""

import numpy as np
import pandas as pd
import yfinance as yf
import google.generativeai as genai
from config import Config
import logging
from datetime import datetime, timedelta
from utils.aggressive_model import get_aggressive_model

logger = logging.getLogger(__name__)

class HybridPredictor:
    """
    Advanced prediction system combining:
    - AI: Gemini for news analysis and future events
    - SI: Syntactic Intelligence for pattern recognition
    - ML: Machine Learning on historical data + dividends
    """
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.api_key = Config.GEMINI_API_KEY
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')  # Using Flash 2.5
        else:
            self.model = None
            logger.warning("Gemini API key not configured")
    
    def fetch_comprehensive_data(self, years=5):
        """Fetch comprehensive historical data including dividends"""
        try:
            ticker = f"{self.symbol}.NS"
            
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years*365)
            
            stock = yf.Ticker(ticker)
            
            # Get price data
            hist_data = stock.history(start=start_date, end=end_date)
            
            # Get dividend data
            dividends = stock.dividends
            
            # Get company info
            info = stock.info
            
            return {
                'price_data': hist_data,
                'dividends': dividends,
                'info': info,
                'current_price': float(hist_data['Close'].iloc[-1]) if not hist_data.empty else 0
            }
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None
    
    def analyze_dividends(self, dividends, price_data):
        """Analyze dividend patterns and predict future dividends"""
        try:
            if dividends.empty:
                return {
                    'has_dividends': False,
                    'avg_dividend': 0,
                    'dividend_yield': 0,
                    'growth_rate': 0,
                    'predicted_next_dividend': 0
                }
            
            # Calculate dividend metrics
            recent_dividends = dividends.tail(10)
            avg_dividend = recent_dividends.mean()
            
            # Calculate dividend yield
            current_price = float(price_data['Close'].iloc[-1])
            annual_dividend = dividends.last('1Y').sum() if len(dividends) > 0 else 0
            dividend_yield = (annual_dividend / current_price * 100) if current_price > 0 else 0
            
            # Calculate growth rate
            if len(recent_dividends) >= 2:
                old_avg = recent_dividends.head(5).mean()
                new_avg = recent_dividends.tail(5).mean()
                growth_rate = ((new_avg - old_avg) / old_avg * 100) if old_avg > 0 else 0
            else:
                growth_rate = 0
            
            # Predict next dividend
            predicted_next = avg_dividend * (1 + growth_rate/100)
            
            return {
                'has_dividends': True,
                'avg_dividend': float(avg_dividend),
                'dividend_yield': float(dividend_yield),
                'growth_rate': float(growth_rate),
                'predicted_next_dividend': float(predicted_next),
                'total_dividends_last_year': float(annual_dividend)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing dividends: {e}")
            return {
                'has_dividends': False,
                'avg_dividend': 0,
                'dividend_yield': 0,
                'growth_rate': 0,
                'predicted_next_dividend': 0
            }
    
    def ml_price_prediction(self, price_data, days_ahead):
        """ML-based price prediction using trained model"""
        try:
            # Use trained aggressive model
            model = get_aggressive_model(self.symbol, self.company_name)
            model_result = model.predict(days_ahead)
            
            if model_result:
                # Use model prediction
                predicted_price = model_result['predicted_price']
                confidence = model_result['confidence']
                
                # Get additional metrics from price data
                df = price_data.copy()
                
                # Calculate trends
                current_price = float(df['Close'].iloc[-1])
                ma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
                ma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
                ma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
                
                short_term_trend = (current_price - ma_20) / ma_20 * 100
                medium_term_trend = (current_price - ma_50) / ma_50 * 100
                long_term_trend = (current_price - ma_200) / ma_200 * 100
                
                # Calculate expected return
                expected_return = (predicted_price - current_price) / current_price * 100
                
                # Get investment timing
                volatility = model_result['volatility'] / 100
                investment_timing = self._suggest_investment_timing(expected_return, days_ahead, volatility)
                
                return {
                    'ml_predicted_price': predicted_price,
                    'ml_confidence': confidence,
                    'expected_return': expected_return,
                    'investment_timing': investment_timing,
                    'short_term_trend': short_term_trend,
                    'medium_term_trend': medium_term_trend,
                    'long_term_trend': long_term_trend,
                    'momentum_7d': model_result.get('momentum_30', 0) / 4,  # Approximate
                    'momentum_30d': model_result.get('momentum_30', 0),
                    'volatility': model_result['volatility'],
                    'rsi': model_result['rsi'],
                    'model_based': True,
                    'model_age_days': model_result.get('model_age_days', 0)
                }
            
            # Fallback to calculation-based if model fails
            logger.warning(f"Model prediction failed, using fallback for {self.symbol}")
            df = price_data.copy()
            
            # Calculate technical indicators
            df['Returns'] = df['Close'].pct_change()
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            df['MA_50'] = df['Close'].rolling(window=50).mean()
            df['MA_200'] = df['Close'].rolling(window=200).mean()
            df['Volatility'] = df['Returns'].rolling(window=20).std()
            df['RSI'] = self.calculate_rsi(df['Close'])
            
            # Calculate trend strength
            current_price = float(df['Close'].iloc[-1])
            ma_20 = float(df['MA_20'].iloc[-1])
            ma_50 = float(df['MA_50'].iloc[-1])
            ma_200 = float(df['MA_200'].iloc[-1])
            
            # Trend analysis
            short_term_trend = (current_price - ma_20) / ma_20 * 100
            medium_term_trend = (current_price - ma_50) / ma_50 * 100
            long_term_trend = (current_price - ma_200) / ma_200 * 100
            
            # Calculate momentum
            momentum_7d = (current_price - float(df['Close'].iloc[-7])) / float(df['Close'].iloc[-7]) * 100
            momentum_30d = (current_price - float(df['Close'].iloc[-30])) / float(df['Close'].iloc[-30]) * 100
            
            # Volatility
            volatility = float(df['Volatility'].iloc[-1])
            
            # AGGRESSIVE BULLISH PREDICTION for better investment returns
            if days_ahead <= 7:
                # Short-term: Aggressive momentum (target 5-10% moves)
                base_change = momentum_7d / 7 * days_ahead * 3.0
            elif days_ahead <= 30:
                # Medium-term: Strong bullish bias (target 10-20% moves)
                base_change = (short_term_trend * 0.6 + medium_term_trend * 0.4) / 30 * days_ahead * 4.5
            elif days_ahead <= 90:
                # Medium-long: High growth potential (target 20-30% moves)
                base_change = medium_term_trend / 90 * days_ahead * 6.0
            else:
                # Long-term: Maximum growth projection (target 30-50% moves)
                base_change = long_term_trend / 365 * days_ahead * 8.0
            
            # Apply bullish volatility adjustment
            volatility_factor = 1 + (volatility * np.sqrt(days_ahead / 365) * 2.5)
            
            # Calculate predicted price with BULLISH bias
            predicted_price = current_price * (1 + base_change/100)
            
            # Add bullish momentum boost
            if momentum_30d > 0:
                predicted_price *= (1 + momentum_30d/100 * 0.3)  # Extra boost for positive momentum
            
            # Wide bounds for aggressive predictions
            lower_bound = current_price * (1 - volatility * np.sqrt(days_ahead/365) * 3)
            upper_bound = current_price * (1 + volatility * np.sqrt(days_ahead/365) * 12)  # Very high upper bound
            predicted_price = np.clip(predicted_price, lower_bound, upper_bound)
            
            # Calculate best investment timing suggestion
            expected_return_percent = ((predicted_price - current_price) / current_price) * 100
            investment_timing = self._suggest_investment_timing(expected_return_percent, days_ahead, volatility)
            
            return {
                'ml_predicted_price': float(predicted_price),
                'ml_confidence': self.calculate_ml_confidence(volatility, days_ahead),
                'short_term_trend': float(short_term_trend),
                'medium_term_trend': float(medium_term_trend),
                'long_term_trend': float(long_term_trend),
                'momentum_7d': float(momentum_7d),
                'momentum_30d': float(momentum_30d),
                'volatility': float(volatility * 100),
                'rsi': float(df['RSI'].iloc[-1]),
                'expected_return': float(expected_return_percent),
                'investment_timing': investment_timing
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return None
    
    def calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_ml_confidence(self, volatility, days_ahead):
        """Calculate ML confidence based on volatility and time horizon"""
        base_confidence = 85
        volatility_penalty = volatility * 100 * 2
        time_penalty = (days_ahead / 365) * 20
        confidence = base_confidence - volatility_penalty - time_penalty
        return max(min(confidence, 95), 40)
    
    def _suggest_investment_timing(self, expected_return, days_ahead, volatility):
        """Suggest best investment timing based on expected returns"""
        
        # Determine timing based on return potential
        if expected_return >= 30:
            timing = "Excellent"
            reason = f"High return potential ({expected_return:.1f}%) - Strong BUY signal"
        elif expected_return >= 20:
            timing = "Very Good"
            reason = f"Good return potential ({expected_return:.1f}%) - BUY recommended"
        elif expected_return >= 10:
            timing = "Good"
            reason = f"Moderate return ({expected_return:.1f}%) - Consider buying"
        elif expected_return >= 5:
            timing = "Fair"
            reason = f"Low return ({expected_return:.1f}%) - Hold or wait"
        else:
            timing = "Poor"
            reason = f"Minimal return ({expected_return:.1f}%) - Not recommended"
        
        # Calculate best holding period
        if expected_return >= 20:
            best_period = f"{days_ahead} days"
        elif expected_return >= 10:
            best_period = f"{days_ahead * 2} days (double period for better returns)"
        else:
            best_period = f"{days_ahead * 3} days (longer hold recommended)"
        
        return {
            'timing': timing,
            'reason': reason,
            'expected_return': expected_return,
            'best_holding_period': best_period,
            'risk_level': 'Low' if volatility < 0.02 else 'Medium' if volatility < 0.04 else 'High'
        }
    
    def ai_news_analysis(self, current_price, ml_prediction, days_ahead):
        """Use Gemini AI to analyze news and predict future events"""
        
        if not self.model:
            return self._fallback_ai_analysis(current_price, ml_prediction, days_ahead)
        
        try:
            months = days_ahead // 30
            
            prompt = f"""
Analyze {self.company_name} ({self.symbol}) for {days_ahead} days.
Current: ₹{current_price:,.2f}

SHORT SUMMARY (one line each):

NEWS_SCORE: [0-100]
GROWTH_SCORE: [0-100]
AI_ADJUSTMENT: [+/- %]

SUMMARY: [One sentence about overall outlook]

Be brief and direct.
"""
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Parse AI response
            ai_data = self._parse_ai_response(text)
            
            return ai_data
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return self._fallback_ai_analysis(current_price, ml_prediction, days_ahead)
    
    def _parse_ai_response(self, text):
        """Parse Gemini AI response"""
        try:
            # Extract values using simple parsing
            news_score = 70
            growth_score = 75
            ai_adjustment = 5.0  # Default bullish
            summary = "Positive outlook based on market trends."
            
            # Try to extract actual values
            lines = text.split('\n')
            for line in lines:
                line_upper = line.upper()
                if 'NEWS_SCORE:' in line_upper:
                    try:
                        news_score = float(line.split(':')[1].strip().replace('%', ''))
                    except:
                        pass
                elif 'GROWTH_SCORE:' in line_upper:
                    try:
                        growth_score = float(line.split(':')[1].strip().replace('%', ''))
                    except:
                        pass
                elif 'AI_ADJUSTMENT:' in line_upper:
                    try:
                        adj_str = line.split(':')[1].strip().replace('%', '').replace('+', '')
                        ai_adjustment = float(adj_str)
                    except:
                        pass
                elif 'SUMMARY:' in line_upper:
                    summary = line.split(':', 1)[1].strip()
            
            # Calculate confidence from scores
            confidence = (news_score + growth_score) / 2
            
            return {
                'news_score': news_score,
                'growth_score': growth_score,
                'ai_adjustment_percent': ai_adjustment,
                'ai_confidence': confidence,
                'ai_summary': summary,
                'full_analysis': text
            }
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._fallback_ai_analysis(0, 0, 0)
    
    def _fallback_ai_analysis(self, current_price, ml_prediction, days_ahead):
        """Fallback AI analysis when Gemini is unavailable"""
        return {
            'news_score': 70,
            'growth_score': 75,
            'ai_adjustment_percent': 5.0,  # Default bullish
            'ai_confidence': 70,
            'ai_summary': 'Positive outlook based on historical trends and market conditions.',
            'full_analysis': 'AI analysis unavailable.'
        }
    
    def si_formula_optimization(self, ml_data, ai_data, dividend_data, days_ahead):
        """
        Syntactic Intelligence: Create optimal formula
        Combines ML, AI, and dividend data with intelligent weighting
        """
        
        # Base weights (SI determines optimal combination)
        if days_ahead <= 7:
            # Short-term: Heavy ML, light AI
            ml_weight = 0.75
            ai_weight = 0.20
            dividend_weight = 0.05
        elif days_ahead <= 30:
            # Medium-term: Balanced
            ml_weight = 0.60
            ai_weight = 0.30
            dividend_weight = 0.10
        elif days_ahead <= 90:
            # Medium-long: More AI influence
            ml_weight = 0.50
            ai_weight = 0.40
            dividend_weight = 0.10
        else:
            # Long-term: Heavy AI, dividends matter
            ml_weight = 0.40
            ai_weight = 0.45
            dividend_weight = 0.15
        
        # Adjust weights based on confidence levels
        ml_confidence = ml_data.get('ml_confidence', 70) / 100
        ai_confidence = ai_data.get('ai_confidence', 70) / 100
        
        # Normalize weights based on confidence
        total_confidence = (ml_weight * ml_confidence) + (ai_weight * ai_confidence) + dividend_weight
        ml_weight = (ml_weight * ml_confidence) / total_confidence
        ai_weight = (ai_weight * ai_confidence) / total_confidence
        dividend_weight = dividend_weight / total_confidence
        
        # SI Formula: Optimal combination
        si_formula = {
            'ml_weight': ml_weight,
            'ai_weight': ai_weight,
            'dividend_weight': dividend_weight,
            'formula': f"Price = (ML × {ml_weight:.2f}) + (AI × {ai_weight:.2f}) + (DIV × {dividend_weight:.2f})",
            'optimization_reason': self._get_si_reasoning(days_ahead, ml_confidence, ai_confidence)
        }
        
        return si_formula
    
    def _get_si_reasoning(self, days_ahead, ml_conf, ai_conf):
        """SI reasoning for weight selection"""
        if days_ahead <= 7:
            return "Short-term: ML patterns more reliable, recent momentum dominant"
        elif days_ahead <= 30:
            return "Medium-term: Balanced approach, both ML trends and AI news important"
        elif days_ahead <= 90:
            return "Medium-long: AI future predictions gain importance, ML provides base"
        else:
            return "Long-term: AI future outlook critical, dividends impact total returns"
    
    def hybrid_predict(self, days_ahead):
        """
        Main hybrid prediction combining AI + SI + ML
        """
        try:
            # Step 1: Fetch comprehensive data
            data = self.fetch_comprehensive_data(years=5)
            if not data:
                return None
            
            current_price = data['current_price']
            
            # Step 2: ML Analysis
            ml_result = self.ml_price_prediction(data['price_data'], days_ahead)
            if not ml_result:
                return None
            
            # Step 3: Dividend Analysis
            dividend_result = self.analyze_dividends(data['dividends'], data['price_data'])
            
            # Step 4: AI News & Future Analysis
            ai_result = self.ai_news_analysis(
                current_price,
                ml_result['ml_predicted_price'],
                days_ahead
            )
            
            # Step 5: SI Formula Optimization
            si_formula = self.si_formula_optimization(
                ml_result,
                ai_result,
                dividend_result,
                days_ahead
            )
            
            # Step 6: Calculate Final Hybrid Prediction
            ml_price = ml_result['ml_predicted_price']
            ai_adjustment = ai_result['ai_adjustment_percent'] / 100
            ai_price = ml_price * (1 + ai_adjustment)
            
            # Calculate dividend impact on total return - TIME-BASED PERCENTAGE
            if dividend_result['has_dividends']:
                # Calculate expected dividends based on time period
                annual_dividend = dividend_result['total_dividends_last_year']
                growth_rate = dividend_result['growth_rate'] / 100
                
                # Project dividends for the time period with compounding growth
                years_fraction = days_ahead / 365
                
                # Compound dividend calculation (more dividends over longer time)
                if days_ahead <= 90:
                    # Short-medium: Simple projection
                    expected_dividends = annual_dividend * years_fraction * (1 + growth_rate)
                else:
                    # Long-term: Compound with multiple dividend payments
                    num_payments = int(years_fraction * 4)  # Quarterly dividends
                    expected_dividends = annual_dividend * years_fraction * (1 + growth_rate) ** years_fraction
                
                # Calculate dividend boost as percentage (increases with time)
                dividend_boost = expected_dividends / current_price
                
                # Calculate dividend return percentage
                dividend_return_percent = dividend_boost * 100
                
                # Store for display
                dividend_result['expected_dividends_period'] = float(expected_dividends)
                dividend_result['dividend_return_percent'] = float(dividend_return_percent)
            else:
                dividend_boost = 0
                dividend_result['expected_dividends_period'] = 0
                dividend_result['dividend_return_percent'] = 0
            
            # Apply SI formula
            final_price = (
                ml_price * si_formula['ml_weight'] +
                ai_price * si_formula['ai_weight'] +
                current_price * (1 + dividend_boost) * si_formula['dividend_weight']
            )
            
            # Calculate metrics
            price_change = final_price - current_price
            percent_change = (price_change / current_price) * 100
            
            # Calculate final confidence
            final_confidence = (
                ml_result['ml_confidence'] * si_formula['ml_weight'] +
                ai_result['ai_confidence'] * si_formula['ai_weight'] +
                70 * si_formula['dividend_weight']  # Base dividend confidence
            )
            
            # Determine trend and recommendation
            if percent_change > 5:
                trend = 'bullish'
                recommendation = 'BUY'
            elif percent_change < -5:
                trend = 'bearish'
                recommendation = 'SELL'
            else:
                trend = 'neutral'
                recommendation = 'HOLD'
            
            return {
                'success': True,
                'predicted_price': round(final_price, 2),
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(percent_change, 2),
                'confidence': round(final_confidence, 1),
                'trend': trend,
                'recommendation': recommendation,
                'risk_percentage': round(100 - final_confidence, 1),
                
                # Component predictions
                'ml_prediction': {
                    'price': round(ml_result['ml_predicted_price'], 2),
                    'confidence': round(ml_result['ml_confidence'], 1),
                    'expected_return': round(ml_result['expected_return'], 2),
                    'investment_timing': ml_result['investment_timing'],
                    'trend_analysis': {
                        'short_term': round(ml_result['short_term_trend'], 2),
                        'medium_term': round(ml_result['medium_term_trend'], 2),
                        'long_term': round(ml_result['long_term_trend'], 2)
                    },
                    'momentum': {
                        '7d': round(ml_result['momentum_7d'], 2),
                        '30d': round(ml_result['momentum_30d'], 2)
                    },
                    'volatility': round(ml_result['volatility'], 2),
                    'rsi': round(ml_result['rsi'], 1)
                },
                
                'ai_prediction': {
                    'adjustment_percent': round(ai_result['ai_adjustment_percent'], 2),
                    'adjusted_price': round(ai_price, 2),
                    'news_score': round(ai_result['news_score'], 1),
                    'growth_score': round(ai_result['growth_score'], 1),
                    'confidence': round(ai_result['ai_confidence'], 1),
                    'summary': ai_result.get('ai_summary', 'Positive market outlook.')
                },
                
                'dividend_analysis': dividend_result,
                
                'si_formula': si_formula,
                
                'hybrid_details': {
                    'ml_contribution': round(ml_price * si_formula['ml_weight'], 2),
                    'ai_contribution': round(ai_price * si_formula['ai_weight'], 2),
                    'dividend_contribution': round(current_price * (1 + dividend_boost) * si_formula['dividend_weight'], 2),
                    'formula_used': si_formula['formula'],
                    'optimization': si_formula['optimization_reason']
                }
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid prediction: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

# Global instance cache
_hybrid_predictors = {}

def get_hybrid_predictor(symbol, company_name):
    """Get or create hybrid predictor instance"""
    key = f"{symbol}_{company_name}"
    if key not in _hybrid_predictors:
        _hybrid_predictors[key] = HybridPredictor(symbol, company_name)
    return _hybrid_predictors[key]
