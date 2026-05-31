import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
META_PATH = DATA_DIR / "metadata.json"

app = FastAPI(title="RAG Service")
metadata: list[dict[str, Any]] = []
MIN_SCORE = float((__import__("os").getenv("RAG_MIN_SCORE", "0.4")))


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)


class SearchResponse(BaseModel):
    content: str
    sources: list[dict[str, Any]]


def _load_metadata() -> None:
    global metadata
    if not META_PATH.exists():
        metadata = []
        return
    with META_PATH.open("r", encoding="utf-8") as f:
        metadata = json.load(f)


def _normalize_text(value: str) -> str:
    return "".join(value.split()).lower()


def _query_ngrams(query: str) -> list[str]:
    cleaned = _normalize_text(query)
    if not cleaned:
        return []
    if len(cleaned) <= 2:
        return [cleaned]
    ngrams = set()
    for size in (2, 3):
        if len(cleaned) >= size:
            for index in range(len(cleaned) - size + 1):
                ngrams.add(cleaned[index : index + size])
    return list(ngrams)


def _lexical_score(query: str, text: str) -> float:
    query_norm = _normalize_text(query)
    text_norm = _normalize_text(text)
    if not query_norm or not text_norm:
        return 0.0
    exact_count = text_norm.count(query_norm)
    if exact_count:
        return 2.0 + min(exact_count, 5) * 0.2
    grams = _query_ngrams(query_norm)
    if not grams:
        return 0.0
    matched = sum(1 for gram in grams if gram in text_norm)
    return matched / len(grams)


def _format_content(hits: list[dict[str, Any]]) -> str:
    lines = []
    for hit in hits:
        snippet = hit["text"].strip().replace("\n", " ")
        if len(snippet) > 240:
            snippet = snippet[:237] + "..."
        lines.append(f"- {snippet}")
    return "\n".join(lines)


def _extract_location_tokens(query: str) -> list[str]:
    tokens = []
    for keyword in ("雅安", "成都", "都江堰", "温江", "雨城", "校区"):
        if keyword in query:
            tokens.append(keyword)
    return tokens


def _extract_address_snippets(query: str, text: str) -> list[str]:
    if "地址" not in query:
        return []
    locations = [loc for loc in ("雅安", "成都", "都江堰") if loc in query]
    location_part = "|".join(locations) if locations else "雅安|成都|都江堰"
    pattern = rf"({location_part}).{{0,80}}?地址[^。；;\n]*?号"
    matches = []
    for match in re.finditer(pattern, text):
        snippet = match.group(0).strip()
        if snippet:
            matches.append(snippet)
    return matches


def _extract_relevant_sentences(query: str, text: str) -> list[str]:
    address_hits = _extract_address_snippets(query, text)
    if address_hits:
        return address_hits
    keywords = ("地址", "校区", "住所地", "位于", "地址为", "法定住所")
    tokens = _extract_location_tokens(query)
    sentences = [s.strip() for s in _split_sentences(text) if s.strip()]
    matches = []
    for sentence in sentences:
        if not any(keyword in sentence for keyword in keywords):
            continue
        if tokens and not any(token in sentence for token in tokens):
            continue
        matches.append(sentence)
    return matches


def _split_sentences(text: str) -> list[str]:
    return [s for s in text.replace("\n", " ").split("。") if s]


@app.on_event("startup")
def startup() -> None:
    _load_metadata()


@app.post("/rag/search", response_model=SearchResponse)
def rag_search(body: SearchRequest) -> SearchResponse:
    if not metadata:
        raise HTTPException(503, "Index not ready. Run indexer.py first.")

    scored: list[dict[str, Any]] = []
    for meta in metadata:
        text = str(meta.get("text", ""))
        score = _lexical_score(body.query, text)
        if score < MIN_SCORE:
            continue
        scored.append({
            "text": text,
            "page": meta.get("page"),
            "source": meta.get("source"),
            "score": score,
        })

    if not scored:
        loose_tokens = _extract_location_tokens(body.query) or ["校区", "地址", "住所地"]
        for meta in metadata:
            text = str(meta.get("text", ""))
            if any(token in text for token in loose_tokens):
                scored.append({
                    "text": text,
                    "page": meta.get("page"),
                    "source": meta.get("source"),
                    "score": 0.1,
                })
                if len(scored) >= body.top_k:
                    break
        if not scored:
            return SearchResponse(
                content="未检索到相关内容，请尝试更具体的问题。",
                sources=[],
            )

    scored.sort(key=lambda item: (item.get("score", 0.0), -int(item.get("page") or 0), -len(str(item.get("text", "")))), reverse=True)
    hits = scored[: body.top_k]

    extracted: list[str] = []
    for hit in hits:
        text = str(hit.get("text", ""))
        extracted.extend(_extract_relevant_sentences(body.query, text))
        if len(extracted) >= body.top_k:
            break

    content = _format_content(hits)
    if extracted:
        content = "\n".join(f"- {item}" for item in extracted[: body.top_k])

    return SearchResponse(
        content=content,
        sources=[
            {
                "title": hit.get("source"),
                "page": hit.get("page"),
                "score": hit.get("score"),
            }
            for hit in hits
        ],
    )
