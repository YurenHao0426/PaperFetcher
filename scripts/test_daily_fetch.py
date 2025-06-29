#!/usr/bin/env python3
"""
Test script for daily paper fetching functionality.

This script tests the daily paper fetching with a small sample to verify
the system works correctly before running in production.
"""

import os
import sys
from datetime import datetime, timezone, timedelta

# Add the parent directory to the path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_papers import ArxivPaperFetcher


def test_daily_fetch():
    """Test fetching papers from the last 3 days (to ensure we get some results)."""
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY environment variable is required")  
        print("Please set your OpenAI API key in the environment variable")
        sys.exit(1)
        
    print("Testing daily paper fetching (last 3 days)...")
    
    # Initialize fetcher
    fetcher = ArxivPaperFetcher(openai_api_key)
    
    # Test with last 3 days to ensure we get some results
    papers = fetcher.fetch_recent_papers(days=3)
    
    print(f"\nFetch completed!")
    print(f"Found {len(papers)} relevant LLM bias papers in the last 3 days")
    
    if papers:
        print("\nRelevant papers found:")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:3])}")
            if len(paper['authors']) > 3:
                print("   et al.")
            print(f"   Categories: {', '.join(paper['categories'])}")
            print(f"   Published: {paper['published']}")
            print(f"   arXiv ID: {paper['arxiv_id']}")
            print(f"   Link: {paper['link']}")
            print(f"   Abstract: {paper['abstract'][:200]}...")
            print("-" * 50)
    else:
        print("\nNo relevant papers found in the last 3 days.")
        print("This could be normal - LLM bias papers are not published every day.")


def test_system_components():
    """Test individual system components."""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    print("\nTesting system components...")
    
    # Test fetcher initialization
    try:
        fetcher = ArxivPaperFetcher(openai_api_key)
        print("✓ ArxivPaperFetcher initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize ArxivPaperFetcher: {e}")
        return False
    
    # Test arXiv API connectivity
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)
        papers = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=5)
        print(f"✓ arXiv API connectivity works (fetched {len(papers)} papers)")
    except Exception as e:
        print(f"✗ Failed to connect to arXiv API: {e}")
        return False
    
    # Test OpenAI API connectivity (if we have papers to test)
    if papers:
        try:
            sample_paper = papers[0]
            is_relevant = fetcher._check_paper_relevance(sample_paper)
            print(f"✓ OpenAI API connectivity works (test result: {is_relevant})")
        except Exception as e:
            print(f"✗ Failed to connect to OpenAI API: {e}")
            return False
    
    return True


if __name__ == "__main__":
    print("ArXiv Daily Paper Fetcher Test")
    print("=" * 40)
    
    try:
        # Test system components first
        if test_system_components():
            print("\nAll system components working correctly!")
            
            # Run main test
            test_daily_fetch()
            
            print("\n" + "=" * 40)
            print("Test completed successfully!")
            print("\nTo run the actual daily fetch:")
            print("python scripts/fetch_papers.py")
            
        else:
            print("\nSystem component test failed!")
            sys.exit(1)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        sys.exit(1) 