import os
import requests
import feedparser
import datetime
from github import Github

ARXIV_CATEGORIES = "cs.CL OR cs.AI OR stat.ML OR cs.IR"
KEYWORDS = ["bias", "debias", "fairness", "equity", "inclusivity", "diversity", "ethical AI", "responsible AI"]

TARGET_REPO_TOKEN = os.getenv("TARGET_REPO_TOKEN")
TARGET_REPO_NAME = os.getenv("TARGET_REPO_NAME")

def fetch_arxiv_papers():
    """
    从arXiv获取过去24小时的新论文，并打印一些调试信息
    """
    # 使用带时区的UTC时间
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    yesterday_utc = now_utc - datetime.timedelta(days=1)

    print("DEBUG: 当前UTC时间:", now_utc)
    print("DEBUG: 过去24小时阈值:", yesterday_utc)

    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"cat:{ARXIV_CATEGORIES}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 100
    }

    # 发起请求
    r = requests.get(base_url, params=params)
    print(f"DEBUG: 请求URL = {r.url}")
    print(f"DEBUG: HTTP状态码 = {r.status_code}")

    feed = feedparser.parse(r.content)
    print(f"DEBUG: feed.entries 长度 = {len(feed.entries)}")

    papers = []
    for idx, entry in enumerate(feed.entries):
        published_naive = datetime.datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
        published_utc = published_naive.replace(tzinfo=datetime.timezone.utc)

        # 调试输出
        print(f"\n=== 第 {idx+1} 篇论文 ===")
        print("标题: ", entry.title)
        print("发布时间(UTC): ", published_utc)
        print("链接: ", entry.link)
        print("摘要(前200字符): ", entry.summary[:200], "...")

        if published_utc > yesterday_utc:
            papers.append({
                "title": entry.title,
                "url": entry.link,
                "abstract": entry.summary
            })
            print("--> 该论文在24小时之内，加入papers列表")
        else:
            print("--> 该论文超过24小时，不加入")

    print(f"\nDEBUG: 最终 papers 长度 = {len(papers)}")
    return papers

def filter_papers(papers):
    """
    用关键词匹配，返回与 KEYWORDS 匹配的论文，并打印调试信息
    """
    relevant = []
    for idx, p in enumerate(papers):
        abstract_lower = p["abstract"].lower()
        title_lower = p["title"].lower()

        # 调试打印
        found_keywords = []
        for kw in KEYWORDS:
            if kw.lower() in abstract_lower or kw.lower() in title_lower:
                found_keywords.append(kw)

        if found_keywords:
            print(f"\n[匹配] 第 {idx+1} 篇论文: {p['title']}")
            print("匹配到的关键词: ", found_keywords)
            relevant.append(p)
        else:
            print(f"\n[未匹配] 第 {idx+1} 篇论文: {p['title']}")
            print("没有匹配到任何关键词")

    print(f"\nDEBUG: relevant_papers 长度 = {len(relevant)}")
    return relevant

def update_readme_in_target(relevant_papers):
    """
    将匹配到的论文信息追加到目标仓库的 README.md
    """
    if not relevant_papers:
        print("No relevant papers found. Skipping README update.")
        return

    # 创建 GitHub 客户端
    g = Github(TARGET_REPO_TOKEN)
    repo = g.get_repo(TARGET_REPO_NAME)

    # 获取 README
    print(f"DEBUG: 获取目标仓库 {TARGET_REPO_NAME} 的 README.md")
    readme_file = repo.get_contents("README.md", ref="main")
    readme_content = readme_file.decoded_content.decode("utf-8")

    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    new_section = f"\n\n### {date_str}\n"

    for p in relevant_papers:
        new_section += f"- **[{p['title']}]({p['url']})**\n"

    updated_content = readme_content + new_section
    print(f"DEBUG: 即将在 README.md 添加的内容:\n{new_section}")

    # 更新 README
    repo.update_file(
        path="README.md",
        message=f"Auto Update README with {len(relevant_papers)} papers ({date_str})",
        content=updated_content,
        sha=readme_file.sha,
        branch="main"
    )
    print("DEBUG: README.md 更新完成")

def main():
    print("DEBUG: 开始执行 main() ...")
    papers = fetch_arxiv_papers()
    relevant_papers = filter_papers(papers)
    update_readme_in_target(relevant_papers)
    print("DEBUG: 脚本执行结束.")

if __name__ == "__main__":
    main()
