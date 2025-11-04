"""
AI Stock Recommender
Analyzes all predictions and recommends best stocks to buy/sell
Runs after 10 AM predictions are complete
"""

import requests
import logging
from datetime import datetime
from models import db, Stock, Prediction
from sqlalchemy import desc

logger = logging.getLogger(__name__)

class AIStockRecommender:
    """AI-powered stock recommendation system"""
    
    def __init__(self):
        self.api_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
    
    def get_todays_predictions(self):
        """Get all predictions made today"""
        try:
            today = datetime.now().date()
            
            predictions = Prediction.query.filter(
                db.func.date(Prediction.created_at) == today
            ).order_by(desc(Prediction.created_at)).all()
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error fetching predictions: {e}")
            return []
    
    def analyze_predictions(self, predictions):
        """Analyze predictions and categorize stocks"""
        try:
            if not predictions:
                return {
                    'strong_buy': [],
                    'buy': [],
                    'hold': [],
                    'sell': [],
                    'strong_sell': []
                }
            
            categorized = {
                'strong_buy': [],
                'buy': [],
                'hold': [],
                'sell': [],
                'strong_sell': []
            }
            
            for pred in predictions:
                stock = Stock.query.get(pred.stock_id)
                if not stock:
                    continue
                
                stock_data = {
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'predicted_price': pred.predicted_price,
                    'current_price': pred.current_price or 0,
                    'percent_change': ((pred.predicted_price - (pred.current_price or pred.predicted_price)) / (pred.current_price or pred.predicted_price) * 100) if pred.current_price else 0,
                    'trend': pred.trend,
                    'confidence': pred.confidence,
                    'recommendation': pred.recommendation,
                    'sentiment_score': pred.sentiment_score or 0,
                    'risk': pred.risk_percentage or 0
                }
                
                # Categorize based on trend and confidence
                if pred.trend == 'bullish':
                    if pred.confidence >= 80 and stock_data['percent_change'] > 2:
                        categorized['strong_buy'].append(stock_data)
                    elif pred.confidence >= 70:
                        categorized['buy'].append(stock_data)
                    else:
                        categorized['hold'].append(stock_data)
                elif pred.trend == 'bearish':
                    if pred.confidence >= 80 and stock_data['percent_change'] < -2:
                        categorized['strong_sell'].append(stock_data)
                    elif pred.confidence >= 70:
                        categorized['sell'].append(stock_data)
                    else:
                        categorized['hold'].append(stock_data)
                else:
                    categorized['hold'].append(stock_data)
            
            # Sort by confidence and percent change
            for category in categorized:
                if category in ['strong_buy', 'buy']:
                    categorized[category].sort(key=lambda x: (x['confidence'], x['percent_change']), reverse=True)
                elif category in ['strong_sell', 'sell']:
                    categorized[category].sort(key=lambda x: (x['confidence'], -x['percent_change']), reverse=True)
                else:
                    categorized[category].sort(key=lambda x: x['confidence'], reverse=True)
            
            return categorized
            
        except Exception as e:
            logger.error(f"Error analyzing predictions: {e}")
            import traceback
            traceback.print_exc()
            return {
                'strong_buy': [],
                'buy': [],
                'hold': [],
                'sell': [],
                'strong_sell': []
            }
    
    def generate_ai_recommendations(self, categorized_stocks):
        """Generate AI-powered recommendations"""
        try:
            # Prepare summary for AI
            summary = "Today's Stock Analysis:\n\n"
            
            summary += f"STRONG BUY ({len(categorized_stocks['strong_buy'])} stocks):\n"
            for stock in categorized_stocks['strong_buy'][:3]:
                summary += f"- {stock['name']} ({stock['symbol']}): {stock['percent_change']:+.2f}%, Confidence: {stock['confidence']:.0f}%\n"
            
            summary += f"\nBUY ({len(categorized_stocks['buy'])} stocks):\n"
            for stock in categorized_stocks['buy'][:3]:
                summary += f"- {stock['name']} ({stock['symbol']}): {stock['percent_change']:+.2f}%, Confidence: {stock['confidence']:.0f}%\n"
            
            summary += f"\nSTRONG SELL ({len(categorized_stocks['strong_sell'])} stocks):\n"
            for stock in categorized_stocks['strong_sell'][:3]:
                summary += f"- {stock['name']} ({stock['symbol']}): {stock['percent_change']:+.2f}%, Confidence: {stock['confidence']:.0f}%\n"
            
            summary += f"\nSELL ({len(categorized_stocks['sell'])} stocks):\n"
            for stock in categorized_stocks['sell'][:3]:
                summary += f"- {stock['name']} ({stock['symbol']}): {stock['percent_change']:+.2f}%, Confidence: {stock['confidence']:.0f}%\n"
            
            # Ask AI for recommendations
            prompt = f"""Based on today's stock predictions, provide investment recommendations:

{summary}

Provide:
1. TOP 3 RECOMMENDED STOCKS TO BUY (with reasons)
2. TOP 3 STOCKS TO AVOID/SELL (with reasons)
3. OVERALL MARKET SENTIMENT
4. KEY INVESTMENT STRATEGY FOR TODAY

Be specific and actionable."""
            
            headers = {'Content-Type': 'application/json'}
            data = {"prompt": prompt}
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=15)
            
            if response.status_code != 200:
                return self._generate_fallback_recommendations(categorized_stocks)
            
            result = response.json()
            ai_response = (result.get('text') or result.get('response') or result.get('output') or '').strip()
            
            return {
                'success': True,
                'ai_recommendations': ai_response,
                'categorized_stocks': categorized_stocks,
                'summary': summary,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}")
            return self._generate_fallback_recommendations(categorized_stocks)
    
    def _generate_fallback_recommendations(self, categorized_stocks):
        """Generate fallback recommendations if AI fails"""
        recommendations = "AI STOCK RECOMMENDATIONS\n\n"
        
        # Top buys
        recommendations += "TOP 3 RECOMMENDED STOCKS TO BUY:\n"
        for i, stock in enumerate(categorized_stocks['strong_buy'][:3], 1):
            recommendations += f"{i}. {stock['name']} ({stock['symbol']})\n"
            recommendations += f"   Expected gain: {stock['percent_change']:+.2f}%\n"
            recommendations += f"   Confidence: {stock['confidence']:.0f}%\n"
            recommendations += f"   Reason: Strong bullish trend with high confidence\n\n"
        
        # Top sells
        recommendations += "TOP 3 STOCKS TO AVOID/SELL:\n"
        for i, stock in enumerate(categorized_stocks['strong_sell'][:3], 1):
            recommendations += f"{i}. {stock['name']} ({stock['symbol']})\n"
            recommendations += f"   Expected loss: {stock['percent_change']:+.2f}%\n"
            recommendations += f"   Confidence: {stock['confidence']:.0f}%\n"
            recommendations += f"   Reason: Strong bearish trend with high confidence\n\n"
        
        # Market sentiment
        total_bullish = len(categorized_stocks['strong_buy']) + len(categorized_stocks['buy'])
        total_bearish = len(categorized_stocks['strong_sell']) + len(categorized_stocks['sell'])
        
        if total_bullish > total_bearish:
            market_sentiment = "BULLISH - More buying opportunities than selling"
        elif total_bearish > total_bullish:
            market_sentiment = "BEARISH - More stocks showing weakness"
        else:
            market_sentiment = "NEUTRAL - Mixed signals in the market"
        
        recommendations += f"OVERALL MARKET SENTIMENT: {market_sentiment}\n\n"
        
        recommendations += "KEY INVESTMENT STRATEGY:\n"
        recommendations += "- Focus on high-confidence predictions\n"
        recommendations += "- Diversify across multiple stocks\n"
        recommendations += "- Monitor news and market trends\n"
        recommendations += "- Set stop-loss orders to manage risk\n"
        
        return {
            'success': True,
            'ai_recommendations': recommendations,
            'categorized_stocks': categorized_stocks,
            'summary': '',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_recommendations(self):
        """Get complete stock recommendations"""
        try:
            # Get today's predictions
            predictions = self.get_todays_predictions()
            
            if not predictions:
                return {
                    'success': False,
                    'message': 'No predictions available for today',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # Analyze and categorize
            categorized = self.analyze_predictions(predictions)
            
            # Generate AI recommendations
            recommendations = self.generate_ai_recommendations(categorized)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def get_top_picks(self, limit=5):
        """Get top stock picks for quick view"""
        try:
            predictions = self.get_todays_predictions()
            categorized = self.analyze_predictions(predictions)
            
            top_buys = categorized['strong_buy'][:limit]
            top_sells = categorized['strong_sell'][:limit]
            
            return {
                'success': True,
                'top_buys': top_buys,
                'top_sells': top_sells,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error getting top picks: {e}")
            return {
                'success': False,
                'top_buys': [],
                'top_sells': [],
                'message': str(e)
            }


def get_ai_recommender():
    """Get AI recommender instance"""
    return AIStockRecommender()
