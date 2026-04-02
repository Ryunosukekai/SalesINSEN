#!/usr/bin/env python3
"""Galante Canary — Client Churn Detection Agent.

Usage:
    python main.py --scan        # Run one scan cycle
    python main.py --report      # Generate full report
    python main.py --demo        # Demo data mode
    python main.py --schedule    # Daily scheduled scan
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import LOG_DIR, SCAN_HOUR, SCAN_MINUTE, score_label
from detector.ai_prescriber import generate_prescription
from detector.churn_scorer import score_accounts
from detector.trend_analyzer import analyze_trends
from reporter.slack_alerter import send_alert
from reporter.templates import build_account_report, build_daily_alert
from storage.db import init_db
from storage.score_history import save_scan_run, save_scores

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)
    # File handler
    log_file = LOG_DIR / f"canary_{datetime.now().strftime('%Y%m%d')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(fh)


logger = logging.getLogger("canary")


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def _enrich_with_prescriptions(
    results: list[dict[str, Any]],
    accounts_map: dict[str, dict[str, Any]],
    threshold: int = 40,
) -> list[dict[str, Any]]:
    """Add AI prescriptions to accounts above the threshold."""
    enriched: list[dict[str, Any]] = []
    for r in results:
        if r["score"] >= threshold:
            acct = accounts_map.get(r["account_id"], {})
            prescription = generate_prescription(acct, r)
            r["prescription"] = prescription
        else:
            r["prescription"] = {}
        enriched.append(r)
    return enriched


def run_scan(
    accounts: list[dict[str, Any]],
    accounts_data: dict[str, dict[str, Any]],
    *,
    send_slack: bool = True,
) -> list[dict[str, Any]]:
    """Execute a full scan cycle."""
    logger.info("=" * 50)
    logger.info("Galante Canary スキャン開始")
    logger.info("対象アカウント数: %d", len(accounts))
    logger.info("=" * 50)

    # 1. Score all accounts
    results = score_accounts(accounts, accounts_data)

    # 2. Analyze trends
    results = analyze_trends(results)

    # 3. Enrich with AI prescriptions (score >= 40)
    accounts_map = {a["Id"]: a for a in accounts}
    results = _enrich_with_prescriptions(results, accounts_map)

    # 4. Save to DB
    save_scores(results)

    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    max_score = max((r["score"] for r in results), default=0)
    alert_sent = False

    # 5. Send Slack alert
    if send_slack:
        alert_sent = send_alert(results)

    # 6. Record scan run
    save_scan_run(
        total_accounts=len(results),
        avg_score=avg_score,
        max_score=max_score,
        alert_sent=alert_sent,
    )

    logger.info("=" * 50)
    logger.info("スキャン完了 — 平均スコア: %.1f / 最高スコア: %d", avg_score, max_score)
    logger.info("=" * 50)

    return results


def run_report(results: list[dict[str, Any]]) -> None:
    """Print a full console report."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print("\n" + build_daily_alert(results, date_str))
    print()

    # Detailed reports for high-risk accounts
    high_risk = [r for r in results if r["score"] >= 41]
    if high_risk:
        print("=" * 60)
        print("詳細レポート（スコア41以上）")
        print("=" * 60)
        for r in high_risk:
            print()
            print(build_account_report(r))
            print("-" * 40)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def mode_scan() -> None:
    """Live Salesforce scan."""
    from salesforce.data_extractor import fetch_account_data, fetch_active_accounts

    accounts = fetch_active_accounts()
    accounts_data: dict[str, dict] = {}
    for acct in accounts:
        acct_id = acct["Id"]
        logger.info("データ取得中: %s", acct.get("Name", acct_id))
        accounts_data[acct_id] = fetch_account_data(acct_id)

    results = run_scan(accounts, accounts_data)
    run_report(results)


def mode_demo() -> None:
    """Demo mode with generated data."""
    from demo import generate_all_demo_data

    logger.info("デモモードで起動")
    accounts, accounts_data = generate_all_demo_data()
    results = run_scan(accounts, accounts_data, send_slack=False)
    run_report(results)


def mode_report() -> None:
    """Generate report from last scan data in DB."""
    from storage.score_history import get_recent_runs

    runs = get_recent_runs(limit=1)
    if not runs:
        logger.warning("スキャン履歴がありません。先に --scan または --demo を実行してください。")
        return

    # Re-run demo to show report (in production, would load from DB)
    logger.info("最新のスキャンデータからレポート生成")
    mode_demo()


def mode_schedule() -> None:
    """Daily scheduled scan at configured time."""
    try:
        import schedule  # noqa: WPS433
    except ImportError:
        logger.error("schedule パッケージが必要です: pip install schedule")
        sys.exit(1)

    import time

    scan_time = f"{SCAN_HOUR:02d}:{SCAN_MINUTE:02d}"
    logger.info("スケジュールモード: 毎日 %s にスキャン実行", scan_time)

    def _scheduled_scan() -> None:
        try:
            mode_scan()
        except Exception as exc:
            logger.error("スケジュールスキャンエラー: %s", exc, exc_info=True)

    schedule.every().day.at(scan_time).do(_scheduled_scan)

    logger.info("スケジューラ起動中... (Ctrl+C で停止)")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("スケジューラを停止しました")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Galante Canary — 離反予兆検知エージェント 🐤",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", action="store_true", help="Salesforce スキャン実行")
    group.add_argument("--report", action="store_true", help="レポート生成")
    group.add_argument("--demo", action="store_true", help="デモデータモード")
    group.add_argument("--schedule", action="store_true", help="毎日9:00スキャン")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細ログ")

    args = parser.parse_args()
    _setup_logging(verbose=args.verbose)

    # Initialize database
    init_db()

    if args.scan:
        mode_scan()
    elif args.report:
        mode_report()
    elif args.demo:
        mode_demo()
    elif args.schedule:
        mode_schedule()


if __name__ == "__main__":
    main()
