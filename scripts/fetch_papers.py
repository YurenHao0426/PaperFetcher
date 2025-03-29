import requests
import feedparser
import datetime

def fetch_arxiv_bias_fairness(days=3):
    """
    从 arXiv 中搜索过去 N 天内包含 'bias' OR 'fairness' 等关键词的论文
    分类限定为 cs.IR (可自行改)，使用 all: 字段 + submittedDate range + 本地过滤
    """
    now = datetime.datetime.utcnow()
    start_day = now - datetime.timedelta(days=days)
    # 构造日期范围 (只精确到天就行)
    # 格式: [YYYYMMDD0000 TO YYYYMMDD2359]
    start_str = start_day.strftime("%Y%m%d0000")
    end_str = now.strftime("%Y%m%d2359")

    # arXiv 布尔搜索表达式
    # 这里演示2个关键词 bias, fairness
    # 用 (all:bias OR all:fairness)
    # 同时限制分类 cat:cs.IR
    # 同时限制日期 submittedDate:[start_str TO end_str]
    # 并指定 sortBy=submittedDate
    search_query = f"(all:bias+OR+all:fairness)+AND+cat:cs.IR+AND+submittedDate:[{start_str}+TO+{end_str}]"

    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": search_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 100
    }
    print("[DEBUG] search_query=", search_query)

    response = requests.get(base_url, params=params)
    print("[DEBUG] Full URL =", response.url)
    if response.status_code != 200:
        print("[ERROR] HTTP Status:", response.status_code)
        return []

    feed = feedparser.parse(response.content)
    entries = feed.entries
    print("[DEBUG] arXiv 返回条数:", len(entries))

    papers = []
    for e in entries:
        title = e.title
        summary = e.summary
        published = e.published
        link = e.link

        # 在本地再做一个严格的匹配
        # 看标题或摘要中是否真的含 bias/fairness
        # 以免 all:bias 命中其他字段
        text = (title + " " + summary).lower()
        if ("bias" in text) or ("fairness" in text):
            papers.append({
                "title": title,
                "published": published,
                "link": link
            })

    return papers

if __name__ == "__main__":
    # 测试过去3天
    results = fetch_arxiv_bias_fairness(days=3)
    print(f"找到 {len(results)} 篇论文：")
    for i, p in enumerate(results, 1):
        print(f"{i}. {p['title']} - {p['published']} - {p['link']}")
