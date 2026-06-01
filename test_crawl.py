import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import HTTPCrawlerConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy

async def test_crawl():
    # 模拟test3任务的配置
    source_url = "https://www.people.com.cn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    
    # 创建爬虫实例
    http_cfg = HTTPCrawlerConfig(headers=headers, follow_redirects=True)
    crawler = AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy(http_cfg))
    
    try:
        async with crawler:
            # 执行爬取
            result = await crawler.arun(
                url=source_url,
                config=CrawlerRunConfig(page_timeout=60000, wait_until="domcontentloaded")
            )
            
            if result.success:
                print("爬取成功!")
                print(f"状态码: {result.status_code}")
                print(f"页面标题: {result.title}")
                print(f"HTML长度: {len(result.html or result.cleaned_html or 0)} 字符")
                
                # 检查内容提取
                if result.html:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(result.html, 'html.parser')
                    body_content = soup.find('body')
                    if body_content:
                        print("成功提取到body内容")
                    else:
                        print("未找到body标签")
            else:
                print(f"爬取失败: {result.error_message}")
                
    except Exception as e:
        print(f"发生异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_crawl())