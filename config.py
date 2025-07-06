"""Global configuration for the automated LinkedIn posting system.
All values can be overridden by environment variables so that the
same codebase works locally, in GitHub Actions, or on any MCP.
"""

import os
from typing import Optional

# ----------------------------
# Content generation settings
# ----------------------------

# Topic you want to post about every 24 h.
TOPIC: str = os.getenv("TOPIC", "quantum computing")

# How many separate web articles to pull in each run.
NUM_ARTICLES: int = int(os.getenv("NUM_ARTICLES", "4"))

# Number of sentences to keep per-article after summarisation.
SUMMARY_SENTENCES: int = int(os.getenv("SUMMARY_SENTENCES", "5"))

# Maximum number of slides (excluding cover) in the deck.
SLIDES_MAX: int = int(os.getenv("SLIDES_MAX", "5"))

# ----------------------------
# LLM / summariser settings
# ----------------------------

# Abstractive summarisation model hosted on HuggingFace.
HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "sshleifer/distilbart-cnn-12-6")

# Public models can be queried without a token. Supply one to raise the rate-limit.
HUGGINGFACE_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")

# ----------------------------
# LinkedIn API credentials
# ----------------------------
# These should be provided as secrets in your deployment platform.
# Personal profile example: "urn:li:person:xxxxxxxxxxxxxxxxxx"
# Company page example:    "urn:li:organization:12345678"
LINKEDIN_CLIENT_ID: Optional[str] = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET: Optional[str] = os.getenv("LINKEDIN_CLIENT_SECRET")
# Access token generated via the LinkedIn OAuth 2.0 flow with the `w_member_social` scope.
LINKEDIN_ACCESS_TOKEN: Optional[str] = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_OWNER_URN: Optional[str] = os.getenv("LINKEDIN_OWNER_URN")