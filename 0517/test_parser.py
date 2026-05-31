"""本地解析测试（无需网络），使用已保存的样例 HTML。"""

from pathlib import Path

from parser import parse_detail, parse_list_items

ROOT = Path(__file__).parent


def main() -> None:
    list_html = (ROOT / "list_sample.html").read_text(encoding="utf-8")
    items = parse_list_items(list_html, page=1)
    assert len(items) >= 20, f"列表应有多条，实际 {len(items)}"
    print(f"[OK] 列表解析: {len(items)} 条，首条: {items[0]['list_title'][:50]}…")

    detail_html = (ROOT / "detail_sample.html").read_text(encoding="utf-8")
    detail = parse_detail(detail_html, items[0]["url"])
    assert detail["title"], "详情标题为空"
    assert detail["publish_time"], "发布时间为空"
    assert detail["content"], "正文为空"
    print(f"[OK] 详情标题: {detail['title'][:50]}…")
    print(f"[OK] 发布时间: {detail['publish_time']}")
    print(f"[OK] 来源: {detail['source']}")
    print(f"[OK] 正文长度: {len(detail['content'])} 字")
    print("\n全部本地解析测试通过。")


if __name__ == "__main__":
    main()
