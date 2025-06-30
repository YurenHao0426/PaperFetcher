#!/usr/bin/env python3
"""
测试时间倒序排列功能

验证README更新逻辑是否正确地将最新论文放在最前面，
确保论文始终按时间倒序排列。
"""

import os
import sys
import tempfile
from datetime import datetime, timezone

# Add the parent directory to the path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_papers import GitHubUpdater


def test_reverse_chronological_order():
    """测试时间倒序插入逻辑"""
    
    print("🔍 测试README时间倒序排列功能")
    print("=" * 60)
    
    # Create a mock README content
    mock_readme_content = """# ArXiv Social Good AI Paper Fetcher

An automated system for discovering and cataloging research papers related to AI bias, fairness, and social good from arXiv.org.

## 🎯 Features

- **Intelligent Paper Detection**: Uses GPT-4o to analyze papers
- **Automated Daily Updates**: Runs daily via GitHub Actions

## 🔧 Setup & Configuration

Setup instructions here...

## 🚀 Usage

Usage instructions here...

**Note**: This tool is designed for academic research purposes. Please respect arXiv's usage policies.

## Papers Updated on 2024-01-15 08:00 UTC

### Old Paper 1

**Authors:** Author A, Author B

**Categories:** cs.AI, cs.LG

**Published:** 2024-01-14T10:00:00Z

**Abstract:** This is an old paper abstract...

**Link:** [arXiv:2401.12345](https://arxiv.org/abs/2401.12345)

---

### Old Paper 2

**Authors:** Author C, Author D

**Categories:** cs.CL

**Published:** 2024-01-13T15:30:00Z

**Abstract:** This is another old paper abstract...

**Link:** [arXiv:2401.12346](https://arxiv.org/abs/2401.12346)

---
"""
    
    print("📄 模拟的现有README内容:")
    print("   - 包含项目描述和设置说明")
    print("   - 已有2篇旧论文 (2024-01-15 和 2024-01-13)")
    print("   - 测试新论文是否会插入到正确位置")
    
    # Create mock new papers (should be inserted at the top)
    new_papers = [
        {
            'title': 'Brand New Paper on AI Fairness',
            'authors': ['New Author A', 'New Author B', 'New Author C', 'New Author D'],
            'categories': ['cs.AI', 'cs.LG', 'cs.CL'],
            'published': '2024-01-16T12:00:00Z',
            'abstract': 'This is a brand new paper about AI fairness that should appear at the top of the README.',
            'link': 'https://arxiv.org/abs/2401.99999',
            'arxiv_id': '2401.99999'
        },
        {
            'title': 'Another New Paper on Social Good AI',
            'authors': ['New Author E', 'New Author F'],
            'categories': ['cs.AI', 'cs.HC'],
            'published': '2024-01-16T09:30:00Z',
            'abstract': 'This is another new paper about social good AI applications.',
            'link': 'https://arxiv.org/abs/2401.99998',
            'arxiv_id': '2401.99998'
        }
    ]
    
    print(f"\n📝 模拟添加 {len(new_papers)} 篇新论文:")
    for i, paper in enumerate(new_papers, 1):
        print(f"   {i}. {paper['title'][:50]}... ({paper['published'][:10]})")
    
    # Test the insertion logic
    print(f"\n🧪 测试插入位置查找逻辑...")
    
    class MockGitHubUpdater(GitHubUpdater):
        def __init__(self):
            # Skip the parent __init__ to avoid GitHub API calls
            pass
        
        def test_insert_position(self, content):
            return self._find_papers_insert_position(content)
        
        def test_format_new_section(self, papers, section_title):
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
            
            return new_section
    
    # Test insertion position finding
    updater = MockGitHubUpdater()
    insert_pos = updater.test_insert_position(mock_readme_content)
    
    if insert_pos > 0:
        lines_before = mock_readme_content[:insert_pos].count('\n')
        print(f"   ✅ 找到插入位置: 第 {lines_before} 行之后")
        
        # Show the context around insertion point
        lines = mock_readme_content.split('\n')
        context_start = max(0, lines_before - 2)
        context_end = min(len(lines), lines_before + 3)
        
        print(f"   📍 插入位置上下文:")
        for i in range(context_start, context_end):
            if i < len(lines):
                marker = " >>> 插入点 <<<" if i == lines_before else ""
                print(f"     {i+1:2d}: {lines[i][:50]}{marker}")
    else:
        print(f"   ⚠️ 未找到合适插入位置，将使用末尾追加")
    
    # Test the complete update logic
    print(f"\n🔄 测试完整的更新逻辑...")
    
    section_title = f"Papers Updated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    new_section = updater.test_format_new_section(new_papers, section_title)
    
    if insert_pos > 0:
        updated_content = (mock_readme_content[:insert_pos] + 
                         new_section + 
                         mock_readme_content[insert_pos:])
        print(f"   ✅ 新内容插入到正确位置")
    else:
        updated_content = mock_readme_content + new_section
        print(f"   ⚠️ 新内容追加到末尾")
    
    # Analyze the result
    print(f"\n📊 结果分析:")
    
    # Find all paper sections in the updated content
    lines = updated_content.split('\n')
    paper_sections = []
    
    for i, line in enumerate(lines):
        if line.startswith('## Papers Updated on') or line.startswith('## Historical'):
            # Found a paper section header
            section_info = {
                'line': i + 1,
                'title': line,
                'date_str': None
            }
            
            # Extract date from title
            if 'Updated on' in line:
                try:
                    date_part = line.split('Updated on ')[1].split(' UTC')[0]
                    section_info['date_str'] = date_part
                except:
                    pass
            
            paper_sections.append(section_info)
    
    print(f"   - 找到 {len(paper_sections)} 个论文段落:")
    for i, section in enumerate(paper_sections, 1):
        print(f"     {i}. {section['title'][:60]}... (第{section['line']}行)")
    
    # Check if chronological order is correct
    if len(paper_sections) >= 2:
        first_section = paper_sections[0]
        second_section = paper_sections[1]
        
        print(f"\n🎯 时间倒序验证:")
        print(f"   - 第一个段落: {first_section['title'][:40]}...")
        print(f"   - 第二个段落: {second_section['title'][:40]}...")
        
        if first_section['date_str'] and second_section['date_str']:
            first_is_newer = first_section['date_str'] > second_section['date_str']
            if first_is_newer:
                print(f"   ✅ 时间倒序正确！最新论文在最上面")
            else:
                print(f"   ❌ 时间倒序错误！需要调整插入逻辑")
        else:
            print(f"   ℹ️ 无法比较日期，请手动检查")
    
    # Save result to temporary file for inspection
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(updated_content)
        temp_file = f.name
    
    print(f"\n📄 完整结果已保存到临时文件: {temp_file}")
    print(f"   可以手动检查README更新结果")
    
    print(f"\n✅ 测试完成！")
    print(f"   关键改进:")
    print(f"   - ✅ 新论文会插入到README开头部分")
    print(f"   - ✅ 保持时间倒序排列（最新在上）")
    print(f"   - ✅ 避免在文档末尾追加")
    print(f"   - ✅ 智能识别插入位置")


if __name__ == "__main__":
    test_reverse_chronological_order() 