import os
import requests
import feedparser
import datetime
from github import Github

# ========== 你可以根据需要修改的参数 ==========

# 多分类
CATEGORIES = ["cs.CL", "cs.AI", "stat.ML", "cs.IR"]

# 多关键词，这里用的纯文本搜索，尽量只用单词或简单词组
# 注意：arXiv 搜索并不支持很复杂的布尔运算，也不支持真正的模糊匹配
KEYWORDS = ["bias", "debias", "fairness", "equity", "inclusivity", "diversity", "ethical AI", "responsible AI"]

# 在构造查询时，我们会把 KEYWORDS 用 (ti:xxx OR abs:xxx) OR (ti:yyy OR abs:yyy) 组合起来
# 这样 arXiv 只返回标题或摘要中出现这些关键词的论文

# 最多要处理多少结果（翻页抓取上限）
MAX_PER_CATEGORY = 300

# GitHub 相关
TARGET_REPO_TOKEN = os.getenv("TARGET_REPO_TOKEN")
TARGET_REPO_NAME = os.getenv("TARGET_REPO_NAME")

def build_search_query(keywords, category):
    """
    构造 arXiv API 中的 search_query 字符串（示例： (ti:bias OR abs:bias) OR (ti:fairness OR abs:fairness) ... AND cat:cs.AI）
    """
    # 针对多关键词，构造括号表达式
    # (ti:bias OR abs:bias) OR (ti:debias OR abs:debias) OR ...
    kw_expressions = []
    for kw in keywords:
        kw_escaped = kw.replace(" ", "+")  # 避免空格等符号出问题
        part = f"(ti:{kw_escaped}+OR+abs:{kw_escaped})"
        kw_expressions.append(part)
    # 用 +OR+ 串联每个关键词
    combined_keywords = "+OR+".join(kw_expressions)

    # 最终把分类也加进来: AND cat:cs.AI
    query = f"({combined_keywords})+AND+cat:{category}"
    return query

def search_category_for_24h(category, keywords, hours=24):
    """
    在给定分类下，用关键词搜索，按提交时间降序遍历，直到遇到超过24小时的论文就停止。
    返回满足条件的论文列表
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now_utc - datetime.timedelta(hours=hours)

    base_url = "http://export.arxiv.org/api/query"
    query_str = build_search_query(keywords, category)

    all_papers = []
    start = 0
    step = 50  # 每次取多少条，可以 50 或 100
    while True:
        params = {
            "search_query": query_str,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": start,
            "max_results": step
        }
        print(f"\n[DEBUG] 正在请求分类: {category}, start={start}, 查询URL参数: {params}")

        resp = requests.get(base_url, params=params)
        print("[DEBUG] HTTP状态码:", resp.status_code)
        feed = feedparser.parse(resp.content)

        entries = feed.entries
        print(f"[DEBUG] 本批返回 {len(entries)} 篇论文 (start={start}).")

        if not entries:
            break  # 没有更多结果，退出

        for i, entry in enumerate(entries):
            # 解析发布时间
            published_naive = datetime.datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
            published_utc = published_naive.replace(tzinfo=datetime.timezone.utc)

            if published_utc < cutoff:
                # 一旦发现超过24小时的论文，因为是降序，所以后面都没必要看了
                print(f"[DEBUG] 论文 {entry.title} 时间 {published_utc} 已超过 {cutoff}, 提前退出本分类循环")
                break

            # 如果在24小时内，加入列表
            all_papers.append({
                "title": entry.title,
                "url": entry.link,
                "abstract": entry.summary,
                "published": published_utc
            })

        else:
            # 如果 for 循环是正常结束（没有 break），说明本批都在24小时内
            # 需要翻页继续抓取下一批
            # 但要防止无限翻页：如果超过我们设定的上限，也跳出
            start += step
            if start >= MAX_PER_CATEGORY:
                print(f"[DEBUG] 已达本分类抓取上限 {MAX_PER_CATEGORY} 篇, 停止继续翻页。")
                break
            continue

        # 如果执行到了 break，则要退出 while True
        break

    print(f"[DEBUG] 分类 {category} 最终收集到 {len(all_papers)} 篇论文（24小时内）")
    return all_papers

def fetch_arxiv_papers_24h():
    """
    遍历多个分类，对每个分类做关键词搜索并合并结果
    去重逻辑(简单版本)可按title+published来判断是否已出现
    """
    unique_papers = []
    seen_set = set()  # 用来去重，存放 (title, published)

    for cat in CATEGORIES:
        cat_papers = search_category_for_24h(cat, KEYWORDS, hours=24)
        for p in cat_papers:
            key = (p["title"], p["published"])
            if key not in seen_set:
                seen_set.add(key)
                unique_papers.append(p)

    print(f"[DEBUG] 全部分类合并后共 {len(unique_papers)} 篇论文。")
    return unique_papers

def update_readme_in_target(relevant_papers):
    """
    将匹配到的论文信息追加到目标仓库的 README.md
    """
    if not relevant_papers:
        print("No relevant papers found. Skipping README update.")
        return

    # 按提交时间降序排序再写入，也许你想先写最新的
    relevant_papers.sort(key=lambda x: x["published"], reverse=True)

    g = Github(TARGET_REPO_TOKEN)
    repo = g.get_repo(TARGET_REPO_NAME)

    readme_file = repo.get_contents("README.md", ref="main")
    readme_content = readme_file.decoded_content.decode("utf-8")

    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    new_section = f"\n\n### {date_str} (自动关键词搜索)\n"
    for p in relevant_papers:
        # 时间显示一下
        pub_str = p["published"].strftime("%Y-%m-%d %H:%M UTC")
        new_section += f"- **[{p['title']}]({p['url']})** (Published: {pub_str})\n"

    updated_content = readme_content + new_section
    print(f"[DEBUG] 即将在 README.md 添加的内容:\n{new_section}")

    repo.update_file(
        path="README.md",
        message=f"Auto Update README with {len(relevant_papers)} papers ({date_str})",
        content=updated_content,
        sha=readme_file.sha,
        branch="main"
    )
    print("[DEBUG] README.md 更新完成")

def main():
    print("[DEBUG] 开始执行 main() ...")
    # 1. 从 arXiv 获取过去24小时的论文（带关键词搜索 & 多分类 & 自动停止）
    papers_24h = fetch_arxiv_papers_24h()

    # 2. 将结果写入目标仓库
    update_readme_in_target(papers_24h)

    print("[DEBUG] 脚本执行结束.")

if __name__ == "__main__":
    main()
