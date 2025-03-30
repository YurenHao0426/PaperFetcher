import os
import requests
import feedparser
import datetime
from github import Github

def fetch_papers_wide_then_filter(days=1, keywords=None):
    """
    抓过去 N 天的论文(只限制 submittedDate)，然后本地判断:
     - 是否 cs.* 或 stat.*
     - 标题/摘要是否含 keywords
    返回一个列表，每个元素是字典:
      { 'title':..., 'published':..., 'link':..., 'categories':[...] }
    """
    if keywords is None:
        keywords = ["bias", "fairness"]

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_utc = now_utc - datetime.timedelta(days=days)

    start_str = start_utc.strftime("%Y%m%d%H%M")
    end_str = now_utc.strftime("%Y%m%d%H%M")

    search_query = f"submittedDate:[{start_str} TO {end_str}]"
    base_url = "http://export.arxiv.org/api/query"

    step = 100
    start = 0
    all_entries = []

    print(f"[DEBUG] Time range: {start_str} ~ {end_str}, days={days}")
    while True:
        params = {
            "search_query": search_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": start,
            "max_results": step
        }
        print(f"[DEBUG] fetching: {start} -> {start+step}")
        r = requests.get(base_url, params=params)
        if r.status_code != 200:
            print("[ERROR] HTTP status:", r.status_code)
            break

        feed = feedparser.parse(r.content)
        got = len(feed.entries)
        print(f"[DEBUG] got {got} entries this batch.")
        if got == 0:
            break

        all_entries.extend(feed.entries)
        start += step

        if start >= 3000:
            print("[DEBUG] reached 3000, stop.")
            break

    print(f"[DEBUG] total in date range: {len(all_entries)}")

    matched = []
    for e in all_entries:
        title = getattr(e, 'title', '')
        summary = getattr(e, 'summary', '')
        published = getattr(e, 'published', '')
        link = getattr(e, 'link', '')
        if hasattr(e, 'tags'):
            categories = [t.term for t in e.tags]
        else:
            categories = []

        # 判定分类
        has_cs_stat = any(c.startswith("cs.") or c.startswith("stat.") for c in categories)
        if not has_cs_stat:
            continue

        # 判定关键词
        text_lower = (title + " " + summary).lower()
        if any(kw.lower() in text_lower for kw in keywords):
            matched.append({
                "title": title,
                "published": published,
                "link": link,
                "categories": categories
            })

    print(f"[DEBUG] matched {len(matched)} papers after local filter (cs./stat.+keywords)")
    return matched

def update_readme_in_repo(papers, token, repo_name):
    """
    将匹配到的论文列表写入目标repo的 README.md
    """
    if not papers:
        print("[INFO] No matched papers, skip README update.")
        return

    g = Github(token)
    repo = g.get_repo(repo_name)

    # 获取 README 内容
    readme_file = repo.get_contents("README.md", ref="main")
    readme_content = readme_file.decoded_content.decode("utf-8")

    now_utc_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_section = f"\n\n### Auto-captured papers on {now_utc_str}\n"
    for p in papers:
        cat_str = ", ".join(p["categories"])
        new_section += f"- **{p['title']}** (Published={p['published']})  \n"
        new_section += f"  - Categories: {cat_str}  \n"
        new_section += f"  - Link: {p['link']}\n\n"

    updated_content = readme_content + new_section
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
    # 1. 获取过去3天, keywords=["bias","fairness"] 的论文
    days = 1
    keywords = ["bias", "fairness"]
    papers = fetch_papers_wide_then_filter(days=days, keywords=keywords)
    print(f"[RESULT] matched {len(papers)} papers. Now let's update README in target repo if any.")

    # 2. 如果有匹配论文,更新 README
    #    需要在 secrets 或 env 里获取 token, repo name
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
