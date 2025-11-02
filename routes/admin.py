from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Stock, EmailConfig, ModelTraining, HistoricalData
from utils.stock_data import get_historical_data_yfinance
from utils.ml_model import StockPredictionModel, get_model_path
from utils.gemini_ai import get_gemini
from werkzeug.utils import secure_filename
import pandas as pd
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/stocks')
@login_required
@admin_required
def stocks():
    """Stock management page"""
    return render_template('admin/stocks.html')

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    return render_template('admin/users.html')

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Admin settings page"""
    return render_template('admin/settings.html')

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """Get dashboard statistics"""
    try:
        total_users = User.query.filter_by(is_admin=False).count()
        active_users = User.query.filter_by(is_admin=False, is_active=True).count()
        total_stocks = Stock.query.count()
        trained_models = Stock.query.filter_by(has_model=True).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'total_stocks': total_stocks,
                'trained_models': trained_models
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/users')
@login_required
@admin_required
def api_users():
    """Get all users"""
    try:
        users = User.query.filter_by(is_admin=False).all()
        
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_verified': user.is_verified,
                'is_active': user.is_active,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'watchlist_count': len(user.watchlist)
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/user/toggle-status', methods=['POST'])
@login_required
@admin_required
def api_user_toggle_status():
    """Activate/deactivate user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if user.is_admin:
            return jsonify({'success': False, 'message': 'Cannot modify admin user'}), 400
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'User {status}'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/stocks')
@login_required
@admin_required
def api_stocks():
    """Get all stocks"""
    try:
        stocks = Stock.query.all()
        
        result = []
        for stock in stocks:
            result.append({
                'id': stock.id,
                'symbol': stock.symbol,
                'name': stock.name,
                'sector': stock.sector,
                'exchange': stock.exchange,
                'is_active': stock.is_active,
                'has_model': stock.has_model,
                'model_version': stock.model_version,
                'last_trained': stock.last_trained.strftime('%Y-%m-%d %H:%M:%S') if stock.last_trained else None,
                'created_at': stock.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/stock/add', methods=['POST'])
@login_required
@admin_required
def api_stock_add():
    """Add new stock"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        name = data.get('name')
        sector = data.get('sector')
        
        if not symbol or not name:
            return jsonify({'success': False, 'message': 'Symbol and name required'}), 400
        
        # Check if exists
        if Stock.query.filter_by(symbol=symbol).first():
            return jsonify({'success': False, 'message': 'Stock already exists'}), 400
        
        stock = Stock(
            symbol=symbol,
            name=name,
            sector=sector,
            exchange='NSE'
        )
        db.session.add(stock)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Stock added successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/stock/upload-csv', methods=['POST'])
@login_required
@admin_required
def api_stock_upload_csv():
    """Upload historical data CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        stock_id = request.form.get('stock_id')
        
        if not stock_id:
            return jsonify({'success': False, 'message': 'Stock ID required'}), 400
        
        stock = Stock.query.get(stock_id)
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'Only CSV files allowed'}), 400
        
        # Save file
        filename = secure_filename(f"{stock.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        filepath = os.path.join(current_app.config['DATA_FOLDER'], filename)
        file.save(filepath)
        
        # Read and validate CSV
        df = pd.read_csv(filepath)
        
        # Expected columns
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            os.remove(filepath)
            return jsonify({
                'success': False,
                'message': f'Missing columns: {", ".join(missing_cols)}'
            }), 400
        
        # Parse and store data
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Delete existing data
        HistoricalData.query.filter_by(stock_id=stock.id).delete()
        
        # Insert new data
        for _, row in df.iterrows():
            hist_data = HistoricalData(
                stock_id=stock.id,
                date=row['Date'].date(),
                open_price=row['Open'],
                high_price=row['High'],
                low_price=row['Low'],
                close_price=row['Close'],
                volume=row['Volume'],
                dividend=row.get('Dividend', 0.0)
            )
            db.session.add(hist_data)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Uploaded {len(df)} data points',
            'rows': len(df)
        })
        
    except Exception as e:
        db.session.rollback()
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/stock/download-data', methods=['POST'])
@login_required
@admin_required
def api_stock_download_data():
    """Download historical data from yfinance"""
    try:
        data = request.get_json()
        stock_id = data.get('stock_id')
        period = data.get('period', '5y')
        
        if not stock_id:
            return jsonify({'success': False, 'message': 'Stock ID required'}), 400
        
        stock = Stock.query.get(stock_id)
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        # Download data
        df = get_historical_data_yfinance(stock.symbol, period)
        
        if df is None or df.empty:
            return jsonify({'success': False, 'message': 'Unable to download data'}), 500
        
        # Delete existing data
        HistoricalData.query.filter_by(stock_id=stock.id).delete()
        
        # Insert new data
        for _, row in df.iterrows():
            hist_data = HistoricalData(
                stock_id=stock.id,
                date=row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                open_price=row['open_price'],
                high_price=row['high_price'],
                low_price=row['low_price'],
                close_price=row['close_price'],
                volume=row['volume'],
                dividend=row.get('dividend', 0.0)
            )
            db.session.add(hist_data)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Downloaded {len(df)} data points',
            'rows': len(df)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/stock/train-model', methods=['POST'])
