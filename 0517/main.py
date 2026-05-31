"""
四川省人民政府网站爬虫 - 党中央国务院信息

用法:
  python main.py              # 爬取全部列表页及详情（约30页×30条）
  python main.py --test       # 仅第1页列表 + 前3篇详情（用于课程演示/调试）

首次运行前请安装依赖:
  pip install -r requirements.txt
  playwright install chromium   # 仅在使用 --browser 时需要
"""

from __future__ import annotations

import argparse
import sys

import config
from scraper import main as run_scraper


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="sc.gov.cn 新闻爬虫 (Crawl4AI)")
    p.add_argument(
        "--test",
        action="store_true",
        help="测试模式：仅爬第1页列表和前3篇详情",
    )
    p.add_argument(
        "--pages",
        type=int,
        default=0,
        metavar="N",
        help="限制列表页数（0=全部30页）",
    )
    p.add_argument(
        "--max-articles",
        type=int,
        default=0,
        metavar="N",
        help="限制文章总数（0=不限制）",
    )
    p.add_argument(
        "--browser",
        action="store_true",
        help="使用 Playwright 浏览器模式（默认 HTTP 模式）",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.test:
        config.MAX_LIST_PAGES = 1
        config.MAX_ARTICLES = 3
        config.MAX_CONCURRENT_DETAILS = 1
    if args.pages:
        config.MAX_LIST_PAGES = args.pages
    if args.max_articles:
        config.MAX_ARTICLES = args.max_articles
    if args.browser:
        config.USE_BROWSER = True

    try:
        run_scraper()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
