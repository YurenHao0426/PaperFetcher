import os
import requests
import feedparser
import datetime
from github import Github

ALLOWED_CATEGORIES = [
    "cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.RO",
    "cs.IR", "stat.ML"
]

def advanced_filter(entry):
    """
    基于标题+摘要，本地进行“正面关键词 + 负面关键词”筛选
    """
    title = getattr(entry, 'title', '').lower()
    summary = getattr(entry, 'summary', '').lower()
    full_text = title + " " + summary

    # 正面关键词
    general_terms = ["bias", "fairness"]
    model_terms = ["llm", "language model", "transformer", "gpt", "nlp",
                   "pretrained", "embedding", "generation", "alignment", "ai"]
    # 负面关键词
    negative_terms = [
        "estimation", "variance", "quantum", "physics",
        "sensor", "circuit", "electronics", "hardware"
    ]

    has_general = any(term in full_text for term in general_terms)
    has_model   = any(term in full_text for term in model_terms)
    has_negative = any(term in full_text for term in negative_terms)

    return (has_general and has_model) and (not has_negative)

API_URL = "https://uiuc.chat/api/chat-api/chat"
MODEL_NAME = "qwen2.5:14b-instruct-fp16"
SYSTEM_PROMPT = (
    "You are a helpful assistant. The user will give you a paper title and abstract. "
    "Your task: Decide if this paper is about large language models (or generative text models) AND about bias/fairness. "
    "If yes, respond with just a single character: 1. Otherwise, respond with a single character: 0. "
    "No extra explanation, no punctuation—only the number."
)

def is_relevant_by_api(title, summary, api_key):
    """
    调用外部API，根据title+summary判别是否相关（返回 True/False），
    并打印调试信息。
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
                "content": SYSTEM_PROMPT + f"Title: {title}\nAbstract: {summary}"
            }
        ],
        "api_key": api_key,
        "course_name": "llm-bias-papers",
        "stream": False,
        "temperature": 0.0
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        full_json = resp.json()
        # 获取API返回的message
        response_msg = full_json.get("message", "")
        print(f"[DEBUG][API] return message='{response_msg.strip()}' for paper title='{title[:60]}...'")
        return (response_msg.strip() == "1")
    except Exception as e:
        print("[ERROR][API] calling external API:", e)
        return False

def fetch_papers_combined(days=1):
    """
    1) 抓过去days天 arXiv论文(宽松)
    2) 本地先过滤(分类 + advanced_filter)
    3) 对“通过本地筛”的候选，调用API二次判定 + debug输出
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

    # --- 本地过滤1: 分类 + advanced_filter ---
    local_candidates = []
    for e in all_entries:
        title = getattr(e, "title", "")
        summary = getattr(e, "summary", "")
        published = getattr(e, "published", "")
        link = getattr(e, "link", "")
        categories = [t.term for t in e.tags] if hasattr(e, 'tags') else []

        if not any(cat in ALLOWED_CATEGORIES for cat in categories):
            continue

        if advanced_filter(e):
            local_candidates.append({
                "title": title,
                "summary": summary,
                "published": published,
                "link": link,
                "categories": categories
            })

    print(f"[DEBUG] local_candidates = {len(local_candidates)} after local filter")

    # Debug: 打印所有local_candidates的标题，看看是不是你预期的那几篇
    for idx, paper in enumerate(local_candidates, 1):
        print(f"[DEBUG][LOCAL] #{idx}, title='{paper['title']}' cat={paper['categories']}")

    # --- 2) 调API二次判定 ---
    api_key = os.getenv("UIUC_API_KEY")  # 你在Secrets中配置
    if not api_key:
        print("[WARNING] No UIUC_API_KEY found. Skip second filter.")
        return local_candidates

    final_matched = []
    for idx, paper in enumerate(local_candidates, 1):
        relevant = is_relevant_by_api(paper["title"], paper["summary"], api_key)
        if relevant:
            final_matched.append({
                "title": paper["title"],
                "published": paper["published"],
                "link": paper["link"],
                "categories": paper["categories"]
            })
        else:
            # 如果不相关，就打印个提示
            print(f"[DEBUG][API] => '0' => exclude paper #{idx}, title='{paper['title'][:60]}...'")

    print(f"[DEBUG] final_matched = {len(final_matched)} after API check")
    return final_matched

def update_readme_in_repo(papers, token, repo_name):
    if not papers:
        print("[INFO] No matched papers, skip README update.")
        return

    g = Github(token)
    repo = g.get_repo(repo_name)

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
    # 抓过去5天(你例子里是5) 或根据需要改
    days = 5
    papers = fetch_papers_combined(days=days)
    print(f"\n[RESULT] matched {len(papers)} papers total after double filter. Now update README if not empty...")

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
