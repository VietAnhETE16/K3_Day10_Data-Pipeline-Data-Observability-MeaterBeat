from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from typing import Any, Iterable

import pandas as pd

from core.config import load_settings
from core.utils import ensure_parent, normalize_whitespace, write_csv
from ingestion.crossref import PaperRecord


class _TextExtractor(HTMLParser):
    """Small dependency-free XML/HTML text extractor for Crossref JATS."""

    _BLOCK_TAGS = {
        "abstract",
        "br",
        "div",
        "jats:p",
        "jats:sec",
        "li",
        "p",
        "sec",
        "title",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._BLOCK_TAGS:
            self.parts.append(" ")


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = " ".join(str(item) for item in value if item is not None)
    parser = _TextExtractor()
    try:
        parser.feed(str(value))
        parser.close()
        text = "".join(parser.parts)
    except (TypeError, ValueError):
        text = str(value)
    return normalize_whitespace(text)


def _author_name(value: Any) -> str:
    if isinstance(value, dict):
        explicit_name = _clean_text(value.get("name"))
        if explicit_name:
            return explicit_name
        return normalize_whitespace(
            " ".join(
                part
                for part in (_clean_text(value.get("given")), _clean_text(value.get("family")))
                if part
            )
        )
    return _clean_text(value)


def _clean_list(values: Any, *, author_names: bool = False) -> list[str]:
    if values is None:
        candidates: Iterable[Any] = []
    elif isinstance(values, (list, tuple, set)):
        candidates = values
    else:
        candidates = [values]

    cleaned: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        text = _author_name(value) if author_names else _clean_text(value)
        key = text.casefold()
        if text and key not in seen:
            cleaned.append(text)
            seen.add(key)
    return cleaned


def _normalise_date(value: Any) -> tuple[str, pd.Timestamp | None]:
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return "", None
    timestamp = pd.Timestamp(parsed)
    return timestamp.date().isoformat(), timestamp


_CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "comment",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "age_days",
    "text_for_embedding",
]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw paper records into the retrieval-ready dataframe schema."""
    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.tz_localize("UTC")
    else:
        run_timestamp = run_timestamp.tz_convert("UTC")

    rows: list[dict[str, Any]] = []
    for record in records:
        paper_id = _clean_text(record.paper_id)
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        authors = _clean_list(record.authors, author_names=True)
        categories = _clean_list(record.categories)

        # A summary of exactly 100 characters is valid; only shorter values are dropped.
        if not paper_id or not title or len(summary) < 100:
            continue

        published, published_timestamp = _normalise_date(record.published)
        updated, _ = _normalise_date(record.updated)
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        primary_category = _clean_text(record.primary_category)
        if not primary_category and categories:
            primary_category = categories[0]

        age_days: Any
        if published_timestamp is None:
            age_days = pd.NA
        else:
            age_days = (run_timestamp.date() - published_timestamp.date()).days

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": _clean_text(record.abs_url),
                "pdf_url": _clean_text(record.pdf_url),
                "comment": _clean_text(record.comment),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": (
                    f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"
                ),
            }
        )

    if not rows:
        df = pd.DataFrame(columns=_CLEAN_COLUMNS).astype(
            {"summary_chars": "Int64", "age_days": "Int64"}
        )
    else:
        df = pd.DataFrame(rows, columns=_CLEAN_COLUMNS)
        df["summary_chars"] = df["summary_chars"].astype("Int64")
        df["age_days"] = df["age_days"].astype("Int64")
        df = df.drop_duplicates(subset=["paper_id"], keep="first")
        df = df.sort_values(
            by=["published", "paper_id"],
            ascending=[False, True],
            kind="stable",
            na_position="last",
        ).reset_index(drop=True)

    paths = load_settings().paths
    write_csv(df, paths.clean_csv)
    ensure_parent(paths.clean_json)
    df.to_json(
        paths.clean_json,
        orient="records",
        indent=2,
        force_ascii=False,
    )
    return df
