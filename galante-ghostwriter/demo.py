#!/usr/bin/env python3
"""
Galante Ghostwriter — Demo Mode.

Runs the full pipeline with hardcoded sample orien data.
No API keys required — uses placeholder content when AI is unavailable.

Usage:
    python demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import setup_logging


def main() -> None:
    """Run the demo pipeline."""
    logger = setup_logging("INFO")

    print(
        "\n"
        "╔══════════════════════════════════════════════════════════╗\n"
        "║        Galante Ghostwriter — デモモード                 ║\n"
        "║                                                        ║\n"
        "║  サンプルのオリエン情報から提案書を自動生成します。     ║\n"
        "║  ANTHROPIC_API_KEY が設定されていれば AI を使用し、     ║\n"
        "║  未設定の場合はプレースホルダーで出力します。           ║\n"
        "╚══════════════════════════════════════════════════════════╝\n"
    )

    from main import run_pipeline

    result = run_pipeline(demo=True)

    # Print summary
    print("\n--- デモ結果サマリー ---")
    print(f"提案タイトル: {result['plan'].get('proposal_title', '?')}")
    print(f"コアコンセプト: {result['plan'].get('core_concept', '?')}")
    print(f"セクション数: {len(result['sections'])}")
    print(f"品質スコア: {result['quality'].get('overall_score', '?')}/10")
    print(f"出力ファイル: {result['output_path']}")

    if result.get("gdocs_url"):
        print(f"Google Docs: {result['gdocs_url']}")

    # Show the generated Markdown preview (first 80 lines)
    print("\n--- 提案書プレビュー (先頭80行) ---\n")
    lines = result["markdown"].split("\n")
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"\n... (残り {len(lines) - 80} 行)")

    print("\n--- デモ完了 ---\n")


if __name__ == "__main__":
    main()
