"""Simple startup script"""
import os
import sys

print("=" * 60)
print("  Starting AI Stock Market Prediction Platform")
print("=" * 60)
print()

# Check if .env exists
if not os.path.exists('.env'):
    print("⚠️  Warning: .env file not found!")
    print("   Please configure .env file with your credentials")
    print()

# Initialize database
print("[1/2] Initializing database...")
try:
    from app import create_app, db
    from models import User, Stock
    
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create admin if not exists
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
            print("   ✓ Admin user created")
        else:
            print("   ✓ Admin user exists")
        
        # Add default stocks if none
        if Stock.query.count() == 0:
            default_stocks = [
                {'symbol': 'TCS', 'name': 'Tata Consultancy Services', 'sector': 'IT'},
                {'symbol': 'RELIANCE', 'name': 'Reliance Industries', 'sector': 'Conglomerate'},
                {'symbol': 'HDFCBANK', 'name': 'HDFC Bank', 'sector': 'Banking'},
                {'symbol': 'INFY', 'name': 'Infosys', 'sector': 'IT'},
            ]
            for stock_data in default_stocks:
                stock = Stock(**stock_data)
                db.session.add(stock)
            db.session.commit()
            print(f"   ✓ Added {len(default_stocks)} default stocks")
        
    print("   ✓ Database ready")
except Exception as e:
    print(f"   ✗ Database error: {e}")
    sys.exit(1)

print()
print("[2/2] Starting Flask application...")
print()
print("=" * 60)
print("  Application Starting!")
print("=" * 60)
print()
print("  URL: http://localhost:5000")
print()
print("  Admin Login:")
print("    Email: admin@stockai.com")
print("    Password: admin123")
print()
print("  ⚠️  Change admin password after first login!")
print("=" * 60)
print()

# Start app
try:
    from utils.scheduler import start_scheduler
    start_scheduler(app)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1)
