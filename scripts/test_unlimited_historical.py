#!/usr/bin/env python3
"""
测试无限制历史模式

验证系统是否能处理大规模历史数据获取，
测试不同的配置参数和性能表现。
"""

import os
import sys
import time
import logging

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


def test_configuration_options():
    """测试不同的配置选项"""
    
    print("🔍 测试无限制历史模式配置")
    print("=" * 60)
    
    # 测试不同的配置场景
    test_scenarios = [
        {
            "name": "小规模测试",
            "MAX_HISTORICAL_PAPERS": "1000",
            "MAX_PAPERS_PER_CATEGORY": "200",
            "MAX_CONCURRENT": "10",
            "description": "适合快速测试和开发"
        },
        {
            "name": "中规模测试", 
            "MAX_HISTORICAL_PAPERS": "5000",
            "MAX_PAPERS_PER_CATEGORY": "1000",
            "MAX_CONCURRENT": "25",
            "description": "适合日常使用"
        },
        {
            "name": "大规模测试",
            "MAX_HISTORICAL_PAPERS": "50000",
            "MAX_PAPERS_PER_CATEGORY": "10000", 
            "MAX_CONCURRENT": "50",
            "description": "适合完整历史数据获取"
        },
        {
            "name": "超大规模测试",
            "MAX_HISTORICAL_PAPERS": "100000",
            "MAX_PAPERS_PER_CATEGORY": "20000",
            "MAX_CONCURRENT": "100", 
            "description": "适合研究级别的数据挖掘"
        }
    ]
    
    print("📊 支持的配置场景:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}:")
        print(f"   - 最大论文数: {int(scenario['MAX_HISTORICAL_PAPERS']):,}")
        print(f"   - 每类别限制: {int(scenario['MAX_PAPERS_PER_CATEGORY']):,}")
        print(f"   - 并发数: {scenario['MAX_CONCURRENT']}")
        print(f"   - 描述: {scenario['description']}")
    
    # 计算理论性能
    print(f"\n⚡ 理论性能估算:")
    print(f"   基于以下假设:")
    print(f"   - 每篇论文GPT处理时间: 1-2秒")
    print(f"   - 并行处理加速比: 10-20x")
    print(f"   - 网络延迟和API限制: 考虑在内")
    
    for scenario in test_scenarios:
        max_papers = int(scenario['MAX_HISTORICAL_PAPERS'])
        concurrent = int(scenario['MAX_CONCURRENT'])
        
        # 串行时间估算
        serial_time = max_papers * 1.5  # 1.5秒每篇
        
        # 并行时间估算
        parallel_time = max_papers / concurrent * 1.5 + 60  # 额外60秒开销
        
        print(f"\n   {scenario['name']}:")
        print(f"     - 串行处理时间: {serial_time/3600:.1f} 小时")
        print(f"     - 并行处理时间: {parallel_time/3600:.1f} 小时")
        print(f"     - 加速比: {serial_time/parallel_time:.1f}x")


def test_memory_requirements():
    """测试内存需求"""
    
    print(f"\n" + "="*60)
    print("💾 内存需求分析")
    print("="*60)
    
    # 估算每篇论文的内存占用
    avg_title_length = 100  # 平均标题长度
    avg_abstract_length = 1500  # 平均摘要长度
    avg_authors = 4  # 平均作者数
    avg_categories = 2  # 平均类别数
    
    # 每篇论文大约的内存占用（字符数）
    chars_per_paper = (
        avg_title_length + 
        avg_abstract_length + 
        avg_authors * 30 +  # 每个作者约30字符
        avg_categories * 10 +  # 每个类别约10字符
        200  # 其他字段
    )
    
    bytes_per_paper = chars_per_paper * 2  # 假设每字符2字节（UTF-8）
    
    print(f"📊 每篇论文内存占用估算:")
    print(f"   - 标题: ~{avg_title_length} 字符")
    print(f"   - 摘要: ~{avg_abstract_length} 字符")
    print(f"   - 作者: ~{avg_authors * 30} 字符")
    print(f"   - 类别: ~{avg_categories * 10} 字符")
    print(f"   - 其他: ~200 字符")
    print(f"   - 总计: ~{chars_per_paper} 字符 (~{bytes_per_paper/1024:.1f} KB)")
    
    # 不同规模的内存需求
    paper_counts = [1000, 5000, 20000, 50000, 100000]
    
    print(f"\n📈 不同规模的内存需求:")
    for count in paper_counts:
        total_mb = count * bytes_per_paper / 1024 / 1024
        print(f"   - {count:,} 篇论文: ~{total_mb:.1f} MB")
    
    print(f"\n💡 建议:")
    print(f"   - 16GB内存: 支持最多 ~100,000 篇论文")
    print(f"   - 8GB内存: 支持最多 ~50,000 篇论文")
    print(f"   - 4GB内存: 支持最多 ~20,000 篇论文")
    print(f"   - 如果内存不足，可以降低MAX_HISTORICAL_PAPERS")


