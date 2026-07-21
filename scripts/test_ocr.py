"""测试扫描件 OCR（按当前 OCR_PROVIDER 配置：百度云 API 或本地 PaddleOCR）。

用法：
    python scripts/test_ocr.py path/to/图片或扫描件.pdf
    python scripts/test_ocr.py path/to/合同扫描页.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.engine.parser import parse_file  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python scripts/test_ocr.py <图片或扫描件PDF路径>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"文件不存在: {path}")
        sys.exit(1)

    print("=" * 60)
    print("OCR_PROVIDER :", settings.OCR_PROVIDER)
    if settings.OCR_PROVIDER == "baidu_api":
        ak = settings.BAIDU_OCR_API_KEY or ""
        sk = settings.BAIDU_OCR_SECRET_KEY or ""
        print("百度 AK :", (ak[:8] + "...") if ak else "(空)")
        print("百度 SK :", ("已配置" if sk else "(空)"))
        if not (ak and sk):
            print("⚠️  OCR_PROVIDER=baidu_api 但 AK/SK 为空，请在 .env 配置后重试。")
    print("=" * 60)

    result = parse_file(path)
    meta = result.get("ocr_meta", {})
    print("\nocr_meta:", meta)
    print("\n--- 识别文本（前 800 字）---")
    print(result.get("text", "")[:800])
    if result.get("tables"):
        print("\n--- 表格还原 ---")
        for i, t in enumerate(result["tables"], 1):
            print(f"[表 {i}]", t[:300])


if __name__ == "__main__":
    main()