@login_required
@admin_required
def api_stock_train_model():
    """Train ML model for stock"""
    try:
        data = request.get_json()
        stock_id = data.get('stock_id')
        
        if not stock_id:
            return jsonify({'success': False, 'message': 'Stock ID required'}), 400
        
        stock = Stock.query.get(stock_id)
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        # Get historical data
        hist_data = HistoricalData.query.filter_by(stock_id=stock.id).order_by(HistoricalData.date).all()
        
        if len(hist_data) < 100:
            return jsonify({
                'success': False,
                'message': f'Insufficient data. Have {len(hist_data)}, need at least 100 points'
            }), 400
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': d.date,
            'open_price': d.open_price,
            'high_price': d.high_price,
            'low_price': d.low_price,
            'close_price': d.close_price,
            'volume': d.volume,
            'dividend': d.dividend
        } for d in hist_data])
        
        # Get sentiment score from recent news
        sentiment_score = 0.0
        gemini = get_gemini()
        if gemini:
            from utils.stock_data import get_stock_news
            news = get_stock_news(stock.symbol, limit=10)
            if news:
                analyzed = gemini.analyze_news_batch(news)
                sentiment_scores = [item.get('sentiment_score', 0.0) for item in analyzed]
                sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # Create training record
        training = ModelTraining(
            stock_id=stock.id,
            model_version=f"v{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            training_start=datetime.utcnow(),
            status='running',
            data_points=len(df)
        )
        db.session.add(training)
        db.session.commit()
        
        # Train model
        model = StockPredictionModel(stock.symbol)
        result = model.train(df, sentiment_score)
        
        if result['success']:
            # Save model
            model_path = get_model_path(stock.symbol)
            model.save_model(model_path)
            
            # Update stock
            stock.has_model = True
            stock.model_version = result['model_version']
            stock.last_trained = datetime.utcnow()
            
            # Update training record
            training.training_end = datetime.utcnow()
            training.status = 'completed'
            training.accuracy = result['accuracy']
            training.mae = result['mae']
            training.rmse = result['rmse']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Model trained successfully',
                'accuracy': result['accuracy'],
                'mae': result['mae'],
                'rmse': result['rmse']
            })
        else:
            training.training_end = datetime.utcnow()
            training.status = 'failed'
            training.error_message = result.get('error', 'Unknown error')
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': result.get('error', 'Training failed')
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/email-config')
@login_required
@admin_required
def api_email_config_get():
    """Get email configuration"""
    try:
        config = EmailConfig.query.filter_by(is_active=True).first()
        
        if not config:
            return jsonify({
                'success': True,
                'data': {
                    'mail_server': current_app.config.get('MAIL_SERVER'),
                    'mail_port': current_app.config.get('MAIL_PORT'),
                    'mail_use_tls': current_app.config.get('MAIL_USE_TLS'),
                    'mail_username': current_app.config.get('MAIL_USERNAME'),
                    'mail_default_sender': current_app.config.get('MAIL_DEFAULT_SENDER')
                }
            })
        
        return jsonify({
            'success': True,
            'data': {
                'mail_server': config.mail_server,
                'mail_port': config.mail_port,
                'mail_use_tls': config.mail_use_tls,
                'mail_username': config.mail_username,
                'mail_default_sender': config.mail_default_sender
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/email-config/update', methods=['POST'])
@login_required
@admin_required
def api_email_config_update():
    """Update email configuration"""
    try:
        data = request.get_json()
        
        mail_server = data.get('mail_server')
        mail_port = data.get('mail_port')
        mail_use_tls = data.get('mail_use_tls', True)
        mail_username = data.get('mail_username')
        mail_password = data.get('mail_password')
        mail_default_sender = data.get('mail_default_sender')
        
        if not all([mail_server, mail_port, mail_username, mail_password, mail_default_sender]):
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        # Deactivate old configs
        EmailConfig.query.update({'is_active': False})
        
        # Create new config
        config = EmailConfig(
            mail_server=mail_server,
            mail_port=int(mail_port),
            mail_use_tls=mail_use_tls,
            mail_username=mail_username,
            mail_password=mail_password,
            mail_default_sender=mail_default_sender,
            is_active=True,
            updated_by=current_user.id
        )
        db.session.add(config)
        db.session.commit()
        
        # Update Flask-Mail config
        current_app.config['MAIL_SERVER'] = mail_server
        current_app.config['MAIL_PORT'] = int(mail_port)
        current_app.config['MAIL_USE_TLS'] = mail_use_tls
        current_app.config['MAIL_USERNAME'] = mail_username
        current_app.config['MAIL_PASSWORD'] = mail_password
        current_app.config['MAIL_DEFAULT_SENDER'] = mail_default_sender
        
        return jsonify({'success': True, 'message': 'Email configuration updated'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
