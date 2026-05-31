"""使用 Crawl4AI 爬取四川省人民政府 - 党中央国务院信息"""

from __future__ import annotations

import asyncio
import csv
import json
import time
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import HTTPCrawlerConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy

import config
from parser import list_page_url, parse_detail, parse_list_items

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _make_crawler() -> AsyncWebCrawler:
    """默认 HTTP 策略（页面为服务端渲染，无需浏览器）。"""
    if config.USE_BROWSER:
        return AsyncWebCrawler(
            config=BrowserConfig(headless=True, verbose=False, user_agent=USER_AGENT),
        )
    http_cfg = HTTPCrawlerConfig(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9"},
        follow_redirects=True,
    )
    return AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy(http_cfg))


def _run_config() -> CrawlerRunConfig:
    if config.USE_BROWSER:
        return CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=60000,
            delay_before_return_html=1.0,
        )
    return CrawlerRunConfig(page_timeout=60000)


async def _fetch_html(crawler: AsyncWebCrawler, url: str) -> str | None:
    result = await crawler.arun(url=url, config=_run_config())
    if not result.success:
        print(f"  [失败] {url}: {result.error_message}")
        return None
    return result.html or result.cleaned_html


async def collect_list_links(crawler: AsyncWebCrawler) -> list[dict]:
    """爬取所有列表页，汇总文章链接与列表标题。"""
    max_pages = config.MAX_LIST_PAGES or config.TOTAL_LIST_PAGES
    all_items: list[dict] = []
    seen_urls: set[str] = set()

    for page in range(1, max_pages + 1):
        url = list_page_url(page)
        print(f"[列表] 第 {page}/{max_pages} 页: {url}")
        html = await _fetch_html(crawler, url)
        if not html:
            continue
        items = parse_list_items(html, page)
        new_count = 0
        for item in items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)
                new_count += 1
        print(f"  本页 {len(items)} 条，新增 {new_count} 条，累计 {len(all_items)} 条")
        if config.MAX_ARTICLES and len(all_items) >= config.MAX_ARTICLES:
            all_items = all_items[: config.MAX_ARTICLES]
            break
        await asyncio.sleep(config.REQUEST_DELAY_SEC)

    return all_items


async def _fetch_one_detail(
    crawler: AsyncWebCrawler,
    sem: asyncio.Semaphore,
    index: int,
    total: int,
    list_item: dict,
) -> dict:
    async with sem:
        url = list_item["url"]
        print(f"[详情] ({index}/{total}) {list_item['list_title'][:40]}…")
        html = await _fetch_html(crawler, url)
        await asyncio.sleep(config.REQUEST_DELAY_SEC)
        if not html:
            return {
                **list_item,
                "title": "",
                "publish_time": "",
                "source": "",
                "author": "",
                "column": "",
                "description": "",
                "content": "",
                "crawl_ok": False,
            }
        detail = parse_detail(html, url)
        return {
            **list_item,
            **detail,
            "crawl_ok": bool(detail.get("content") or detail.get("title")),
        }


async def fetch_all_details(
    crawler: AsyncWebCrawler, list_items: list[dict]
) -> list[dict]:
    sem = asyncio.Semaphore(config.MAX_CONCURRENT_DETAILS)
    total = len(list_items)
    tasks = [
        _fetch_one_detail(crawler, sem, i + 1, total, item)
        for i, item in enumerate(list_items)
    ]
    return await asyncio.gather(*tasks)


def save_results(records: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / config.OUTPUT_JSON
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"已保存 JSON: {json_path}")

    csv_path = out_dir / config.OUTPUT_CSV
    fields = [
        "list_title",
        "list_date",
        "title",
        "publish_time",
        "source",
        "author",
        "column",
        "url",
        "list_page",
        "description",
        "content",
        "crawl_ok",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"已保存 CSV: {csv_path}")


async def run() -> list[dict]:
    out_dir = Path(config.OUTPUT_DIR)
    t0 = time.perf_counter()

    async with _make_crawler() as crawler:
        print("=" * 60)
        print("阶段 1：采集列表页（标题 + 链接）")
        print("=" * 60)
        list_items = await collect_list_links(crawler)
        if not list_items:
            print("未获取到任何列表项，请检查网络或网站结构。")
            return []

        print()
        print("=" * 60)
        print(f"阶段 2：进入详情页采集（共 {len(list_items)} 篇）")
        print("=" * 60)
        records = await fetch_all_details(crawler, list_items)

    ok = sum(1 for r in records if r.get("crawl_ok"))
    print()
    print(f"完成：成功 {ok}/{len(records)} 篇，耗时 {time.perf_counter() - t0:.1f}s")
    save_results(records, out_dir)
    return records


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
