import os
import argparse
import logging
from datetime import datetime
from pathlib import Path

from utils.fetcher import fetch_articles
from utils.summarizer import summarize_texts
from utils.trends import build_trend_graph
from utils.linkedin import post_to_linkedin
from utils.slide import build_slide

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def build_post(topic: str, n_articles: int = 5):
    articles = fetch_articles(topic, n_articles)
    logging.info("Fetched %d articles", len(articles))

    summaries = summarize_texts([a["content"] for a in articles])

    bullets = []
    for art, summ in zip(articles, summaries):
        bullets.append(f"• {art['title']} — {summ}")

    post_text = f"Daily digest on {topic.title()} ({datetime.utcnow().strftime('%Y-%m-%d')})\n\n" + "\n".join(bullets)

    graph_path = build_trend_graph(topic)

    # Optional: build pptx slide (not used in posting for now)
    slide_path = build_slide(topic, summaries, graph_path)

    return post_text, graph_path, slide_path


def main():
    parser = argparse.ArgumentParser(description="Auto LinkedIn Poster")
    parser.add_argument("--topic", required=True, help="Topic of interest")
    parser.add_argument("--articles", type=int, default=5, help="Number of articles to pull")
    parser.add_argument("--dry", action="store_true", help="Do not post, just print")
    args = parser.parse_args()

    post_text, graph_path, slide_path = build_post(args.topic, args.articles)

    if args.dry:
        print(post_text)
        print("Graph saved at", graph_path)
        print("Slide saved at", slide_path)
        return

    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    member_urn = os.getenv("LINKEDIN_MEMBER_URN")

    if not access_token or not member_urn:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN and LINKEDIN_MEMBER_URN must be set")

    post_to_linkedin(access_token, member_urn, post_text, Path(graph_path))


if __name__ == "__main__":
    main()