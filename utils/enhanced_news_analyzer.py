"""
Enhanced News Analyzer
Fetches latest news and analyzes each article individually
Categorizes into positive, negative, neutral
"""

import requests
import logging
from utils.stock_data import get_stock_news

logger = logging.getLogger(__name__)

class EnhancedNewsAnalyzer:
    """Analyzes news articles individually and categorizes them"""
    
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name
        self.api_url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
    
    def analyze_single_article(self, headline):
        """Analyze a single news article"""
        try:
            prompt = f"""Analyze this news headline for {self.company_name}:

"{headline}"

Classify as:
CATEGORY: [positive/negative/neutral]
SCORE: [number from -1.0 (very negative) to 1.0 (very positive)]
REASON: [brief reason in one line]

Be honest and accurate."""
            
            headers = {'Content-Type': 'application/json'}
            data = {"prompt": prompt}
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code != 200:
                return {
                    'category': 'neutral',
                    'score': 0.0,
                    'reason': 'Unable to analyze'
                }
            
            result = response.json()
            text = (result.get('text') or result.get('response') or result.get('output') or '').strip()
            
            category = 'neutral'
            score = 0.0
            reason = ''
            
            for line in text.split('\n'):
                line_upper = line.upper()
                if 'CATEGORY:' in line_upper:
                    category = line.split(':', 1)[1].strip().lower()
                    # Ensure valid category
                    if category not in ['positive', 'negative', 'neutral']:
                        category = 'neutral'
                elif 'SCORE:' in line_upper:
                    try:
                        score = float(line.split(':', 1)[1].strip())
                        # Clamp score between -1 and 1
                        score = max(-1.0, min(1.0, score))
                    except:
                        score = 0.0
                elif 'REASON:' in line_upper:
                    reason = line.split(':', 1)[1].strip()
            
            return {
                'category': category,
                'score': score,
                'reason': reason or 'No specific reason provided'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return {
                'category': 'neutral',
                'score': 0.0,
                'reason': 'Analysis error'
            }
    
    def analyze_all_news(self, limit=15):
        """Fetch and analyze all news articles"""
        try:
            # Fetch latest news
            news_items = get_stock_news(self.symbol, limit=limit)
            
            if not news_items:
                return {
                    'success': False,
                    'total_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'overall_score': 0.0,
                    'overall_sentiment': 'neutral',
                    'articles': [],
                    'message': 'No news available'
                }
            
            # Analyze each article
            analyzed_articles = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            total_score = 0.0
            
            for item in news_items:
                headline = item.get('title', item.get('headline', ''))
                
                if not headline:
                    continue
                
                # Analyze this article
                analysis = self.analyze_single_article(headline)
                
                # Count categories
                if analysis['category'] == 'positive':
                    positive_count += 1
                elif analysis['category'] == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1
                
                # Add to total score
                total_score += analysis['score']
                
                # Store analyzed article
                analyzed_articles.append({
                    'headline': headline,
                    'category': analysis['category'],
                    'score': analysis['score'],
                    'reason': analysis['reason'],
                    'source': item.get('source', 'Unknown'),
                    'time': item.get('time', 'Recent'),
                    'url': item.get('url', item.get('link', ''))
                })
            
            # Calculate overall sentiment
            total_count = len(analyzed_articles)
            overall_score = total_score / total_count if total_count > 0 else 0.0
            
            # Determine overall sentiment
            if overall_score > 0.2:
                overall_sentiment = 'positive'
            elif overall_score < -0.2:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'success': True,
                'total_count': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'overall_score': overall_score,
                'overall_sentiment': overall_sentiment,
                'articles': analyzed_articles,
                'sentiment_breakdown': {
                    'positive_percentage': (positive_count / total_count * 100) if total_count > 0 else 0,
                    'negative_percentage': (negative_count / total_count * 100) if total_count > 0 else 0,
                    'neutral_percentage': (neutral_count / total_count * 100) if total_count > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'total_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'overall_score': 0.0,
                'overall_sentiment': 'neutral',
                'articles': [],
                'message': f'Error: {str(e)}'
            }
    
    def get_sentiment_summary(self):
        """Get a quick sentiment summary"""
        analysis = self.analyze_all_news()
        
        if not analysis['success']:
            return "No news sentiment available"
        
        positive = analysis['positive_count']
        negative = analysis['negative_count']
        neutral = analysis['neutral_count']
        total = analysis['total_count']
        
        summary = f"{total} articles analyzed: "
        summary += f"{positive} positive ({positive/total*100:.0f}%), "
        summary += f"{negative} negative ({negative/total*100:.0f}%), "
        summary += f"{neutral} neutral ({neutral/total*100:.0f}%). "
        summary += f"Overall: {analysis['overall_sentiment'].upper()}"
        
        return summary


def get_enhanced_news_analyzer(symbol, company_name):
    """Get enhanced news analyzer instance"""
    return EnhancedNewsAnalyzer(symbol, company_name)
