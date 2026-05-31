@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo === 1. 本地解析测试（无需网络）===
python test_parser.py
if errorlevel 1 goto :fail

echo.
echo === 2. Crawl4AI 爬取测试（第1页 + 3篇详情）===
python main.py --test
if errorlevel 1 goto :fail

echo.
echo.
echo === 3. 生成可视化 ===
python visualize.py
if errorlevel 1 goto :fail

echo.
echo 完成。数据: output\news_data.json  报告: output\visualization.html
goto :end

:fail
echo 运行失败，请确认已执行: pip install -r requirements.txt
exit /b 1

:end
