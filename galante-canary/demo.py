"""Demo data generator — ~15 accounts with various risk levels."""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


def _uid() -> str:
    return uuid.uuid4().hex[:18]


def _date(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def _date_short(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Account templates
# ---------------------------------------------------------------------------

_DEMO_PROFILES: list[dict[str, Any]] = [
    # -- 緊急 (81-100) --
    {
        "name": "サイバーテック株式会社",
        "owner": "田中太郎",
        "industry": "IT",
        "revenue": 5_000_000,
        "last_activity_days": 95,
        "won_amounts": [3_000_000, 1_200_000],
        "lost_recent": 2,
        "open_pipeline": 0,
        "meetings_prev": 4,
        "meetings_curr": 0,
        "emails_no_reply": True,
    },
    {
        "name": "メディアファースト株式会社",
        "owner": "佐藤花子",
        "industry": "メディア",
        "revenue": 8_000_000,
        "last_activity_days": 100,
        "won_amounts": [5_000_000, 2_000_000],
        "lost_recent": 2,
        "open_pipeline": 0,
        "meetings_prev": 6,
        "meetings_curr": 1,
        "emails_no_reply": True,
    },
    # -- 危険 (61-80) --
    {
        "name": "グローバルトレード株式会社",
        "owner": "山田一郎",
        "industry": "商社",
        "revenue": 12_000_000,
        "last_activity_days": 65,
        "won_amounts": [8_000_000, 3_500_000],
        "lost_recent": 1,
        "open_pipeline": 0,
        "meetings_prev": 5,
        "meetings_curr": 2,
        "emails_no_reply": False,
    },
    {
        "name": "ネクストビジョン株式会社",
        "owner": "鈴木美香",
        "industry": "コンサル",
        "revenue": 4_000_000,
        "last_activity_days": 70,
        "won_amounts": [2_500_000, 2_000_000],
        "lost_recent": 1,
        "open_pipeline": 0,
        "meetings_prev": 3,
        "meetings_curr": 0,
        "emails_no_reply": True,
    },
    {
        "name": "フューチャーリテール株式会社",
        "owner": "田中太郎",
        "industry": "小売",
        "revenue": 6_000_000,
        "last_activity_days": 62,
        "won_amounts": [4_000_000, 1_500_000],
        "lost_recent": 0,
        "open_pipeline": 0,
        "meetings_prev": 4,
        "meetings_curr": 1,
        "emails_no_reply": True,
    },
    # -- 警戒 (41-60) --
    {
        "name": "イノベーションラボ株式会社",
        "owner": "佐藤花子",
        "industry": "製造",
        "revenue": 3_000_000,
        "last_activity_days": 35,
        "won_amounts": [2_000_000, 1_500_000],
        "lost_recent": 1,
        "open_pipeline": 0,
        "meetings_prev": 3,
        "meetings_curr": 2,
        "emails_no_reply": False,
    },
    {
        "name": "アーバンデザイン株式会社",
        "owner": "山田一郎",
        "industry": "不動産",
        "revenue": 7_000_000,
        "last_activity_days": 40,
        "won_amounts": [5_000_000, 4_000_000],
        "lost_recent": 0,
        "open_pipeline": 0,
        "meetings_prev": 2,
        "meetings_curr": 1,
        "emails_no_reply": True,
    },
    {
        "name": "テクノフロンティア株式会社",
        "owner": "鈴木美香",
        "industry": "IT",
        "revenue": 2_500_000,
        "last_activity_days": 32,
        "won_amounts": [1_800_000, 1_500_000],
        "lost_recent": 1,
        "open_pipeline": 1,
        "meetings_prev": 4,
        "meetings_curr": 2,
        "emails_no_reply": False,
    },
    # -- 注意 (21-40) --
    {
        "name": "スカイネットワーク株式会社",
        "owner": "田中太郎",
        "industry": "通信",
        "revenue": 10_000_000,
        "last_activity_days": 35,
        "won_amounts": [6_000_000, 5_500_000],
        "lost_recent": 0,
        "open_pipeline": 1,
        "meetings_prev": 3,
        "meetings_curr": 2,
        "emails_no_reply": False,
    },
    {
        "name": "ブリッジコンサルティング",
        "owner": "佐藤花子",
        "industry": "コンサル",
        "revenue": 3_500_000,
        "last_activity_days": 20,
        "won_amounts": [2_000_000, 1_600_000],
        "lost_recent": 0,
        "open_pipeline": 0,
        "meetings_prev": 2,
        "meetings_curr": 1,
        "emails_no_reply": False,
    },
    {
        "name": "プレミアムフーズ株式会社",
        "owner": "山田一郎",
        "industry": "食品",
        "revenue": 15_000_000,
        "last_activity_days": 25,
        "won_amounts": [9_000_000, 8_000_000],
        "lost_recent": 0,
        "open_pipeline": 1,
        "meetings_prev": 4,
        "meetings_curr": 3,
        "emails_no_reply": False,
    },
    # -- 健全 (0-20) --
    {
        "name": "サンライズエンタープライズ",
        "owner": "鈴木美香",
        "industry": "エネルギー",
        "revenue": 20_000_000,
        "last_activity_days": 5,
        "won_amounts": [12_000_000, 11_000_000],
        "lost_recent": 0,
        "open_pipeline": 2,
        "meetings_prev": 5,
        "meetings_curr": 6,
        "emails_no_reply": False,
    },
    {
        "name": "ハーモニーデザイン株式会社",
        "owner": "田中太郎",
        "industry": "デザイン",
        "revenue": 4_500_000,
        "last_activity_days": 3,
        "won_amounts": [3_000_000, 2_800_000],
        "lost_recent": 0,
        "open_pipeline": 1,
        "meetings_prev": 3,
        "meetings_curr": 4,
        "emails_no_reply": False,
    },
    {
        "name": "アクアテクノロジー株式会社",
        "owner": "佐藤花子",
        "industry": "環境",
        "revenue": 6_000_000,
        "last_activity_days": 10,
        "won_amounts": [4_000_000, 3_800_000],
        "lost_recent": 0,
        "open_pipeline": 3,
        "meetings_prev": 4,
        "meetings_curr": 5,
        "emails_no_reply": False,
    },
    {
        "name": "クリエイティブパートナーズ",
        "owner": "山田一郎",
        "industry": "広告",
        "revenue": 9_000_000,
        "last_activity_days": 7,
        "won_amounts": [6_000_000, 5_800_000],
        "lost_recent": 0,
        "open_pipeline": 2,
        "meetings_prev": 6,
        "meetings_curr": 7,
        "emails_no_reply": False,
    },
]


def generate_demo_accounts() -> list[dict[str, Any]]:
    """Generate ~15 demo account records."""
    accounts: list[dict[str, Any]] = []
    for p in _DEMO_PROFILES:
        acct_id = _uid()
        accounts.append({
            "Id": acct_id,
            "Name": p["name"],
            "OwnerId": _uid(),
            "Owner": {"Name": p["owner"]},
            "Industry": p["industry"],
            "AnnualRevenue": p["revenue"],
            "LastActivityDate": _date_short(p["last_activity_days"]),
            "CreatedDate": _date(730),
        })
    return accounts


def generate_demo_account_data(
    account: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Generate account data (opps, tasks, events, emails) from a profile."""
    acct_id = account["Id"]
    last_days = profile["last_activity_days"]

    # -- Opportunities ---------------------------------------------------
    opps: list[dict] = []
    won_amounts = profile.get("won_amounts", [])
    for i, amt in enumerate(won_amounts):
        days_ago = 30 + i * 120
        opps.append({
            "Id": _uid(),
            "Name": f"{profile['name']} - 案件{i+1}",
            "AccountId": acct_id,
            "Account": {"Name": profile["name"]},
            "StageName": "Closed Won",
            "Amount": amt,
            "CloseDate": _date_short(days_ago),
            "IsClosed": True,
            "IsWon": True,
            "CreatedDate": _date(days_ago + 30),
            "LastModifiedDate": _date(days_ago),
        })

    lost_count = profile.get("lost_recent", 0)
    for i in range(lost_count):
        days_ago = 10 + i * 15
        opps.append({
            "Id": _uid(),
            "Name": f"{profile['name']} - 失注案件{i+1}",
            "AccountId": acct_id,
            "Account": {"Name": profile["name"]},
            "StageName": "Closed Lost",
            "Amount": random.randint(500_000, 3_000_000),
            "CloseDate": _date_short(days_ago),
            "IsClosed": True,
            "IsWon": False,
            "CreatedDate": _date(days_ago + 20),
            "LastModifiedDate": _date(days_ago),
        })

    # Sort by CloseDate desc
    opps.sort(key=lambda o: o["CloseDate"], reverse=True)

    # -- Open pipeline ---------------------------------------------------
    pipeline: list[dict] = []
    open_count = profile.get("open_pipeline", 0)
    for i in range(open_count):
        pipeline.append({
            "Id": _uid(),
            "Name": f"{profile['name']} - 進行中{i+1}",
            "AccountId": acct_id,
            "StageName": "Proposal",
            "Amount": random.randint(1_000_000, 5_000_000),
            "CloseDate": _date_short(-30 - i * 30),  # future
        })

    # -- Tasks -----------------------------------------------------------
    tasks: list[dict] = []
    if last_days < 60:
        for i in range(3):
            days_ago = last_days + i * 20
            tasks.append({
                "Id": _uid(),
                "Subject": f"フォローアップ {i+1}",
                "ActivityDate": _date_short(days_ago),
                "Status": "Completed",
                "WhoId": None,
                "WhatId": acct_id,
                "OwnerId": _uid(),
                "CreatedDate": _date(days_ago),
            })

    # -- Events (meetings) -----------------------------------------------
    events: list[dict] = []
    meetings_prev = profile.get("meetings_prev", 0)
    meetings_curr = profile.get("meetings_curr", 0)

    for i in range(meetings_curr):
        days_ago = random.randint(1, 89)
        events.append({
            "Id": _uid(),
            "Subject": f"定例MTG",
            "StartDateTime": _date(days_ago),
            "EndDateTime": _date(days_ago),
            "WhoId": None,
            "WhatId": acct_id,
            "OwnerId": _uid(),
            "CreatedDate": _date(days_ago),
        })

    for i in range(meetings_prev):
        days_ago = random.randint(91, 179)
        events.append({
            "Id": _uid(),
            "Subject": f"定例MTG",
            "StartDateTime": _date(days_ago),
            "EndDateTime": _date(days_ago),
            "WhoId": None,
            "WhatId": acct_id,
            "OwnerId": _uid(),
            "CreatedDate": _date(days_ago),
        })

    # -- Emails ----------------------------------------------------------
    emails: list[dict] = []
    if profile.get("emails_no_reply"):
        # 3 outgoing with no reply
        for i in range(3):
            days_ago = 5 + i * 10
            emails.append({
                "Id": _uid(),
                "Subject": f"ご提案の件 ({i+1})",
                "Status": "Sent",
                "MessageDate": _date(days_ago),
                "FromAddress": "sales@galante.co.jp",
                "ToAddress": f"contact@{profile['name']}.co.jp",
                "Incoming": False,
                "HasAttachment": False,
                "RelatedToId": acct_id,
            })
    else:
        # Normal email flow
        for i in range(4):
            days_ago = 5 + i * 7
            is_incoming = i % 2 == 1
            emails.append({
                "Id": _uid(),
                "Subject": f"Re: ご提案の件",
                "Status": "Read" if is_incoming else "Sent",
                "MessageDate": _date(days_ago),
                "FromAddress": "contact@client.co.jp" if is_incoming else "sales@galante.co.jp",
                "ToAddress": "sales@galante.co.jp" if is_incoming else "contact@client.co.jp",
                "Incoming": is_incoming,
                "HasAttachment": False,
                "RelatedToId": acct_id,
            })

    return {
        "opportunities": opps,
        "open_pipeline": pipeline,
        "tasks": tasks,
        "events": events,
        "emails": emails,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_all_demo_data() -> tuple[list[dict], dict[str, dict]]:
    """Generate all demo accounts and their data.

    Returns:
        (accounts, accounts_data) where accounts_data is keyed by account ID.
    """
    accounts = generate_demo_accounts()
    accounts_data: dict[str, dict] = {}

    for acct, profile in zip(accounts, _DEMO_PROFILES):
        accounts_data[acct["Id"]] = generate_demo_account_data(acct, profile)

    return accounts, accounts_data
