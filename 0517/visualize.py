"""
从爬取结果生成可视化图表与 HTML 报告。

用法:
  python visualize.py
  python visualize.py -i output/news_data.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import config

CHARTS_DIR = Path(config.OUTPUT_DIR) / "charts"
REPORT_HTML = Path(config.OUTPUT_DIR) / "visualization.html"


def _setup_chinese_font() -> None:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"未找到数据文件: {path}\n请先运行: python main.py --test"
        )
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        raise ValueError("数据为空，请先爬取更多新闻（如 python main.py --pages 2）")
    return data


def to_dataframe(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if "list_date" in df.columns:
        df["list_date"] = pd.to_datetime(df["list_date"], errors="coerce")
    if "publish_time" in df.columns:
        df["publish_time"] = pd.to_datetime(df["publish_time"], errors="coerce")
    df["content_len"] = df.get("content", pd.Series(dtype=str)).fillna("").str.len()
    df["date"] = df["list_date"]
    if "publish_time" in df.columns:
        missing = df["date"].isna()
        df.loc[missing, "date"] = df.loc[missing, "publish_time"].dt.normalize()
    return df


def plot_timeline(df: pd.DataFrame, out: Path) -> None:
    sub = df.dropna(subset=["date"]).copy()
    if sub.empty:
        return
    daily = sub.groupby(sub["date"].dt.date).size().reset_index(name="count")
    daily.columns = ["date", "count"]
    daily["date"] = pd.to_datetime(daily["date"])

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(daily["date"], daily["count"], width=0.8, color="#c41e3a", alpha=0.85)
    ax.set_title("新闻发布数量（按日期）", fontsize=14, pad=12)
    ax.set_xlabel("日期")
    ax.set_ylabel("篇数")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_sources(df: pd.DataFrame, out: Path) -> None:
    sources = df["source"].fillna("未知").replace("", "未知")
    counts = sources.value_counts()
    if counts.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = plt.cm.Set3(range(len(counts)))
    ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
    )
    ax.set_title("新闻来源分布", fontsize=14, pad=12)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_content_length(df: pd.DataFrame, out: Path) -> None:
    lengths = df["content_len"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if len(lengths) >= 5:
        bins = min(20, max(5, len(lengths) // 2))
        ax.hist(lengths, bins=bins, color="#2e6da4", edgecolor="white")
        ax.set_xlabel("字符数")
        ax.set_ylabel("篇数")
    else:
        ax.bar(range(len(lengths)), lengths, color="#2e6da4")
        ax.set_xticks(range(len(lengths)))
        ax.set_xticklabels([f"#{i + 1}" for i in range(len(lengths))], fontsize=9)
        ax.set_xlabel("新闻序号")
        ax.set_ylabel("字符数")
    ax.set_title("正文长度分布", fontsize=14, pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_top_keywords(df: pd.DataFrame, out: Path, top_n: int = 15) -> bool:
    stop = {
        "的", "了", "和", "在", "是", "与", "等", "为", "以", "将", "对",
        "中", "及", "要", "上", "下", "到", "从", "并", "于", "也", "都",
    }
    counter: Counter[str] = Counter()
    for title in df["title"].fillna(""):
        for w in re.findall(r"[\u4e00-\u9fff]{2,}", str(title)):
            if w not in stop:
                counter[w] += 1
    if not counter:
        return False

    items = counter.most_common(top_n)
    labels, values = zip(*items)
    fig, ax = plt.subplots(figsize=(9, max(4, len(items) * 0.35)))
    y_pos = range(len(labels))
    ax.barh(list(y_pos), values, color="#5cb85c", alpha=0.9)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_title("标题高频词（2字及以上）", fontsize=14, pad=12)
    ax.set_xlabel("出现次数")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return True


def build_html_report(
    df: pd.DataFrame,
    chart_files: dict[str, Path],
    total: int,
) -> str:
    titles = {
        "timeline": "① 发布日期趋势",
        "sources": "② 来源分布",
        "length": "③ 正文长度",
        "keywords": "④ 标题高频词",
    }
    sections = []
    for key, title in titles.items():
        path = chart_files.get(key)
        if path and path.exists():
            sections.append(
                f'<section><h2>{title}</h2>'
                f'<img src="charts/{path.name}" alt="{title}" style="max-width:100%;">'
                f"</section>"
            )

    date_min, date_max = df["date"].min(), df["date"].max()
    if pd.notna(date_min) and pd.notna(date_max):
        date_range = f"{date_min.strftime('%Y-%m-%d')} ~ {date_max.strftime('%Y-%m-%d')}"
    else:
        date_range = "—"

    ok = int(df["crawl_ok"].sum()) if "crawl_ok" in df.columns else total
    avg_len = int(df["content_len"].mean()) if len(df) else 0

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>新闻数据可视化报告</title>
  <style>
    body {{ font-family: "Microsoft YaHei", sans-serif; max-width: 960px; margin: 0 auto;
           padding: 24px; background: #f5f5f5; }}
    h1 {{ color: #b10001; border-bottom: 2px solid #b10001; padding-bottom: 8px; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
              gap: 12px; margin: 20px 0; }}
    .card {{ background: #fff; padding: 16px; border-radius: 8px;
             box-shadow: 0 1px 4px rgba(0,0,0,.08); text-align: center; }}
    .card b {{ font-size: 1.8em; color: #b10001; display: block; }}
    section {{ background: #fff; margin: 20px 0; padding: 20px; border-radius: 8px;
               box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
    section h2 {{ margin-top: 0; font-size: 1.1em; color: #333; }}
  </style>
</head>
<body>
  <h1>四川省人民政府 · 党中央国务院信息 — 数据可视化</h1>
  <div class="stats">
    <div class="card"><b>{total}</b>新闻总数</div>
    <div class="card"><b>{ok}</b>爬取成功</div>
    <div class="card"><b style="font-size:1em">{date_range}</b>日期范围</div>
    <div class="card"><b>{avg_len}</b>平均正文字数</div>
  </div>
  {"".join(sections)}
  <p style="color:#888;font-size:12px;text-align:center;">由 visualize.py 自动生成</p>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="新闻数据可视化")
    parser.add_argument(
        "-i",
        "--input",
        default=str(Path(config.OUTPUT_DIR) / config.OUTPUT_JSON),
        help="输入 JSON 路径",
    )
    args = parser.parse_args()

    _setup_chinese_font()
    input_path = Path(args.input)
    records = load_records(input_path)
    df = to_dataframe(records)

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    charts: dict[str, Path] = {
        "timeline": CHARTS_DIR / "01_timeline.png",
        "sources": CHARTS_DIR / "02_sources.png",
        "length": CHARTS_DIR / "03_content_length.png",
        "keywords": CHARTS_DIR / "04_keywords.png",
    }

    plot_timeline(df, charts["timeline"])
    plot_sources(df, charts["sources"])
    plot_content_length(df, charts["length"])
    if not plot_top_keywords(df, charts["keywords"]):
        charts.pop("keywords")

    html = build_html_report(df, charts, len(df))
    REPORT_HTML.write_text(html, encoding="utf-8")

    print(f"共 {len(df)} 条记录")
    print(f"图表目录: {CHARTS_DIR.resolve()}")
    for name, p in charts.items():
        if p.exists():
            print(f"  - {p.name}")
    print(f"HTML 报告: {REPORT_HTML.resolve()}")
    print("用浏览器打开 visualization.html 即可查看。")


if __name__ == "__main__":
    main()
