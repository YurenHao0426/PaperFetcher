import os
import requests
import feedparser
import datetime
from github import Github

#####################
# 1. 配置/常量
#####################

ALLOWED_CATEGORIES = [
    "cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.RO",
    "cs.IR", "stat.ML"
]

API_URL = "https://uiuc.chat/api/chat-api/chat"
API_KEY = os.getenv("UIUC_API_KEY")  # 你自己的密钥
MODEL_NAME = "qwen2.5:14b-instruct-fp16"       # 你的model

SYSTEM_PROMPT = (
    "Based on the given title and abstract, please determine if the paper "
    "is relevant to both language models and bias (or fairness). "
    "If yes, respond 1; otherwise respond 0."
)

#####################
# 2. 函数: 调用外部API 判别
#####################

def is_relevant_by_api(title, abstract):
    """
    调用外部API, 给一段title+abstract, 返回 True(1) or False(0).
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                # 填入我们的标题+摘要, 作为"content"
                "content": f"Title: {title}\nAbstract: {abstract}"
            }
        ],
        "api_key": API_KEY,
        "course_name": "llm-bias-papers",
        "stream": False,
        "temperature": 0.0,
        "retrieval_only": False
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        # resp.json() 应该包含 'message'
        response_msg = resp.json().get('message','')
        # 如果 message="1", 就 True, 否则 False
        return (response_msg.strip() == "1")
    except requests.RequestException as e:
        print("[ERROR] calling external API:", e)
        # 如果出错, 默认返回 False or do something
        return False

#####################
# 3. 函数: 抓论文, 调API判别
#####################

def fetch_arxiv_papers_with_api(days=1):
    """
    宽松抓 + 本地分类过滤 + 外部API做判别
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_utc = now_utc - datetime.timedelta(days=days)

    start_str = start_utc.strftime("%Y%m%d%H%M")
    end_str = now_utc.strftime("%Y%m%d%H%M")

    print(f"[DEBUG] date range (UTC): {start_str} ~ {end_str}, days={days}")
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
        try:
            resp = requests.get(base_url, params=params, timeout=30)
            if resp.status_code != 200:
                print("[ERROR] HTTP Status:", resp.status_code)
                break
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print("[ERROR] fetching arXiv:", e)
            break

        batch = feed.entries
        got_count = len(batch)
        print(f"[DEBUG] got {got_count} entries in this batch.")
        if got_count == 0:
            break

        all_entries.extend(batch)
        start += step
        if start >= 3000:
            print("[DEBUG] reached 3000, stop.")
            break

    print(f"[DEBUG] total retrieved in date range: {len(all_entries)}")

    matched = []
    for entry in all_entries:
        title = getattr(entry, 'title', '')
        summary = getattr(entry, 'summary', '')
        published = getattr(entry, 'published', '')
        link = getattr(entry, 'link', '')
        # 先检查分类
        if hasattr(entry, 'tags'):
            categories = [t.term for t in entry.tags]
        else:
            categories = []

        # 是否有至少一个分类在 ALLOWED_CATEGORIES 里
        in_allowed_cat = any(cat in ALLOWED_CATEGORIES for cat in categories)
        if not in_allowed_cat:
            continue

        # 调用外部 API 判别: relevant or not
        relevant = is_relevant_by_api(title, summary)
        if relevant:
            matched.append({
                "title": title,
                "published": published,
                "link": link,
                "categories": categories
            })

    print(f"[DEBUG] matched {len(matched)} papers after external API check.")
    return matched

#####################
# 4. 函数: update README
#####################

def update_readme_in_repo(papers, token, repo_name):
    if not papers:
        print("[INFO] No matched papers, skip README update.")
        return

    g = Github(token)
    repo = g.get_repo(repo_name)

    # 获取 README
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

#####################
# 5. main
#####################

def main():
    days = 7
    papers = fetch_arxiv_papers_with_api(days=days)
    print(f"[RESULT] matched {len(papers)} papers. Will update README if not empty.")

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
