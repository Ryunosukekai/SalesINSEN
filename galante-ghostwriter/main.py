#!/usr/bin/env python3
"""
Galante Ghostwriter — CLI Entry Point.

Generates Galante-style marketing proposals from orientation notes.

Usage:
    python main.py --orien "URL_or_filepath" --client "デロンギ" --industry "家電"
    python main.py --file "./orien_notes.txt" --client "ヒラキ" --industry "靴小売"
    python main.py --orien "URL" --reference "ref_URL" --client "ABC-MART"
    python main.py --type "influencer" --orien "URL" --client "クライアント名"
    python main.py --demo
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import setup_logging

logger: logging.Logger | None = None


def _is_url(value: str) -> bool:
    """Check if a string looks like a URL."""
    return value.startswith("http://") or value.startswith("https://")


def _is_file(value: str) -> bool:
    """Check if a string looks like a file path that exists."""
    return Path(value).is_file()


def _send_slack_notification(
    client_name: str,
    proposal_title: str,
    output_path: str,
    gdocs_url: str | None,
    quality: dict[str, Any],
) -> None:
    """Send a Slack notification about the generated proposal."""
    from config import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID

    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        if logger:
            logger.info("Slack未設定 — 通知をスキップ")
        return

    try:
        from slack_sdk import WebClient
    except ImportError:
        if logger:
            logger.warning("slack-sdkが未インストール — 通知をスキップ")
        return

    client = WebClient(token=SLACK_BOT_TOKEN)

    needs_conf = quality.get("needs_confirmation", [])
    conf_text = ""
    if needs_conf:
        conf_items = "\n".join(f"  - {item}" for item in needs_conf[:5])
        conf_text = f"\n\n*要確認事項:*\n{conf_items}"

    score = quality.get("overall_score", "?")
    link_text = f"\n<{gdocs_url}|Google Docsで開く>" if gdocs_url else ""

    message = (
        f":page_facing_up: *提案書生成完了*\n"
        f"*クライアント:* {client_name}\n"
        f"*タイトル:* {proposal_title}\n"
        f"*品質スコア:* {score}/10\n"
        f"*ファイル:* `{output_path}`"
        f"{link_text}"
        f"{conf_text}"
    )

    try:
        client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=message)
        if logger:
            logger.info("Slack通知を送信しました")
    except Exception as e:
        if logger:
            logger.error("Slack通知の送信に失敗: %s", e)


def run_pipeline(
    orien_source: str | None = None,
    file_path: str | None = None,
    client_name: str = "",
    industry: str = "",
    proposal_type: str = "general",
    reference_source: str | None = None,
    demo: bool = False,
) -> dict[str, Any]:
    """Run the full proposal generation pipeline.

    Returns
    -------
    dict
        Pipeline result with keys: plan, sections, quality, markdown,
        output_path, gdocs_url.
    """
    from intake.context_assembler import ContextAssembler
    from generator.proposal_planner import plan_proposal
    from generator.section_writer import write_all_sections
    from generator.number_estimator import estimate_numbers
    from generator.quality_checker import check_quality
    from output.markdown_writer import render_proposal_markdown, write_proposal_file

    start = time.time()

    # ── STEP 0: Input ─────────────────────────────────────────────────────
    if demo:
        from config import DEMO_CLIENT, DEMO_INDUSTRY, DEMO_ORIEN_TEXT
        client_name = client_name or DEMO_CLIENT
        industry = industry or DEMO_INDUSTRY
        orien_text = DEMO_ORIEN_TEXT
        if logger:
            logger.info("デモモードで実行: %s (%s)", client_name, industry)
    else:
        orien_text = None

    assembler = ContextAssembler(
        client_name=client_name,
        industry=industry,
        proposal_type=proposal_type,
    )

    # Load orien data
    if demo and orien_text:
        assembler.add_orien_text(orien_text)
    elif file_path and _is_file(file_path):
        assembler.add_orien_file(file_path)
    elif orien_source:
        if _is_url(orien_source):
            try:
                assembler.add_orien_gdoc(orien_source)
            except (ImportError, RuntimeError) as e:
                if logger:
                    logger.warning("Google Docs読み取り失敗: %s — ファイルとして試行", e)
                if _is_file(orien_source):
                    assembler.add_orien_file(orien_source)
                else:
                    print(f"エラー: オリエン情報を読み取れません: {e}", file=sys.stderr)
                    sys.exit(1)
        elif _is_file(orien_source):
            assembler.add_orien_file(orien_source)
        else:
            # Treat as raw text (e.g. piped stdin)
            assembler.add_orien_text(orien_source)
    else:
        print("エラー: --orien, --file, または --demo を指定してください。", file=sys.stderr)
        sys.exit(1)

    # Load reference proposal
    if reference_source:
        if _is_url(reference_source):
            try:
                from intake.gdocs_reader import read_google_doc
                ref_text = read_google_doc(reference_source)
                assembler.add_reference_text(ref_text)
            except (ImportError, RuntimeError) as e:
                if logger:
                    logger.warning("参考提案の読み取り失敗: %s", e)
        elif _is_file(reference_source):
            ref_text = Path(reference_source).read_text(encoding="utf-8")
            assembler.add_reference_text(ref_text)

    context = assembler.assemble()

    print(f"\n{'='*60}")
    print(f"  Galante Ghostwriter — 提案書自動生成")
    print(f"  クライアント: {client_name}")
    print(f"  業界: {industry}")
    print(f"  タイプ: {proposal_type}")
    print(f"{'='*60}\n")

    # ── STEP 1: Plan ──────────────────────────────────────────────────────
    print("[STEP 1/4] 提案構成をプランニング中...")
    plan = plan_proposal(context)
    print(f"  → タイトル: {plan.get('proposal_title', '?')}")
    print(f"  → コンセプト: {plan.get('core_concept', '?')}")

    # ── STEP 2: Write ─────────────────────────────────────────────────────
    print("[STEP 2/4] 各セクションを執筆中...")
    sections = write_all_sections(plan, context)
    print(f"  → {len(sections)}セクション執筆完了")

    # ── STEP 2.5: Number Estimation ───────────────────────────────────────
    print("  → KPI・予算を推定中...")
    estimates = estimate_numbers(plan, context)
    context["estimates"] = estimates

    # ── STEP 3: Quality Check ─────────────────────────────────────────────
    print("[STEP 3/4] 品質チェック中...")
    quality = check_quality(sections, plan, context)
    score = quality.get("overall_score", "?")
    acceptable = quality.get("is_acceptable", False)
    print(f"  → スコア: {score}/10 ({'PASS' if acceptable else 'REVIEW NEEDED'})")

    # ── STEP 4: Output ────────────────────────────────────────────────────
    print("[STEP 4/4] 提案書を出力中...")
    markdown = render_proposal_markdown(plan, sections, quality, context)
    output_path = write_proposal_file(markdown, client_name)
    print(f"  → Markdown: {output_path}")

    # Google Docs output (if configured)
    gdocs_url: str | None = None
    try:
        from output.gdocs_writer import create_proposal_doc, is_configured
        if is_configured():
            gdocs_url = create_proposal_doc(
                markdown,
                plan.get("proposal_title", "Galante提案書"),
            )
            print(f"  → Google Docs: {gdocs_url}")
    except (ImportError, RuntimeError) as e:
        if logger:
            logger.info("Google Docs出力をスキップ: %s", e)

    # Slack notification
    _send_slack_notification(
        client_name=client_name,
        proposal_title=plan.get("proposal_title", ""),
        output_path=str(output_path),
        gdocs_url=gdocs_url,
        quality=quality,
    )

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  完了！ ({elapsed:.1f}秒)")
    if quality.get("needs_confirmation"):
        print(f"  ⚠ 要確認事項: {len(quality['needs_confirmation'])}件")
    print(f"{'='*60}\n")

    return {
        "plan": plan,
        "sections": sections,
        "quality": quality,
        "estimates": estimates,
        "markdown": markdown,
        "output_path": str(output_path),
        "gdocs_url": gdocs_url,
    }


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Galante Ghostwriter — 提案書自動生成エージェント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            "  python main.py --demo\n"
            '  python main.py --orien "URL" --client "デロンギ" --industry "家電"\n'
            '  python main.py --file "./notes.txt" --client "ヒラキ" --industry "靴小売"\n'
        ),
    )
    parser.add_argument(
        "--orien",
        help="オリエン情報（Google Docs URL、ファイルパス、またはテキスト）",
    )
    parser.add_argument(
        "--file",
        help="オリエンテキストファイルのパス",
    )
    parser.add_argument(
        "--client",
        default="",
        help="クライアント名",
    )
    parser.add_argument(
        "--industry",
        default="",
        help="業界",
    )
    parser.add_argument(
        "--type",
        dest="proposal_type",
        default="general",
        choices=["general", "influencer", "digital", "branding"],
        help="提案タイプ（デフォルト: general）",
    )
    parser.add_argument(
        "--reference",
        help="参考提案（Google Docs URL またはファイルパス）",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="デモモード（サンプルデータで実行、API不要）",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="ログレベル（デフォルト: INFO）",
    )

    args = parser.parse_args()

    global logger
    logger = setup_logging(args.log_level)

    if not args.demo and not args.orien and not args.file:
        # Check stdin
        if not sys.stdin.isatty():
            orien_text = sys.stdin.read()
            if orien_text.strip():
                args.orien = orien_text

    run_pipeline(
        orien_source=args.orien,
        file_path=args.file,
        client_name=args.client,
        industry=args.industry,
        proposal_type=args.proposal_type,
        reference_source=args.reference,
        demo=args.demo,
    )


if __name__ == "__main__":
    main()
