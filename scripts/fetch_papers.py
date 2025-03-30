import os
import requests
import feedparser
import datetime
from github import Github

# 你想要的分类列表
ALLOWED_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.CL",  # Computation and Language
    "cs.CV",  # Computer Vision and Pattern Recognition
    "cs.LG",  # Machine Learning
    "cs.NE",  # Neural and Evolutionary Computing
    "cs.RO",  # Robotics
    "cs.IR",  # Information Retrieval
    "stat.ML" # Stat.ML
]

def advanced_filter(entry):
    """
    判断一篇论文是否含有正面关键词组合（bias/fairness + LLM/transformer/GPT等），
    且不包含负面关键词（统计、物理、电路等）。
    """
    import re

    # 减少重复处理，先统一转小写
    title = getattr(entry, 'title', '').lower()
    summary = getattr(entry, 'summary', '').lower()
    full_text = title + " " + summary

    # 1) 正面关键词
    #    - 必须含有 "bias" 或 "fairness"（泛泛概念）
    #    - 且含有至少一个模型相关关键词
    general_terms = ["bias", "fairness"]
    model_terms = ["llm", "language model", "transformer", "gpt", "nlp",
                   "pretrained", "embedding", "generation", "alignment", "ai"]

    # 2) 负面关键词（排除统计、物理、电路等无关方向）
    negative_terms = [
        "estimation", "variance", "statistical", "sample", "sensor", "circuit",
        "quantum", "physics", "electronics", "hardware", "transistor", "amplifier"
    ]

    # 检查正面关键词
    has_general = any(term in full_text for term in general_terms)
    has_model   = any(term in full_text for term in model_terms)

    # 检查负面关键词（命中则排除）
    has_negative = any(term in full_text for term in negative_terms)

    # 只有同时满足“general + model”并且“无负面”才返回True
    return (has_general and has_model) and (not has_negative)


def fetch_papers_wide_then_filter(days=1):
    """
    从 arXiv 中抓取过去 N 天内提交的所有论文（限制时间），然后在本地过滤：
      1) 只保留 tags 中包含 ALLOWED_CATEGORIES（若论文有多分类，只要有任意一个符合就OK）
      2) 用 advanced_filter() 检查标题或摘要是否满足要求
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_utc = now_utc - datetime.timedelta(days=days)

    start_str = start_utc.strftime("%Y%m%d%H%M")
    end_str = now_utc.strftime("%Y%m%d%H%M")
    print(f"[DEBUG] date range (UTC): {start_str} ~ {end_str} (past {days} days)")

    # 构造搜索query，仅用时间
    search_query = f"submittedDate:[{start_str} TO {end_str}]"

    base_url = "http://export.arxiv.org/api/query"
    step = 100
    start = 0
    all_entries = []

    while True:
        params = {
            "search_query": search_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": start,
            "max_results": step
        }
        print(f"[DEBUG] fetching: {start} -> {start+step}")
        resp = requests.get(base_url, params=params)
        if resp.status_code != 200:
            print("[ERROR] HTTP Status:", resp.status_code)
            break

        feed = feedparser.parse(resp.content)
        batch = feed.entries
        got_count = len(batch)
        print(f"[DEBUG] got {got_count} entries in this batch")
        if got_count == 0:
            # 没有更多了
            break

        all_entries.extend(batch)
        start += step

        # 安全上限
        if start >= 3000:
            print("[DEBUG] reached 3000, stop.")
            break

    print(f"[DEBUG] total retrieved in date range: {len(all_entries)}")

    # -- 本地过滤 --
    matched = []
    for e in all_entries:
        if hasattr(e, 'tags'):
            # e.tags: a list of objects with .term
            categories = [t.term for t in e.tags]
        else:
            categories = []

        # 1) 是否属于 ALLOWED_CATEGORIES
        in_allowed_cat = any(cat in ALLOWED_CATEGORIES for cat in categories)
        if not in_allowed_cat:
            continue

        # 2) 更精准的组合式关键词筛选
        if advanced_filter(e):
            matched.append({
                "title": e.title,
                "published": e.published,
                "link": e.link,
                "categories": categories
            })

    print(f"[DEBUG] matched {len(matched)} papers after local filtering (categories + advanced_filter)")
    return matched

def update_readme_in_repo(papers, token, repo_name):
    """
    将匹配到的论文列表追加到目标repo的 README.md (main分支)
    """
    if not papers:
        print("[INFO] No matched papers, skip README update.")
        return

    g = Github(token)
    repo = g.get_repo(repo_name)

    # 读取现有 README
    readme_file = repo.get_contents("README.md", ref="main")
    old_content = readme_file.decoded_content.decode("utf-8")

    now_utc_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_section = f"\n\n### Auto-captured papers on {now_utc_str}\n"
    for p in papers:
        cat_str = ", ".join(p["categories"])
        new_section += f"- **{p['title']}** (Published={p['published']})  \n"
        new_section += f"  - Categories: {cat_str}  \n"
        new_section += f"  - Link: {p['link']}\n\n"

    updated_content = old_content + new_section
    commit_msg = f"Auto update README with {len(papers)} new papers"

    repo.update_file(
        path="README.md",
        message=commit_msg,
        content=updated_content,
        sha=readme_file.sha,
        branch="main"
    )
    print(f"[INFO] README updated with {len(papers)} papers.")

def main():
    # 1) 抓取过去1天
    days = 1
    papers = fetch_papers_wide_then_filter(days=days)
    print(f"\n[RESULT] matched {len(papers)} papers. Will update README if not empty.")

    # 2) 更新README
    github_token = os.getenv("TARGET_REPO_TOKEN")
    target_repo_name = os.getenv("TARGET_REPO_NAME")

    if not github_token or not target_repo_name:
        print("[ERROR] Missing environment variables: TARGET_REPO_TOKEN / TARGET_REPO_NAME.")
        return

    if papers:
        update_readme_in_repo(papers, github_token, target_repo_name)
    else:
        print("[INFO] No matched papers, done without update.")

if __name__ == "__main__":
    main()
