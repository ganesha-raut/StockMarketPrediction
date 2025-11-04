"""
AI Summary Generator for Prediction Page
Generates concise news analysis with bullet points
"""

import requests
import logging
from utils.stock_data import get_stock_news

logger = logging.getLogger(__name__)

class AISummaryGenerator:
    """Generate AI summary for prediction page"""
    
    def __init__(self):
        self.api_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
    
    def generate_summary(self, symbol, company_name):
        """Generate AI summary with news analysis"""
        try:
            # Fetch latest news (reduced to 6 for faster processing)
            news_items = get_stock_news(symbol, limit=6)
            
            if not news_items:
                return {
                    'success': False,
                    'message': 'No news available'
                }
            
            # Prepare news text (only top 6 for speed)
            news_text = "\n".join([f"- {item['title']}" for item in news_items[:6]])
            
            # AI prompt for concise summary
            prompt = f"""Analyze news for {company_name}.

NEWS:
{news_text}

Generate ONLY bullet points with 10-15 word summaries:

• [Key Point 1]
  - [10-15 word summary]

• [Key Point 2]
  - [10-15 word summary]

• [Key Point 3]
  - [10-15 word summary]

Be brief. 3-4 points only."""
            
            headers = {'Content-Type': 'application/json'}
            data = {"prompt": prompt}
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=8)
            
            if response.status_code != 200:
                return self._generate_fallback_summary(news_items, company_name)
            
            result = response.json()
            ai_summary = (result.get('text') or result.get('response') or result.get('output') or '').strip()
            
            if not ai_summary:
                return self._generate_fallback_summary(news_items, company_name)
            
            return {
                'success': True,
                'summary': ai_summary,
                'news_count': len(news_items)
            }
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return self._generate_fallback_summary(news_items if 'news_items' in locals() else [], company_name)
    
    def _generate_fallback_summary(self, news_items, company_name):
        """Generate fallback summary if AI fails"""
        if not news_items:
            return {
                'success': False,
                'message': 'No news available'
            }
        
        summary = f"Latest News & AI Analysis for {company_name}\n\n"
        
        # Group news by sentiment (simple keyword matching)
        positive_keywords = ['growth', 'profit', 'gain', 'rise', 'increase', 'success', 'leader', 'award']
        negative_keywords = ['loss', 'decline', 'fall', 'drop', 'lawsuit', 'issue', 'problem']
        
        positive_news = []
        negative_news = []
        neutral_news = []
        
        for item in news_items[:10]:
            title_lower = item['title'].lower()
            if any(word in title_lower for word in positive_keywords):
                positive_news.append(item)
            elif any(word in title_lower for word in negative_keywords):
                negative_news.append(item)
            else:
                neutral_news.append(item)
        
        # Generate bullet points
        if positive_news:
            summary += "• Positive Developments\n"
            summary += f"  - {len(positive_news)} positive news items indicating growth and success\n\n"
        
        if negative_news:
            summary += "• Challenges & Concerns\n"
            summary += f"  - {len(negative_news)} news items highlighting potential issues or concerns\n\n"
        
        if neutral_news:
            summary += "• Market Updates\n"
            summary += f"  - {len(neutral_news)} general market updates and company announcements\n\n"
        
        # Add recent news summary
        if news_items:
            summary += "• Recent Headlines\n"
            recent = news_items[0]['title'][:60] + "..." if len(news_items[0]['title']) > 60 else news_items[0]['title']
            summary += f"  - Latest: {recent}\n"
        
        return {
            'success': True,
            'summary': summary,
            'news_count': len(news_items)
        }


def get_ai_summary(symbol, company_name):
    """Get AI summary for stock"""
    generator = AISummaryGenerator()
    return generator.generate_summary(symbol, company_name)
