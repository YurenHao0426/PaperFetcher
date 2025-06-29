#!/usr/bin/env python3
"""
测试论文抓取功能 - 显示改进的日志

这个脚本只测试论文抓取部分，展示分页过程和日期分布，不需要OpenAI API。
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from collections import Counter

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_papers import ArxivPaperFetcher


def test_paper_fetching_with_detailed_logs():
    """测试论文抓取，显示详细的分页和日期信息"""
    
    print("🚀 测试改进后的论文抓取日志显示")
    print("=" * 60)
    
    # 创建一个模拟的fetcher（不需要OpenAI API）
    class MockArxivFetcher:
        def __init__(self):
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'PaperFetcher/1.0 (Test)'
            })
        
        def fetch_papers_by_date_range(self, start_date, end_date, max_papers=300):
            """模拟我们改进后的抓取函数"""
            logger.info(f"🔍 开始从arXiv抓取论文: {start_date.date()} 到 {end_date.date()}")
            logger.info(f"📋 目标类别: cs.AI, cs.CL, cs.CV, cs.LG, cs.NE, cs.RO, cs.IR, cs.HC, stat.ML")
            
            from scripts.fetch_papers import ARXIV_BASE_URL, CS_CATEGORIES, MAX_RESULTS_PER_BATCH
            import requests
            import feedparser
            
            # Build category query
            category_query = " OR ".join(f"cat:{cat}" for cat in CS_CATEGORIES)
            
            all_papers = []
            start_index = 0
            batch_count = 0
            total_raw_papers = 0
            
            while len(all_papers) < max_papers:
                try:
                    batch_count += 1
                    search_query = f"({category_query})"
                    
                    params = {
                        "search_query": search_query,
                        "sortBy": "submittedDate",
                        "sortOrder": "descending",
                        "start": start_index,
                        "max_results": min(MAX_RESULTS_PER_BATCH, max_papers - len(all_papers))
                    }
                    
                    logger.info(f"📦 第{batch_count}批次: 从索引{start_index}开始抓取...")
                    
                    response = self.session.get(ARXIV_BASE_URL, params=params, timeout=30)
                    response.raise_for_status()
                    
                    feed = feedparser.parse(response.content)
                    entries = feed.entries
                    total_raw_papers += len(entries)
                    
                    logger.info(f"✅ 第{batch_count}批次获取了 {len(entries)} 篇论文")
                    
                    if not entries:
                        logger.info("📭 没有更多论文可用")
                        break
                    
                    # Filter papers by date and parse them
                    batch_papers = []
                    older_papers = 0
                    for entry in entries:
                        paper_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                        
                        if paper_date < start_date:
                            older_papers += 1
                            continue
                        
                        if start_date <= paper_date <= end_date:
                            paper_data = {
                                "title": entry.title.replace('\n', ' ').strip(),
                                "abstract": entry.summary.replace('\n', ' ').strip(),
                                "authors": [author.name for author in entry.authors] if hasattr(entry, 'authors') else [],
                                "published": entry.published,
                                "updated": entry.updated,
                                "link": entry.link,
                                "arxiv_id": entry.id.split('/')[-1],
                                "categories": [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []
                            }
                            batch_papers.append(paper_data)
                    
                    all_papers.extend(batch_papers)
                    logger.info(f"📊 第{batch_count}批次筛选结果: {len(batch_papers)}篇在日期范围内, {older_papers}篇过旧")
                    logger.info(f"📈 累计获取论文: {len(all_papers)}篇")
                    
                    if older_papers > 0:
                        logger.info(f"🔚 发现{older_papers}篇超出日期范围的论文，停止抓取")
                        break
                    
                    if len(entries) < MAX_RESULTS_PER_BATCH:
                        logger.info("🔚 已达到arXiv数据末尾")
                        break
                    
                    start_index += MAX_RESULTS_PER_BATCH
                    
                except Exception as e:
                    logger.error(f"❌ 抓取论文时出错: {e}")
                    break
            
            # 显示总结信息
            logger.info(f"📊 抓取总结:")
            logger.info(f"   - 总共处理了 {batch_count} 个批次")
            logger.info(f"   - 从arXiv获取了 {total_raw_papers} 篇原始论文")
            logger.info(f"   - 筛选出 {len(all_papers)} 篇符合日期范围的论文")
            
            # 显示日期分布
            if all_papers:
                dates = []
                for paper in all_papers:
                    paper_date = datetime.strptime(paper['updated'][:10], '%Y-%m-%d')
                    dates.append(paper_date.strftime('%Y-%m-%d'))
                
                date_counts = Counter(dates)
                logger.info(f"📅 论文日期分布 (前5天):")
                for date, count in date_counts.most_common(5):
                    days_ago = (datetime.now(timezone.utc).date() - datetime.strptime(date, '%Y-%m-%d').date()).days
                    logger.info(f"   - {date}: {count}篇 ({days_ago}天前)")
            
            return all_papers
    
    # 测试不同的时间范围
    fetcher = MockArxivFetcher()
    
    print("\n🕐 测试1: 过去1天")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=1)
    papers_1day = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=50)
    
    print(f"\n🕐 测试2: 过去7天")
    start_date = end_date - timedelta(days=7)
    papers_7days = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=200)
    
    print(f"\n📊 对比结果:")
    print(f"   - 过去1天: {len(papers_1day)} 篇论文")
    print(f"   - 过去7天: {len(papers_7days)} 篇论文")
    print(f"   - 这解释了为什么日常模式很快完成!")


if __name__ == "__main__":
    test_paper_fetching_with_detailed_logs() 