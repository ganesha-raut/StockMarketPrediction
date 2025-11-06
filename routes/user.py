from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Stock, Watchlist, Notification, NotificationSetting, HistoricalData, User
from utils.stock_data import get_google_stock_data, check_market_status, get_stock_news
from utils.gemini_ai import get_gemini
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

user_bp = Blueprint('user', __name__)

@user_bp.route('/home')
@login_required
def home():
    """User home page - SPA version for fast loading"""
    return render_template('user/User_dash.html')

@user_bp.route('/watchlist')
@login_required
def watchlist():
    """User watchlist page"""
    return render_template('user/watchlist.html')

@user_bp.route('/notifications')
@login_required
def notifications():
    """User notifications page"""
    return render_template('user/notifications.html')

@user_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('user/profile.html')

@user_bp.route('/prediction/<symbol>')
@login_required
def prediction(symbol):
    """Stock prediction page"""
    stock = Stock.query.filter_by(symbol=symbol).first()
    if not stock:
        return render_template('errors/404.html'), 404
    return render_template('user/prediction.html', stock=stock, symbol=symbol)

@user_bp.route('/api/market-status')
@login_required
def api_market_status():
    """Get market status"""
    try:
        status = check_market_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@user_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()

        # Validate inputs
        if not username:
            return jsonify({
                'success': False,
                'errors': {'username': 'Username is required'}
            }), 400

        if not email:
            return jsonify({
                'success': False,
                'errors': {'email': 'Email is required'}
            }), 400

        # Check if username is taken (excluding current user)
        existing_user = User.query.filter(
            User.username == username,
            User.id != current_user.id
        ).first()
        if existing_user:
            return jsonify({
                'success': False,
                'errors': {'username': 'Username is already taken'}
            }), 400

        # Check if email is taken (excluding current user)
        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        if existing_user:
            return jsonify({
                'success': False,
                'errors': {'email': 'Email is already taken'}
            }), 400

        # Update user profile
        current_user.username = username
        current_user.email = email
        current_user.updated_at = datetime.utcnow()
        
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/ai-suggestions')
@login_required
def api_ai_suggestions():
    """Get AI suggested stocks"""
    try:
        gemini = get_gemini()
        if not gemini:
            return jsonify({'success': False, 'message': 'AI service unavailable'}), 503
        
        suggestions = gemini.get_stock_suggestions(limit=4)
        
        # Enrich with live data
        enriched = []
        for suggestion in suggestions:
            live_data = get_google_stock_data(suggestion['symbol'])
            if live_data:
                suggestion.update({
                    'live_price': live_data['live_price'],
                    'live_price_formatted': live_data['live_price_formatted'],
                    'change_price': live_data['change_price'],
                    'percent_change': live_data['percent_change'],
                    'trend': live_data['trend']
                })
                enriched.append(suggestion)
        
        return jsonify({'success': True, 'data': enriched})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/all-stocks')
