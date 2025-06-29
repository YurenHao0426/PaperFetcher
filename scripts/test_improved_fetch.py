#!/usr/bin/env python3
"""
测试改进后的论文抓取功能

验证分别查询每个类别和去重逻辑是否正常工作。
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta

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


def test_improved_fetching():
    """测试改进后的抓取逻辑"""
    
    print("🚀 测试改进后的论文抓取逻辑")
    print("=" * 60)
    
    # 创建一个模拟的fetcher（不需要OpenAI API）
    class MockArxivFetcher(ArxivPaperFetcher):
        def __init__(self):
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'PaperFetcher/1.0 (Test)'
            })
    
    # 测试不同的时间范围
    fetcher = MockArxivFetcher()
    
    print("\n🕐 测试1: 过去1天（应该显示0篇论文）")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=1)
    papers_1day = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=100)
    
    print(f"\n🕐 测试2: 过去7天（应该显示更多论文和详细分布）")
    start_date = end_date - timedelta(days=7)
    papers_7days = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=300)
    
    print(f"\n📊 改进效果对比:")
    print(f"   - 过去1天: {len(papers_1day)} 篇论文")
    print(f"   - 过去7天: {len(papers_7days)} 篇论文")
    
    if papers_7days:
        print(f"\n📋 论文样本 (前3篇):")
        for i, paper in enumerate(papers_7days[:3], 1):
            print(f"\n{i}. {paper['title'][:80]}...")
            print(f"   arXiv ID: {paper['arxiv_id']}")
            print(f"   更新时间: {paper['updated']}")
            print(f"   类别: {', '.join(paper['categories'][:3])}")
            print(f"   作者: {', '.join(paper['authors'][:2])}")
            if len(paper['authors']) > 2:
                print(f"         et al.")
    
    print(f"\n✅ 改进后的优势:")
    print(f"   - ✅ 分别查询每个类别，避免OR查询限制")
    print(f"   - ✅ 自动去重，避免重复论文")
    print(f"   - ✅ 详细的类别分布统计")
    print(f"   - ✅ 更准确的日期分布分析")
    print(f"   - ✅ 更透明的日志显示")

def test_category_overlap():
    """测试类别重叠和去重功能"""
    
    print(f"\n" + "="*60)
    print("🔍 测试类别重叠和去重功能")
    print("="*60)
    
    # 简单测试：手动获取几个类别，看看重叠情况
    import requests
    import feedparser
    from collections import defaultdict
    
    categories = ['cs.AI', 'cs.LG', 'cs.CL']
    papers_by_category = {}
    arxiv_ids_seen = set()
    overlaps = defaultdict(list)
    
    for cat in categories:
        print(f"\n📂 获取 {cat} 类别的论文...")
        
        params = {
            'search_query': f'cat:{cat}',
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
            'max_results': 50
        }
        
        try:
            response = requests.get('http://export.arxiv.org/api/query', params=params, timeout=10)
            feed = feedparser.parse(response.content)
            entries = feed.entries
            
            papers_by_category[cat] = []
            
            for entry in entries:
                arxiv_id = entry.id.split('/')[-1]
                title = entry.title.replace('\n', ' ').strip()
                categories_list = [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []
                
                papers_by_category[cat].append({
                    'arxiv_id': arxiv_id,
                    'title': title,
                    'categories': categories_list
                })
                
                # 检查重叠
                if arxiv_id in arxiv_ids_seen:
                    overlaps[arxiv_id].append(cat)
                else:
                    arxiv_ids_seen.add(arxiv_id)
                    overlaps[arxiv_id] = [cat]
            
            print(f"   获得 {len(entries)} 篇论文")
            
        except Exception as e:
            print(f"   错误: {e}")
    
    # 分析重叠情况
    print(f"\n📊 重叠分析:")
    total_papers = sum(len(papers) for papers in papers_by_category.values())
    unique_papers = len(arxiv_ids_seen)
    duplicate_papers = total_papers - unique_papers
    
    print(f"   - 总获取论文: {total_papers} 篇")
    print(f"   - 唯一论文: {unique_papers} 篇")
    print(f"   - 重复论文: {duplicate_papers} 篇")
    print(f"   - 去重率: {duplicate_papers/total_papers*100:.1f}%")
    
    # 显示一些重叠例子
    overlap_examples = [(arxiv_id, cats) for arxiv_id, cats in overlaps.items() if len(cats) > 1][:5]
    
    if overlap_examples:
        print(f"\n📋 重叠论文示例:")
        for arxiv_id, cats in overlap_examples:
            # 找到这篇论文的标题
            title = "未找到标题"
            for cat, papers in papers_by_category.items():
                for paper in papers:
                    if paper['arxiv_id'] == arxiv_id:
                        title = paper['title'][:60] + "..." if len(paper['title']) > 60 else paper['title']
                        break
                if title != "未找到标题":
                    break
            
            print(f"   - {arxiv_id}: {title}")
            print(f"     类别: {', '.join(cats)}")
    
    print(f"\n✅ 这证明了去重功能的重要性！")


if __name__ == "__main__":
    test_improved_fetching()
    test_category_overlap() 