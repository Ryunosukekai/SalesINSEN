"""Galante Fortune Teller — メインCLIエントリポイント.

Usage:
    python main.py --daily        # 日次レポート
    python main.py --weekly       # 週次サマリー（月曜朝）
    python main.py --monthly      # 月次レポート（月初）
    python main.py --demo         # デモデータ・DRY_RUN
    python main.py --schedule     # スケジュール実行
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

# プロジェクトルートを sys.path に追加
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config import AppConfig
from analyzer.pipeline_analyzer import PipelineAnalyzer
from analyzer.forecast_engine import ForecastEngine
from analyzer.alert_detector import AlertDetector
from analyzer.ai_commentator import AICommentator
from reporter.slack_reporter import SlackReporter
from reporter.templates import DailyTemplate, WeeklyTemplate, MonthlyTemplate
from storage.db import Database
from storage.history import ForecastHistory

logger = logging.getLogger("fortune_teller")


# ======================================================================
# レポート実行
# ======================================================================
def run_daily(config: AppConfig, use_demo: bool = False) -> None:
    """日次レポートを実行."""
    logger.info("=" * 60)
    logger.info("日次レポート開始: %s", datetime.now().isoformat())
    logger.info("=" * 60)

    opportunities, closed_won = _fetch_data(config, use_demo)

    # 分析
    analyzer = PipelineAnalyzer(config)
    summary = analyzer.summarize(opportunities, closed_won)

    engine = ForecastEngine(config)
    forecast = engine.generate(opportunities, closed_won)

    detector = AlertDetector(config)
    alerts = detector.detect(opportunities)

    commentator = AICommentator(config)
    ai_advice = commentator.generate_advice(summary, forecast, alerts)

    # レポート生成
    message = DailyTemplate.render(forecast, alerts, ai_advice)

    # Slack投稿
    reporter = SlackReporter(config)
    success = reporter.post(message)

    # 履歴保存
    _save_history(config, forecast, summary, alerts, "daily")

    _log_summary(forecast, alerts, success)


def run_weekly(config: AppConfig, use_demo: bool = False) -> None:
    """週次レポートを実行."""
    logger.info("=" * 60)
    logger.info("週次レポート開始: %s", datetime.now().isoformat())
    logger.info("=" * 60)

    opportunities, closed_won = _fetch_data(config, use_demo)

    # 先週の受注/失注
    if use_demo:
        from demo import generate_demo_weekly_data
        weekly_won, weekly_lost = generate_demo_weekly_data()
    else:
        from salesforce.data_extractor import DataExtractor
        extractor = DataExtractor(config)
        weekly_won, weekly_lost = extractor.fetch_weekly_won_lost()

    # 分析
    analyzer = PipelineAnalyzer(config)
    summary = analyzer.summarize(opportunities, closed_won)

    engine = ForecastEngine(config)
    forecast = engine.generate(opportunities, closed_won)

    detector = AlertDetector(config)
    alerts = detector.detect(opportunities)

    commentator = AICommentator(config)
    ai_advice = commentator.generate_advice(summary, forecast, alerts)

    # 履歴データ取得
    db = Database(config.db_path)
    history = ForecastHistory(db)
    close_rate_trend = history.get_close_rate_trend(weeks=4)
    pipeline_history = history.get_pipeline_history(days=60)

    # レポート生成
    message = WeeklyTemplate.render(
        forecast, alerts, ai_advice,
        weekly_won=weekly_won,
        weekly_lost=weekly_lost,
        close_rate_trend=close_rate_trend,
        pipeline_history=pipeline_history,
    )

    reporter = SlackReporter(config)
    success = reporter.post(message)

    _save_history(config, forecast, summary, alerts, "weekly")
    db.close()

    _log_summary(forecast, alerts, success)


def run_monthly(config: AppConfig, use_demo: bool = False) -> None:
    """月次レポートを実行."""
    logger.info("=" * 60)
    logger.info("月次レポート開始: %s", datetime.now().isoformat())
    logger.info("=" * 60)

    opportunities, closed_won = _fetch_data(config, use_demo)

    analyzer = PipelineAnalyzer(config)
    summary = analyzer.summarize(opportunities, closed_won)

    engine = ForecastEngine(config)
    forecast = engine.generate(opportunities, closed_won)

    detector = AlertDetector(config)
    alerts = detector.detect(opportunities)

    commentator = AICommentator(config)
    ai_advice = commentator.generate_advice(summary, forecast, alerts)

    # 月次履歴
    db = Database(config.db_path)
    history = ForecastHistory(db)
    monthly_history = history.get_monthly_actuals(months=12)

    message = MonthlyTemplate.render(
        forecast, alerts, ai_advice,
        pipeline_summary=summary,
        monthly_history=monthly_history,
    )

    reporter = SlackReporter(config)
    success = reporter.post(message)

    _save_history(config, forecast, summary, alerts, "monthly")
    db.close()

    _log_summary(forecast, alerts, success)


# ======================================================================
# ヘルパー
# ======================================================================
def _fetch_data(
    config: AppConfig, use_demo: bool,
) -> tuple[list, list]:
    """データ取得（デモ or Salesforce）."""
    if use_demo:
        from demo import generate_demo_opportunities, generate_demo_closed_won
        logger.info("デモデータを使用します（Salesforce接続なし）")
        return generate_demo_opportunities(), generate_demo_closed_won()
    else:
        from salesforce.data_extractor import DataExtractor
        extractor = DataExtractor(config)
        opps = extractor.fetch_open_pipeline(months_ahead=config.forecast.forecast_months)
        closed = extractor.fetch_closed_won_this_month()
        return opps, closed


def _save_history(
    config: AppConfig,
    forecast: dict,
    summary: dict,
    alerts: list,
    report_type: str,
) -> None:
    """履歴をSQLiteに保存."""
    try:
        db = Database(config.db_path)
        history = ForecastHistory(db)
        today = date.today()
        history.save_snapshot(today, report_type, forecast, len(alerts))
        history.save_pipeline_snapshot(today, summary)
        db.close()
        logger.info("履歴を保存しました")
    except Exception as exc:
        logger.warning("履歴保存に失敗: %s", exc)


def _log_summary(forecast: dict, alerts: list, success: bool) -> None:
    """サマリーをログ出力."""
    current = forecast.get("current_month", {})
    status = "成功" if success else "失敗"
    logger.info(
        "サマリー — 加重予測: ¥%s / アラート: %d件 / 送信: %s",
        f"{current.get('weighted', 0):,}",
        len(alerts),
        status,
    )


# ======================================================================
# スケジューラ
# ======================================================================
def run_schedule(config: AppConfig, use_demo: bool = False) -> None:
    """スケジュール実行モード."""
    import schedule as sched

    daily_time = config.scheduler.daily_run_time.strftime("%H:%M")
    weekly_time = config.scheduler.weekly_run_time.strftime("%H:%M")
    monthly_time = config.scheduler.monthly_run_time.strftime("%H:%M")

    logger.info("スケジュール登録:")
    logger.info("  日次: 毎日 %s", daily_time)
    logger.info("  週次: 毎週月曜 %s", weekly_time)
    logger.info("  月次: 毎月1日 %s", monthly_time)

    # 日次: 毎日
    sched.every().day.at(daily_time).do(run_daily, config, use_demo)

    # 週次: 月曜
    sched.every().monday.at(weekly_time).do(run_weekly, config, use_demo)

    # 月次: 毎日チェックして1日のみ実行
    def monthly_check() -> None:
        if date.today().day == 1:
            run_monthly(config, use_demo)

    sched.every().day.at(monthly_time).do(monthly_check)

    # 初回即時実行
    logger.info("初回レポートを即時実行します...")
    run_daily(config, use_demo=use_demo)

    logger.info("スケジューラ起動中... (Ctrl+C で停止)")
    while True:
        sched.run_pending()
        time.sleep(60)


# ======================================================================
# CLI
# ======================================================================
def main() -> None:
    """CLI エントリポイント."""
    parser = argparse.ArgumentParser(
        description="Galante Fortune Teller — 売上パイプライン予測エージェント"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--daily", action="store_true", help="日次レポート")
    mode.add_argument("--weekly", action="store_true", help="週次サマリー")
    mode.add_argument("--monthly", action="store_true", help="月次レポート")
    mode.add_argument("--schedule", action="store_true", help="スケジュール実行")
    parser.add_argument("--demo", action="store_true", help="デモデータ使用（SF接続不要）")
    args = parser.parse_args()

    config = AppConfig()

    # デモモードの場合は DRY_RUN を強制
    if args.demo:
        config.dry_run = True

    # ログ設定
    log_dir = _PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                str(log_dir / f"fortune_teller_{date.today().isoformat()}.log"),
                encoding="utf-8",
            ),
        ],
    )

    if args.schedule:
        run_schedule(config, use_demo=args.demo)
    elif args.weekly:
        run_weekly(config, use_demo=args.demo)
    elif args.monthly:
        run_monthly(config, use_demo=args.demo)
    else:
        # デフォルトは日次
        run_daily(config, use_demo=args.demo)


if __name__ == "__main__":
    main()
