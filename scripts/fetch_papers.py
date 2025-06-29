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
        logger.info(f"🔍 开始从arXiv抓取论文: {start_date.date()} 到 {end_date.date()}")
        logger.info(f"📋 目标类别: {', '.join(CS_CATEGORIES)}")
        logger.info(f"🔧 改进策略: 分别查询每个类别以避免OR查询限制")
        
        all_papers_dict = {}  # 使用字典去重，key为arxiv_id
        total_categories_processed = 0
        total_raw_papers = 0
        
        # 分别查询每个类别
        for category in CS_CATEGORIES:
            total_categories_processed += 1
            logger.info(f"📂 处理类别 {total_categories_processed}/{len(CS_CATEGORIES)}: {category}")
            
            category_papers = self._fetch_papers_for_category(
                category, start_date, end_date, max_papers_per_category=500
            )
            
            # 合并到总结果中（去重）
            new_papers_count = 0
            for paper in category_papers:
                arxiv_id = paper['arxiv_id']
                if arxiv_id not in all_papers_dict:
                    all_papers_dict[arxiv_id] = paper
                    new_papers_count += 1
            
            total_raw_papers += len(category_papers)
            logger.info(f"   ✅ {category}: 获得{len(category_papers)}篇, 新增{new_papers_count}篇")
        
        # 转换为列表并按日期排序
        all_papers = list(all_papers_dict.values())
        all_papers.sort(key=lambda x: x['updated'], reverse=True)
        
        logger.info(f"📊 抓取总结:")
        logger.info(f"   - 处理了 {total_categories_processed} 个类别")
        logger.info(f"   - 从arXiv获取了 {total_raw_papers} 篇原始论文")
        logger.info(f"   - 去重后得到 {len(all_papers)} 篇唯一论文")
        
        # 显示类别分布
        if all_papers:
            from collections import Counter
            
            # 日期分布
            dates = []
            for paper in all_papers:
                paper_date = datetime.strptime(paper['updated'][:10], '%Y-%m-%d')
                dates.append(paper_date.strftime('%Y-%m-%d'))
            
            date_counts = Counter(dates)
            logger.info(f"📅 论文日期分布 (前5天):")
            for date, count in date_counts.most_common(5):
                days_ago = (datetime.now(timezone.utc).date() - datetime.strptime(date, '%Y-%m-%d').date()).days
                logger.info(f"   - {date}: {count}篇 ({days_ago}天前)")
            
            # 类别分布
            category_counts = Counter()
            for paper in all_papers:
                for cat in paper['categories']:
                    if cat in CS_CATEGORIES:
                        category_counts[cat] += 1
            
            logger.info(f"📊 类别分布:")
            for cat, count in category_counts.most_common():
                logger.info(f"   - {cat}: {count}篇")
        
        return all_papers
    
    def _fetch_papers_for_category(self, category: str, start_date: datetime, 
                                 end_date: datetime, max_papers_per_category: int = 500) -> List[Dict]:
        """
        Fetch papers for a specific category.
        
        Args:
            category: arXiv category (e.g., 'cs.AI')
            start_date: Start date for paper search
            end_date: End date for paper search
            max_papers_per_category: Maximum papers to fetch for this category
            
        Returns:
            List of paper dictionaries for this category
        """
        papers = []
        start_index = 0
        batch_count = 0
        
        while len(papers) < max_papers_per_category:
            try:
                batch_count += 1
                
                params = {
                    "search_query": f"cat:{category}",
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                    "start": start_index,
                    "max_results": min(MAX_RESULTS_PER_BATCH, max_papers_per_category - len(papers))
                }
                
                logger.debug(f"   📦 {category}第{batch_count}批次: 从索引{start_index}开始...")
                
                response = self.session.get(ARXIV_BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                entries = feed.entries
                
                logger.debug(f"   ✅ {category}第{batch_count}批次获取了 {len(entries)} 篇论文")
                
                if not entries:
                    logger.debug(f"   📭 {category}: 没有更多论文")
                    break
                
                # Filter papers by date
                batch_papers = []
                older_papers = 0
                for entry in entries:
                    paper_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    
                    if paper_date < start_date:
                        older_papers += 1
                        continue
                    
                    if start_date <= paper_date <= end_date:
                        paper_data = self._parse_paper_entry(entry)
                        batch_papers.append(paper_data)
                
                papers.extend(batch_papers)
                logger.debug(f"   📊 {category}第{batch_count}批次: {len(batch_papers)}篇符合日期, {older_papers}篇过旧")
                
                # If we found older papers, we can stop
                if older_papers > 0:
                    logger.debug(f"   🔚 {category}: 发现过旧论文，停止")
                    break
                
                # If we got fewer papers than requested, we've reached the end
                if len(entries) < MAX_RESULTS_PER_BATCH:
                    logger.debug(f"   🔚 {category}: 到达数据末尾")
                    break
                
                start_index += MAX_RESULTS_PER_BATCH
                
                # Safety limit per category
                if start_index >= 1000:
                    logger.debug(f"   ⚠️ {category}: 达到单类别安全上限")
                    break
                
            except Exception as e:
                logger.error(f"   ❌ {category}抓取出错: {e}")
                break
        
        return papers
    
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
        if not papers:
            logger.warning("⚠️ 没有论文需要过滤！")
            return []
            
        logger.info(f"🤖 开始使用GPT-4o过滤论文...")
        logger.info(f"📝 待处理论文数量: {len(papers)} 篇")
        
        relevant_papers = []
        processed_count = 0
        
        for i, paper in enumerate(papers, 1):
            try:
                logger.info(f"🔍 处理第 {i}/{len(papers)} 篇论文: {paper['title'][:60]}...")
                is_relevant = self._check_paper_relevance(paper)
                processed_count += 1
                
                if is_relevant:
                    relevant_papers.append(paper)
                    logger.info(f"✅ 第 {i} 篇论文 [相关]: {paper['title'][:80]}...")
                else:
                    logger.info(f"❌ 第 {i} 篇论文 [不相关]: {paper['title'][:80]}...")
                    
                # 每处理10篇论文显示一次进度
                if i % 10 == 0:
                    logger.info(f"📊 进度更新: 已处理 {i}/{len(papers)} 篇论文，发现 {len(relevant_papers)} 篇相关论文")
                    
            except Exception as e:
                logger.error(f"❌ 处理第 {i} 篇论文时出错: {e}")
                continue
        
        logger.info(f"🎯 GPT-4o过滤完成!")
        logger.info(f"   - 总共处理: {processed_count} 篇论文")
        logger.info(f"   - 发现相关: {len(relevant_papers)} 篇论文")
        logger.info(f"   - 相关比例: {len(relevant_papers)/processed_count*100:.1f}%" if processed_count > 0 else "   - 相关比例: 0%")
        
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
            is_relevant = result == "1"
            
            logger.debug(f"GPT-4o响应: '{result}' -> {'相关' if is_relevant else '不相关'}")
            return is_relevant
            
        except Exception as e:
            logger.error(f"调用GPT-4o API时出错: {e}")
            return False
    
    def fetch_recent_papers(self, days: int = 1) -> List[Dict]:
        """Fetch papers from the last N days."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"📅 日常模式: 获取 {days} 天内的论文")
        logger.info(f"🕐 时间范围: {start_date.strftime('%Y-%m-%d %H:%M')} UTC ~ {end_date.strftime('%Y-%m-%d %H:%M')} UTC")
        
        papers = self.fetch_papers_by_date_range(start_date, end_date)
        
        if papers:
            logger.info(f"📋 开始GPT-4o智能过滤阶段...")
            return self.filter_papers_with_gpt(papers)
        else:
            logger.warning("⚠️ 未获取到任何论文，跳过GPT过滤步骤")
            return []
    
    def fetch_historical_papers(self, years: int = 2) -> List[Dict]:
        """Fetch papers from the past N years."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years * 365)
        
        logger.info(f"📚 历史模式: 获取过去 {years} 年的论文")
        logger.info(f"🕐 时间范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"⚠️ 注意: 历史模式最多处理 5000 篇论文，可能需要较长时间")
        
        papers = self.fetch_papers_by_date_range(start_date, end_date, max_papers=5000)
        
        if papers:
            logger.info(f"📋 开始GPT-4o智能过滤阶段...")
            return self.filter_papers_with_gpt(papers)
        else:
            logger.warning("⚠️ 未获取到任何论文，跳过GPT过滤步骤")
            return []


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
    import time
    
    start_time = time.time()
    logger.info("🚀 开始执行ArXiv论文抓取任务")
    logger.info("=" * 60)
    
    # Get environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("TARGET_REPO_TOKEN")
    target_repo = os.getenv("TARGET_REPO_NAME", "YurenHao0426/awesome-llm-bias-papers")
    
    logger.info("🔧 配置信息:")
    logger.info(f"   - OpenAI API Key: {'已设置' if openai_api_key else '未设置'}")
    logger.info(f"   - GitHub Token: {'已设置' if github_token else '未设置'}")
    logger.info(f"   - 目标仓库: {target_repo}")
    
    # Check for required environment variables
    if not openai_api_key:
        logger.error("❌ OPENAI_API_KEY 环境变量未设置")
        sys.exit(1)
    
    if not github_token:
        logger.error("❌ TARGET_REPO_TOKEN 环境变量未设置")
        sys.exit(1)
    
    # Get command line arguments
    mode = os.getenv("FETCH_MODE", "daily")  # daily or historical
    days = int(os.getenv("FETCH_DAYS", "1"))
    
    logger.info(f"📋 执行模式: {mode}")
    if mode == "daily":
        logger.info(f"📅 抓取天数: {days} 天")
    
    try:
        step_start = time.time()
        
        # Initialize fetcher
        logger.info("🔄 初始化论文抓取器...")
        fetcher = ArxivPaperFetcher(openai_api_key)
        logger.info(f"✅ 初始化完成 ({time.time() - step_start:.1f}秒)")
        
        # Fetch papers
        step_start = time.time()
        if mode == "historical":
            logger.info("📚 运行历史模式 - 抓取过去2年的论文")
            papers = fetcher.fetch_historical_papers(years=2)
            section_title = "Historical LLM Bias Papers (Past 2 Years)"
        else:
            logger.info(f"📰 运行日常模式 - 抓取过去{days}天的论文")
            papers = fetcher.fetch_recent_papers(days=days)
            section_title = None  # Use default timestamp
        
        fetch_time = time.time() - step_start
        logger.info(f"⏱️ 论文抓取和过滤完成 ({fetch_time:.1f}秒)")
        
        # Update GitHub repository
        if papers:
            step_start = time.time()
            logger.info(f"📤 开始更新GitHub仓库...")
            updater = GitHubUpdater(github_token, target_repo)
            updater.update_readme_with_papers(papers, section_title)
            update_time = time.time() - step_start
            logger.info(f"✅ GitHub仓库更新完成 ({update_time:.1f}秒)")
            
            logger.info("🎉 任务完成!")
            logger.info(f"   - 找到相关论文: {len(papers)} 篇")
            logger.info(f"   - 总执行时间: {time.time() - start_time:.1f} 秒")
        else:
            logger.warning("⚠️ 没有找到相关论文")
            logger.info("可能的原因:")
            logger.info("   - 指定日期范围内没有新的LLM偏见相关论文")
            logger.info("   - arXiv API连接问题")
            logger.info("   - GPT-4o过滤条件过于严格")
            logger.info(f"   - 总执行时间: {time.time() - start_time:.1f} 秒")
            
    except Exception as e:
        logger.error(f"❌ 执行过程中出现错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
