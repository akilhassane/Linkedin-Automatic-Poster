"""main.py

Entry point for the automated LinkedIn posting pipeline.

Run this once (manually or via cron) and it will:
1. Crawl the web for fresh articles on ``config.TOPIC``
2. Summarise them with an LLM
3. Build a LinkedIn-ready post, PPTX slide deck, and graph PNG
4. Publish everything via the LinkedIn UGC Post API

Environment variables (see ``config.py``) control credentials & overrides.
"""
from __future__ import annotations

import logging
import sys
import traceback

import config
import crawler
import summariser
import generator
import linkedin_poster

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("main")


def run() -> None:  # noqa: D401
    logger.info("Fetching up to %d articles about '%s'…", config.NUM_ARTICLES, config.TOPIC)
    raw_articles = crawler.fetch_articles(config.TOPIC, config.NUM_ARTICLES)
    if not raw_articles:
        logger.error("No articles could be fetched – aborting run.")
        return

    logger.info("Summarising %d articles…", len(raw_articles))
    summaries = summariser.summarise_batch(
        [article["text"] for article in raw_articles], max_len=120
    )

    logger.info("Building assets (post body, slides, chart)…")
    body_text, slide_path, graph_path = generator.build_assets(raw_articles, summaries)

    logger.info("Posting to LinkedIn (owner=%s)…", config.LINKEDIN_OWNER_URN or "<dry-run>")
    linkedin_poster.post(body_text, slide_path=slide_path, image_path=graph_path)

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # noqa: BLE001
        logger.error("Fatal error: %s", exc)
        traceback.print_exc()
        sys.exit(1)