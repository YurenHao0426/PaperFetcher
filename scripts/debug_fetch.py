#!/usr/bin/env python3
"""
调试脚本 - 详细显示论文抓取过程

这个脚本专门用于调试和诊断论文抓取系统，会显示每个步骤的详细信息，
帮助用户了解系统是否正常工作，以及在哪个环节可能出现问题。
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta

# 设置详细的调试日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Add the parent directory to the path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_papers import ArxivPaperFetcher


def debug_arxiv_connection():
    """调试arXiv连接"""
    print("🔍 测试arXiv API连接...")
    
    import requests
    import feedparser
    
    try:
        # 测试最基本的arXiv查询
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI",
            "sortBy": "submittedDate", 
            "sortOrder": "descending",
            "max_results": 5
        }
        
        print(f"📡 发送请求到: {url}")
        print(f"📋 查询参数: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        print(f"✅ HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            entries = feed.entries
            print(f"📄 获取到 {len(entries)} 篇论文")
            
            if entries:
                print(f"📝 第一篇论文示例:")
                entry = entries[0]
                print(f"   - 标题: {entry.title}")
                print(f"   - 发布时间: {entry.published}")
                print(f"   - 更新时间: {entry.updated}")
                print(f"   - 类别: {[tag.term for tag in entry.tags] if hasattr(entry, 'tags') else '无'}")
                print(f"   - 摘要长度: {len(entry.summary)} 字符")
                return True
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ arXiv连接测试失败: {e}")
        return False


def debug_openai_connection(api_key):
    """调试OpenAI连接"""
    print("\n🤖 测试OpenAI API连接...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # 测试一个简单的请求
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond with just the number 1."},
                {"role": "user", "content": "Test"}
            ],
            temperature=0,
            max_tokens=1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI API连接成功")
        print(f"📤 发送模型: gpt-4o")
        print(f"📨 API响应: '{result}'")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI连接测试失败: {e}")
        return False


def debug_paper_fetch():
    """调试论文抓取过程"""
    print("\n" + "="*60)
    print("🔍 ArXiv论文抓取系统调试")
    print("="*60)
    
    # 检查环境变量
    openai_api_key = os.getenv("OPENAI_API_KEY")
    print(f"🔑 OpenAI API Key: {'已设置' if openai_api_key else '❌ 未设置'}")
    
    if not openai_api_key:
        print("❌ 请设置OPENAI_API_KEY环境变量")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    # 测试API连接
    if not debug_arxiv_connection():
        return False
        
    if not debug_openai_connection(openai_api_key):
        return False
    
    # 测试论文抓取器
    print(f"\n📋 开始测试论文抓取器...")
    
    try:
        fetcher = ArxivPaperFetcher(openai_api_key)
        print("✅ 论文抓取器初始化成功")
        
        # 测试获取最近3天的论文（确保有一些结果）
        print(f"\n🕐 测试获取最近3天的论文...")
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=3)
        
        print(f"📅 时间范围: {start_date.date()} 到 {end_date.date()}")
        
        # 限制到20篇论文进行测试
        papers = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=20)
        
        print(f"\n📊 抓取结果分析:")
        print(f"   - 总共获取: {len(papers)} 篇论文")
        
        if papers:
            print(f"\n📄 论文样本 (前3篇):")
            for i, paper in enumerate(papers[:3], 1):
                print(f"\n   {i}. {paper['title']}")
                print(f"      发布时间: {paper['published']}")
                print(f"      类别: {', '.join(paper['categories'])}")
                print(f"      摘要长度: {len(paper['abstract'])} 字符")
            
            # 测试GPT过滤（只测试前5篇）
            print(f"\n🤖 测试GPT-4o过滤 (前5篇论文)...")
            sample_papers = papers[:5]
            filtered_papers = fetcher.filter_papers_with_gpt(sample_papers)
            
            print(f"\n🎯 过滤结果:")
            print(f"   - 输入论文: {len(sample_papers)} 篇")
            print(f"   - 相关论文: {len(filtered_papers)} 篇")
            print(f"   - 相关比例: {len(filtered_papers)/len(sample_papers)*100:.1f}%")
            
            if filtered_papers:
                print(f"\n✅ 发现相关论文:")
                for i, paper in enumerate(filtered_papers, 1):
                    print(f"   {i}. {paper['title']}")
            
            return True
        else:
            print("⚠️ 未获取到任何论文")
            print("可能的原因:")
            print("   - 最近3天内这些类别没有新论文")
            print("   - arXiv API响应延迟")
            print("   - 网络连接问题")
            return False
            
    except Exception as e:
        print(f"❌ 论文抓取测试失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print("🚀 开始ArXiv论文抓取系统调试...")
    
    success = debug_paper_fetch()
    
    print(f"\n" + "="*60)
    if success:
        print("✅ 调试完成！系统工作正常")
        print("\n🎯 接下来可以:")
        print("   - 运行 python scripts/fetch_papers.py 进行实际抓取")
        print("   - 运行 python scripts/test_daily_fetch.py 进行完整测试")
    else:
        print("❌ 调试发现问题，请检查上述错误信息")
        
    print("="*60) 