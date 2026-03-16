from __future__ import annotations

import httpx
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult


class PNCPCollector:
    source_key = "pncp"

    def run(self, db: Session) -> CollectorResult:
        del db
        fetched = 0
        timeout = httpx.Timeout(timeout=20.0)
        probe_urls = [
            "https://pncp.gov.br/",
            "https://pncp.gov.br/app/editais",
        ]
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            for url in probe_urls:
                try:
                    response = client.get(url)
                except httpx.HTTPError:
                    continue
                if response.status_code < 400:
                    fetched += 1
        return CollectorResult(fetched=fetched, saved=0)
