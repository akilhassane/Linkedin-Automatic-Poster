from datetime import datetime
from typing import List
import logging
import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq


def build_trend_graph(topic: str, days: int = 30, out_path: str | None = None) -> str:
    """Downloads Google Trends data and saves a PNG graph file."""
    pytrends = TrendReq(hl="en-US", tz=0)
    kw_list = [topic]
    timeframe = f"now {days}-d"

    logging.info("Fetching Google Trends data for '%s' (%s)...", topic, timeframe)
    pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo='', gprop='')
    data = pytrends.interest_over_time()
    if data.empty:
        logging.warning("No trends data returned for %s", topic)
        return ""

    if out_path is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        out_path = f"trend_{topic.replace(' ', '_')}_{timestamp}.png"

    plt.figure(figsize=(8,4))
    for kw in kw_list:
        plt.plot(data.index, data[kw], label=kw.title())
    plt.title(f"Google search interest (last {days} days)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

    return out_path