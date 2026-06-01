import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_crawl():
    # 模拟test3任务的配置
    source_url = "https://www.people.com.cn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    
    try:
        # 使用aiohttp直接爬取
        async with aiohttp.ClientSession() as session:
            async with session.get(source_url, headers=headers, timeout=60) as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    print(f"HTML长度: {len(html)} 字符")
                    
                    # 解析页面
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string if soup.title else "无标题"
                    print(f"页面标题: {title}")
                    
                    # 提取body内容
                    body_content = soup.find('body')
                    if body_content:
                        print("成功提取到body内容")
                        # 可以添加更多解析逻辑
                    else:
                        print("未找到body标签")
                    
                    print("\n爬取成功!")
                else:
                    print(f"爬取失败，状态码: {response.status}")
                    
    except Exception as e:
        print(f"发生异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_crawl())