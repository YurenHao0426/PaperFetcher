#!/usr/bin/env python3
"""
Arxiv Paper Fetcher for LLM Bias Research
==========================================

This script fetches computer science papers from arxiv.org, filters them using 
GPT-4o to identify papers related to LLM bias and fairness, and updates a 
target GitHub repository's README with the results.

Features:
- Fetches papers from the last 24 hours (or specified days)
- Can also fetch historical papers from the past 2 years
- Uses GPT-4o for intelligent filtering
- Updates target repository via GitHub API
- Supports GitHub Actions automation
"""

import os
import sys
import json
import logging
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from github import Github
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Configuration
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
MAX_RESULTS_PER_BATCH = 100
MAX_RETRIES = 3

# Computer Science categories related to AI/ML
CS_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.CL",  # Computation and Language
    "cs.CV",  # Computer Vision and Pattern Recognition
    "cs.LG",  # Machine Learning
    "cs.NE",  # Neural and Evolutionary Computing
    "cs.RO",  # Robotics
    "cs.IR",  # Information Retrieval
    "cs.HC",  # Human-Computer Interaction
    "stat.ML" # Machine Learning (Statistics)
]

GPT_SYSTEM_PROMPT = """You are an expert researcher in AI/ML bias and fairness. 

Your task is to analyze a paper's title and abstract to determine if it's relevant to LLM (Large Language Model) bias and fairness research.

A paper is relevant if it discusses:
- Bias in large language models, generative AI, or foundation models
- Fairness issues in NLP models or text generation
- Ethical concerns with language models
- Demographic bias in AI systems
- Alignment and safety of language models
- Bias evaluation or mitigation in NLP

Respond with exactly "1" if the paper is relevant, or "0" if it's not relevant.
Do not include any other text in your response."""


class ArxivPaperFetcher:
    """Main class for fetching and filtering arxiv papers."""
    
    def __init__(self, openai_api_key: str):
        """Initialize the fetcher with OpenAI API key."""
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PaperFetcher/1.0 (https://github.com/YurenHao0426/PaperFetcher)'
        })
    
    def fetch_papers_by_date_range(self, start_date: datetime, end_date: datetime, 
                                 max_papers: int = 1000) -> List[Dict]:
        """
        Fetch papers from arxiv within a specific date range.
        
        Args:
            start_date: Start date for paper search
            end_date: End date for paper search
            max_papers: Maximum number of papers to fetch
            
        Returns:
            List of paper dictionaries
        """
        logger.info(f"Fetching papers from {start_date.date()} to {end_date.date()}")
        
        # Build category query
        category_query = " OR ".join(f"cat:{cat}" for cat in CS_CATEGORIES)
        
        all_papers = []
        start_index = 0
        
        while len(all_papers) < max_papers:
            try:
                # Build search query
                search_query = f"({category_query})"
                
                params = {
                    "search_query": search_query,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                    "start": start_index,
                    "max_results": min(MAX_RESULTS_PER_BATCH, max_papers - len(all_papers))
                }
                
                logger.debug(f"Fetching batch starting at index {start_index}")
                response = self.session.get(ARXIV_BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                entries = feed.entries
                
                if not entries:
                    logger.info("No more papers available")
                    break
                
                # Filter papers by date
                batch_papers = []
                for entry in entries:
                    paper_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    
                    if paper_date < start_date:
                        # Papers are sorted by date, so we can stop here
                        logger.info(f"Reached papers older than start date: {paper_date.date()}")
                        return all_papers
                    
                    if start_date <= paper_date <= end_date:
                        paper_data = self._parse_paper_entry(entry)
                        batch_papers.append(paper_data)
                
                all_papers.extend(batch_papers)
                logger.info(f"Fetched {len(batch_papers)} papers in date range from this batch. Total: {len(all_papers)}")
                
                # If we got fewer papers than requested, we've reached the end
                if len(entries) < MAX_RESULTS_PER_BATCH:
                    break
                
                start_index += MAX_RESULTS_PER_BATCH
                
            except Exception as e:
                logger.error(f"Error fetching papers: {e}")
                break
        
        logger.info(f"Total papers fetched: {len(all_papers)}")
        return all_papers
    
    def _parse_paper_entry(self, entry) -> Dict:
        """Parse a feedparser entry into a paper dictionary."""
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
    
    def filter_papers_with_gpt(self, papers: List[Dict]) -> List[Dict]:
        """
        Filter papers using GPT-4o to identify bias-related research.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of relevant papers
        """
        logger.info(f"Filtering {len(papers)} papers using GPT-4o")
        relevant_papers = []
        
        for i, paper in enumerate(papers, 1):
            try:
                is_relevant = self._check_paper_relevance(paper)
                if is_relevant:
                    relevant_papers.append(paper)
                    logger.info(f"✓ Paper {i}/{len(papers)}: {paper['title'][:80]}...")
                else:
                    logger.debug(f"✗ Paper {i}/{len(papers)}: {paper['title'][:80]}...")
                    
            except Exception as e:
                logger.error(f"Error filtering paper {i}: {e}")
                continue
        
        logger.info(f"Found {len(relevant_papers)} relevant papers out of {len(papers)}")
        return relevant_papers
    
    def _check_paper_relevance(self, paper: Dict) -> bool:
        """Check if a paper is relevant using GPT-4o."""
        prompt = f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": GPT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1
            )
            
            result = response.choices[0].message.content.strip()
            return result == "1"
            
        except Exception as e:
            logger.error(f"Error calling GPT-4o: {e}")
            return False
    
    def fetch_recent_papers(self, days: int = 1) -> List[Dict]:
        """Fetch papers from the last N days."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        papers = self.fetch_papers_by_date_range(start_date, end_date)
        return self.filter_papers_with_gpt(papers)
    
    def fetch_historical_papers(self, years: int = 2) -> List[Dict]:
        """Fetch papers from the past N years."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years * 365)
        
        logger.info(f"Fetching historical papers from the past {years} years")
        papers = self.fetch_papers_by_date_range(start_date, end_date, max_papers=5000)
        return self.filter_papers_with_gpt(papers)


