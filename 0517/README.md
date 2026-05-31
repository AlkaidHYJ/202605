# 四川省人民政府新闻爬虫（Crawl4AI）

课程项目：使用 [Crawl4AI](https://github.com/unclecode/crawl4ai) 爬取 [党中央国务院信息](https://www.sc.gov.cn/10462/13241/list.shtml) 栏目数据。

## 功能

1. **列表页**：采集每条新闻的列表标题、列表日期、详情链接（支持 30 页分页）
2. **详情页**：逐篇进入，采集新闻标题、发布时间、来源、责任编辑、栏目、摘要、正文

## 环境准备

```bash
cd c:\Users\ALKAID\Desktop\0517
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

默认使用 Crawl4AI **HTTP 模式**（无需安装浏览器）。若需 Playwright：

```bash
playwright install chromium
python main.py --browser --test
```

## 运行

```bash
# 测试模式（第1页 + 前3篇详情，推荐先跑通）
python main.py --test

# 仅爬前 2 页列表
python main.py --pages 2

# 全量爬取（约 900 条，耗时较长）
python main.py
```

## 输出

结果保存在 `output/` 目录：

| 文件 | 说明 |
|------|------|
| `news_data.json` | 完整 JSON |
| `news_data.csv` | Excel 可打开的 CSV（UTF-8 BOM） |

## 项目结构

```
0517/
├── config.py      # 配置（URL、并发、输出路径）
├── parser.py      # BeautifulSoup 解析列表/详情
├── scraper.py     # Crawl4AI 异步爬取主逻辑
├── main.py        # 命令行入口
└── requirements.txt
```

## 字段说明

| 字段 | 来源 |
|------|------|
| list_title | 列表页链接标题 |
| list_date | 列表页日期 `(YYYY-MM-DD)` |
| title | 详情页 `UCAPTITLE` |
| publish_time | 详情页发布时间 / `PubDate` meta |
| source | 来源（如新华社） |
| content | 正文 `#cmsArticleContent` |
| url | 详情页地址 |

默认仅爬取 `sc.gov.cn` 本站详情（`/10462/13241/`），跳过跳转 `www.gov.cn` 的外链。

## 数据可视化

爬取完成后，根据 JSON 生成统计图与 HTML 报告：

```bash
pip install matplotlib pandas   # 若尚未安装
python visualize.py
```

生成内容：

| 输出 | 说明 |
|------|------|
| `output/charts/*.png` | 日期趋势、来源分布、正文长度、标题高频词 |
| `output/visualization.html` | 汇总报告（浏览器打开） |

数据量较少时（如 `--test` 仅 3 条），图表仍可生成，建议先 `python main.py --pages 2` 再可视化，效果更好。
