#!/usr/bin/env python3
"""
测试Social Good导向的prompt

验证新的prompt是否能正确识别社会影响相关的偏见研究，
包括各种应用领域如医疗、教育、司法等。
"""

import os
import sys
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

from scripts.fetch_papers import ArxivPaperFetcher, GPT_SYSTEM_PROMPT


def test_prompt_with_examples():
    """使用示例论文测试新的prompt"""
    
    print("🔍 测试Social Good导向的prompt")
    print("=" * 60)
    
    # 检查API密钥
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ 请设置OPENAI_API_KEY环境变量")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("✅ OpenAI API密钥已设置")
    print(f"\n📋 当前prompt概要:")
    print("   - 专注于社会影响的AI偏见研究")
    print("   - 涵盖医疗、教育、司法、招聘等应用领域")
    print("   - 关注弱势群体和社会公正")
    
    # 初始化fetcher
    fetcher = ArxivPaperFetcher(openai_api_key)
    
    # 测试用例：应该被识别为相关的论文
    positive_examples = [
        {
            "title": "Algorithmic Bias in Healthcare AI: Impact on Minority Populations",
            "abstract": "This study examines how machine learning models used in healthcare decision-making exhibit systematic bias against racial minorities, leading to disparate treatment outcomes. We analyze bias in diagnostic algorithms and propose mitigation strategies to ensure equitable healthcare delivery."
        },
        {
            "title": "Fairness in Hiring: Bias Detection in Resume Screening AI",
            "abstract": "We investigate gender and racial bias in AI-powered resume screening systems used by major corporations. Our analysis reveals significant discrimination patterns and proposes fairness-aware algorithms to promote equal employment opportunities."
        },
        {
            "title": "Criminal Justice AI: Bias in Recidivism Prediction Systems",
            "abstract": "This paper analyzes bias in algorithmic risk assessment tools used in criminal justice, showing how these systems perpetuate racial disparities in sentencing and parole decisions. We propose bias auditing frameworks for judicial AI systems."
        },
        {
            "title": "Educational Equity: Bias in AI-Powered Learning Platforms",
            "abstract": "We examine how bias in educational AI systems affects learning outcomes for students from different socioeconomic backgrounds, identifying disparities in recommendation algorithms and assessment tools that impact educational equity."
        },
        {
            "title": "Social Media Content Moderation: Bias Against Marginalized Communities",
            "abstract": "This study reveals how AI content moderation systems disproportionately flag and remove content from LGBTQ+ and minority communities, examining the social impact of biased algorithmic enforcement on free expression and community safety."
        }
    ]
    
    # 测试用例：应该被识别为不相关的论文
    negative_examples = [
        {
            "title": "Optimizing Deep Neural Network Architecture for Image Classification",
            "abstract": "We propose a novel neural network architecture that achieves state-of-the-art performance on ImageNet classification tasks. Our method introduces efficient attention mechanisms and demonstrates superior accuracy on standard benchmarks."
        },
        {
            "title": "Quantum Computing Algorithms for Optimization Problems",
            "abstract": "This paper presents quantum algorithms for solving complex optimization problems, demonstrating computational advantages over classical approaches. We analyze quantum circuit design and error correction techniques."
        },
        {
            "title": "Blockchain Technology for Supply Chain Management",
            "abstract": "We develop a blockchain-based framework for transparent supply chain tracking, improving traceability and reducing fraud in manufacturing and logistics. The system demonstrates scalability and security benefits."
        },
        {
            "title": "5G Network Performance Optimization Using Machine Learning",
            "abstract": "This study applies machine learning techniques to optimize 5G network performance, improving bandwidth allocation and reducing latency. We propose adaptive algorithms for network resource management."
        }
    ]
    
    print(f"\n🧪 开始测试...")
    
    # 测试正面例子
    print(f"\n✅ 测试应该识别为相关的论文:")
    positive_results = []
    for i, example in enumerate(positive_examples, 1):
        try:
            is_relevant = fetcher._check_paper_relevance(example)
            positive_results.append(is_relevant)
            status = "✅ 正确" if is_relevant else "❌ 错误"
            print(f"   {i}. {status}: {example['title'][:50]}...")
        except Exception as e:
            print(f"   {i}. ⚠️ 错误: {e}")
            positive_results.append(False)
    
    # 测试负面例子
    print(f"\n❌ 测试应该识别为不相关的论文:")
    negative_results = []
    for i, example in enumerate(negative_examples, 1):
        try:
            is_relevant = fetcher._check_paper_relevance(example)
            negative_results.append(not is_relevant)  # 期望不相关，所以取反
            status = "✅ 正确" if not is_relevant else "❌ 错误"
            print(f"   {i}. {status}: {example['title'][:50]}...")
        except Exception as e:
            print(f"   {i}. ⚠️ 错误: {e}")
            negative_results.append(False)
    
    # 计算准确率
    print(f"\n📊 测试结果统计:")
    positive_accuracy = sum(positive_results) / len(positive_results) * 100
    negative_accuracy = sum(negative_results) / len(negative_results) * 100
    overall_accuracy = (sum(positive_results) + sum(negative_results)) / (len(positive_results) + len(negative_results)) * 100
    
    print(f"   - 正面例子准确率: {positive_accuracy:.1f}% ({sum(positive_results)}/{len(positive_results)})")
    print(f"   - 负面例子准确率: {negative_accuracy:.1f}% ({sum(negative_results)}/{len(negative_results)})")
    print(f"   - 总体准确率: {overall_accuracy:.1f}%")
    
    # 评估结果
    print(f"\n🎯 prompt评估:")
    if overall_accuracy >= 80:
        print(f"   🎉 excellent! prompt表现优秀")
    elif overall_accuracy >= 60:
        print(f"   ✅ 良好，prompt表现不错")
    else:
        print(f"   ⚠️ 需要改进，prompt可能需要调整")
    
    # 显示具体的改进点
    if positive_accuracy < 80:
        print(f"   💡 建议: 可能需要强化对Social Good应用场景的识别")
    if negative_accuracy < 80:
        print(f"   💡 建议: 可能需要更明确地排除纯技术性研究")


def display_new_prompt():
    """显示新的prompt内容"""
    
    print(f"\n" + "="*60)
    print("📖 新的Social Good导向prompt")
    print("="*60)
    
    print(f"\n🎯 主要变化:")
    print("   - 从专注LLM偏见 → 扩展到所有AI社会影响")
    print("   - 增加了具体应用领域 (医疗、教育、司法等)")
    print("   - 强调对弱势群体和社会公正的关注")
    print("   - 明确排除纯技术性研究")
    
    print(f"\n📋 新的识别标准:")
    domains = [
        "医疗AI中的偏见",
        "教育技术的公平性",
        "司法算法的歧视",
        "招聘AI的偏见",
        "金融AI的公平性",
        "推荐系统的偏见",
        "内容审核的偏见",
        "数据集的代表性",
        "AI系统的包容性",
        "算法审计和评估"
    ]
    
    for domain in domains:
        print(f"   ✅ {domain}")
    
    print(f"\n🎯 关注重点:")
    print("   - 社会影响和社会公正")
    print("   - 弱势群体和边缘化社区")
    print("   - 实际应用中的公平性")
    print("   - 系统性偏见的社会后果")


if __name__ == "__main__":
    display_new_prompt()
    test_prompt_with_examples() 