class GitHubUpdater:
    """Handle GitHub repository updates."""
    
    def __init__(self, token: str, repo_name: str):
        """Initialize GitHub updater."""
        self.github = Github(token)
        self.repo_name = repo_name
        self.repo = self.github.get_repo(repo_name)
    
    def update_readme_with_papers(self, papers: List[Dict], section_title: str = None):
        """Update README with new papers."""
        if not papers:
            logger.info("No papers to add to README")
            return
        
        if section_title is None:
            section_title = f"Papers Updated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        
        try:
            # Get current README
            readme_file = self.repo.get_contents("README.md", ref="main")
            current_content = readme_file.decoded_content.decode("utf-8")
            
            # Create new section
            new_section = f"\n\n## {section_title}\n\n"
            
            for paper in papers:
                # Format paper entry
                authors_str = ", ".join(paper['authors'][:3])  # First 3 authors
                if len(paper['authors']) > 3:
                    authors_str += " et al."
                
                categories_str = ", ".join(paper['categories'])
                
                new_section += f"### {paper['title']}\n\n"
                new_section += f"**Authors:** {authors_str}\n\n"
                new_section += f"**Categories:** {categories_str}\n\n"
                new_section += f"**Published:** {paper['published']}\n\n"
                new_section += f"**Abstract:** {paper['abstract']}\n\n"
                new_section += f"**Link:** [arXiv:{paper['arxiv_id']}]({paper['link']})\n\n"
                new_section += "---\n\n"
            
            # Update README
            updated_content = current_content + new_section
            commit_message = f"Auto-update: Added {len(papers)} new papers on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
            
            self.repo.update_file(
                path="README.md",
                message=commit_message,
                content=updated_content,
                sha=readme_file.sha,
                branch="main"
            )
            
            logger.info(f"Successfully updated README with {len(papers)} papers")
            
        except Exception as e:
            logger.error(f"Error updating README: {e}")
            raise


def main():
    """Main function to run the paper fetcher."""
    # Get environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("TARGET_REPO_TOKEN")
    target_repo = os.getenv("TARGET_REPO_NAME", "YurenHao0426/awesome-llm-bias-papers")
    
    # Check for required environment variables
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    if not github_token:
        logger.error("TARGET_REPO_TOKEN environment variable is required")
        sys.exit(1)
    
    # Get command line arguments
    mode = os.getenv("FETCH_MODE", "daily")  # daily or historical
    days = int(os.getenv("FETCH_DAYS", "1"))
    
    try:
        # Initialize fetcher
        fetcher = ArxivPaperFetcher(openai_api_key)
        
        if mode == "historical":
            logger.info("Running in historical mode - fetching papers from past 2 years")
            papers = fetcher.fetch_historical_papers(years=2)
            section_title = "Historical LLM Bias Papers (Past 2 Years)"
        else:
            logger.info(f"Running in daily mode - fetching papers from last {days} day(s)")
            papers = fetcher.fetch_recent_papers(days=days)
            section_title = None  # Use default timestamp
        
        # Update GitHub repository
        if papers:
            updater = GitHubUpdater(github_token, target_repo)
            updater.update_readme_with_papers(papers, section_title)
            logger.info(f"Successfully processed {len(papers)} papers")
        else:
            logger.info("No relevant papers found")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
