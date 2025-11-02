from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config
from models import db, User, Stock, EmailConfig
from utils.email_service import mail
from utils.gemini_ai import init_gemini
from datetime import datetime
import os

# Import blueprints
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.api import api_bp

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    
    # Initialize Gemini AI
    if app.config.get('GEMINI_API_KEY'):
        init_gemini(app.config['GEMINI_API_KEY'])
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'app_name': app.config['APP_NAME'],
            'current_year': datetime.now().year
        }
    
    # Main routes
    @app.route('/')
    def index():
        """Landing page"""
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.home'))
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@stockai.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@stockai.com',
                is_admin=True,
                is_verified=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin@stockai.com / admin123")
        
        # Add some default stocks if none exist
        if Stock.query.count() == 0:
            default_stocks = [
                {'symbol': 'TCS', 'name': 'Tata Consultancy Services', 'sector': 'IT'},
                {'symbol': 'RELIANCE', 'name': 'Reliance Industries', 'sector': 'Conglomerate'},
                {'symbol': 'HDFCBANK', 'name': 'HDFC Bank', 'sector': 'Banking'},
                {'symbol': 'INFY', 'name': 'Infosys', 'sector': 'IT'},
                {'symbol': 'ICICIBANK', 'name': 'ICICI Bank', 'sector': 'Banking'},
                {'symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever', 'sector': 'FMCG'},
                {'symbol': 'ITC', 'name': 'ITC Limited', 'sector': 'FMCG'},
                {'symbol': 'SBIN', 'name': 'State Bank of India', 'sector': 'Banking'},
                {'symbol': 'BHARTIARTL', 'name': 'Bharti Airtel', 'sector': 'Telecom'},
                {'symbol': 'WIPRO', 'name': 'Wipro', 'sector': 'IT'}
            ]
            
            for stock_data in default_stocks:
                stock = Stock(**stock_data)
                db.session.add(stock)
            
            db.session.commit()
            print(f"Added {len(default_stocks)} default stocks")
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    
    # Start background scheduler
    from utils.scheduler import start_scheduler
    start_scheduler(app)
    
    app.run(port=5000, debug=True)
