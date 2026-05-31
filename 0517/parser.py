"""HTML 解析：列表页与详情页字段提取"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

import config


def list_page_url(page: int) -> str:
    if page <= 1:
        return config.LIST_URL
    return f"{config.BASE_URL}/10462/13241/list_{page}.shtml"


def normalize_url(href: str) -> str:
    return urljoin(config.BASE_URL, href.strip())


def parse_list_items(html: str, page: int) -> list[dict]:
    """从列表页提取标题、列表日期、详情链接。"""
    soup = BeautifulSoup(html, "lxml")
    items: list[dict] = []
    container = soup.select_one("#dash-table") or soup.select_one(".mytabul")
    if not container:
        return items

    for li in container.select("li"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = a["href"].strip()
        if config.ONLY_SC_GOV_DETAIL and not href.startswith(config.LIST_PATH_PREFIX):
            continue
        title = (a.get("title") or a.get_text(strip=True) or "").strip()
        list_date = ""
        span = li.find("span")
        if span:
            m = re.search(r"\((\d{4}-\d{2}-\d{2})\)", span.get_text())
            if m:
                list_date = m.group(1)
        items.append(
            {
                "list_title": title,
                "list_date": list_date,
                "url": normalize_url(href),
                "list_page": page,
            }
        )
    return items


def _text(el) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.get_text(separator=" ", strip=True))


def parse_detail(html: str, url: str) -> dict:
    """从详情页提取标题、发布时间、来源、正文等。"""
    soup = BeautifulSoup(html, "lxml")

    title = ""
    ucap = soup.select_one("#articlecontent h2 UCAPTITLE")
    if ucap:
        title = _text(ucap).replace(" ", "")
    if not title:
        meta = soup.find("meta", attrs={"name": "ArticleTitle"})
        if meta and meta.get("content"):
            title = meta["content"].strip()

    publish_time = ""
    pub_meta = soup.find("meta", attrs={"name": "PubDate"})
    if pub_meta and pub_meta.get("content"):
        publish_time = pub_meta["content"].strip()
    if not publish_time:
        for li in soup.select("#articleattribute li"):
            t = li.get_text(strip=True)
            if re.search(r"\d{4}年\d{1,2}月\d{1,2}日", t):
                publish_time = t
                break

    source = ""
    src_meta = soup.find("meta", attrs={"name": "ContentSource"})
    if src_meta and src_meta.get("content"):
        source = src_meta["content"].strip()
    else:
        for li in soup.select("#articleattribute li"):
            t = li.get_text(strip=True)
            if t.startswith("来源"):
                source = re.sub(r"^来源[:：\s]*", "", t).strip()
                break

    author = ""
    author_meta = soup.find("meta", attrs={"name": "Author"})
    if author_meta and author_meta.get("content"):
        author = author_meta["content"].strip()
    else:
        zrbj = soup.select_one(".zrbj")
        if zrbj:
            m = re.search(r"责任编辑[:：\s]*(.+)", zrbj.get_text())
            if m:
                author = m.group(1).strip()

    column = ""
    col_meta = soup.find("meta", attrs={"name": "ColumnName"})
    if col_meta and col_meta.get("content"):
        column = col_meta["content"].strip()

    content = ""
    content_el = soup.select_one("#cmsArticleContent UCAPCONTENT") or soup.select_one(
        "#cmsArticleContent"
    )
    if content_el:
        for tag in content_el.find_all(["script", "style"]):
            tag.decompose()
        paragraphs = [
            p.strip() for p in content_el.stripped_strings if p.strip()
        ]
        content = "\n\n".join(paragraphs)

    description = ""
    desc_meta = soup.find("meta", attrs={"name": "Description"})
    if desc_meta and desc_meta.get("content"):
        description = desc_meta["content"].strip()

    return {
        "url": url,
        "title": title,
        "publish_time": publish_time,
        "source": source,
        "author": author,
        "column": column,
        "description": description,
        "content": content,
    }
