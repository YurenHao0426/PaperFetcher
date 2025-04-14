import os
import requests
import feedparser
import datetime
from github import Github
from openai import OpenAI

ALLOWED_CATEGORIES = [
    "cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.RO",
    "cs.IR", "stat.ML"
]

SYSTEM_PROMPT = (
    "You are a helpful assistant. The user will give you a paper title and abstract. "
    "Your task: Decide if this paper is about large language models (or generative text models) AND about bias/fairness. "
    "If yes, respond with just a single character: 1. Otherwise, respond with a single character: 0. "
    "No extra explanation, no punctuation—only the number."
)

def advanced_filter(entry):
    title = getattr(entry, 'title', '').lower()
    summary = getattr(entry, 'summary', '').lower()
    full_text = title + " " + summary

    general_terms = ["bias", "fairness"]
    model_terms = ["llm", "language model", "transformer", "gpt", "nlp",
                   "pretrained", "embedding", "generation", "alignment", "ai"]
    negative_terms = ["estimation", "variance", "quantum", "physics",
                      "sensor", "circuit", "electronics", "hardware"]

    has_general = any(term in full_text for term in general_terms)
    has_model   = any(term in full_text for term in model_terms)
    has_negative = any(term in full_text for term in negative_terms)

    return (has_general and has_model) and (not has_negative)

def is_relevant_by_api(title, summary, client, model="gpt-4-turbo"):
    prompt = f"Title: {title}\nAbstract: {summary}"
    try:
        dialogue = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1
        )
        response_msg = dialogue.choices[0].message.content.strip()
        print(f"[DEBUG][API] return message='{response_msg}' for paper title='{title[:60]}...'")
        return response_msg == "1"
    except Exception as e:
        print("[ERROR][API] calling OpenAI API:", e)
        return False

def fetch_papers_combined(days=1):
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_utc = now_utc - datetime.timedelta(days=days)
    start_str = start_utc.strftime("%Y%m%d%H%M")
    end_str = now_utc.strftime("%Y%m%d%H%M")

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
        resp = requests.get(base_url, params=params, timeout=30)
        if resp.status_code != 200:
            break
        feed = feedparser.parse(resp.content)
        batch = feed.entries
        if not batch:
            break

        all_entries.extend(batch)
        start += step
        if start >= 3000:
            break

    local_candidates = [
        {
            "title": e.title,
            "summary": e.summary,
            "published": e.published,
            "link": e.link,
            "categories": [t.term for t in e.tags]
        }
        for e in all_entries
        if any(cat in ALLOWED_CATEGORIES for cat in [t.term for t in e.tags]) and advanced_filter(e)
    ]

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("[WARNING] No OPENAI_API_KEY found. Skip second filter.")
        return local_candidates

    client = OpenAI(api_key=openai_api_key)
    final_matched = [p for p in local_candidates if is_relevant_by_api(p["title"], p["summary"], client)]

    return final_matched

def update_readme_in_repo(papers, token, repo_name):
    if not papers:
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

def main():
    days = 1
    papers = fetch_papers_combined(days=days)

    print(f"[FINAL RESULT] Total papers matched: {len(papers)}")  # <--- 添加此行

    github_token = os.getenv("TARGET_REPO_TOKEN")
    target_repo_name = os.getenv("TARGET_REPO_NAME")
    if github_token and target_repo_name and papers:
        update_readme_in_repo(papers, github_token, target_repo_name)
    else:
        print("[INFO] No matched papers or missing GitHub credentials.")

if __name__ == "__main__":
    main()