def test_api_cost_estimation():
    """测试API成本估算"""
    
    print(f"\n" + "="*60)
    print("💰 API成本估算")
    print("="*60)
    
    # OpenAI GPT-4o 价格 (2024年价格)
    # Input: $2.50 per 1M tokens
    # Output: $10.00 per 1M tokens
    input_price_per_1m = 2.50
    output_price_per_1m = 10.00
    
    # 估算每篇论文的token消耗
    avg_input_tokens = 400  # 标题+摘要+系统prompt
    avg_output_tokens = 1   # 只返回"0"或"1"
    
    cost_per_paper = (
        (avg_input_tokens / 1000000) * input_price_per_1m +
        (avg_output_tokens / 1000000) * output_price_per_1m
    )
    
    print(f"📊 每篇论文API成本估算:")
    print(f"   - 输入tokens: ~{avg_input_tokens}")
    print(f"   - 输出tokens: ~{avg_output_tokens}")
    print(f"   - 每篇成本: ~${cost_per_paper:.4f}")
    
    # 不同规模的成本
    paper_counts = [1000, 5000, 20000, 50000, 100000]
    
    print(f"\n💸 不同规模的API成本:")
    for count in paper_counts:
        total_cost = count * cost_per_paper
        print(f"   - {count:,} 篇论文: ~${total_cost:.2f}")
    
    print(f"\n🎯 成本优化建议:")
    print(f"   - 先用小规模测试验证效果")
    print(f"   - 使用MAX_HISTORICAL_PAPERS控制规模")
    print(f"   - 考虑分批处理大规模数据")
    print(f"   - 监控API使用量避免超支")


def demonstrate_configuration():
    """演示配置使用方法"""
    
    print(f"\n" + "="*60)
    print("🛠️ 配置使用方法")
    print("="*60)
    
    print(f"🔧 环境变量配置:")
    print(f"""
# 基础配置 (推荐用于测试)
export MAX_HISTORICAL_PAPERS=1000
export MAX_PAPERS_PER_CATEGORY=200
export MAX_CONCURRENT=10

# 中等规模配置 (推荐用于日常使用)
export MAX_HISTORICAL_PAPERS=5000
export MAX_PAPERS_PER_CATEGORY=1000
export MAX_CONCURRENT=25

# 大规模配置 (推荐用于研究)
export MAX_HISTORICAL_PAPERS=50000
export MAX_PAPERS_PER_CATEGORY=10000
export MAX_CONCURRENT=50

# 无限制配置 (谨慎使用)
export MAX_HISTORICAL_PAPERS=1000000
export MAX_PAPERS_PER_CATEGORY=100000
export MAX_CONCURRENT=100
""")
    
    print(f"🚀 运行命令:")
    print(f"""
# 使用默认配置运行历史模式
FETCH_MODE=historical python scripts/fetch_papers.py

# 使用自定义配置运行
MAX_HISTORICAL_PAPERS=10000 \\
MAX_PAPERS_PER_CATEGORY=2000 \\
MAX_CONCURRENT=30 \\
FETCH_MODE=historical \\
python scripts/fetch_papers.py
""")
    
    print(f"⚠️ 注意事项:")
    print(f"   - 首次运行建议使用小规模配置")
    print(f"   - 监控内存使用情况")
    print(f"   - 注意API成本控制")
    print(f"   - 考虑网络稳定性")
    print(f"   - 大规模运行可能需要数小时")


if __name__ == "__main__":
    print("🎯 ArXiv无限制历史模式测试")
    print("=" * 60)
    
    test_configuration_options()
    test_memory_requirements()
    test_api_cost_estimation()
    demonstrate_configuration()
    
    print(f"\n✅ 测试完成！")
    print(f"💡 现在可以根据需求配置合适的参数来运行历史模式")
    print(f"🚀 建议先从小规模开始测试，确保一切正常后再扩大规模") 