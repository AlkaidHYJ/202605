from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import HTTPCrawlerConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from lxml import html as lxml_html

DEFAULT_PARSE_CONFIG: dict[str, Any] = {
    "request": {
        "method": "GET",
        "headers": {},
        "body": None,
    },
    "parse": {
        "type": "css",
        "selector": "body",
        "title_selector": "title",
    },
    "output": {
        "mode": "markdown",
    },
    "runtime": {
        "use_browser": False,
        "page_timeout": 60000,
        "wait_until": "domcontentloaded",
    },
}


def _safe_json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _merge_config(overrides: dict[str, Any]) -> dict[str, Any]:
    config = json.loads(json.dumps(DEFAULT_PARSE_CONFIG))
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key].update(value)
        else:
            config[key] = value
    return config


def _make_crawler(parse_config: dict[str, Any]) -> AsyncWebCrawler:
    runtime = parse_config.get("runtime") or {}
    headers = (parse_config.get("request") or {}).get("headers") or {}
    use_browser = bool(runtime.get("use_browser"))
    if use_browser:
        return AsyncWebCrawler(
            config=BrowserConfig(
                headless=True,
                verbose=False,
                user_agent=headers.get("User-Agent"),
            )
        )
    http_cfg = HTTPCrawlerConfig(headers=headers, follow_redirects=True)
    method = (parse_config.get("request") or {}).get("method")
    body = (parse_config.get("request") or {}).get("body")
    for attr, value in (("method", method), ("body", body), ("data", body)):
        if value is None:
            continue
        try:
            setattr(http_cfg, attr, value)
        except Exception:
            pass
    return AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy(http_cfg))


def _run_config(parse_config: dict[str, Any]) -> CrawlerRunConfig:
    runtime = parse_config.get("runtime") or {}
    page_timeout = int(runtime.get("page_timeout") or 60000)
    wait_until = runtime.get("wait_until") or "domcontentloaded"
    return CrawlerRunConfig(page_timeout=page_timeout, wait_until=wait_until)


def _extract_text_with_css(html: str, selector: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    nodes = soup.select(selector) if selector else []
    if not nodes:
        return "", ""
    raw_html = "\n".join(str(node) for node in nodes)
    text = "\n".join(node.get_text("\n", strip=True) for node in nodes)
    return raw_html, text


def _extract_text_with_xpath(html: str, selector: str) -> tuple[str, str]:
    if not selector:
        return "", ""
    tree = lxml_html.fromstring(html)
    nodes = tree.xpath(selector)
    if not nodes:
        return "", ""
    raw_chunks = []
    text_chunks = []
    for node in nodes:
        if hasattr(node, "text_content"):
            raw_chunks.append(lxml_html.tostring(node, encoding="unicode"))
            text_chunks.append(node.text_content())
        else:
            raw_chunks.append(str(node))
            text_chunks.append(str(node))
    return "\n".join(raw_chunks), "\n".join(text_chunks)


def _extract_title(html: str, parse_config: dict[str, Any]) -> str:
    selector = (parse_config.get("parse") or {}).get("title_selector") or "title"
    if not selector:
        return ""
    if (parse_config.get("parse") or {}).get("type") == "xpath":
        _, text = _extract_text_with_xpath(html, selector)
        return text.strip()
    _, text = _extract_text_with_css(html, selector)
    return text.strip()


def _normalize_lines(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)


def _to_markdown(text: str, title: str, source_url: str) -> str:
    body = _normalize_lines(text)
    parts = []
    if title:
        parts.append(f"# {title}")
    if source_url:
        parts.append(f"> Source: {source_url}")
    if body:
        parts.append(body)
    return "\n\n".join(parts).strip()


def _apply_cleaning_rule(markdown: str, rule: dict[str, Any]) -> tuple[str, int, str | None]:
    text = markdown or ""
    replace_map = rule.get("replace_map") or {}
    for key, value in replace_map.items():
        text = text.replace(str(key), str(value))

    fill_text = rule.get("fill_text")
    if not text.strip() and fill_text:
        text = str(fill_text)

    if rule.get("normalize_whitespace"):
        text = re.sub(r"[ \t]+", " ", text)

    if rule.get("remove_empty_lines"):
        text = "\n".join(line for line in text.splitlines() if line.strip())

    if rule.get("dedupe_lines"):
        seen = set()
        unique_lines = []
        for line in text.splitlines():
            if line in seen:
                continue
            seen.add(line)
            unique_lines.append(line)
        text = "\n".join(unique_lines)

    drop_if_contains = rule.get("drop_if_contains") or []
    for keyword in drop_if_contains:
        if keyword and keyword in text:
            return "", 2, f"contains:{keyword}"

    min_length = int(rule.get("min_length") or 0)
    if min_length and len(text.strip()) < min_length:
        return "", 2, f"min_length:{min_length}"

    return text.strip(), 1, None


async def crawl_once(source_url: str, parse_config_raw: str | None) -> dict[str, Any]:
    overrides = _safe_json_loads(parse_config_raw)
    parse_config = _merge_config(overrides)
    parser = parse_config.get("parse") or {}
    output_mode = (parse_config.get("output") or {}).get("mode") or "markdown"

    async with _make_crawler(parse_config) as crawler:
        result = await crawler.arun(url=source_url, config=_run_config(parse_config))
    if not result.success:
        return {
            "success": False,
            "error": result.error_message or "crawl_failed",
        }

    html = result.html or result.cleaned_html or ""
    parse_type = parser.get("type") or "css"
    selector = parser.get("selector") or "body"
    if parse_type == "xpath":
        raw_html, text = _extract_text_with_xpath(html, selector)
    else:
        raw_html, text = _extract_text_with_css(html, selector)

    title = _extract_title(html, parse_config)
    markdown = _to_markdown(text, title, source_url) if output_mode == "markdown" else text

    return {
        "success": True,
        "title": title,
        "raw_html": raw_html,
        "extracted_text": text,
        "markdown": markdown,
        "html": html,
    }


def clean_markdown(markdown: str | None, rule_raw: str | None) -> tuple[str | None, int, str | None]:
    if not rule_raw:
        return markdown, 0, None
    rule = _safe_json_loads(rule_raw)
    cleaned, status, reason = _apply_cleaning_rule(markdown or "", rule)
    return cleaned if status == 1 else "", status, reason