@login_required
def api_all_stocks():
    """Get all active stocks with live data - FIXED version with cache info"""
    try:
        stocks = Stock.query.filter_by(is_active=True).all()
        user_id = current_user.id
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Get watchlist stocks for current user
        watchlist_stock_ids = set([w.stock_id for w in Watchlist.query.filter_by(user_id=user_id).all()])
        
        result = []
        for stock in stocks:
            try:
                live_data = get_google_stock_data(stock.symbol, force_refresh=force_refresh)
                if live_data:
                    result.append({
                        'id': stock.id,
                        'symbol': stock.symbol,
                        'name': live_data.get('name', stock.name),
                        'live_price': live_data['live_price'],
                        'live_price_formatted': live_data['live_price_formatted'],
                        'change_price': live_data['change_price'],
                        'change_price_formatted': live_data['change_price_formatted'],
                        'percent_change': live_data['percent_change'],
                        'percent_change_formatted': live_data['percent_change_formatted'],
                        'trend': live_data['trend'],
                        'day_range': live_data['day_range'],
                        'volume': live_data['volume'],
                        'market_cap': live_data.get('market_cap', 'N/A'),
                        'in_watchlist': stock.id in watchlist_stock_ids,
                        'has_model': stock.has_model,
                        'last_updated': live_data.get('last_updated', '')
                    })
            except Exception as e:
                print(f"Error fetching {stock.symbol}: {e}")
                continue
        
        return jsonify({'success': True, 'data': result, 'cached': not force_refresh})
        
    except Exception as e:
        print(f"Error in api_all_stocks: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/stock/<symbol>')
@login_required
def api_stock_detail(symbol):
    """Get detailed stock information"""
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'success': False, 'message': 'Stock not found in database'}), 404
        
        # Check market status first
        try:
            market_status = check_market_status()
            is_market_open = market_status.get('is_open', False)
        except Exception as e:
            print(f"Warning: Could not check market status: {e}")
            is_market_open = False
        
        # Try to get live data (try regardless of market status, will fallback if fails)
        live_data = None
        try:
            live_data = get_google_stock_data(symbol)
        except Exception as e:
            print(f"Warning: Could not fetch live data: {e}")
        
        # If live data fails or market closed, use latest historical data
        if not live_data:
            print(f"Using historical data for {symbol} (Market: {'Open' if is_market_open else 'Closed'})")
            
            # Get latest historical data from database
            latest_data = HistoricalData.query.filter_by(
                stock_id=stock.id
            ).order_by(HistoricalData.date.desc()).first()
            
            if latest_data:
                # Calculate change from previous day
                prev_data = HistoricalData.query.filter_by(
                    stock_id=stock.id
                ).filter(HistoricalData.date < latest_data.date).order_by(
                    HistoricalData.date.desc()
                ).first()
                
                change_price = 0.0
                percent_change = 0.0
                if prev_data:
                    change_price = latest_data.close_price - prev_data.close_price
                    percent_change = (change_price / prev_data.close_price) * 100
                
                live_data = {
                    'name': stock.name,
                    'symbol': symbol,
                    'live_price': float(latest_data.close_price),
                    'live_price_formatted': f'₹{latest_data.close_price:,.2f}',
                    'change_price': float(change_price),
                    'change_price_formatted': f'₹{change_price:,.2f}',
                    'percent_change': float(percent_change),
                    'percent_change_formatted': f'{percent_change:+.2f}%',
                    'trend': 'up' if change_price > 0 else 'down' if change_price < 0 else 'neutral',
                    'day_range': f'₹{latest_data.low_price:,.2f} - ₹{latest_data.high_price:,.2f}',
                    'volume': f'{int(latest_data.volume):,}',
                    'market_cap': 'N/A',
                    'last_updated': latest_data.date.strftime('%Y-%m-%d')
                }
            else:
                # Final fallback if no historical data
                live_data = {
                    'name': stock.name,
                    'symbol': symbol,
                    'live_price': 0.0,
                    'live_price_formatted': '₹0.00',
                    'change_price': 0.0,
                    'change_price_formatted': '₹0.00',
                    'percent_change': 0.0,
                    'percent_change_formatted': '0.00%',
                    'trend': 'neutral',
                    'day_range': 'N/A',
                    'volume': 'N/A',
                    'market_cap': 'N/A'
                }
        
        # Get news (optional, don't fail if it doesn't work)
        news = []
        try:
            news = get_stock_news(symbol, limit=5)
            # Analyze news sentiment
            gemini = get_gemini()
            if gemini and news:
                news = gemini.analyze_news_batch(news)
        except Exception as news_error:
            print(f"Warning: Unable to fetch news for {symbol}: {news_error}")
        
        # Check watchlist status
        in_watchlist = Watchlist.query.filter_by(
            user_id=current_user.id,
            stock_id=stock.id
        ).first() is not None
        
        result = {
            'id': stock.id,
            'symbol': stock.symbol,
            'name': live_data.get('name', stock.name),
            'live_data': live_data,
            'news': news,
            'in_watchlist': in_watchlist,
            'has_model': stock.has_model,
            'sector': stock.sector
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        print(f"Error in api_stock_detail for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a more helpful error message
        error_msg = str(e)
        if "HistoricalData" in error_msg:
            error_msg = "Database error. Please ensure historical data exists for this stock."
        
        return jsonify({
            'success': False, 
            'message': error_msg,
            'details': 'Check server console for full error trace'
        }), 500

@user_bp.route('/api/watchlist/add', methods=['POST'])
@login_required
def api_watchlist_add():
    """Add stock to watchlist"""
    try:
        data = request.get_json()
        print(f"Watchlist add request data: {data}")  # Debug log
        
        stock_id = data.get('stock_id')
        
        if not stock_id:
            print("Error: Stock ID not provided")
            return jsonify({'success': False, 'message': 'Stock ID required'}), 400
        
        # Verify stock exists
        stock = Stock.query.get(stock_id)
        if not stock:
            print(f"Error: Stock ID {stock_id} not found")
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        # Check if already in watchlist
        existing = Watchlist.query.filter_by(
            user_id=current_user.id,
            stock_id=stock_id
        ).first()
        
        if existing:
            print(f"Stock {stock_id} already in watchlist for user {current_user.id}")
            return jsonify({'success': False, 'message': 'Already in watchlist'}), 400
        
        # Add to watchlist
        watchlist_item = Watchlist(
            user_id=current_user.id,
            stock_id=stock_id
        )
        db.session.add(watchlist_item)
        db.session.commit()
        
        print(f"Successfully added stock {stock_id} to watchlist for user {current_user.id}")
        return jsonify({'success': True, 'message': f'Added {stock.symbol} to watchlist'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding to watchlist: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/watchlist/remove', methods=['POST'])
@login_required
def api_watchlist_remove():
    """Remove stock from watchlist"""
    try:
        data = request.get_json()
        stock_id = data.get('stock_id')
        
        if not stock_id:
            return jsonify({'success': False, 'message': 'Stock ID required'}), 400
        
        # Find and remove
        watchlist_item = Watchlist.query.filter_by(
            user_id=current_user.id,
            stock_id=stock_id
        ).first()
        
        if not watchlist_item:
            return jsonify({'success': False, 'message': 'Not in watchlist'}), 404
        
        db.session.delete(watchlist_item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Removed from watchlist'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/watchlist')
@login_required
def api_watchlist_get():
    """Get user's watchlist"""
    try:
        print(f"Fetching watchlist for user {current_user.id}")
        watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
        print(f"Found {len(watchlist_items)} watchlist items")
        
        result = []
        for item in watchlist_items:
            try:
                stock = item.stock
                print(f"Processing stock: {stock.symbol}")
                
                live_data = get_google_stock_data(stock.symbol)
                
                if live_data:
                    # Get notification settings
                    notif_setting = NotificationSetting.query.filter_by(
                        user_id=current_user.id,
                        stock_id=stock.id
                    ).first()
                    
                    result.append({
                        'id': stock.id,
                        'symbol': stock.symbol,
                        'name': live_data.get('name', stock.name),
                        'live_price': live_data.get('live_price', 0),
                        'live_price_formatted': live_data.get('live_price_formatted', '₹0.00'),
                        'change_price': live_data.get('change_price', 0),
                        'percent_change': live_data.get('percent_change', 0),
                        'trend': live_data.get('trend', 'neutral'),
                        'added_at': item.added_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'has_notification': notif_setting is not None,
                        'notification_enabled': notif_setting.email_enabled if notif_setting else False
                    })
                else:
                    # Add with fallback data if live data unavailable
                    print(f"No live data for {stock.symbol}, using fallback")
                    result.append({
                        'id': stock.id,
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'live_price': 0,
                        'live_price_formatted': '₹0.00',
                        'change_price': 0,
                        'percent_change': 0,
                        'trend': 'neutral',
                        'added_at': item.added_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'has_notification': False,
                        'notification_enabled': False
                    })
            except Exception as item_error:
                print(f"Error processing watchlist item {item.id}: {str(item_error)}")
                continue
        
        print(f"Returning {len(result)} watchlist items")
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        print(f"Error fetching watchlist: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/notification/set', methods=['POST'])
@login_required
def api_notification_set():
    """Set notification preferences for a stock"""
    try:
        data = request.get_json()
        stock_id = data.get('stock_id')
        target_price = data.get('target_price')
        email_enabled = data.get('email_enabled', True)
        notify_on_prediction = data.get('notify_on_prediction', True)
        notify_on_drop = data.get('notify_on_drop', True)
        drop_threshold = data.get('drop_threshold', 5.0)
        
        if not stock_id:
            return jsonify({'success': False, 'message': 'Stock ID required'}), 400
        
        # Find or create notification setting
        setting = NotificationSetting.query.filter_by(
            user_id=current_user.id,
            stock_id=stock_id
        ).first()
        
        if not setting:
            setting = NotificationSetting(
                user_id=current_user.id,
                stock_id=stock_id
            )
            db.session.add(setting)
        
        # Update settings
        if target_price:
            setting.target_price = float(target_price)
        setting.email_enabled = email_enabled
        setting.notify_on_prediction = notify_on_prediction
        setting.notify_on_drop = notify_on_drop
        setting.drop_threshold = float(drop_threshold)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notification settings updated'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/notifications')
@login_required
def api_notifications_get():
    """Get user notifications"""
    try:
        notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(50).all()
        
        result = []
        for notif in notifications:
            result.append({
                'id': notif.id,
                'stock_symbol': notif.stock.symbol,
                'stock_name': notif.stock.name,
                'type': notif.notification_type,
                'title': notif.title,
                'message': notif.message,
                'email_sent': notif.email_sent,
                'is_read': notif.is_read,
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/notification/mark-read', methods=['POST'])
@login_required
def api_notification_mark_read():
    """Mark notification as read"""
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return jsonify({'success': False, 'message': 'Notification ID required'}), 400
        
        notif = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notif:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
        notif.is_read = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Marked as read'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/api/profile/update', methods=['POST'])
@login_required
def api_profile_update():
    """Update user profile"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        user = current_user
        
        # Update username
        if username and username != user.username:
            # Check if username is taken
            if User.query.filter_by(username=username).first():
                return jsonify({'success': False, 'message': 'Username already taken'}), 400
            user.username = username
        
        # Update email (requires verification)
        if email and email != user.email:
            # Check if email is taken
            if User.query.filter_by(email=email).first():
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            # TODO: Send verification email for new email
            return jsonify({
                'success': False,
                'message': 'Email change requires verification (feature coming soon)'
            }), 400
        
        # Update password
        if new_password:
            if not current_password:
                return jsonify({'success': False, 'message': 'Current password required'}), 400
            
            if not user.check_password(current_password):
                return jsonify({'success': False, 'message': 'Current password incorrect'}), 401
            
            user.set_password(new_password)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
