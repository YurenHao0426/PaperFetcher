#!/usr/bin/env python3
"""
测试arXiv连接 - 不需要OpenAI API密钥

这个脚本只测试arXiv API连接和论文抓取功能，不涉及GPT过滤。
"""

import requests
import feedparser
from datetime import datetime, timezone, timedelta

def test_arxiv_connection():
    """测试arXiv API连接"""
    print("🔍 测试arXiv API连接...")
    
    try:
        # 测试最基本的arXiv查询
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI",
            "sortBy": "submittedDate", 
            "sortOrder": "descending",
            "max_results": 10
        }
        
        print(f"📡 发送请求到: {url}")
        print(f"📋 查询参数: {params}")
        
        response = requests.get(url, params=params, timeout=15)
        print(f"✅ HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            entries = feed.entries
            print(f"📄 获取到 {len(entries)} 篇论文")
            
            if entries:
                print(f"\n📝 论文样本:")
                for i, entry in enumerate(entries[:3], 1):
                    print(f"\n{i}. 标题: {entry.title}")
                    print(f"   发布时间: {entry.published}")
                    print(f"   更新时间: {entry.updated}")
                    print(f"   类别: {[tag.term for tag in entry.tags] if hasattr(entry, 'tags') else '无'}")
                    print(f"   摘要长度: {len(entry.summary)} 字符")
                    print(f"   摘要预览: {entry.summary[:150]}...")
                return True
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ arXiv连接测试失败: {e}")
        return False

def test_date_filtering():
    """测试日期过滤功能"""
    print(f"\n🕐 测试日期过滤功能...")
    
    try:
        # 测试最近3天的论文
        url = "http://export.arxiv.org/api/query"
        
        # 构建包含多个CS类别的查询
        categories = ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.RO", "cs.IR", "cs.HC", "stat.ML"]
        category_query = " OR ".join(f"cat:{cat}" for cat in categories)
        
        params = {
            "search_query": f"({category_query})",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 100
        }
        
        print(f"📋 搜索类别: {', '.join(categories)}")
        print(f"📦 请求最多100篇论文...")
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            entries = feed.entries
            print(f"📄 总共获取: {len(entries)} 篇论文")
            
            # 分析日期分布
            now = datetime.now(timezone.utc)
            cutoff_1day = now - timedelta(days=1)
            cutoff_3days = now - timedelta(days=3)
            cutoff_7days = now - timedelta(days=7)
            
            recent_1day = 0
            recent_3days = 0
            recent_7days = 0
            
            for entry in entries:
                paper_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                if paper_date >= cutoff_1day:
                    recent_1day += 1
                if paper_date >= cutoff_3days:
                    recent_3days += 1
                if paper_date >= cutoff_7days:
                    recent_7days += 1
            
            print(f"\n📊 日期分布统计:")
            print(f"   - 最近1天: {recent_1day} 篇")
            print(f"   - 最近3天: {recent_3days} 篇")
            print(f"   - 最近7天: {recent_7days} 篇")
            
            # 显示最新的几篇论文
            if entries:
                print(f"\n📝 最新论文样本:")
                for i, entry in enumerate(entries[:5], 1):
                    paper_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    print(f"\n{i}. {entry.title[:80]}...")
                    print(f"   更新时间: {paper_date.strftime('%Y-%m-%d %H:%M')} UTC")
                    print(f"   类别: {', '.join([tag.term for tag in entry.tags][:3])}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 日期过滤测试失败: {e}")
        return False

def main():
    print("🚀 开始ArXiv连接测试...")
    print("=" * 60)
    
    success1 = test_arxiv_connection()
    success2 = test_date_filtering()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ arXiv连接测试通过！")
        print("\n🎯 测试结果:")
        print("   - arXiv API连接正常")
        print("   - 论文抓取功能正常")
        print("   - 日期过滤功能正常")
        print("\n💡 接下来需要:")
        print("   - 设置OPENAI_API_KEY环境变量")
        print("   - 运行完整的调试脚本: python scripts/debug_fetch.py")
    else:
        print("❌ 测试发现问题，请检查网络连接")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 