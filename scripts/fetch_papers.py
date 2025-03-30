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
    "cs.CY",  # Computers and Society
    "cs.HC",  # Human-Computer Interaction
    "cs.IR",  # Information Retrieval
    "cs.GL",  # General Literature
    "cs.SI",  # Social and Information Networks
    "stat.ML" # Stat.ML
]

def fetch_papers_wide_then_filter(days=1, keywords=None):
    """
    从 arXiv 中抓取过去 N 天内提交的所有论文（只限制时间 submittedDate），
    然后在本地过滤：
      1) 只保留 tags 中包含 ALLOWED_CATEGORIES（若论文有多分类，只要有任意一个符合就OK）
      2) 标题或摘要里包含指定关键词
    """
    if keywords is None:
        keywords = ["bias", "fairness"]

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_utc = now_utc - datetime.timedelta(days=days)

    start_str = start_utc.strftime("%Y%m%d%H%M")
    end_str = now_utc.strftime("%Y%m%d%H%M")
    print(f"[DEBUG] date range (UTC): {start_str} ~ {end_str} (past {days} days)")

    # 构造 search_query，仅用时间
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
        title = getattr(e, 'title', '')
        summary = getattr(e, 'summary', '')
        published = getattr(e, 'published', '')
        link = getattr(e, 'link', '')

        if hasattr(e, 'tags'):
            # e.tags: a list of objects with .term
            categories = [t.term for t in e.tags]
        else:
            categories = []

        # 1) 是否属于 ALLOWED_CATEGORIES
        #    有些论文有多分类，只要其中一个在 ALLOWED_CATEGORIES 里就OK
        #    例如 "cs.IR", "cs.AI"
        in_allowed_cat = any(cat in ALLOWED_CATEGORIES for cat in categories)
        if not in_allowed_cat:
            continue

        # 2) 是否含关键词
        text_lower = (title + " " + summary).lower()
        has_keyword = any(kw.lower() in text_lower for kw in keywords)
        if has_keyword:
            matched.append({
                "title": title,
                "published": published,
                "link": link,
                "categories": categories
            })

    print(f"[DEBUG] matched {len(matched)} papers after local filtering (categories + keywords)")
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
    # 1) 抓取过去3天, 关键词=["bias","fairness"]
    days = 3
    keywords = ["bias", "fairness"]
    papers = fetch_papers_wide_then_filter(days=days, keywords=keywords)
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
