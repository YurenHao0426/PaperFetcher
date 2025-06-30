#!/usr/bin/env python3
"""
Test 3-Day Paper Fetch

Detailed analysis of paper availability in the past 3 days
to identify why 0 papers were retrieved.
"""

import os
import sys
import logging
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from collections import Counter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_papers import ArxivPaperFetcher, CS_CATEGORIES

def analyze_recent_papers():
    """Analyze papers from the past week with daily breakdown"""
    
    print("🔍 Analyzing Recent Paper Availability")
    print("=" * 60)
    
    # Calculate time ranges
    now = datetime.now(timezone.utc)
    print(f"📅 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Test different time ranges
    time_ranges = [
        ("Past 1 day", now - timedelta(days=1)),
        ("Past 2 days", now - timedelta(days=2)), 
        ("Past 3 days", now - timedelta(days=3)),
        ("Past 7 days", now - timedelta(days=7))
    ]
    
    # Create a fake fetcher instance for accessing private methods
    class TestFetcher:
        def __init__(self):
            import requests
            self.session = requests.Session()
            
        def _parse_paper_entry(self, entry):
            return {
                "title": entry.title.replace('\n', ' ').strip(),
                "abstract": entry.summary.replace('\n', ' ').strip(),
                "authors": [author.name for author in entry.authors] if hasattr(entry, 'authors') else [],
                "published": entry.published,
                "updated": entry.updated,
                "link": entry.link,
                "arxiv_id": entry.id.split('/')[-1],
                "categories": [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []
            }
        
        def fetch_recent_sample(self, start_date, end_date, max_papers=500):
            """Fetch a sample of papers from the date range"""
            all_papers = []
            
            # Check a few key categories
            test_categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
            
            for category in test_categories:
                try:
                    params = {
                        "search_query": f"cat:{category}",
                        "sortBy": "submittedDate", 
                        "sortOrder": "descending",
                        "start": 0,
                        "max_results": 100
                    }
                    
                    response = self.session.get("http://export.arxiv.org/api/query", 
                                              params=params, timeout=30)
                    response.raise_for_status()
                    
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries:
                        paper_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                        
                        if start_date <= paper_date <= end_date:
                            paper_data = self._parse_paper_entry(entry)
                            all_papers.append(paper_data)
                    
                except Exception as e:
                    print(f"   ❌ Error fetching {category}: {e}")
            
            # Remove duplicates
            unique_papers = {}
            for paper in all_papers:
                unique_papers[paper['arxiv_id']] = paper
            
            return list(unique_papers.values())
    
    fetcher = TestFetcher()
    
    # Test each time range
    for range_name, start_date in time_ranges:
        print(f"\n📊 {range_name} ({start_date.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}):")
        
        papers = fetcher.fetch_recent_sample(start_date, now)
        print(f"   📄 Found: {len(papers)} papers")
        
        if papers:
            # Analyze dates
            dates = []
            for paper in papers:
                paper_date = datetime.strptime(paper['updated'][:10], '%Y-%m-%d')
                dates.append(paper_date.strftime('%Y-%m-%d'))
            
            date_counts = Counter(dates)
            print(f"   📅 Daily distribution:")
            for date, count in sorted(date_counts.items(), reverse=True)[:5]:
                days_ago = (now.date() - datetime.strptime(date, '%Y-%m-%d').date()).days
                print(f"     - {date}: {count} papers ({days_ago} days ago)")
            
            # Show some sample titles
            print(f"   📝 Sample papers:")
            for i, paper in enumerate(papers[:3], 1):
                paper_date = datetime.strptime(paper['updated'][:10], '%Y-%m-%d')
                days_ago = (now.date() - paper_date.date()).days
                print(f"     {i}. {paper['title'][:60]}... ({days_ago} days ago)")
        else:
            print(f"   ❌ No papers found in this range")


def check_weekend_effect():
    """Check if weekend affects paper submission patterns"""
    
    print(f"\n" + "="*60)
    print("📅 Weekend Effect Analysis")
    print("="*60)
    
    now = datetime.now(timezone.utc)
    current_weekday = now.strftime('%A')
    
    print(f"🗓️ Today is: {current_weekday}")
    print(f"📊 Checking if weekend timing affects paper submissions...")
    
    # Analyze the past week day by day
    for i in range(7):
        date = now - timedelta(days=i)
        weekday = date.strftime('%A')
        date_str = date.strftime('%Y-%m-%d')
        
        if i == 0:
            status = "(Today)"
        elif i == 1:
            status = "(Yesterday)" 
        else:
            status = f"({i} days ago)"
        
        print(f"   {date_str} {weekday} {status}")
    
    print(f"\n💡 Possible explanations for low paper count:")
    if current_weekday in ['Saturday', 'Sunday']:
        print(f"   🏠 It's {current_weekday} - researchers typically don't submit on weekends")
    elif current_weekday == 'Monday':
        print(f"   📅 It's Monday - weekend submissions are rare, Monday submissions may be low")
    else:
        print(f"   📚 It's {current_weekday} - should be normal submission day")
    
    print(f"   🕐 Time zone effects: arXiv updates happen at specific times")
    print(f"   ⏰ Current UTC time: {now.strftime('%H:%M')} - submissions may not be processed yet")


def test_specific_fetch():
    """Test the actual fetch function with 3 days"""
    
    print(f"\n" + "="*60)
    print("🧪 Testing Actual Fetch Function")
    print("="*60)
    
    print(f"🔄 Testing the same logic your main script uses...")
    
    # Simulate the fetch without OpenAI API
    class MockFetcher(ArxivPaperFetcher):
        def __init__(self):
            import requests
            self.session = requests.Session()
        
        def filter_papers_with_gpt(self, papers, use_parallel=True, max_concurrent=16):
            # Skip GPT filtering, return all papers
            print(f"   ⏭️ Skipping GPT filtering, would have processed {len(papers)} papers")
            return papers
    
    try:
        # Test with mock fetcher
        fetcher = MockFetcher()
        
        # Use the same parameters as your actual run
        papers = fetcher.fetch_recent_papers(days=3)
        
        print(f"📄 Raw papers fetched: {len(papers)} papers")
        
        if papers:
            print(f"✅ Papers found! The issue is likely in GPT filtering or API key")
            print(f"📋 Sample papers:")
            for i, paper in enumerate(papers[:3], 1):
                print(f"   {i}. {paper['title'][:60]}...")
        else:
            print(f"❌ No papers found in raw fetch - arXiv issue or date range problem")
            
    except Exception as e:
        print(f"❌ Error in fetch test: {e}")


if __name__ == "__main__":
    analyze_recent_papers()
    check_weekend_effect() 
    test_specific_fetch()
    
    print(f"\n" + "="*60)
    print("🎯 Diagnosis Summary")
    print("="*60)
    print(f"If this analysis shows:")
    print(f"   📄 Papers exist → Problem is with GPT filtering or API key")
    print(f"   ❌ No papers → Weekend effect or arXiv submission patterns")
    print(f"   🕐 Time zone → Wait a few hours and try again")
    print(f"   📅 Date issue → Check date range logic in fetch function") 