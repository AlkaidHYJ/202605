"""爬虫配置：四川省人民政府 - 党中央国务院信息栏目"""

BASE_URL = "https://www.sc.gov.cn"
LIST_URL = "https://www.sc.gov.cn/10462/13241/list.shtml"
LIST_PATH_PREFIX = "/10462/13241/"

# 列表分页：第1页 list.shtml，第2页起 list_2.shtml … list_30.shtml
TOTAL_LIST_PAGES = 30

# 仅爬取本站详情页（排除跳转 www.gov.cn 的外链）
ONLY_SC_GOV_DETAIL = True

# True 时使用 Playwright 浏览器（需 playwright install chromium）
USE_BROWSER = False

# 并发与限速
MAX_CONCURRENT_DETAILS = 3
REQUEST_DELAY_SEC = 0.5

# 输出
OUTPUT_DIR = "output"
OUTPUT_JSON = "news_data.json"
OUTPUT_CSV = "news_data.csv"

# 调试：限制页数/条数，0 表示不限制
MAX_LIST_PAGES = 0
MAX_ARTICLES = 0
