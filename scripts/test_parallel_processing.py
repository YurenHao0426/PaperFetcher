#!/usr/bin/env python3
"""
测试并行化OpenAI请求处理

比较串行处理和并行处理的性能差异，展示加速效果。
"""

import os
import sys
import time
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


def test_parallel_performance():
    """测试并行处理性能"""
    
    print("🚀 测试OpenAI请求并行化性能")
    print("=" * 60)
    
    # 检查API密钥
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ 请设置OPENAI_API_KEY环境变量")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("✅ OpenAI API密钥已设置")
    
    try:
        # 初始化fetcher
        fetcher = ArxivPaperFetcher(openai_api_key)
        
        # 获取一些论文作为测试数据
        print("\n📋 获取测试数据...")
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        all_papers = fetcher.fetch_papers_by_date_range(start_date, end_date, max_papers=100)
        
        if len(all_papers) < 10:
            print(f"⚠️ 只获取到 {len(all_papers)} 篇论文，可能不足以展示并行效果")
            if len(all_papers) < 5:
                print("❌ 论文数量太少，无法进行有效测试")
                return
        
        # 选择测试子集（避免API费用过高）
        test_papers = all_papers[:min(20, len(all_papers))]  # 最多测试20篇论文
        print(f"📝 将测试 {len(test_papers)} 篇论文")
        
        print(f"\n📋 测试论文样本:")
        for i, paper in enumerate(test_papers[:3], 1):
            print(f"   {i}. {paper['title'][:60]}...")
        
        if len(test_papers) > 3:
            print(f"   ... 还有 {len(test_papers) - 3} 篇论文")
        
        # 测试1: 串行处理
        print(f"\n" + "="*60)
        print("🔄 测试1: 串行处理")
        print("="*60)
        
        start_time = time.time()
        serial_results = fetcher.filter_papers_with_gpt(
            test_papers.copy(), 
            use_parallel=False
        )
        serial_time = time.time() - start_time
        
        print(f"🔄 串行处理结果:")
        print(f"   - 处理时间: {serial_time:.1f} 秒")
        print(f"   - 平均每篇: {serial_time/len(test_papers):.2f} 秒")
        print(f"   - 相关论文: {len(serial_results)} 篇")
        
        # 测试2: 并行处理（低并发）
        print(f"\n" + "="*60)
        print("🚀 测试2: 并行处理 (并发=5)")
        print("="*60)
        
        start_time = time.time()
        parallel_results_5 = fetcher.filter_papers_with_gpt(
            test_papers.copy(), 
            use_parallel=True,
            max_concurrent=5
        )
        parallel_time_5 = time.time() - start_time
        
        print(f"🚀 并行处理结果 (并发=5):")
        print(f"   - 处理时间: {parallel_time_5:.1f} 秒")
        print(f"   - 平均每篇: {parallel_time_5/len(test_papers):.2f} 秒")
        print(f"   - 相关论文: {len(parallel_results_5)} 篇")
        print(f"   - 加速比: {serial_time/parallel_time_5:.1f}x")
        
        # 测试3: 并行处理（高并发）
        print(f"\n" + "="*60)
        print("🚀 测试3: 并行处理 (并发=10)")
        print("="*60)
        
        start_time = time.time()
        parallel_results_10 = fetcher.filter_papers_with_gpt(
            test_papers.copy(), 
            use_parallel=True,
            max_concurrent=10
        )
        parallel_time_10 = time.time() - start_time
        
        print(f"🚀 并行处理结果 (并发=10):")
        print(f"   - 处理时间: {parallel_time_10:.1f} 秒")
        print(f"   - 平均每篇: {parallel_time_10/len(test_papers):.2f} 秒")
        print(f"   - 相关论文: {len(parallel_results_10)} 篇")
        print(f"   - 加速比: {serial_time/parallel_time_10:.1f}x")
        
        # 验证结果一致性
        print(f"\n" + "="*60)
        print("🔍 结果一致性验证")
        print("="*60)
        
        # 获取相关论文的ID
        serial_ids = set(paper['arxiv_id'] for paper in serial_results)
        parallel_ids_5 = set(paper['arxiv_id'] for paper in parallel_results_5)
        parallel_ids_10 = set(paper['arxiv_id'] for paper in parallel_results_10)
        
        print(f"📊 结果对比:")
        print(f"   - 串行结果: {len(serial_ids)} 篇相关论文")
        print(f"   - 并行结果(5): {len(parallel_ids_5)} 篇相关论文")
        print(f"   - 并行结果(10): {len(parallel_ids_10)} 篇相关论文")
        
        # 检查一致性
        consistency_5 = len(serial_ids.symmetric_difference(parallel_ids_5))
        consistency_10 = len(serial_ids.symmetric_difference(parallel_ids_10))
        
        print(f"📋 一致性检查:")
        if consistency_5 == 0:
            print(f"   ✅ 串行 vs 并行(5): 结果完全一致")
        else:
            print(f"   ⚠️ 串行 vs 并行(5): {consistency_5} 篇论文结果不同")
            
        if consistency_10 == 0:
            print(f"   ✅ 串行 vs 并行(10): 结果完全一致")
        else:
            print(f"   ⚠️ 串行 vs 并行(10): {consistency_10} 篇论文结果不同")
        
        # 最终总结
        print(f"\n" + "="*60)
        print("📊 性能测试总结")
        print("="*60)
        
        print(f"📈 处理时间对比:")
        print(f"   - 串行处理:     {serial_time:6.1f} 秒")
        print(f"   - 并行处理(5):  {parallel_time_5:6.1f} 秒 ({serial_time/parallel_time_5:.1f}x 加速)")
        print(f"   - 并行处理(10): {parallel_time_10:6.1f} 秒 ({serial_time/parallel_time_10:.1f}x 加速)")
        
        # 计算理论最大加速
        theoretical_speedup = min(len(test_papers), 10)  # 理论上最大加速等于并发数或论文数
        actual_speedup = serial_time / parallel_time_10
        efficiency = (actual_speedup / theoretical_speedup) * 100
        
        print(f"\n💡 性能分析:")
        print(f"   - 理论最大加速: {theoretical_speedup}x")
        print(f"   - 实际最大加速: {actual_speedup:.1f}x")
        print(f"   - 并行效率: {efficiency:.1f}%")
        
        if actual_speedup > 3:
            print(f"   🎉 并行化效果excellent!")
        elif actual_speedup > 2:
            print(f"   ✅ 并行化效果良好!")
        else:
            print(f"   ⚠️ 并行化效果一般，可能受网络延迟影响")
        
        print(f"\n💰 成本估算:")
        total_requests = len(test_papers) * 3  # 3次测试
        estimated_cost = total_requests * 0.0001  # 估算每次请求成本
        print(f"   - 总API调用: {total_requests} 次")
        print(f"   - 估算成本: ${estimated_cost:.4f}")
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


