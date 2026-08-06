from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
import webbrowser


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_DIR / "demo"
DATA_DIR = PROJECT_DIR / "data"


def _read_json(relative_path: str, default):
    path = DATA_DIR / relative_path
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _plain_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", without_tags).strip()


def _artifact(relative_path: str, label: str, kind: str) -> dict:
    path = DATA_DIR / relative_path
    return {
        "label": label,
        "kind": kind,
        "path": f"data/{Path(relative_path).as_posix()}",
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "updated_at": (
            datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
            if path.exists()
            else None
        ),
    }


def build_dashboard_payload() -> dict:
    raw_response = _read_json("raw/crossref_response.json", {"message": {"items": []}})
    raw_records = _read_json("raw/crossref_records.json", [])
    clean_records = _read_json("clean/papers_clean.json", [])
    corrupted_records = _read_json("clean/papers_clean_corrupted.json", [])
    repaired_records = _read_json("clean/papers_clean_repaired.json", [])
    test_set = _read_json("eval/test_set.json", [])
    embeddings = _read_json("embeddings/papers_embeddings.json", {"documents": []})
    corruption_log = _read_json("results/corruption_log.json", {"corrupted_records": []})

    states = {
        "baseline": {
            "label": "Baseline",
            "tone": "healthy",
            "metrics": _read_json("results/baseline_metrics.json", {}),
            "quality": _read_json("quality/baseline_quality.json", {}),
            "freshness": _read_json("quality/freshness_report.json", {}),
            "records": len(clean_records),
        },
        "corrupted": {
            "label": "Corrupted",
            "tone": "danger",
            "metrics": _read_json("results/corrupted_metrics.json", {}),
            "quality": _read_json("quality/corrupted_quality.json", {}),
            "freshness": _read_json("quality/corrupted_freshness_report.json", {}),
            "records": len(corrupted_records),
        },
        "repaired": {
            "label": "Repaired",
            "tone": "recovered",
            "metrics": _read_json("results/repaired_metrics.json", {}),
            "quality": _read_json("quality/repaired_quality.json", {}),
            "freshness": _read_json("quality/repaired_freshness_report.json", {}),
            "records": len(repaired_records),
        },
    }

    logged_corruptions = corruption_log.get("corrupted_records", [])
    corruption_counts = Counter(
        item.get("corruption_type", "unknown") for item in logged_corruptions
    )
    corruption_labels = {
        "blank_summary": "Blank summary",
        "stale_date": "Stale publication date",
        "duplicate_record": "Duplicate document",
        "noise_injection": "Injected text noise",
        "truncated_title": "Truncated title",
    }

    sample_question = test_set[0] if test_set else {}
    sample_ids = sample_question.get("ground_truth_doc_ids", [])
    sample_id = sample_ids[0] if sample_ids else (clean_records[0].get("paper_id") if clean_records else "")
    source_items = raw_response.get("message", {}).get("items", [])
    source_item = next((item for item in source_items if item.get("DOI") == sample_id), {})
    raw_item = next((item for item in raw_records if item.get("paper_id") == sample_id), {})
    clean_item = next((item for item in clean_records if item.get("paper_id") == sample_id), {})

    artifacts = [
        _artifact("raw/crossref_response.json", "Crossref response", "RAW"),
        _artifact("raw/crossref_records.json", "Parsed paper records", "RAW"),
        _artifact("clean/papers_clean.json", "Clean corpus", "CLEAN"),
        _artifact("embeddings/papers_embeddings.json", "Embedding manifest", "INDEX"),
        _artifact("eval/test_set.json", "Frozen evaluation set", "EVAL"),
        _artifact("results/baseline_metrics.json", "Baseline metrics", "RESULT"),
        _artifact("results/corrupted_metrics.json", "Corrupted metrics", "RESULT"),
        _artifact("results/repaired_metrics.json", "Repaired metrics", "RESULT"),
        _artifact("quality/baseline_quality.json", "Baseline quality", "QUALITY"),
        _artifact("results/corruption_log.json", "Corruption log", "LINEAGE"),
    ]

    pipeline = [
        {
            "id": "source",
            "eyebrow": "SOURCE",
            "label": "Crossref API",
            "value": len(source_items),
            "unit": "works",
            "detail": "Keyword query with abstract filter and retry/backoff.",
        },
        {
            "id": "raw",
            "eyebrow": "LANDING",
            "label": "Raw artifacts",
            "value": len(raw_records),
            "unit": "records",
            "detail": "Original response plus flat PaperRecord snapshot.",
        },
        {
            "id": "clean",
            "eyebrow": "TRANSFORM",
            "label": "Clean corpus",
            "value": len(clean_records),
            "unit": "papers",
            "detail": "Markup removed, authors flattened, freshness computed.",
        },
        {
            "id": "index",
            "eyebrow": "RETRIEVAL",
            "label": "Vector index",
            "value": len(embeddings.get("documents", [])),
            "unit": "vectors",
            "detail": "Embedding manifest backed by ChromaDB semantic search.",
        },
        {
            "id": "evaluate",
            "eyebrow": "EVALUATE",
            "label": "Frozen test set",
            "value": len(test_set),
            "unit": "questions",
            "detail": "The same factual questions across all three states.",
        },
        {
            "id": "observe",
            "eyebrow": "OBSERVE",
            "label": "Quality gates",
            "value": 3,
            "unit": "checks",
            "detail": "Completeness, uniqueness, and freshness from real rows.",
        },
        {
            "id": "repair",
            "eyebrow": "RECOVER",
            "label": "Repair loop",
            "value": len(repaired_records),
            "unit": "restored",
            "detail": "Rebuild from trusted raw records and re-evaluate.",
        },
    ]

    questions = [
        {
            "id": item.get("id"),
            "question": item.get("question"),
            "ground_truth": item.get("ground_truth"),
            "paper_id": (item.get("ground_truth_doc_ids") or [""])[0],
        }
        for item in test_set
    ]
    paper_preview = [
        {
            "paper_id": item.get("paper_id"),
            "title": item.get("title"),
            "authors": item.get("authors_joined"),
            "published": item.get("published"),
            "age_days": item.get("age_days"),
            "summary": item.get("summary", "")[:280],
        }
        for item in clean_records[:8]
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "project": {
            "name": "RAG Data Observatory",
            "team": "MeaterBeat",
            "owner": "Lương Đăng Doanh",
            "role": "Role 1 · Ingestion & Cleaning",
        },
        "overview": {
            "source_items": len(source_items),
            "raw_records": len(raw_records),
            "clean_records": len(clean_records),
            "evaluation_questions": len(test_set),
            "corruption_events": len(logged_corruptions),
        },
        "pipeline": pipeline,
        "states": states,
        "corruptions": [
            {
                "type": corruption_type,
                "label": corruption_labels.get(corruption_type, corruption_type.replace("_", " ").title()),
                "count": count,
            }
            for corruption_type, count in corruption_counts.items()
        ],
        "lineage": {
            "paper_id": sample_id,
            "source_title": (source_item.get("title") or [""])[0] if source_item else "",
            "raw_title": raw_item.get("title", ""),
            "clean_title": clean_item.get("title", ""),
            "raw_summary_preview": _plain_text(raw_item.get("summary", ""))[:180],
            "clean_summary_preview": clean_item.get("summary", "")[:180],
            "question": sample_question.get("question", ""),
            "ground_truth": sample_question.get("ground_truth", ""),
        },
        "artifacts": artifacts,
        "questions": questions,
        "papers": paper_preview,
    }


class DemoHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        request_path = self.path.split("?", 1)[0]
        if request_path == "/api/dashboard":
            try:
                payload = json.dumps(build_dashboard_payload(), ensure_ascii=False).encode("utf-8")
            except Exception as exc:  # pragma: no cover - visible in browser during demo
                payload = json.dumps({"error": str(exc)}).encode("utf-8")
                self.send_response(500)
            else:
                self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return
        if request_path == "/":
            self.path = "/index.html"
        super().do_GET()

    def log_message(self, message_format: str, *args) -> None:
        print(f"[demo] {self.address_string()} - {message_format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local RAG observability demo dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args()

    handler = partial(DemoHandler, directory=str(DEMO_DIR))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}"
    print(f"RAG Data Observatory is live at {url}")
    print("Press Ctrl+C to stop.")
    if args.open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping demo server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
