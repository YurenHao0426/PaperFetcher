#!/usr/bin/env python3
"""
Test script for historical paper fetching functionality.

This script tests the ArxivPaperFetcher class with a smaller date range
to verify the historical fetching works correctly before running on 2 years of data.
"""

import os
import sys
from datetime import datetime, timezone, timedelta

# Add the parent directory to the path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_papers import ArxivPaperFetcher


def test_recent_historical_fetch():
    """Test fetching papers from the last 30 days as a historical test."""
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY environment variable is required")
        sys.exit(1)
        
    print("Testing historical paper fetching (last 30 days)...")
    
    # Initialize fetcher
    fetcher = ArxivPaperFetcher(openai_api_key)
    
    # Test with last 30 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    print(f"Fetching papers from {start_date.date()} to {end_date.date()}")
    
    # Fetch papers (limit to 200 for testing)
    papers = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=200)
    
    print(f"\nFetched {len(papers)} papers total")
    
    if papers:
        print("\nSample papers:")
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:2])}")
            print(f"   Categories: {', '.join(paper['categories'])}")
            print(f"   Published: {paper['published']}")
            print(f"   Abstract: {paper['abstract'][:150]}...")
        
        # Test GPT filtering on a smaller subset
        print(f"\nTesting GPT-4o filtering on first 10 papers...")
        sample_papers = papers[:10]
        filtered_papers = fetcher.filter_papers_with_gpt(sample_papers)
        
        print(f"\nFiltering results: {len(filtered_papers)}/{len(sample_papers)} papers are relevant")
        
        if filtered_papers:
            print("\nRelevant papers found:")
            for i, paper in enumerate(filtered_papers, 1):
                print(f"\n{i}. {paper['title']}")
                print(f"   Abstract: {paper['abstract'][:200]}...")
        else:
            print("No relevant papers found in the sample.")
    
    else:
        print("No papers found in the date range.")


def test_specific_date_range():
    """Test fetching papers from a specific date range known to have bias papers."""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY environment variable is required")
        sys.exit(1)
        
    print("\nTesting specific date range (January 2024)...")
    
    fetcher = ArxivPaperFetcher(openai_api_key)
    
    # Test January 2024 (likely to have some relevant papers)
    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
    
    print(f"Fetching papers from {start_date.date()} to {end_date.date()}")
    
    papers = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=500)
    print(f"Fetched {len(papers)} papers from January 2024")
    
    if papers:
        # Filter for bias-related papers
        filtered_papers = fetcher.filter_papers_with_gpt(papers)
        
        print(f"\nFound {len(filtered_papers)} bias-related papers in January 2024")
        
        for i, paper in enumerate(filtered_papers[:5], 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   arXiv ID: {paper['arxiv_id']}")
            print(f"   Link: {paper['link']}")


if __name__ == "__main__":
    print("ArXiv Historical Paper Fetcher Test")
    print("=" * 40)
    
    try:
        test_recent_historical_fetch()
        test_specific_date_range()
        print("\n" + "=" * 40)
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        sys.exit(1) 