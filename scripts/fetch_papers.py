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
        print(f"[DEBUG][API] OpenAI response='{response_msg}' for paper '{title[:60]}...'")
        return response_msg == "1"
    except Exception as e:
        print("[ERROR][API] calling OpenAI API:", e)
        return False

def fetch_papers_combined(days=1):
    import datetime
    import requests
    import feedparser

    now_utc   = datetime.datetime.now(datetime.timezone.utc)
    cutoff_utc = now_utc - datetime.timedelta(days=days)

    # 1. Build an OR‑joined category filter:
    cat_query = " OR ".join(f"cat:{c}" for c in ALLOWED_CATEGORIES)
    # If you really want *no* category filtering, just set: cat_query = "all:*"

    base_url = "http://export.arxiv.org/api/query"
    step     = 100
    start    = 0
    all_entries = []

    while True:
        params = {
            "search_query": cat_query,
            "sortBy":       "submittedDate",
            "sortOrder":    "descending",
            "start":        start,
            "max_results":  step
        }
        print(f"[DEBUG] fetching arXiv entries: {start} to {start+step}")
        resp = requests.get(base_url, params=params, timeout=30)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        batch = feed.entries
        print(f"[DEBUG] fetched batch size: {len(batch)}")

        if not batch:
            break

        # 2. Filter by published date >= cutoff
        for entry in batch:
            published = datetime.datetime.fromisoformat(entry.published)
            if published >= cutoff_utc:
                all_entries.append(entry)
            else:
                # since sorted descending, once we hit older papers we can stop entirely
                start = None
                break

        if start is None or len(batch) < step:
            break

        start += step

    print(f"[DEBUG] total fetched papers from arXiv in last {days} day(s): {len(all_entries)}")

    # …then proceed with OpenAI filtering exactly as before…
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("[ERROR] OPENAI_API_KEY missing, aborting.")
        return []

    client = OpenAI(api_key=openai_api_key)
    final_matched = []

    for idx, entry in enumerate(all_entries, 1):
        title    = entry.title
        summary  = entry.summary
        # if you *really* want to disable *all* filtering aside from the LLM check,
        # you can comment out the category check below:
        categories = [t.term for t in getattr(entry, 'tags', [])]
        if not any(cat in ALLOWED_CATEGORIES for cat in categories):
            continue

        if is_relevant_by_api(title, summary, client):
            final_matched.append({
                "title":      title,
                "summary":    summary,
                "published":  entry.published,
                "link":       entry.link,
                "categories": categories
            })
            print(f"[DEBUG][API] Included #{idx}: {title[:60]}...")
        else:
            print(f"[DEBUG][API] Excluded #{idx}: {title[:60]}...")

    print(f"[DEBUG] final matched papers after OpenAI filter: {len(final_matched)}")
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
    days = 1
    print(f"[DEBUG] Starting fetch_papers_combined with days={days}")
    papers = fetch_papers_combined(days=days)

    print(f"[DEBUG] After fetch_papers_combined: {len(papers)} papers matched.")

    github_token = os.getenv("TARGET_REPO_TOKEN")
    target_repo_name = os.getenv("TARGET_REPO_NAME")
    print(f"[DEBUG] Github Token Set: {'Yes' if github_token else 'No'}")
    print(f"[DEBUG] Target Repo Name: {target_repo_name}")

    if github_token and target_repo_name and papers:
        update_readme_in_repo(papers, github_token, target_repo_name)
    else:
        print("[INFO] Skipped README update due to missing credentials or no papers matched.")

if __name__ == "__main__":
    main()
