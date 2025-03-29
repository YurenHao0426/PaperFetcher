import os
import requests
import feedparser
import datetime
from github import Github

# ========== 你可以根据需要修改的参数 ==========

# 多分类
CATEGORIES = ["cs.CL", "cs.AI", "stat.ML", "cs.IR"]

# 单个关键词列表（避免多词短语搜索不到）
# 如果想搜索短语，可尝试 "ti:\"ethical AI\"+OR+abs:\"ethical AI\"" 但效果可能并不好
KEYWORDS = [
    "bias",
    "debias",
    "fairness",
    "equity",
    "inclusivity",
    "diversity",
    "ethical",
    "responsible",
    # 如果想搜索 AI 这个单词，可以加进去，但“AI”几乎会命中太多论文
    # "AI"
]

# 设置要抓取的时间范围（过去 7 天，便于测试）
HOURS_TO_FETCH = 24 * 7  # 7天

# 最大抓取数
MAX_PER_CATEGORY = 300

# GitHub 相关
TARGET_REPO_TOKEN = os.getenv("TARGET_REPO_TOKEN")
TARGET_REPO_NAME = os.getenv("TARGET_REPO_NAME")


def build_search_query_single_word(keyword, category):
    """
    对单个词构造类似于  (ti:bias OR abs:bias) AND cat:cs.AI
    注意：arXiv搜索要求把空格等转成 "+"
    """
    kw_escaped = keyword.replace(" ", "+")
    query = f"(ti:{kw_escaped}+OR+abs:{kw_escaped})+AND+cat:{category}"
    return query

def search_category_7days(category, keywords, hours=HOURS_TO_FETCH):
    """
    在给定分类下，用【单词关键词】循环搜索，每个keyword都请求一次，然后合并去重。
    这样避免了 (keyword1 OR keyword2) 对arXiv API可能无效的问题。
    依旧按提交时间降序遍历，直到遇到超过 hours 范围的论文就停。
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now_utc - datetime.timedelta(hours=hours)

    all_papers = []
    seen = set()  # 用来去重

    for kw in keywords:
        base_url = "http://export.arxiv.org/api/query"
        start = 0
        step = 50

        while True:
            query_str = build_search_query_single_word(kw, category)
            params = {
                "search_query": query_str,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "start": start,
                "max_results": step
            }

            print(f"\n[DEBUG] 分类={category}, 关键词={kw}, start={start}, 请求参数={params}")
            resp = requests.get(base_url, params=params)
            print("[DEBUG] HTTP状态码:", resp.status_code)
            feed = feedparser.parse(resp.content)
            entries = feed.entries
            print(f"[DEBUG] 本批返回 {len(entries)} 篇论文.")

            if not entries:
                break  # 没有更多结果了

            stop_fetch = False  # 如果遇到超过7天的论文，就置为 True 并跳出

            for entry in entries:
                published_naive = datetime.datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
                published_utc = published_naive.replace(tzinfo=datetime.timezone.utc)

                if published_utc < cutoff:
                    # 这篇及后面都不用看了，按提交时间降序
                    print(f"[DEBUG] 论文 {entry.title[:60]}... 已超过 {cutoff} 提交时间")
                    stop_fetch = True
                    break

                # 去重判断
                unique_key = (entry.id, published_utc)
                if unique_key in seen:
                    continue

                seen.add(unique_key)
                all_papers.append({
                    "title": entry.title,
                    "url": entry.link,
                    "abstract": entry.summary,
                    "published": published_utc
                })

            if stop_fetch:
                # 跳出 while True
                break

            start += step
            if start >= MAX_PER_CATEGORY:
                print(f"[DEBUG] 已达本分类抓取上限 {MAX_PER_CATEGORY} 篇, 停止继续翻页。")
                break

    print(f"[DEBUG] 分类 {category} 最终收集到 {len(all_papers)} 篇论文（过去{hours}小时内，含重复去重）")
    return all_papers

def fetch_arxiv_papers():
    """
    遍历多个分类，对每个分类做关键词搜索再合并
    """
    total_papers = []
    for cat in CATEGORIES:
        cat_papers = search_category_7days(cat, KEYWORDS, HOURS_TO_FETCH)
        total_papers.extend(cat_papers)

    print(f"[DEBUG] 所有分类加起来总数: {len(total_papers)}")

    # 这里不再二次去重，因为我们在search_category_7days内部对同分类+同一关键词已做去重
    # 如果你想进一步去重（不同分类之间有重叠），可以在此做 set() 处理

    return total_papers

def update_readme_in_target(papers):
    if not papers:
        print("[DEBUG] No relevant papers found. Skipping README update.")
        return

    # 按提交时间降序
    papers.sort(key=lambda x: x["published"], reverse=True)

    g = Github(TARGET_REPO_TOKEN)
    repo = g.get_repo(TARGET_REPO_NAME)

    readme_file = repo.get_contents("README.md", ref="main")
    readme_content = readme_file.decoded_content.decode("utf-8")

    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    new_section = f"\n\n### {date_str} (过去{HOURS_TO_FETCH}小时内单词搜索)\n"
    for p in papers:
        pub_str = p["published"].strftime("%Y-%m-%d %H:%M")
        new_section += f"- **[{p['title']}]({p['url']})** (Published: {pub_str} UTC)\n"

    updated_content = readme_content + new_section

    print(f"[DEBUG] 即将在 README.md 添加的内容:\n{new_section[:500]}...")  # 只打印500字作为示例

    repo.update_file(
        path="README.md",
        message=f"Auto Update README with {len(papers)} papers ({date_str})",
        content=updated_content,
        sha=readme_file.sha,
        branch="main"
    )
    print("[DEBUG] README.md 更新完成")

def main():
    print("[DEBUG] 脚本开始执行...")
    papers = fetch_arxiv_papers()
    print(f"[DEBUG] fetch_arxiv_papers() 返回 {len(papers)} 篇最终论文.")
    update_readme_in_target(papers)
    print("[DEBUG] 脚本执行结束.")

if __name__ == "__main__":
    main()
