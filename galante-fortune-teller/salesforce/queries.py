"""SOQL クエリ定義."""

from __future__ import annotations


class SOQL:
    """Salesforce SOQL クエリテンプレート.

    全クエリは .format() または f-string で日付パラメータを埋め込む想定。
    """

    # 1. オープン商談（予測対象）
    OPEN_OPPORTUNITIES = """
        SELECT
            Id, Name, Amount, StageName, CloseDate,
            Type, Owner.Name, Account.Name, Probability,
            CreatedDate, LastActivityDate, NextStep,
            ForecastCategory
        FROM Opportunity
        WHERE IsClosed = false
          AND CloseDate <= {end_date}
        ORDER BY CloseDate ASC
    """

    # 2. 今月の受注済み（Closed Won）
    CLOSED_WON_THIS_MONTH = """
        SELECT
            Id, Name, Amount, StageName, CloseDate,
            Type, Owner.Name, Account.Name
        FROM Opportunity
        WHERE StageName = 'Closed Won'
          AND CloseDate >= {month_start}
          AND CloseDate <= {month_end}
        ORDER BY CloseDate ASC
    """

    # 3. クローズ日変更履歴
    CLOSE_DATE_HISTORY = """
        SELECT OpportunityId, COUNT(Id) cnt
        FROM OpportunityFieldHistory
        WHERE Field = 'CloseDate'
          AND OpportunityId IN ({ids})
        GROUP BY OpportunityId
    """

    # 4. 先週の受注・失注サマリー（ウィークリー用）
    WEEKLY_WON_LOST = """
        SELECT
            Id, Name, Amount, StageName, CloseDate,
            Type, Owner.Name, Account.Name
        FROM Opportunity
        WHERE IsClosed = true
          AND CloseDate >= {week_start}
          AND CloseDate <= {week_end}
        ORDER BY StageName, Amount DESC
    """
