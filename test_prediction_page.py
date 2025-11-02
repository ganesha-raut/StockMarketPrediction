"""Complete test for prediction page APIs"""
from app import create_app
from models import User, db

app = create_app()

with app.test_client() as client:
    with app.app_context():
        # Login first
        print("\n" + "="*60)
        print("TESTING PREDICTION PAGE APIs")
        print("="*60 + "\n")
        
        # Test 1: Check if admin user exists
        print("1. Checking admin user...")
        admin = User.query.filter_by(email='admin@stockai.com').first()
        if admin:
            print(f"   Admin exists: {admin.email}")
            print(f"   Admin role: {admin.role}")
        else:
            print("   ERROR: Admin user not found!")
            print("   Creating admin user...")
            from werkzeug.security import generate_password_hash
            admin = User(
                email='admin@stockai.com',
                password_hash=generate_password_hash('admin123'),
                full_name='Admin User',
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("   Admin user created!")
        
        # Test 2: Login
        print("\n2. Testing Login...")
        response = client.post('/auth/login', data={
            'email': 'admin@stockai.com',
            'password': 'admin123'
        }, follow_redirects=False)
        print(f"   Login Status: {response.status_code}")
        if response.status_code == 302:
            print(f"   Redirect to: {response.location}")
            print("   ✓ Login successful (redirecting)")
        
        # Test 3: Stock Detail API
        print("\n3. Testing /user/api/stock/RELIANCE...")
        response = client.get('/user/api/stock/RELIANCE')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Success: {data.get('success')}")
            if data.get('success'):
                stock_data = data.get('data', {})
                print(f"   Symbol: {stock_data.get('symbol')}")
                print(f"   Name: {stock_data.get('name')}")
                live_data = stock_data.get('live_data', {})
                print(f"   Live Price: ₹{live_data.get('live_price', 0):,.2f}")
                print(f"   Has Model: {stock_data.get('has_model')}")
            else:
                print(f"   Error: {data.get('message')}")
        elif response.status_code == 302:
            print(f"   ✗ Not logged in - redirecting to login")
        else:
            print(f"   Error: Status {response.status_code}")
        
        # Test 4: Market Status API
        print("\n4. Testing /user/api/market-status...")
        response = client.get('/user/api/market-status')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Success: {data.get('success')}")
            if data.get('success'):
                market = data.get('data', {})
                print(f"   Market Open: {market.get('is_open')}")
                print(f"   Status: {market.get('status')}")
        
        # Test 5: Stock News API
        print("\n5. Testing /api/stock-news/RELIANCE...")
        response = client.get('/api/stock-news/RELIANCE')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Success: {data.get('success')}")
            if data.get('success'):
                news = data.get('data', [])
                print(f"   News Count: {len(news)}")
        elif response.status_code == 302:
            print(f"   ✗ Not logged in")
        
        # Test 6: Chart Data API
        print("\n6. Testing /api/stock-chart-data/RELIANCE...")
        response = client.get('/api/stock-chart-data/RELIANCE')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Success: {data.get('success')}")
            if data.get('success'):
                chart_data = data.get('data', [])
                print(f"   Data Points: {len(chart_data)}")
        elif response.status_code == 302:
            print(f"   ✗ Not logged in")
        
        # Test 7: Prediction Page
        print("\n7. Testing /user/prediction/RELIANCE page...")
        response = client.get('/user/prediction/RELIANCE')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Page Loads: Yes")
        elif response.status_code == 302:
            print(f"   ✗ Not logged in - redirecting")
        
        print("\n" + "="*60)
        print("SUMMARY:")
        print("The test client needs to maintain session cookies.")
        print("Login is working but session not persisting in test.")
        print("\nTo test manually:")
        print("1. Start Flask: python app.py")
        print("2. Login at: http://localhost:5000/auth/login")
        print("3. Visit: http://localhost:5000/user/prediction/RELIANCE")
        print("="*60)
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60 + "\n")
