"""Main entry point for the Sales Forecast Agent.

Usage:
    # Run once immediately
    python -m sales_forecast_agent

    # Run with scheduler (daily at configured time)
    python -m sales_forecast_agent --schedule

    # Dry run (print to console instead of Slack)
    DRY_RUN=true python -m sales_forecast_agent

    # Use demo data (no Salesforce connection needed)
    python -m sales_forecast_agent --demo
"""

import argparse
import logging
import sys
import time
from datetime import datetime

import schedule

from .config import AgentConfig
from .demo import generate_demo_opportunities
from .forecast_engine import ForecastEngine
from .salesforce_client import SalesforceClient
from .slack_notifier import SlackNotifier

logger = logging.getLogger("sales_forecast_agent")


def run_forecast(config: AgentConfig, use_demo: bool = False) -> None:
    """Execute a single forecast cycle."""
    logger.info("=" * 60)
    logger.info("Sales Forecast Agent starting at %s", datetime.now().isoformat())
    logger.info("=" * 60)

    # 1. Fetch pipeline data
    if use_demo:
        logger.info("Using demo data (no Salesforce connection).")
        opportunities = generate_demo_opportunities()
    else:
        client = SalesforceClient(config)
        opportunities = client.fetch_open_opportunities(
            months_ahead=config.forecast.forecast_months
        )

        # Enrich with close-date change history
        opp_ids = [o.id for o in opportunities]
        history = client.fetch_close_date_history(opp_ids)
        for opp in opportunities:
            opp.close_date_change_count = history.get(opp.id, 0)

    logger.info("Processing %d opportunities...", len(opportunities))

    # 2. Generate forecast
    engine = ForecastEngine(config)
    report = engine.generate_report(opportunities)

    # 3. Post to Slack
    notifier = SlackNotifier(config)
    success = notifier.send_report(report)

    if success:
        logger.info("Forecast report sent successfully.")
    else:
        logger.error("Failed to send forecast report.")

    # 4. Log summary
    logger.info(
        "Summary — This month: %.0f万円 (%.1f%% of target), "
        "Danger signals: %d, Valley: %s",
        report.current_month.weighted_forecast,
        report.current_month.attainment_pct,
        len(report.danger_signals),
        f"{report.valley_month.month.year}/{report.valley_month.month.month}"
        if report.valley_month
        else "N/A",
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sales Forecast Agent - The Fortune Teller"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a daily schedule instead of once",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo data instead of connecting to Salesforce",
    )
    args = parser.parse_args()

    config = AgentConfig()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.schedule:
        run_time = config.scheduler.daily_run_time.strftime("%H:%M")
        logger.info(
            "Scheduling daily forecast at %s (%s)",
            run_time,
            config.scheduler.timezone,
        )
        schedule.every().day.at(run_time).do(run_forecast, config, args.demo)

        # Also run immediately on start
        run_forecast(config, use_demo=args.demo)

        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_forecast(config, use_demo=args.demo)


if __name__ == "__main__":
    main()
