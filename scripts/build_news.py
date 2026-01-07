#!/usr/bin/env python3
"""
FullSpectrum.News Build Script - Matrix Edition (Expanded)

Fetches top news for Global, US, Singapore, and India regions.
Uses broad mix of sources across the political spectrum.
Outputs data in matrix-compatible format with political leaning and tone.

Requirements:
    pip install feedparser requests beautifulsoup4 python-dateutil

Usage:
    python build_news.py
"""

import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
import time

CONFIG = {
    "output_file": "news_data.json",
    "num_stories_per_region": 9,
    "request_timeout": 15,
    "request_delay": 0.3,
}

# Expanded RSS feeds for each region with broad political spectrum
REGION_FEEDS = {
    "global": [
        # Left-leaning
        ("The Guardian World", "https://www.theguardian.com/world/rss"),
        ("HuffPost", "https://www.huffpost.com/section/world-news/feed"),
        
        # Center-left
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("NPR World", "https://feeds.npr.org/1004/rss.xml"),
        
        # Center
        ("Reuters World", "https://www.reutersagency.com/feed/?best-topics=world-news&post_type=best"),
        ("AP News", "https://rsshub.app/apnews/topics/world-news"),
        ("Google News World", "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("France 24", "https://www.france24.com/en/rss"),
        
        # Center-right
        ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss"),
        ("WSJ World", "https://feeds.a]ontentbackend.wsj.com/public/rss/RSSWorldNews"),
        
        # Right-leaning
        ("Fox News World", "http://feeds.foxnews.com/foxnews/world"),
        ("NY Post", "https://nypost.com/news/feed/"),
    ],
    "us": [
        # Left-leaning
        ("HuffPost Politics", "https://www.huffpost.com/section/politics/feed"),
        ("MSNBC", "https://www.msnbc.com/feeds/latest"),
        ("Vox", "https://www.vox.com/rss/index.xml"),
        
        # Center-left
        ("NYT US", "https://rss.nytimes.com/services/xml/rss/nyt/US.xml"),
        ("Washington Post", "http://feeds.washingtonpost.com/rss/national"),
        ("NPR News", "https://feeds.npr.org/1001/rss.xml"),
        ("CNN", "http://rss.cnn.com/rss/cnn_topstories.rss"),
        
        # Center
        ("AP US News", "https://rsshub.app/apnews/topics/us-news"),
        ("Reuters US", "https://www.reutersagency.com/feed/?best-topics=usa&post_type=best"),
        ("Google News US", "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"),
        ("The Hill", "https://thehill.com/feed/"),
        ("Politico", "https://www.politico.com/rss/politicopicks.xml"),
        
        # Center-right
        ("WSJ US", "https://feeds.a]ontentbackend.wsj.com/public/rss/RSSUnitedStates"),
        
        # Right-leaning
        ("Fox News Politics", "http://feeds.foxnews.com/foxnews/politics"),
        ("NY Post News", "https://nypost.com/news/feed/"),
        ("Washington Examiner", "https://www.washingtonexaminer.com/feed"),
        ("Daily Wire", "https://www.dailywire.com/feeds/rss.xml"),
    ],
    "singapore": [
        # Singapore sources (mostly center)
        ("Straits Times", "https://www.straitstimes.com/news/singapore/rss.xml"),
        ("CNA Singapore", "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511"),
        ("CNA Asia", "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936"),
        ("Today Online", "https://www.todayonline.com/feed"),
        ("Google News Singapore", "https://news.google.com/rss?hl=en-SG&gl=SG&ceid=SG:en"),
        
        # International coverage of Singapore
        ("Reuters Asia", "https://www.reutersagency.com/feed/?best-topics=asia&post_type=best"),
        ("Bloomberg Asia", "https://feeds.bloomberg.com/markets/news.rss"),
        ("BBC Asia", "http://feeds.bbci.co.uk/news/world/asia/rss.xml"),
    ],
    "india": [
        # Left-leaning
        ("The Hindu", "https://www.thehindu.com/news/national/feeder/default.rss"),
        ("NDTV", "https://feeds.feedburner.com/ndtvnews-top-stories"),
        ("The Wire", "https://thewire.in/feed"),
        ("Indian Express", "https://indianexpress.com/feed/"),
        
        # Center
        ("Times of India", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"),
        ("Hindustan Times", "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml"),
        ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
        ("Google News India", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"),
        ("Reuters India", "https://www.reutersagency.com/feed/?best-topics=india&post_type=best"),
        ("Bloomberg India", "https://feeds.bloomberg.com/markets/news.rss"),
        
        # Right-leaning
        ("Republic World", "https://www.republicworld.com/rss/india-news.xml"),
        ("Swarajya", "https://swarajyamag.com/feed"),
        ("OpIndia", "https://www.opindia.com/feed/"),
    ],
}

# Comprehensive source data with bias and initials
SOURCE_DATA = {
    # Wire Services / Neutral (bias: 0)
    'reuters.com': {'name': 'Reuters', 'initials': 'R', 'bias': 0},
    'apnews.com': {'name': 'AP', 'initials': 'AP', 'bias': 0},
    'afp.com': {'name': 'AFP', 'initials': 'AFP', 'bias': 0},
    
    # Left-leaning (bias: -2)
    'theguardian.com': {'name': 'The Guardian', 'initials': 'TG', 'bias': -2},
    'huffpost.com': {'name': 'HuffPost', 'initials': 'HP', 'bias': -2},
    'huffingtonpost.com': {'name': 'HuffPost', 'initials': 'HP', 'bias': -2},
    'msnbc.com': {'name': 'MSNBC', 'initials': 'MS', 'bias': -2},
    'vox.com': {'name': 'Vox', 'initials': 'VOX', 'bias': -2},
    'slate.com': {'name': 'Slate', 'initials': 'SL', 'bias': -2},
    'motherjones.com': {'name': 'Mother Jones', 'initials': 'MJ', 'bias': -2},
    
    # Center-left (bias: -1)
    'bbc.com': {'name': 'BBC', 'initials': 'BBC', 'bias': -1},
    'bbc.co.uk': {'name': 'BBC', 'initials': 'BBC', 'bias': -1},
    'npr.org': {'name': 'NPR', 'initials': 'NPR', 'bias': -1},
    'nytimes.com': {'name': 'New York Times', 'initials': 'NYT', 'bias': -1},
    'washingtonpost.com': {'name': 'Washington Post', 'initials': 'WP', 'bias': -1},
    'cnn.com': {'name': 'CNN', 'initials': 'CNN', 'bias': -1},
    'politico.com': {'name': 'Politico', 'initials': 'POL', 'bias': -1},
    'theatlantic.com': {'name': 'The Atlantic', 'initials': 'ATL', 'bias': -1},
    'usatoday.com': {'name': 'USA Today', 'initials': 'USA', 'bias': -1},
    'latimes.com': {'name': 'LA Times', 'initials': 'LAT', 'bias': -1},
    'aljazeera.com': {'name': 'Al Jazeera', 'initials': 'AJ', 'bias': -1},
    
    # Center (bias: 0)
    'thehill.com': {'name': 'The Hill', 'initials': 'TH', 'bias': 0},
    'axios.com': {'name': 'Axios', 'initials': 'AX', 'bias': 0},
    'bloomberg.com': {'name': 'Bloomberg', 'initials': 'BB', 'bias': 0},
    'dw.com': {'name': 'DW News', 'initials': 'DW', 'bias': 0},
    'france24.com': {'name': 'France 24', 'initials': 'F24', 'bias': 0},
    
    # Center-right (bias: 1)
    'wsj.com': {'name': 'Wall Street Journal', 'initials': 'WSJ', 'bias': 1},
    'forbes.com': {'name': 'Forbes', 'initials': 'FB', 'bias': 1},
    'washingtonexaminer.com': {'name': 'Washington Examiner', 'initials': 'WE', 'bias': 1},
    'reason.com': {'name': 'Reason', 'initials': 'RSN', 'bias': 1},
    
    # Right-leaning (bias: 2)
    'foxnews.com': {'name': 'Fox News', 'initials': 'FN', 'bias': 2},
    'nypost.com': {'name': 'NY Post', 'initials': 'NYP', 'bias': 2},
    'dailywire.com': {'name': 'Daily Wire', 'initials': 'DW', 'bias': 2},
    'breitbart.com': {'name': 'Breitbart', 'initials': 'BB', 'bias': 2},
    'nationalreview.com': {'name': 'National Review', 'initials': 'NR', 'bias': 2},
    'dailycaller.com': {'name': 'Daily Caller', 'initials': 'DC', 'bias': 2},
    
    # Singapore (mostly center)
    'straitstimes.com': {'name': 'Straits Times', 'initials': 'ST', 'bias': 0},
    'channelnewsasia.com': {'name': 'CNA', 'initials': 'CNA', 'bias': 0},
    'todayonline.com': {'name': 'Today', 'initials': 'TD', 'bias': 0},
    'businesstimes.com.sg': {'name': 'Business Times', 'initials': 'BT', 'bias': 0},
    
    # India - Left-leaning
    'thehindu.com': {'name': 'The Hindu', 'initials': 'TH', 'bias': -1},
    'ndtv.com': {'name': 'NDTV', 'initials': 'NDTV', 'bias': -1},
    'thewire.in': {'name': 'The Wire', 'initials': 'TW', 'bias': -2},
    'indianexpress.com': {'name': 'Indian Express', 'initials': 'IE', 'bias': -1},
    'scroll.in': {'name': 'Scroll', 'initials': 'SCR', 'bias': -2},
    
    # India - Center
    'timesofindia.indiatimes.com': {'name': 'Times of India', 'initials': 'TOI', 'bias': 0},
    'timesofindia.com': {'name': 'Times of India', 'initials': 'TOI', 'bias': 0},
    'hindustantimes.com': {'name': 'Hindustan Times', 'initials': 'HT', 'bias': 0},
    'economictimes.indiatimes.com': {'name': 'Economic Times', 'initials': 'ET', 'bias': 0},
    'economictimes.com': {'name': 'Economic Times', 'initials': 'ET', 'bias': 0},
    'livemint.com': {'name': 'Mint', 'initials': 'MINT', 'bias': 0},
    'news18.com': {'name': 'News18', 'initials': 'N18', 'bias': 0},
    
    # India - Right-leaning
    'republicworld.com': {'name': 'Republic', 'initials': 'REP', 'bias': 2},
    'swarajyamag.com': {'name': 'Swarajya', 'initials': 'SWR', 'bias': 2},
    'opindia.com': {'name': 'OpIndia', 'initials': 'OPI', 'bias': 2},
}

def get_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def get_source_info(url: str, source_name: str = '') -> Optional[dict]:
    domain = get_domain(url)
    
    # Try domain lookup first
    if domain in SOURCE_DATA:
        return SOURCE_DATA[domain]
    
    # Try partial domain match
    for key, info in SOURCE_DATA.items():
        if key in domain or domain in key:
            return info
    
    # Try matching by source name
    source_lower = source_name.lower()
    for d, info in SOURCE_DATA.items():
        if info['name'].lower() in source_lower or source_lower in info['name'].lower():
            return info
    
    # Default for unknown sources
    initials = ''.join(word[0].upper() for word in source_name.split()[:2]) if source_name else '?'
    return {'name': source_name or 'Unknown', 'initials': initials[:3], 'bias': 0}

def bias_to_political(bias: int) -> str:
    """Convert numeric bias to political position (3 categories)."""
    if bias <= -1:
        return 'left'
    elif bias >= 1:
        return 'right'
    return 'center'

def analyze_tone(text: str) -> str:
    """Analyze text tone and return optimistic/neutral/pessimistic."""
    if not text:
        return 'neutral'
    
    text_lower = text.lower()
    
    optimistic = ['success', 'breakthrough', 'victory', 'hope', 'promising', 'progress',
                  'growth', 'improvement', 'opportunity', 'celebrate', 'achievement',
                  'historic', 'milestone', 'positive', 'recover', 'solution', 'surge',
                  'boom', 'soar', 'record high', 'beat', 'exceeds', 'strong', 'gains',
                  'wins', 'triumph', 'boost', 'optimism', 'thrives', 'rally', 'jumps']
    
    pessimistic = ['crisis', 'fear', 'threat', 'danger', 'warning', 'concern', 'worry',
                   'decline', 'failure', 'disaster', 'collapse', 'struggle', 'problem',
                   'risk', 'uncertainty', 'turmoil', 'chaos', 'devastating', 'alarming',
                   'grim', 'bleak', 'dire', 'criticism', 'backlash', 'plunge', 'crash',
                   'death', 'killed', 'attack', 'violence', 'conflict', 'warns', 'fears',
                   'slams', 'fails', 'worst', 'critical', 'outrage', 'scandal', 'tensions']
    
    opt_count = sum(1 for word in optimistic if word in text_lower)
    pess_count = sum(1 for word in pessimistic if word in text_lower)
    score = opt_count - pess_count
    
    if score >= 2:
        return 'optimistic'
    elif score <= -2:
        return 'pessimistic'
    return 'neutral'

def fetch_region_news(region: str) -> List[dict]:
    """Fetch news articles for a specific region from multiple RSS feeds."""
    print(f"  Fetching {region} news...")
    articles = []
    feeds = REGION_FEEDS.get(region, [])
    
    for feed_name, feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                title = entry.get('title', '')
                source = feed_name.split()[0]
                
                # Google News format: "Title - Source"
                if ' - ' in title and 'Google' in feed_name:
                    parts = title.rsplit(' - ', 1)
                    if len(parts) == 2:
                        title = parts[0]
                        source = parts[1]
                
                if len(title) < 20:
                    continue
                
                articles.append({
                    'title': title.strip(),
                    'link': entry.get('link', ''),
                    'description': entry.get('summary', entry.get('description', '')).strip(),
                    'source': source,
                    'published': entry.get('published', ''),
                })
            
            time.sleep(CONFIG['request_delay'])
            
        except Exception as e:
            print(f"    Error fetching {feed_name}: {e}")
    
    print(f"    Found {len(articles)} articles from {len(feeds)} feeds")
    return articles

def get_keywords(text: str) -> set:
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    stopwords = {'this', 'that', 'with', 'from', 'have', 'were', 'been', 'will',
                'their', 'what', 'when', 'where', 'which', 'about', 'would', 'could',
                'should', 'after', 'before', 'other', 'there', 'these', 'those',
                'says', 'said', 'just', 'like', 'also', 'more', 'than', 'into',
                'news', 'report', 'reports', 'according', 'year', 'years', 'first',
                'last', 'next', 'back', 'over', 'most', 'only', 'some', 'many'}
    return set(words) - stopwords

def similarity(kw1: set, kw2: set) -> float:
    if not kw1 or not kw2:
        return 0
    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    return intersection / union if union > 0 else 0

def group_similar_stories(articles: List[dict], num_stories: int) -> List[List[dict]]:
    """Group articles covering the same story."""
    groups = []
    used = set()
    
    for i, article in enumerate(articles):
        if i in used:
            continue
            
        keywords_i = get_keywords(article['title'])
        group = [article]
        used.add(i)
        
        for j, other in enumerate(articles[i+1:], start=i+1):
            if j in used:
                continue
            
            keywords_j = get_keywords(other['title'])
            sim = similarity(keywords_i, keywords_j)
            if sim > 0.2:
                # Allow same source only if significantly different headline
                if article.get('source') != other.get('source') or sim > 0.5:
                    group.append(other)
                    used.add(j)
        
        groups.append(group)
    
    # Sort by coverage (more sources = more important)
    groups.sort(key=lambda g: len(g), reverse=True)
    return groups[:num_stories]

def create_story_object(story_group: List[dict], story_id: str) -> dict:
    """Create a story object in matrix-compatible format."""
    
    # Find most neutral version for headline
    neutral_version = story_group[0]
    for article in story_group:
        source_info = get_source_info(article['link'], article['source'])
        if source_info['bias'] == 0:
            neutral_version = article
            break
    
    # Create versions
    versions = []
    seen_sources = set()
    
    for article in story_group:
        source_info = get_source_info(article['link'], article['source'])
        political = bias_to_political(source_info['bias'])
        tone = analyze_tone(article['title'] + ' ' + article.get('description', ''))
        
        # Avoid duplicate sources
        source_key = source_info['initials']
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        
        versions.append({
            'political': political,
            'tone': tone,
            'source': source_info['name'],
            'initials': source_info['initials'],
            'domain': get_domain(article['link']) or source_info.get('domain', ''),
            'headline': article['title'],
            'url': article['link']
        })
    
    # Clean description
    desc = neutral_version.get('description', '')
    if desc:
        desc = re.sub(r'<[^>]+>', '', desc)[:300].strip()
    
    return {
        'id': story_id,
        'neutralHeadline': neutral_version['title'],
        'neutralSummary': desc or neutral_version['title'],
        'versions': versions
    }

def process_region(region: str) -> Dict:
    """Process all news for a single region."""
    print(f"\nProcessing {region.upper()}...")
    
    raw_articles = fetch_region_news(region)
    story_groups = group_similar_stories(raw_articles, CONFIG['num_stories_per_region'])
    
    stories = []
    for i, group in enumerate(story_groups):
        story_id = f"{region}-{i+1}"
        story = create_story_object(group, story_id)
        stories.append(story)
        print(f"    {i+1}. {story['neutralHeadline'][:50]}... ({len(story['versions'])} sources)")
    
    region_names = {
        'global': 'Global',
        'us': 'United States',
        'singapore': 'Singapore',
        'india': 'India'
    }
    
    return {
        'name': region_names.get(region, region),
        'stories': stories
    }

def build_news_data():
    """Main build function."""
    print(f"\n{'='*60}")
    print(f"FullSpectrum.News Build - Expanded Matrix Edition")
    print(f"Started: {datetime.now()}")
    print(f"Stories per region: {CONFIG['num_stories_per_region']}")
    print(f"{'='*60}")
    
    regions = {}
    for region in ['global', 'us', 'singapore', 'india']:
        regions[region] = process_region(region)
    
    output = {
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'regions': regions
    }
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "..", CONFIG['output_file'])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Build complete! Output: {output_path}")
    for region, data in regions.items():
        total_sources = sum(len(s['versions']) for s in data['stories'])
        print(f"  {region}: {len(data['stories'])} stories, {total_sources} total sources")
    print(f"{'='*60}\n")
    
    return output

if __name__ == '__main__':
    build_news_data()