def demo_usage():
    """演示如何使用并行功能"""
    
    print(f"\n" + "="*60)
    print("📖 使用方法说明")
    print("="*60)
    
    print("🔧 环境变量控制:")
    print("   USE_PARALLEL=true/false     # 是否启用并行处理")
    print("   MAX_CONCURRENT=16           # 最大并发请求数")
    
    print("\n💡 使用示例:")
    print("   # 默认并行处理")
    print("   python scripts/fetch_papers.py")
    print("")
    print("   # 关闭并行处理")
    print("   USE_PARALLEL=false python scripts/fetch_papers.py")
    print("")
    print("   # 自定义并发数")
    print("   MAX_CONCURRENT=25 python scripts/fetch_papers.py")
    print("")
    print("   # 历史模式高并发")
    print("   FETCH_MODE=historical MAX_CONCURRENT=40 python scripts/fetch_papers.py")
    
    print("\n⚠️ 注意事项:")
    print("   - 并发数过高可能触发OpenAI速率限制")
    print("   - 建议日常模式并发≤20，历史模式并发≤30")
    print("   - 网络不稳定时建议降低并发数")
    print("   - 并行处理会增加API调用成本（同时间内更多请求）")


if __name__ == "__main__":
    test_parallel_performance()
    demo_usage() 