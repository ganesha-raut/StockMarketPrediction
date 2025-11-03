from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Stock, Prediction, HistoricalData
from utils.stock_data import get_google_stock_data, get_stock_news
from utils.enhanced_ml_model_lite import load_or_create_enhanced_model, get_enhanced_model_path
from utils.gemini_ai import get_gemini
from utils.news_analyzer import get_news_analyzer
from utils.hybrid_predictor import get_hybrid_predictor
from datetime import datetime, timedelta
import pandas as pd
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/predict/<symbol>', methods=['POST'])
@login_required
def predict_stock(symbol):
    """Make stock price prediction"""
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        if not stock.has_model:
            return jsonify({'success': False, 'message': 'Model not trained for this stock'}), 400
        
        data = request.get_json()
        prediction_type = data.get('type', 'intraday')  # 'intraday' or 'long_term'
        prediction_period = int(data.get('period', 7)) if data.get('period') else 7  # Number of days
        
        # Get recent historical data - Enhanced model needs more data for features
        recent_data = HistoricalData.query.filter_by(
            stock_id=stock.id
        ).order_by(HistoricalData.date.desc()).limit(300).all()
        
        if len(recent_data) < 50:
            return jsonify({'success': False, 'message': 'Insufficient historical data. Please ensure stock data is updated.'}), 400
        
        # Convert to DataFrame - Enhanced model needs different column names
        df = pd.DataFrame([{
            'Date': d.date,
            'Open': d.open_price,
            'High': d.high_price,
            'Low': d.low_price,
            'Close': d.close_price,
            'Volume': d.volume
        } for d in reversed(recent_data)])
        
        # Initialize variables
        sentiment_score = 0.0
        gemini = get_gemini()
        
        # Use HYBRID AI + SI + ML Predictor for superior predictions
        hybrid_predictor = get_hybrid_predictor(stock.symbol, stock.name)
        
        # Get hybrid prediction (combines AI, SI, and ML)
        prediction_result = hybrid_predictor.hybrid_predict(days_ahead=prediction_period)
        
        if not prediction_result or not prediction_result.get('success', False):
            return jsonify({'success': False, 'message': prediction_result.get('error', 'Prediction failed')}), 500
        
        # Get live data
        live_data = get_google_stock_data(symbol)
        
        # Save prediction to database
        prediction = Prediction(
            stock_id=stock.id,
            prediction_date=datetime.now().date(),
            predicted_price=prediction_result['predicted_price'],
            confidence=prediction_result['confidence'],
            trend=prediction_result['trend'],
            prediction_type=prediction_type,
            risk_percentage=prediction_result['risk_percentage'],
            sentiment_score=sentiment_score,
            recommendation=prediction_result['recommendation'],
            model_version=stock.model_version
        )
        db.session.add(prediction)
        db.session.commit()
        
        # Get AI insight with news analysis
        ai_insight = ""
        news_analysis = ""
        
        if gemini and live_data:
            ai_insight = gemini.get_stock_prediction_insight(live_data, prediction_result)
        
        # Get news analysis based on prediction type
        news_analyzer = get_news_analyzer()
        if prediction_type == 'intraday':
            news_analysis = news_analyzer.analyze_intraday_news(
                symbol=symbol,
                company_name=stock.name,
                current_price=prediction_result['current_price'],
                predicted_price=prediction_result['predicted_price']
            )
        else:  # long_term
            news_analysis = news_analyzer.analyze_longterm_news(
                symbol=symbol,
                company_name=stock.name,
                current_price=prediction_result['current_price'],
                predicted_price=prediction_result['predicted_price'],
                days_ahead=prediction_period
            )
        
        # Calculate investment details if provided (for both intraday and longterm)
        investment_details = None
        if data.get('investment'):
            investment_amount = float(data.get('investment'))
            current_price = prediction_result['current_price']
            predicted_price = prediction_result['predicted_price']
            
            # Calculate shares that can be bought
            shares = int(investment_amount / current_price)
            actual_investment = shares * current_price
            
            # Calculate potential profit/loss
            predicted_value = shares * predicted_price
            profit_loss = predicted_value - actual_investment
            profit_loss_percent = (profit_loss / actual_investment) * 100 if actual_investment > 0 else 0
            
            investment_details = {
                'investment_amount': investment_amount,
                'shares': shares,
                'actual_investment': actual_investment,
                'buy_price': current_price,
                'target_price': predicted_price,
                'predicted_value': predicted_value,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
                'remaining_cash': investment_amount - actual_investment
            }
        
        # Handle long-term prediction with period
        period_details = None
        if prediction_type == 'longterm':
            period = int(data.get('period', 7))
            target_price = data.get('target_price')
            
            period_details = {
                'period_days': period,
                'target_date': (datetime.now() + timedelta(days=period)).strftime('%Y-%m-%d'),
                'user_target_price': float(target_price) if target_price else None
            }
            
            # If user provided target price, calculate if it's achievable
            if target_price:
                target_price = float(target_price)
                current_price = prediction_result['current_price']
                predicted_price = prediction_result['predicted_price']
                
                required_change = ((target_price - current_price) / current_price) * 100
                predicted_change = ((predicted_price - current_price) / current_price) * 100
                
                period_details['achievable'] = abs(predicted_change) >= abs(required_change) * 0.8
                period_details['required_change_percent'] = required_change
                period_details['predicted_change_percent'] = predicted_change
        
        # Get sentiment score from prediction result if available (enhanced model includes it)
        final_sentiment = prediction_result.get('sentiment_score', 0.0)
        
        response_data = {
            'predicted_price': prediction_result['predicted_price'],
            'current_price': prediction_result['current_price'],
            'price_change': prediction_result['price_change'],
            'percent_change': prediction_result['percent_change'],
            'confidence': prediction_result['confidence'],
            'trend': prediction_result['trend'],
            'recommendation': prediction_result['recommendation'],
            'risk_percentage': prediction_result['risk_percentage'],
            'sentiment_score': final_sentiment,
            'ai_insight': ai_insight,
            'news_analysis': news_analysis,
            'model_type': 'hybrid_ai_si_ml',  # New hybrid model
            'model_version': stock.model_version,
            'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'prediction_type': prediction_type,
            
            # Hybrid prediction details
            'ml_prediction': prediction_result.get('ml_prediction'),
            'ai_prediction': prediction_result.get('ai_prediction'),
            'dividend_analysis': prediction_result.get('dividend_analysis'),
            'si_formula': prediction_result.get('si_formula'),
            'hybrid_details': prediction_result.get('hybrid_details')
        }
        
        # Add type-specific details
        if investment_details:
            response_data['investment'] = investment_details
        if period_details:
            response_data['period'] = period_details
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    """Chat with AI assistant"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'success': False, 'message': 'Message required'}), 400
        
        gemini = get_gemini()
        if not gemini:
            return jsonify({'success': False, 'message': 'AI service unavailable'}), 503
        
        # Check if message is about a specific stock
        context = None
        words = message.upper().split()
        
        # Try to find stock symbol in message
        stocks = Stock.query.filter_by(is_active=True).all()
        mentioned_stock = None
        
        for stock in stocks:
            if stock.symbol in words or stock.name.upper() in message.upper():
                mentioned_stock = stock
                break
        
        # If stock mentioned, add context
        if mentioned_stock:
            live_data = get_google_stock_data(mentioned_stock.symbol)
            if live_data:
                context = f"""
                Stock: {mentioned_stock.name} ({mentioned_stock.symbol})
                Current Price: ₹{live_data['live_price']}
                Change: {live_data['percent_change_formatted']}
                Trend: {live_data['trend']}
                """
        
        # Get AI response
        response = gemini.chat(message, context)
        
        return jsonify({
            'success': True,
            'data': {
                'message': response,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/stock/<symbol>/news')
@login_required
def stock_news(symbol):
    """Get stock news with sentiment"""
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        news = get_stock_news(symbol, limit=10)
        
        # Analyze sentiment
        gemini = get_gemini()
        if gemini and news:
            news = gemini.analyze_news_batch(news)
        
        return jsonify({'success': True, 'data': news})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/stock/<symbol>/chart-data')
@login_required
def stock_chart_data(symbol):
    """Get historical data for charts"""
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        # Get data for last 30 days
        days = int(request.args.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        
        hist_data = HistoricalData.query.filter(
            HistoricalData.stock_id == stock.id,
            HistoricalData.date >= start_date.date()
        ).order_by(HistoricalData.date).all()
        
        result = []
        for d in hist_data:
            result.append({
                'date': d.date.strftime('%Y-%m-%d'),
                'open': d.open_price,
                'high': d.high_price,
                'low': d.low_price,
                'close': d.close_price,
                'volume': d.volume
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/stock/<symbol>/predictions')
@login_required
def stock_predictions(symbol):
    """Get prediction history for stock"""
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        predictions = Prediction.query.filter_by(
            stock_id=stock.id
        ).order_by(Prediction.created_at.desc()).limit(20).all()
        
        result = []
        for pred in predictions:
            result.append({
                'prediction_date': pred.prediction_date.strftime('%Y-%m-%d'),
                'predicted_price': pred.predicted_price,
                'actual_price': pred.actual_price,
                'confidence': pred.confidence,
                'trend': pred.trend,
                'recommendation': pred.recommendation,
                'created_at': pred.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/stock-news/<symbol>')
@login_required
def get_stock_news_api(symbol):
    """Get latest news for a stock"""
    try:
        news = get_stock_news(symbol, limit=10)
        
        if not news:
            return jsonify({'success': True, 'data': []})
        
        # Analyze sentiment with Gemini
        gemini = get_gemini()
        if gemini:
            news = gemini.analyze_news_batch(news)
        
        return jsonify({'success': True, 'data': news})
        
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/stock-chart-data/<symbol>')
@login_required
def get_stock_chart_data(symbol):
    """Get historical chart data for a stock"""
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        # Get last 30 days of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        historical_data = HistoricalData.query.filter(
            HistoricalData.stock_id == stock.id,
            HistoricalData.date >= start_date,
            HistoricalData.date <= end_date
        ).order_by(HistoricalData.date.asc()).all()
        
        if not historical_data:
            return jsonify({'success': True, 'data': []})
        
        result = []
        for data in historical_data:
            result.append({
                'date': data.date.strftime('%Y-%m-%d'),
                'open': float(data.open_price),
                'high': float(data.high_price),
                'low': float(data.low_price),
                'close': float(data.close_price),
                'volume': int(data.volume)
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
