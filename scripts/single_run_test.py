import requests
import feedparser

def test_arxiv():
    base_url = "http://export.arxiv.org/api/query"
    # 时间段设为 2025-03-27 00:00 到 2025-03-29 00:00
    # 注意: 论文在 3月27日 07:54Z 提交，应该在这个区间之内
    search_query = (
        "(all:bias+OR+all:fairness)"
        "+AND+cat:cs.IR"
        "+AND+submittedDate:[202503270000+TO+202503290000]"
    )

    params = {
        "search_query": search_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 100
    }
    print("[DEBUG] search_query =", search_query)

    r = requests.get(base_url, params=params)
    print("[DEBUG] Full URL =", r.url)
    if r.status_code != 200:
        print("[ERROR] HTTP Status:", r.status_code)
        return

    feed = feedparser.parse(r.content)
    print("[DEBUG] Returned entries:", len(feed.entries))

    # 打印出标题和发布时间供检查
    for i, entry in enumerate(feed.entries, start=1):
        print(f"{i}. Title: {entry.title} | updated: {entry.updated} | published: {entry.published}")

if __name__ == "__main__":
    test_arxiv()
