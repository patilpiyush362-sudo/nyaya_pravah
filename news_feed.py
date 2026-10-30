"""Live news feed fetcher for legal news and court updates."""
from datetime import datetime
from typing import List

try:
    import feedparser
except ImportError:
    feedparser = None


# Fallback default notices when feed fails or internet is disconnected
DEFAULT_NOTICES = [
    {
        "title": "Supreme Court Guidelines on E-Filing Procedures",
        "link": "https://www.supremecourt.gov.in/",
        "published_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "title": "Scheduled Server Maintenance for e-Courts Portal",
        "link": "https://www.ecourts.gov.in/",
        "published_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "title": "New Judicial Procedures: Updated Filing Requirements",
        "link": "https://www.supremecourt.gov.in/",
        "published_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "title": "Legal Aid Services: Expanded Availability",
        "link": "https://www.legalaid.gov.in/",
        "published_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "title": "High Court Orders: New Case Management Rules",
        "link": "https://www.supremecourt.gov.in/",
        "published_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
]


def get_latest_updates(limit: int = 5) -> list[dict]:
    """
    Fetch the latest legal news and court updates from RSS feed.
    
    Args:
        limit: Maximum number of articles to return (default: 5)
    
    Returns:
        List of dictionaries containing 'title', 'link', and 'published_date'
    """
    if feedparser is None:
        return DEFAULT_NOTICES[:limit]
    
    try:
        # Fetch from a major Indian legal news source
        feed_url = "https://www.livelaw.in/feed/"
        feed = feedparser.parse(feed_url)
        
        # Check if feed parsing was successful
        if not feed.entries:
            return DEFAULT_NOTICES[:limit]
        
        news_list = []
        for entry in feed.entries[:limit]:
            # Extract published date, handling different formats
            pub_date = entry.get("published", "")
            if not pub_date:
                pub_date = entry.get("updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            news_item = {
                "title": entry.get("title", "Untitled News"),
                "link": entry.get("link", "https://www.livelaw.in/"),
                "published_date": pub_date,
            }
            news_list.append(news_item)
        
        return news_list if news_list else DEFAULT_NOTICES[:limit]
    
    except Exception as e:
        # On any error (network, parsing, etc.), fall back to default notices
        print(f"Error fetching news feed: {e}")
        return DEFAULT_NOTICES[:limit]
