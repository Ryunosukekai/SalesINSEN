"""デモデータ生成器 — Salesforce 不要で動作確認可能."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from salesforce.data_extractor import DealType, make_opportunity


def generate_demo_opportunities() -> list[dict[str, Any]]:
    """リアルなデモ商談データを生成."""
    today = date.today()
    random.seed(42)

    accounts = [
        "東京商事株式会社", "大阪製造株式会社", "名古屋テック合同会社",
        "福岡サービス株式会社", "札幌ソリューションズ", "横浜コンサル株式会社",
        "京都デジタル株式会社", "神戸エンジニアリング", "仙台クリエイト株式会社",
        "広島イノベーション株式会社", "千葉ロジスティクス", "埼玉ファイナンス株式会社",
        "新宿メディア株式会社", "渋谷テクノロジーズ", "品川ソリューション株式会社",
    ]

    owners = ["田中太郎", "佐藤花子", "鈴木一郎", "高橋美咲", "渡辺健太"]

    stages_with_prob = [
        ("リード", 0.10),
        ("ヒアリング", 0.20),
        ("課題特定", 0.35),
        ("提案", 0.50),
        ("見積提示", 0.70),
        ("最終交渉", 0.85),
    ]

    opportunities: list[dict[str, Any]] = []

    # メインの商談群（30件）
    for i in range(30):
        stage, prob = random.choice(stages_with_prob)
        deal_type = random.choice([DealType.NEW, DealType.NEW, DealType.EXISTING])
        account = random.choice(accounts)

        month_offset = random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
        close_day = random.randint(1, 28)
        close_month = today.month + month_offset
        close_year = today.year + (close_month - 1) // 12
        close_month = (close_month - 1) % 12 + 1
        close_date = date(close_year, close_month, close_day)

        # 金額は円（万円ではない）
        amount = random.choice([
            500_000, 800_000, 1_000_000, 1_500_000, 2_000_000,
            2_500_000, 3_000_000, 5_000_000, 8_000_000, 10_000_000,
        ])
        created_days_ago = random.randint(5, 90)
        last_activity_days_ago = random.randint(0, 30)

        opp = make_opportunity(
            id=f"006DEMO{i:05d}",
            name=f"{account} - {'新規導入' if deal_type == DealType.NEW else '契約更新'} #{i+1:03d}",
            amount=amount,
            stage=stage,
            close_date=close_date,
            deal_type=deal_type,
            owner_name=random.choice(owners),
            account_name=account,
            probability=prob,
            created_date=today - timedelta(days=created_days_ago),
            last_activity_date=today - timedelta(days=last_activity_days_ago),
            days_since_last_activity=last_activity_days_ago,
            close_date_change_count=random.choices([0, 1, 2, 3], weights=[0.5, 0.3, 0.15, 0.05])[0],
            next_step=random.choice([
                "提案書送付", "デモ実施", "決裁者面談", "見積調整", "契約書確認", None,
            ]),
        )
        opportunities.append(opp)

    # 意図的にリスクの高い案件を追加
    # 期限超過案件
    opportunities.append(make_opportunity(
        id="006DEMO_OVERDUE",
        name="東京商事株式会社 - 大型案件（期限超過）",
        amount=8_000_000,
        stage="提案",
        close_date=today - timedelta(days=10),
        deal_type=DealType.NEW,
        owner_name="田中太郎",
        account_name="東京商事株式会社",
        probability=0.50,
        created_date=today - timedelta(days=60),
        last_activity_date=today - timedelta(days=20),
        days_since_last_activity=20,
        close_date_change_count=3,
        next_step=None,
    ))

    # 停滞中の大型案件
    opportunities.append(make_opportunity(
        id="006DEMO_STALE",
        name="大阪製造株式会社 - システム刷新（停滞中）",
        amount=15_000_000,
        stage="ヒアリング",
        close_date=today + timedelta(days=20),
        deal_type=DealType.NEW,
        owner_name="佐藤花子",
        account_name="大阪製造株式会社",
        probability=0.20,
        created_date=today - timedelta(days=45),
        last_activity_date=today - timedelta(days=30),
        days_since_last_activity=30,
        close_date_change_count=0,
        next_step=None,
    ))

    # まもなくクローズだが確度が低い案件
    opportunities.append(make_opportunity(
        id="006DEMO_LOWPROB",
        name="渋谷テクノロジーズ - DX推進（確度懸念）",
        amount=5_000_000,
        stage="ヒアリング",
        close_date=today + timedelta(days=5),
        deal_type=DealType.NEW,
        owner_name="鈴木一郎",
        account_name="渋谷テクノロジーズ",
        probability=0.20,
        created_date=today - timedelta(days=30),
        last_activity_date=today - timedelta(days=3),
        days_since_last_activity=3,
        close_date_change_count=1,
        next_step="追加ヒアリング",
    ))

    return opportunities


def generate_demo_closed_won() -> list[dict[str, Any]]:
    """今月の受注済みデモデータ."""
    today = date.today()
    random.seed(99)

    won: list[dict[str, Any]] = []
    accounts = ["品川ソリューション株式会社", "新宿メディア株式会社", "千葉ロジスティクス"]

    for i, account in enumerate(accounts):
        won.append(make_opportunity(
            id=f"006DEMOW{i:03d}",
            name=f"{account} - 受注済み #{i+1}",
            amount=random.choice([2_000_000, 3_000_000, 5_000_000]),
            stage="受注",
            close_date=today - timedelta(days=random.randint(1, 15)),
            deal_type=random.choice([DealType.NEW, DealType.EXISTING]),
            owner_name=random.choice(["田中太郎", "佐藤花子"]),
            account_name=account,
            probability=1.0,
            created_date=today - timedelta(days=random.randint(20, 60)),
        ))

    return won


def generate_demo_weekly_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """先週の受注/失注デモデータ."""
    today = date.today()
    random.seed(77)

    won = [
        make_opportunity(
            id="006DEMOWW1",
            name="横浜コンサル株式会社 - コンサル契約",
            amount=3_000_000,
            stage="受注",
            close_date=today - timedelta(days=3),
            deal_type=DealType.NEW,
            owner_name="高橋美咲",
            account_name="横浜コンサル株式会社",
            probability=1.0,
            created_date=today - timedelta(days=40),
        ),
        make_opportunity(
            id="006DEMOWW2",
            name="京都デジタル株式会社 - 契約更新",
            amount=4_000_000,
            stage="受注",
            close_date=today - timedelta(days=5),
            deal_type=DealType.EXISTING,
            owner_name="渡辺健太",
            account_name="京都デジタル株式会社",
            probability=1.0,
            created_date=today - timedelta(days=20),
        ),
    ]

    lost = [
        make_opportunity(
            id="006DEMOLL1",
            name="札幌ソリューションズ - 新規提案",
            amount=2_000_000,
            stage="失注",
            close_date=today - timedelta(days=4),
            deal_type=DealType.NEW,
            owner_name="鈴木一郎",
            account_name="札幌ソリューションズ",
            probability=0.0,
            created_date=today - timedelta(days=50),
        ),
    ]

    return won, lost
