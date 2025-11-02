#!/usr/bin/env python
"""
Database initialization script
Creates all tables and default data
"""

from app import create_app, db
from models import User, Stock

def init_database():
    """Initialize database with tables and default data"""
    print("=" * 60)
    print("  Database Initialization")
    print("=" * 60)
    print()
    
    app = create_app()
    
    with app.app_context():
        # Drop all tables (use with caution!)
        # db.drop_all()
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created successfully")
        print()
        
        # Create default admin user
        print("Creating default admin user...")
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
            print("✓ Admin user created")
            print("  Email: admin@stockai.com")
            print("  Password: admin123")
        else:
            print("✓ Admin user already exists")
        
        print()
        
        # Add default stocks
        print("Adding default stocks...")
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
        
        stocks_added = 0
        for stock_data in default_stocks:
            existing = Stock.query.filter_by(symbol=stock_data['symbol']).first()
            if not existing:
                stock = Stock(**stock_data)
                db.session.add(stock)
                stocks_added += 1
        
        if stocks_added > 0:
            print(f"✓ Added {stocks_added} default stocks")
        else:
            print("✓ Default stocks already exist")
        
        # Commit all changes
        db.session.commit()
        print()
        
        # Summary
        print("=" * 60)
        print("  Database Initialization Complete!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  Total Users: {User.query.count()}")
        print(f"  Total Stocks: {Stock.query.count()}")
        print()
        print("Next Steps:")
        print("  1. Start the application: python run.py")
        print("  2. Login as admin: admin@stockai.com / admin123")
        print("  3. Download stock data and train models")
        print()
        print("⚠️  Remember to change the admin password!")
        print("=" * 60)

if __name__ == '__main__':
    init_database()
