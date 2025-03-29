import os
import requests
import feedparser
import datetime
from github import Github

ARXIV_CATEGORIES = "cs.CL OR cs.AI OR stat.ML"
KEYWORDS = ["LLM bias", "debias", "fairness", "equity", "inclusivity", "diversity", "ethical AI", "responsible AI"]

TARGET_REPO_TOKEN = os.getenv("TARGET_REPO_TOKEN")
TARGET_REPO_NAME = os.getenv("TARGET_REPO_NAME")

def fetch_arxiv_papers():
    """
    从arXiv获取过去24小时的新论文
    """
    base_url = "http://export.arxiv.org/api/query"
    # 使用带时区的UTC时间
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    yesterday_utc = now_utc - datetime.timedelta(days=1)

    params = {
        "search_query": f"cat:{ARXIV_CATEGORIES}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 100
    }
    r = requests.get(base_url, params=params)
    feed = feedparser.parse(r.content)

    papers = []
    for entry in feed.entries:
        # entry.published 形如 "2025-03-28T10:05:24Z"
        # 先解析出一个 naive datetime
        published_naive = datetime.datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
        # 再为它添加UTC时区，使其成为 aware datetime
        published_utc = published_naive.replace(tzinfo=datetime.timezone.utc)

        if published_utc > yesterday_utc:
            papers.append({
                "title": entry.title,
                "url": entry.link,
                "abstract": entry.summary
            })
    return papers

def filter_papers(papers):
    relevant = []
    for p in papers:
        abstract_lower = p["abstract"].lower()
        title_lower = p["title"].lower()
        if any(kw.lower() in abstract_lower or kw.lower() in title_lower for kw in KEYWORDS):
            relevant.append(p)
    return relevant

def update_readme_in_target(relevant_papers):
    if not relevant_papers:
        print("No relevant papers found. Skipping README update.")
        return

    g = Github(TARGET_REPO_TOKEN)
    repo = g.get_repo(TARGET_REPO_NAME)

    readme_file = repo.get_contents("README.md", ref="main")
    readme_content = readme_file.decoded_content.decode("utf-8")

    # 此处同样可以用带时区的时间来记录日期（格式化字符串不影响）
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    new_section = f"\n\n### {date_str}\n"
    for p in relevant_papers:
        new_section += f"- **[{p['title']}]({p['url']})**\n"

    updated_content = readme_content + new_section

    repo.update_file(
        path="README.md",
        message=f"Auto Update README with {len(relevant_papers)} papers ({date_str})",
        content=updated_content,
        sha=readme_file.sha,
        branch="main"
    )

def main():
    papers = fetch_arxiv_papers()
    relevant_papers = filter_papers(papers)
    update_readme_in_target(relevant_papers)

if __name__ == "__main__":
    main()
