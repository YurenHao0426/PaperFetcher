import requests
import feedparser
import datetime

def fetch_arxiv_full_range():
    """
    不限制分类、关键词，仅根据 submittedDate 做一个宽区间。
    分批次抓取，每批 100 条，直到再也拿不到新条目或达到我们设定的安全上限。
    同时演示如何在循环中检测如果发布时间超过了上限，就可以提前退出。
    """

    base_url = "http://export.arxiv.org/api/query"

    # 宽松的日期范围 [202503250000 TO 202504020000]
    # 你可以改成更广或更精确
    start_date_str = "202503250000"
    end_date_str = "202504020000"

    search_query = f"submittedDate:[{start_date_str} TO {end_date_str}]"

    # 分批抓取
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
        print(f"[DEBUG] Fetching from index={start} to {start+step}, date range = {start_date_str} ~ {end_date_str}")
        resp = requests.get(base_url, params=params)
        if resp.status_code != 200:
            print("[ERROR] HTTP status:", resp.status_code)
            break

        feed = feedparser.parse(resp.content)
        entries = feed.entries
        got_count = len(entries)
        print(f"[DEBUG] Got {got_count} entries this batch.")

        if got_count == 0:
            # 没有更多数据了
            break

        # 把本批加入总list
        all_entries.extend(entries)
        # 下一批
        start += step

        # 自定义一个安全上限，防止无限循环或极大数据
        if start >= 3000:
            # 3k 只是举例
            print("[DEBUG] Over 3000 entries, stopping to avoid extremely large dataset.")
            break

    print("[DEBUG] total retrieved:", len(all_entries))

    # 现在 all_entries 就是我们抓到的全部。
    # 可以查看是否包含 "Bias-Aware Agent..." 或做后续处理

    found = False
    for idx, e in enumerate(all_entries, 1):
        title_lower = e.title.lower()
        if "bias-aware agent" in title_lower:
            found = True
            print(f"\n[FOUND]  Index={idx}, Title={e.title}, published={e.published}, updated={e.updated}")
            break

    if not found:
        print("\n[INFO] 'Bias-Aware Agent...' not found in the entire set.")


if __name__ == "__main__":
    fetch_arxiv_full_range()
