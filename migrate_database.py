"""
Database Migration Script
Adds new columns and tables for monitoring system
"""

import sqlite3
import os

def migrate_database():
    """Add new columns and tables to existing database"""
    
    db_path = 'instance/stock_prediction.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Creating new database...")
        from app import create_app, db
        app = create_app('development')
        with app.app_context():
            db.create_all()
        print("✅ New database created successfully!")
        return
    
    print("🔄 Migrating existing database...")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if email_notifications column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'email_notifications' not in columns:
            print("📝 Adding email_notifications column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT 1")
            print("✅ Added email_notifications column")
        else:
            print("⏭️  email_notifications column already exists")
        
        # Create user_watchlist table
        print("\n📝 Creating user_watchlist table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_id INTEGER NOT NULL,
                notifications_enabled BOOLEAN DEFAULT 1,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (stock_id) REFERENCES stocks(id)
            )
        """)
        print("✅ Created user_watchlist table")
        
        # Create stock_alerts table
        print("\n📝 Creating stock_alerts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_id INTEGER NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                current_price FLOAT NOT NULL,
                predicted_price FLOAT NOT NULL,
                percent_change FLOAT NOT NULL,
                confidence FLOAT NOT NULL,
                risk_percentage FLOAT NOT NULL,
                recommendation VARCHAR(20) NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                is_dismissed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (stock_id) REFERENCES stocks(id)
            )
        """)
        print("✅ Created stock_alerts table")
        
        # Commit changes
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ Database migration completed successfully!")
        print("=" * 60)
        
        # Show table info
        print("\n📊 Database Tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table[0]}: {count} rows")
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
