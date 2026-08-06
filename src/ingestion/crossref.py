from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import ensure_parent, read_json, write_json


CROSSREF_API_URL = "https://api.crossref.org/works"
RETRYABLE_STATUS_CODES = {429, 503}
MAX_ATTEMPTS = 4
REQUEST_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _first_text(value: Any) -> str:
    """Return the first non-empty text value from a Crossref field."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        for item in value:
            text = _first_text(item)
            if text:
                return text
    return ""


def _date_from_field(value: Any) -> str:
    """Convert a Crossref date object to the required ``YYYY-MM-DD`` format."""
    if not isinstance(value, dict):
        return ""

    date_parts = value.get("date-parts")
    if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list):
        parts = date_parts[0]
        try:
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else 1
            day = int(parts[2]) if len(parts) > 2 else 1
            return datetime(year, month, day, tzinfo=UTC).date().isoformat()
        except (IndexError, TypeError, ValueError):
            pass

    date_time = value.get("date-time")
    if isinstance(date_time, str) and date_time.strip():
        try:
            parsed = datetime.fromisoformat(date_time.strip().replace("Z", "+00:00"))
            return parsed.date().isoformat()
        except ValueError:
            return date_time.strip()
    return ""


def _authors_from_item(item: dict[str, Any]) -> list[str]:
    authors: list[str] = []
    raw_authors = item.get("author", [])
    if not isinstance(raw_authors, list):
        return authors

    for author in raw_authors:
        if isinstance(author, str):
            name = author.strip()
        elif isinstance(author, dict):
            name = _first_text(author.get("name"))
            if not name:
                name = " ".join(
                    part
                    for part in (
                        _first_text(author.get("given")),
                        _first_text(author.get("family")),
                    )
                    if part
                )
        else:
            name = ""
        if name:
            authors.append(name)
    return authors


def _pdf_url_from_item(item: dict[str, Any]) -> str:
    links = item.get("link", [])
    if not isinstance(links, list):
        return ""
    for link in links:
        if not isinstance(link, dict):
            continue
        url = _first_text(link.get("URL"))
        content_type = _first_text(link.get("content-type")).lower()
        if url and (content_type == "application/pdf" or url.lower().endswith(".pdf")):
            return url
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref works response into a stable, flat record schema.

    Records without a DOI, title, or an abstract/description are excluded at
    ingestion time. Detailed quality filtering (for example summary length) is
    deliberately left to the cleaning stage.
    """
    if not isinstance(payload, dict):
        raise TypeError("Crossref payload must be a dictionary.")

    message = payload.get("message", {})
    items = message.get("items", []) if isinstance(message, dict) else []
    if not isinstance(items, list):
        raise ValueError("Crossref payload must contain message.items as a list.")

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        paper_id = _first_text(item.get("DOI"))
        title = _first_text(item.get("title"))
        summary = _first_text(item.get("abstract")) or _first_text(item.get("description"))
        if not paper_id or not title or not summary:
            continue

        raw_categories = item.get("subject", [])
        if isinstance(raw_categories, str):
            raw_categories = [raw_categories]
        categories = [
            category.strip()
            for category in raw_categories
            if isinstance(category, str) and category.strip()
        ] if isinstance(raw_categories, list) else []

        published = ""
        for key in ("published", "published-print", "published-online", "issued", "created"):
            published = _date_from_field(item.get(key))
            if published:
                break

        updated = ""
        for key in ("indexed", "deposited", "updated"):
            updated = _date_from_field(item.get(key))
            if updated:
                break

        abs_url = _first_text(item.get("URL"))
        if not abs_url:
            resource = item.get("resource", {})
            primary = resource.get("primary", {}) if isinstance(resource, dict) else {}
            abs_url = _first_text(primary.get("URL")) if isinstance(primary, dict) else ""

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=_authors_from_item(item),
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=_pdf_url_from_item(item),
                comment=_first_text(item.get("publisher")),
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref works with retry/backoff and persist both raw artifacts."""
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "day10-data-observability-lab/0.1 (Crossref metadata ingestion)",
    }

    response: requests.Response | None = None
    for attempt in range(MAX_ATTEMPTS):
        response = requests.get(
            CROSSREF_API_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code not in RETRYABLE_STATUS_CODES:
            break
        if attempt == MAX_ATTEMPTS - 1:
            break

        retry_after = getattr(response, "headers", {}).get("Retry-After", "")
        try:
            delay = max(0.0, float(retry_after))
        except (TypeError, ValueError):
            delay = float(2**attempt)
        time.sleep(delay)

    assert response is not None  # The loop always executes at least once.
    response.raise_for_status()

    # Preserve the successful HTTP body byte-for-byte for source auditing.
    ensure_parent(settings.paths.raw_api_response)
    raw_content = getattr(response, "content", b"")
    if not raw_content:
        raw_content = response.text.encode(getattr(response, "encoding", None) or "utf-8")
    settings.paths.raw_api_response.write_bytes(raw_content)

    payload = response.json()
    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load a parsed JSON snapshot and validate it against ``PaperRecord``."""
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Raw records file must contain a JSON list: {path}")

    records: list[PaperRecord] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Raw record at index {index} must be a JSON object.")
        try:
            records.append(PaperRecord(**item))
        except TypeError as exc:
            raise ValueError(f"Raw record at index {index} has an invalid schema.") from exc
    return records
