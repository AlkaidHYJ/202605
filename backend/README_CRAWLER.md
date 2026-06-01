# Crawler API 文档

后端提供爬虫与清洗相关接口，位于 `/api/v1/crawler`。

主要端点：

- `GET /api/v1/crawler/tasks` - 管理端：列出爬虫任务（管理员权限）
- `POST /api/v1/crawler/tasks` - 管理端：创建新爬虫任务（管理员权限），请求体示例：

```json
{
  "task_name": "示例任务",
  "source_url": "https://example.com/article/1",
  "schedule_cron": "0 */6 * * *",
  "parse_config": {
    "request": { "method": "GET", "headers": {"User-Agent":"Crawler"} },
    "parse": { "type": "css", "selector": "#content", "title_selector": "h1" },
    "output": { "mode": "markdown" },
    "runtime": { "use_browser": false }
  }
}
```

- `GET /api/v1/crawler/tasks/{task_id}` - 获取任务详情（管理员）
- `POST /api/v1/crawler/tasks/{task_id}/run` - 立即运行任务，可选 body: `{ "rule_id": 123 }`，如果提供 `rule_id`，会在入库前应用清洗规则（管理员）
- `GET /api/v1/crawler/tasks/{task_id}/results` - 列出任务的采集结果（管理员）
- `GET /api/v1/crawler/results/{result_id}` - 查看单条结果详情（管理员）
- `GET /api/v1/crawler/public-results` - 用户端：获取最近的公开采集结果（已清洗优先）
- `GET /api/v1/crawler/cleaning-rules` - 列出清洗规则（管理员）
- `POST /api/v1/crawler/cleaning-rules` - 创建清洗规则（管理员），请求体示例：

```json
{
  "rule_name": "默认清洗",
  "rule_dag": {
    "normalize_whitespace": true,
    "remove_empty_lines": true,
    "dedupe_lines": false,
    "min_length": 50,
    "fill_text": "暂无有效内容",
    "drop_if_contains": ["广告", "免责声明"],
    "replace_map": {"\u00a0": " "}
  }
}
```

数据模型：新增表 `crawler_document`，用于保存采集的 HTML、提取文本、markdown 及清洗结果。

注意：该文档仅为开发参考，接口安全依赖现有的管理员鉴权中间件。