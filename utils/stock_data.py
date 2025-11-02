import requests
from bs4 import BeautifulSoup
import random
import yfinance as yf
from datetime import datetime, timedelta
from functools import lru_cache
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Mobile) Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/119.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/118.0",
]

# Cache for stock data (5 minutes for better performance)
_stock_cache = {}
_cache_timeout = 300  # 5 minutes

def clear_stock_cache():
    """Clear the stock data cache"""
    global _stock_cache
    _stock_cache = {}

def get_google_stock_data(symbol, force_refresh=False):
    """Fetch live stock data from Google Finance with caching"""
    # Check cache (skip if force refresh)
    if not force_refresh and symbol in _stock_cache:
        cached_data, cached_time = _stock_cache[symbol]
        if time.time() - cached_time < _cache_timeout:
            return cached_data
    
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all data elements
        elements = soup.find_all("div", class_="P6K39c")
        all_values = [e.get_text(strip=True) for e in elements]
        
        # Get live price
        price_elem = soup.find("div", {"class": "YMlKec fxKbKc"})
        if not price_elem:
            return None
        
        # Get stock name
        full_name = soup.find("div", {"class": "zzDege"})
        name = full_name.get_text(strip=True) if full_name else symbol
        
        # Parse prices
        morning_price = all_values[0].replace("₹", "").replace(",", "").strip()
        today_live_price = price_elem.text.replace("₹", "").replace(",", "").strip()
        
        morning_price = float(morning_price)
        today_live_price = float(today_live_price)
        
        # Calculate changes
        change_price = today_live_price - morning_price
        percent_change = (change_price / morning_price) * 100
        
        # Parse price range
        price_range = all_values[1]
        parts = price_range.split('-')
        low_price = float(parts[0].replace('₹', '').replace(',', '').strip())
        high_price = float(parts[1].replace('₹', '').replace(',', '').strip())
        
        trend = "bullish" if change_price > 0 else "bearish" if change_price < 0 else "neutral"
        
        return {
            "name": name,
            "symbol": symbol,
            "live_price": today_live_price,
            "live_price_formatted": f"₹{today_live_price:,.2f}",
            "change_price": change_price,
            "change_price_formatted": f"₹{change_price:,.2f}",
            "percent_change": percent_change,
            "percent_change_formatted": f"{percent_change:.2f}%",
            "trend": trend,
            "closing_price": morning_price,
            "opening_price": morning_price,
            "low": low_price,
            "high": high_price,
            "day_range": f"₹{low_price:,.2f} - ₹{high_price:,.2f}",
            "volume": all_values[4] if len(all_values) > 4 else "N/A",
            "market_cap": all_values[3] if len(all_values) > 3 else "N/A",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Cache the result
        _stock_cache[symbol] = (data, time.time())
        return data
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        # Return cached data if available, even if expired
        if symbol in _stock_cache:
            return _stock_cache[symbol][0]
        return None

def get_historical_data_yfinance(symbol, period="5y"):
    """Fetch historical data using yfinance"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
        
        # Reset index to get date as column
        hist = hist.reset_index()
        
        # Rename columns to match our schema
        hist = hist.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Dividends': 'dividend'
        })
        
        # Convert to list of dictionaries
        result = []
        for _, row in hist.iterrows():
            result.append({
                'date': row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']),
                'dividend': float(row.get('dividend', 0.0))
            })
        
        return result
        
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return None

def get_stock_news(symbol, limit=5):
    """Fetch latest news for a stock"""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        news_items = []
        
        # Find news section
        news_divs = soup.find_all("div", class_="yY3Lee")
        
        for i, news_div in enumerate(news_divs[:limit]):
            try:
                headline_elem = news_div.find("div", class_="Yfwt5")
                source_elem = news_div.find("div", class_="sfyJob")
                time_elem = news_div.find("div", class_="Adak")
                link_elem = news_div.find("a", class_="z4rs2b")
                
                # Try multiple possible snippet classes
                snippet_elem = (news_div.find("div", class_="AoCdqe") or 
                               news_div.find("div", class_="yY3Lee") or
                               news_div.find("div", class_="Yfwt5"))
                
                # Extract actual URL from Google redirect
                actual_link = ""
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    # Google Finance links are like: ./articles/CBMi...
                    # We'll use Google News search as fallback
                    if href.startswith('./articles/'):
                        # Create a Google search link for the headline
                        headline_text = headline_elem.get_text(strip=True) if headline_elem else ""
                        actual_link = f"https://www.google.com/search?q={headline_text.replace(' ', '+')}"
                    else:
                        actual_link = f"https://www.google.com{href}"
                
                if headline_elem:
                    headline_text = headline_elem.get_text(strip=True)
                    
                    # Get snippet or generate from headline
                    snippet_text = ""
                    if snippet_elem and snippet_elem != headline_elem:
                        snippet_text = snippet_elem.get_text(strip=True)
                    
                    # If no snippet, create a generic one from headline
                    if not snippet_text or len(snippet_text) < 20:
                        snippet_text = f"Latest news about {symbol}: {headline_text}. Stay updated with real-time market information and analysis."
                    
                    news_items.append({
                        "headline": headline_text,
                        "title": headline_text,  # For prediction page
                        "source": source_elem.get_text(strip=True) if source_elem else "Financial News",
                        "time": time_elem.get_text(strip=True) if time_elem else "Recent",
                        "snippet": snippet_text,
                        "link": actual_link,
                        "url": actual_link,
                        "sentiment": 0,  # Will be filled by Gemini
                        "sentiment_score": 0.0  # Will be filled by Gemini
                    })
            except Exception as e:
                print(f"Error parsing news item: {e}")
                continue
        
        return news_items
        
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []

def check_market_status():
    """Check if market is currently open"""
    from pytz import timezone
    
    ist = timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Market hours: 9:15 AM to 3:30 PM IST
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # Check if weekend
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        next_open = now + timedelta(days=(7 - now.weekday()))
        next_open = next_open.replace(hour=9, minute=15, second=0, microsecond=0)
        
        return {
            "is_open": False,
            "status": "Market Closed",
            "reason": "Weekend",
            "next_open": next_open.strftime("%Y-%m-%d %H:%M:%S"),
            "time_until_open": str(next_open - now)
        }
    
    # Check if within market hours
    if market_open <= now <= market_close:
        return {
            "is_open": True,
            "status": "Market Open",
            "closes_at": market_close.strftime("%H:%M:%S"),
            "time_until_close": str(market_close - now)
        }
    else:
        # Market closed, calculate next open
        if now < market_open:
            next_open = market_open
        else:
            next_open = (now + timedelta(days=1)).replace(hour=9, minute=15, second=0, microsecond=0)
            # Skip weekend
            if next_open.weekday() >= 5:
                next_open = next_open + timedelta(days=(7 - next_open.weekday()))
        
        return {
            "is_open": False,
            "status": "Market Closed",
            "next_open": next_open.strftime("%Y-%m-%d %H:%M:%S"),
            "time_until_open": str(next_open - now)
        }

if __name__ == "__main__":
    # Test the functions
    data = get_google_stock_data("TCS")
    if data:
        print("Stock Data:", data)
    
    market = check_market_status()
    print("\nMarket Status:", market)
    
    news = get_stock_news("TCS")
    print(f"\nNews Items: {len(news)}")
