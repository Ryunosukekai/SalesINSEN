"""Demo data generator for testing without Salesforce."""

import random
from datetime import date, timedelta

from .models import DealType, Opportunity


def generate_demo_opportunities() -> list[Opportunity]:
    """Generate realistic demo opportunity data."""
    today = date.today()

    # Japanese company names and deal names
    accounts = [
        "東京商事株式会社", "大阪製造株式会社", "名古屋テック合同会社",
        "福岡サービス株式会社", "札幌ソリューションズ", "横浜コンサル株式会社",
        "京都デジタル株式会社", "神戸エンジニアリング", "仙台クリエイト株式会社",
        "広島イノベーション株式会社", "千葉ロジスティクス", "埼玉ファイナンス株式会社",
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

    opportunities = []
    random.seed(42)  # Reproducible demo data

    for i in range(30):
        stage, prob = random.choice(stages_with_prob)
        deal_type = random.choice([DealType.NEW, DealType.NEW, DealType.EXISTING])
        account = random.choice(accounts)

        # Spread close dates across 3 months
        month_offset = random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
        close_day = random.randint(1, 28)
        close_month = today.month + month_offset
        close_year = today.year + (close_month - 1) // 12
        close_month = (close_month - 1) % 12 + 1
        close_date = date(close_year, close_month, close_day)

        amount = random.choice([100, 200, 300, 500, 800, 1000, 1500, 2000])
        created_days_ago = random.randint(5, 90)
        last_activity_days_ago = random.randint(0, 30)

        opp = Opportunity(
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
                "提案書送付", "デモ実施", "決裁者面談", "見積調整", "契約書確認", None
            ]),
        )
        opportunities.append(opp)

    # Add some deliberately risky deals
    # Overdue deal
    opportunities.append(Opportunity(
        id="006DEMO_OVERDUE",
        name="東京商事株式会社 - 大型案件(期限超過)",
        amount=2000,
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

    # Stale large deal
    opportunities.append(Opportunity(
        id="006DEMO_STALE",
        name="大阪製造株式会社 - システム刷新(停滞中)",
        amount=3000,
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

    return opportunities
