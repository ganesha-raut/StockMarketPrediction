import requests
from flask import current_app
import json

class GeminiAI:
    """Gemini AI integration for stock suggestions and chatbot using REST API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
    def _generate_content(self, prompt):
        """Generate content using Gemini REST API"""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
            
            return None
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None
    
    def get_stock_suggestions(self, market_data=None, limit=4):
        """Get AI-suggested stocks based on market analysis"""
        try:
            if not self.api_key:
                return self._get_fallback_suggestions(limit)
            
            prompt = f"""
            You are a stock market analyst AI. Based on current Indian stock market trends, 
            suggest {limit} stocks that show strong potential.
            
            For each stock, provide:
            1. Stock symbol (NSE)
            2. Stock name
            3. Brief reason (max 50 words)
            4. Sentiment (bullish/bearish/neutral)
            
            Return ONLY a valid JSON array with this structure:
            [
                {{
                    "symbol": "TCS",
                    "name": "Tata Consultancy Services",
                    "reason": "Strong Q4 results with 15% YoY growth. AI suggests bullish momentum.",
                    "sentiment": "bullish"
                }}
            ]
            
            Focus on popular Indian stocks like TCS, INFY, RELIANCE, HDFCBANK, ICICIBANK, WIPRO, etc.
            """
            
            text = self._generate_content(prompt)
            
            if not text:
                return self._get_fallback_suggestions(limit)
            
            # Parse JSON response
            text = text.strip()
            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            
            suggestions = json.loads(text)
            return suggestions[:limit]
            
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_suggestions(limit)
    
    def _get_fallback_suggestions(self, limit=4):
        """Fallback suggestions when AI is unavailable"""
        fallback = [
            {
                "symbol": "TCS",
                "name": "Tata Consultancy Services",
                "reason": "Leading IT services company with strong fundamentals and consistent growth.",
                "sentiment": "bullish"
            },
            {
                "symbol": "RELIANCE",
                "name": "Reliance Industries",
                "reason": "Diversified conglomerate with strong presence in energy and retail sectors.",
                "sentiment": "bullish"
            },
            {
                "symbol": "HDFCBANK",
                "name": "HDFC Bank",
                "reason": "Top private sector bank with robust asset quality and digital banking growth.",
                "sentiment": "bullish"
            },
            {
                "symbol": "INFY",
                "name": "Infosys",
                "reason": "Global IT leader with strong client relationships and digital transformation focus.",
                "sentiment": "neutral"
            }
        ]
        return fallback[:limit]
    
    def chat(self, message, context=None):
        """Chat with Gemini AI about stocks"""
        try:
            if not self.api_key:
                return "AI service is currently unavailable. Please try again later."
            
            system_context = """
            You are an AI stock market assistant. You help users with:
            - Stock price predictions and analysis
            - Market trends and insights
            - Investment advice (with disclaimers)
            - Explaining financial concepts
            
            Always be helpful, accurate, and include disclaimers for investment advice.
            Keep responses concise and actionable.
            """
            
            full_prompt = f"{system_context}\n\nUser: {message}"
            
            if context:
                full_prompt += f"\n\nContext: {context}"
            
            text = self._generate_content(full_prompt)
            return text if text else "I'm having trouble processing your request. Please try again."
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return "I'm having trouble processing your request. Please try again."
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of news or text"""
        try:
            if not self.api_key:
                return {"sentiment": "neutral", "score": 0.0}
            
            prompt = f"""
            Analyze the sentiment of this stock market related text and return ONLY a JSON object:
            
            Text: {text}
            
            Return format:
            {{
                "sentiment": "positive" or "negative" or "neutral",
                "score": float between -1.0 and 1.0,
                "confidence": float between 0 and 100
            }}
            """
            
            text = self._generate_content(prompt)
            
            if not text:
                return {"sentiment": "neutral", "score": 0.0, "confidence": 50.0}
            
            text = text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            
            result = json.loads(text)
            return result
            
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {"sentiment": "neutral", "score": 0.0, "confidence": 50.0}
    
    def get_stock_prediction_insight(self, stock_data, prediction_data):
        """Get AI insight on stock prediction"""
        try:
            if not self.api_key:
                return "Prediction analysis unavailable."
            
            prompt = f"""
            Provide a brief investment insight (max 100 words) based on this stock prediction:
            
            Stock: {stock_data.get('name')} ({stock_data.get('symbol')})
            Current Price: ₹{stock_data.get('live_price')}
            Predicted Price: ₹{prediction_data.get('predicted_price')}
            Confidence: {prediction_data.get('confidence')}%
            Trend: {prediction_data.get('trend')}
            
            Give actionable advice with appropriate risk warnings.
            """
            
            text = self._generate_content(prompt)
            return text if text else "Unable to generate insight at this time."
            
        except Exception as e:
            print(f"Error getting prediction insight: {e}")
            return "Unable to generate insight at this time."
    
    def analyze_news_batch(self, news_items):
        """Analyze sentiment of multiple news items"""
        try:
            if not self.api_key or not news_items:
                return []
            
            headlines = [item.get('headline', '') for item in news_items]
            
            prompt = f"""
            Analyze sentiment for these stock news headlines. Return ONLY a JSON array:
            
            Headlines:
            {json.dumps(headlines, indent=2)}
            
            Return format:
            [
                {{
                    "headline": "original headline",
                    "sentiment": "positive/negative/neutral",
                    "score": float between -1.0 and 1.0
                }}
            ]
            """
            
            text = self._generate_content(prompt)
            
            if not text:
                # Return original items with neutral sentiment
                for item in news_items:
                    item['sentiment'] = 'neutral'
                    item['sentiment_score'] = 0.0
                return news_items
            
            text = text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            
            results = json.loads(text)
            
            # Merge with original news items
            for i, item in enumerate(news_items):
                if i < len(results):
                    item['sentiment'] = results[i].get('sentiment', 'neutral')
                    item['sentiment_score'] = results[i].get('score', 0.0)
            
            return news_items
            
        except Exception as e:
            print(f"Error analyzing news batch: {e}")
            # Return original items with neutral sentiment
            for item in news_items:
                item['sentiment'] = 'neutral'
                item['sentiment_score'] = 0.0
            return news_items

# Global instance
gemini_ai = None

def init_gemini(api_key):
    """Initialize Gemini AI with API key"""
    global gemini_ai
    gemini_ai = GeminiAI(api_key)
    return gemini_ai

def get_gemini():
    """Get Gemini AI instance"""
    global gemini_ai
    if gemini_ai is None:
        api_key = current_app.config.get('GEMINI_API_KEY')
        if api_key:
            gemini_ai = GeminiAI(api_key)
    return gemini_ai
