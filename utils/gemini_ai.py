import requests
from flask import current_app
import json

class GeminiAI:
    """Gemini AI integration for stock suggestions and chatbot using REST API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
    
    def _generate_content(self, prompt):
        """Generate content using Gemini REST API"""
        # if not self.api_key:
        #     return None
        
        try:
            url = f"{self.base_url}"
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
        """Get AI insight on stock prediction with Markdown formatting"""
        try:
            # Fallback if no API key
            if not self.api_key:
                return self._generate_fallback_insight(stock_data, prediction_data)
            
            # Enhanced prompt for better insights
            prompt = f"""
            You are a professional stock market analyst. Provide investment insight in Markdown format.
            
            **Stock Analysis:**
            - Company: {stock_data.get('name', 'N/A')} ({stock_data.get('symbol', 'N/A')})
            - Current Price: ₹{stock_data.get('live_price', 0):.2f}
            - Predicted Price: ₹{prediction_data.get('predicted_price', 0):.2f}
            - Expected Change: {prediction_data.get('percent_change', 0):+.2f}%
            - Confidence Level: {prediction_data.get('confidence', 0):.1f}%
            - Trend: {prediction_data.get('trend', 'neutral').upper()}
            - Recommendation: {prediction_data.get('recommendation', 'HOLD')}
            - Risk Level: {prediction_data.get('risk_percentage', 0):.1f}%
            
            Provide a concise analysis (100-150 words) in Markdown format with:
            1. **Market Outlook** - Brief trend analysis
            2. **Investment Recommendation** - Clear buy/sell/hold advice
            3. **Risk Factors** - Key risks to consider
            4. **Action Points** - 2-3 specific actions
            
            Use Markdown formatting: **bold**, *italic*, bullet points.
            Include appropriate emojis for visual appeal.
            End with a disclaimer about market risks.
            """
            
            text = self._generate_content(prompt)
            
            if text:
                # Clean up the response
                text = text.strip()
                # Remove markdown code blocks if present
                if text.startswith('```'):
                    text = text.split('```')[1]
                    if text.startswith('markdown'):
                        text = text[8:]
                    text = text.strip()
                return text
            else:
                return self._generate_fallback_insight(stock_data, prediction_data)
            
        except Exception as e:
            print(f"Error getting prediction insight: {e}")
            return self._generate_fallback_insight(stock_data, prediction_data)
    
    def _generate_fallback_insight(self, stock_data, prediction_data):
        """Generate fallback insight when AI is unavailable"""
        try:
            symbol = stock_data.get('symbol', 'Stock')
            current = stock_data.get('live_price', 0)
            predicted = prediction_data.get('predicted_price', 0)
            change = prediction_data.get('percent_change', 0)
            trend = prediction_data.get('trend', 'neutral')
            recommendation = prediction_data.get('recommendation', 'HOLD')
            confidence = prediction_data.get('confidence', 0)
            risk = prediction_data.get('risk_percentage', 0)
            
            # Determine sentiment
            if change > 2:
                outlook = "📈 **Strong Bullish Outlook**"
                advice = "Consider buying with proper position sizing"
            elif change > 0:
                outlook = "📊 **Moderately Bullish**"
                advice = "Suitable for gradual accumulation"
            elif change < -2:
                outlook = "📉 **Bearish Trend**"
                advice = "Consider reducing exposure or avoiding"
            elif change < 0:
                outlook = "📊 **Slightly Bearish**"
                advice = "Exercise caution, wait for better entry"
            else:
                outlook = "➡️ **Neutral Stance**"
                advice = "Hold current positions, monitor closely"
            
            # Risk assessment
            if risk > 70:
                risk_text = "🔴 **High Risk** - Volatile conditions expected"
            elif risk > 40:
                risk_text = "🟡 **Moderate Risk** - Normal market volatility"
            else:
                risk_text = "🟢 **Lower Risk** - Relatively stable movement"
            
            insight = f"""
### {outlook}

**Market Analysis for {symbol}:**
The AI model predicts a **{change:+.2f}%** movement from ₹{current:.2f} to ₹{predicted:.2f} with {confidence:.0f}% confidence.

**Investment Recommendation:** *{recommendation}*
{advice}. The current trend is **{trend}**, suggesting {"upward momentum" if change > 0 else "downward pressure" if change < 0 else "sideways movement"}.

**Risk Assessment:**
{risk_text}

**Action Points:**
- {'✅ Consider entry positions' if change > 1 else '⚠️ Wait for confirmation' if change > -1 else '❌ Avoid new positions'}
- 📊 Monitor price action at key levels
- 🎯 Set stop-loss at {(current * 0.95):.2f} (5% below current)

---
*⚠️ Disclaimer: This is an AI-generated analysis for educational purposes. Always conduct your own research and consult financial advisors before making investment decisions.*
"""
            return insight.strip()
            
        except Exception as e:
            print(f"Error generating fallback insight: {e}")
            return "**Analysis Unavailable** - Please try again later."
    
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
