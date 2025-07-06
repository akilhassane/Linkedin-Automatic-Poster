from typing import List
from transformers import pipeline  # type: ignore
import logging
import os

_model_name = "sshleifer/distilbart-cnn-6-6"
_summarizer_pipeline = None


def _load_model():
    global _summarizer_pipeline
    if _summarizer_pipeline is None:
        logging.info("Loading summarization model (%s)...", _model_name)
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        _summarizer_pipeline = pipeline(
            "summarization",
            model=_model_name,
            tokenizer=_model_name,
            device="cpu",
            use_auth_token=hf_token if hf_token else None,
        )
    return _summarizer_pipeline


def summarize_texts(texts: List[str], max_len: int = 128) -> List[str]:
    summarizer = _load_model()
    summaries = []
    for txt in texts:
        if len(txt) < 200:
            summaries.append(txt[:max_len])
            continue
        try:
            res = summarizer(txt[:4000], max_length=max_len, min_length=30, do_sample=False)
            summaries.append(res[0]["summary_text"])
        except Exception as exc:
            logging.warning("Summarization failure: %s", exc)
            summaries.append(txt[:max_len])
    return summaries