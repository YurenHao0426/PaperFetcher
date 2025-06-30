#!/usr/bin/env python3
"""
Test Enhanced Social Good Filtering

This script tests the new prompt to ensure it properly filters out
pure technical CV bias and focuses on social good applications.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_papers import ArxivPaperFetcher, GPT_SYSTEM_PROMPT


def test_enhanced_filtering():
    """Test the enhanced prompt with social good focus"""
    
    print("🎯 Testing Enhanced Social Good Filtering")
    print("=" * 60)
    
    # Check API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("✅ OpenAI API key is set")
    print(f"\n📋 Enhanced prompt focus:")
    print("   - Social good applications (healthcare, education, justice)")
    print("   - Real-world impact on vulnerable populations")
    print("   - Excludes pure technical CV bias research")
    print("   - Focuses on societal implications")
    
    # Initialize fetcher
    fetcher = ArxivPaperFetcher(openai_api_key)
    
    # Test papers that SHOULD be accepted (social good relevance)
    positive_examples = [
        {
            "title": "Algorithmic Bias in Medical Diagnosis: Impact on Minority Patient Care",
            "abstract": "This study examines how AI diagnostic systems exhibit systematic bias against minority patients in hospital settings, leading to delayed treatment and worse health outcomes. We analyze bias in medical imaging and clinical decision support systems, proposing fairness interventions to ensure equitable healthcare delivery for underserved populations."
        },
        {
            "title": "Bias in Criminal Justice Risk Assessment Tools: Perpetuating Racial Inequality",
            "abstract": "We investigate how algorithmic risk assessment tools used in bail and sentencing decisions systematically discriminate against Black and Latino defendants. Our analysis reveals how these systems perpetuate existing inequalities in the justice system, harming vulnerable communities and undermining fair treatment under the law."
        },
        {
            "title": "Educational AI Systems and Socioeconomic Bias: Impact on Student Opportunities",
            "abstract": "This paper examines how AI-powered educational platforms exhibit bias against students from low-income backgrounds, affecting their access to advanced coursework and college recommendations. We demonstrate how algorithmic bias in education technology perpetuates inequality and limits social mobility."
        },
        {
            "title": "Hiring Algorithm Bias: Gender Discrimination in Recruitment AI",
            "abstract": "We analyze gender bias in AI-powered hiring systems used by Fortune 500 companies, showing systematic discrimination against women candidates. Our study reveals how biased algorithms perpetuate workplace inequality and violate equal employment opportunity principles, harming women's career advancement."
        },
        {
            "title": "Social Media Content Moderation: Bias Against LGBTQ+ Communities",
            "abstract": "This research demonstrates how AI content moderation systems disproportionately target and remove content from LGBTQ+ users, effectively silencing marginalized voices. We examine the social harm caused by biased algorithmic enforcement and its impact on community safety and free expression."
        }
    ]
    
    # Test papers that SHOULD be rejected (pure technical CV bias without social context)
    negative_examples = [
        {
            "title": "Mitigating Dataset Bias in Deep Convolutional Networks for ImageNet Classification",
            "abstract": "We propose a novel data augmentation technique to reduce dataset bias in deep convolutional neural networks trained on ImageNet. Our method improves classification accuracy by 3.2% through bias-aware sampling strategies and shows superior performance on standard computer vision benchmarks."
        },
        {
            "title": "Domain Adaptation for Robust Computer Vision Models: Addressing Covariate Shift",
            "abstract": "This paper presents a domain adaptation framework for computer vision models to handle distribution shift between training and test datasets. We demonstrate improved generalization on various vision tasks through adversarial training and achieve state-of-the-art results on adaptation benchmarks."
        },
        {
            "title": "Fairness Metrics for Multi-Class Classification: Technical Evaluation Framework",
            "abstract": "We introduce new mathematical fairness metrics for multi-class classification problems in machine learning. Our framework provides theoretical guarantees for algorithmic fairness and demonstrates computational efficiency on synthetic datasets. The proposed metrics outperform existing approaches in balanced accuracy."
        },
        {
            "title": "Bias Correction in Neural Network Training: Gradient Clipping Techniques",
            "abstract": "This work proposes improved gradient clipping methods to reduce training bias in deep neural networks. We show that our approach leads to faster convergence and better generalization on standard ML benchmarks. The method is evaluated on CIFAR-10, CIFAR-100, and synthetic datasets."
        },
        {
            "title": "Adversarial Training for Robust Feature Learning in Convolutional Networks",
            "abstract": "We develop adversarial training techniques to improve feature robustness in convolutional neural networks. Our method generates adversarial examples during training to enhance model generalization. Experiments on image classification tasks show improved robustness against various attack methods."
        }
    ]
    
    print(f"\n🧪 Testing with example papers...")
    
    # Test positive examples (should be accepted)
    print(f"\n✅ Testing papers that SHOULD be accepted (social good relevance):")
    positive_results = []
    for i, example in enumerate(positive_examples, 1):
        try:
            is_relevant = fetcher._check_paper_relevance(example)
            positive_results.append(is_relevant)
            status = "✅ CORRECT" if is_relevant else "❌ MISSED"
            print(f"   {i}. {status}: {example['title'][:60]}...")
        except Exception as e:
            print(f"   {i}. ⚠️ ERROR: {e}")
            positive_results.append(False)
    
    # Test negative examples (should be rejected)
    print(f"\n❌ Testing papers that SHOULD be rejected (pure technical bias):")
    negative_results = []
    for i, example in enumerate(negative_examples, 1):
        try:
            is_relevant = fetcher._check_paper_relevance(example)
            negative_results.append(not is_relevant)  # Expecting not relevant, so invert
            status = "✅ CORRECT" if not is_relevant else "❌ FALSE POSITIVE"
            print(f"   {i}. {status}: {example['title'][:60]}...")
        except Exception as e:
            print(f"   {i}. ⚠️ ERROR: {e}")
            negative_results.append(False)
    
    # Calculate accuracy
    print(f"\n📊 Filtering Performance:")
    positive_accuracy = sum(positive_results) / len(positive_results) * 100 if positive_results else 0
    negative_accuracy = sum(negative_results) / len(negative_results) * 100 if negative_results else 0
    overall_accuracy = (sum(positive_results) + sum(negative_results)) / (len(positive_results) + len(negative_results)) * 100
    
    print(f"   - Social good detection: {positive_accuracy:.1f}% ({sum(positive_results)}/{len(positive_results)})")
    print(f"   - Pure tech rejection: {negative_accuracy:.1f}% ({sum(negative_results)}/{len(negative_results)})")
    print(f"   - Overall accuracy: {overall_accuracy:.1f}%")
    
    # Evaluation
    print(f"\n🎯 Enhanced Filtering Assessment:")
    if overall_accuracy >= 80:
        print(f"   🎉 EXCELLENT! Enhanced filtering is working well")
        print(f"   ✅ Successfully focuses on social good applications")
        print(f"   ✅ Effectively filters out pure technical CV bias")
    elif overall_accuracy >= 60:
        print(f"   ✅ GOOD performance, minor improvements possible")
        if positive_accuracy < negative_accuracy:
            print(f"   💡 Suggestion: May need to strengthen social good detection")
        else:
            print(f"   💡 Suggestion: May need to better exclude technical bias")
    else:
        print(f"   ⚠️ NEEDS IMPROVEMENT - prompt may need refinement")
        if positive_accuracy < 50:
            print(f"   🔧 Issue: Not capturing enough social good papers")
        if negative_accuracy < 50:
            print(f"   🔧 Issue: Accepting too many pure technical papers")
    
    # Show improvement areas
    print(f"\n💡 Key improvements in enhanced prompt:")
    print(f"   ✅ Clear distinction between social good vs pure technical research")
    print(f"   ✅ Explicit exclusion criteria for technical CV bias")
    print(f"   ✅ Focus on real-world applications affecting people")
    print(f"   ✅ Emphasis on vulnerable populations and social justice")
    
    return overall_accuracy >= 80


def show_prompt_comparison():
    """Show the enhanced prompt focus"""
    
    print(f"\n" + "="*60)
    print("📝 Enhanced Prompt Key Features")
    print("="*60)
    
    print(f"\n✅ ACCEPTS papers with:")
    accepts = [
        "Real-world applications (healthcare, education, justice, hiring)",
        "Impact on marginalized/vulnerable populations",
        "Social implications and consequences of bias",
        "Bias auditing in systems affecting people's lives",
        "Ethical AI deployment addressing social justice",
        "Clear connection to social good and human welfare"
    ]
    
    for item in accepts:
        print(f"   ✅ {item}")
    
    print(f"\n❌ REJECTS papers with:")
    rejects = [
        "Pure technical computer vision without social context",
        "Generic ML fairness metrics without real-world application",
        "Theoretical bias research without societal implications",
        "Technical optimization without considering human impact",
        "Academic benchmarking without social good connection",
        "Algorithmic improvements without addressing social harm"
    ]
    
    for item in rejects:
        print(f"   ❌ {item}")
    
    print(f"\n🎯 Core principle:")
    print(f"   Research must clearly address how AI bias affects society,")
    print(f"   vulnerable populations, or social justice - not just technical metrics.")


if __name__ == "__main__":
    show_prompt_comparison()
    success = test_enhanced_filtering()
    
    print(f"\n✅ Enhanced filtering test completed!")
    if success:
        print(f"🎉 System ready for production with improved social good focus")
    else:
        print(f"⚠️ Consider running additional tests or prompt refinement") 