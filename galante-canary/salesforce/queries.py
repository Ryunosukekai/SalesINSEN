"""SOQL queries for Galante Canary."""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Accounts — 有効な取引先
# ---------------------------------------------------------------------------
QUERY_ACTIVE_ACCOUNTS = """
SELECT
    Id, Name, OwnerId, Owner.Name,
    Industry, AnnualRevenue,
    LastActivityDate,
    CreatedDate
FROM Account
WHERE IsDeleted = false
  AND Type IN ('Customer', 'Partner')
ORDER BY Name
"""

# ---------------------------------------------------------------------------
# Opportunities — 直近12ヶ月の商談
# ---------------------------------------------------------------------------
QUERY_RECENT_OPPORTUNITIES = """
SELECT
    Id, Name, AccountId, Account.Name,
    StageName, Amount, CloseDate,
    IsClosed, IsWon,
    CreatedDate, LastModifiedDate
FROM Opportunity
WHERE AccountId = '{account_id}'
  AND CreatedDate >= LAST_N_DAYS:365
ORDER BY CloseDate DESC
"""

# ---------------------------------------------------------------------------
# Open Pipeline — 進行中案件
# ---------------------------------------------------------------------------
QUERY_OPEN_PIPELINE = """
SELECT
    Id, Name, AccountId, StageName, Amount, CloseDate
FROM Opportunity
WHERE AccountId = '{account_id}'
  AND IsClosed = false
ORDER BY CloseDate ASC
"""

# ---------------------------------------------------------------------------
# Activities — タスク + イベント
# ---------------------------------------------------------------------------
QUERY_RECENT_TASKS = """
SELECT
    Id, Subject, ActivityDate, Status,
    WhoId, WhatId, OwnerId,
    CreatedDate
FROM Task
WHERE AccountId = '{account_id}'
  AND CreatedDate >= LAST_N_DAYS:180
ORDER BY ActivityDate DESC
"""

QUERY_RECENT_EVENTS = """
SELECT
    Id, Subject, StartDateTime, EndDateTime,
    WhoId, WhatId, OwnerId,
    CreatedDate
FROM Event
WHERE AccountId = '{account_id}'
  AND CreatedDate >= LAST_N_DAYS:180
ORDER BY StartDateTime DESC
"""

# ---------------------------------------------------------------------------
# Emails — EmailMessage (if enabled)
# ---------------------------------------------------------------------------
QUERY_RECENT_EMAILS = """
SELECT
    Id, Subject, Status, MessageDate,
    FromAddress, ToAddress,
    Incoming, HasAttachment,
    RelatedToId
FROM EmailMessage
WHERE RelatedToId = '{account_id}'
  AND MessageDate >= LAST_N_DAYS:90
ORDER BY MessageDate DESC
LIMIT 20
"""
