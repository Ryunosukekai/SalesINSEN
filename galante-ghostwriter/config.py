"""
Galante Ghostwriter — Configuration & Framework Definitions.

All Galante proposal frameworks, reference proposals, templates,
and application settings live here.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"

# ---------------------------------------------------------------------------
# API keys (lazy — checked only when needed)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
GOOGLE_SERVICE_ACCOUNT_JSON: str | None = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_DELEGATED_USER: str | None = os.getenv("GOOGLE_DELEGATED_USER")
SLACK_BOT_TOKEN: str | None = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID: str | None = os.getenv("SLACK_CHANNEL_ID")

# ---------------------------------------------------------------------------
# Galante 3 Principles
# ---------------------------------------------------------------------------
GALANTE_PRINCIPLES = {
    "PASSIONE": "情熱 — クライアントの課題に誰よりも本気で向き合う",
    "SFIDA": "挑戦 — 安全策ではなく、市場を動かす大胆な一手を提案する",
    "RISPETTO": "敬意 — クライアントのブランド・歴史・想いに深い敬意を払う",
}

# ---------------------------------------------------------------------------
# Galante Proposal Framework — 9 Sections
# ---------------------------------------------------------------------------
GALANTE_PROPOSAL_FRAMEWORK = {
    "sections": [
        {
            "id": "background",
            "title": "BACKGROUND｜背景",
            "description": "市場環境・クライアント状況・オリエン背景を整理する",
            "required_inputs": ["orien_notes", "industry"],
            "galante_approach": (
                "単なる状況整理ではなく、クライアントが気づいていない市場の「うねり」を"
                "提示し、「この会社は我々の業界を深く理解している」と感じさせる。"
                "データや具体的な事例を交え、説得力のある背景描写を行う。"
            ),
        },
        {
            "id": "objective",
            "title": "OBJECTIVE & PROBLEM｜目的と課題",
            "description": "クライアントの本質的な課題と達成すべき目的を明確化する",
            "required_inputs": ["orien_notes", "client_name"],
            "galante_approach": (
                "クライアントが言語化した課題の「裏側」にある本質的な問題を抽出する。"
                "「御用聞き」ではなく、課題の再定義でクライアントの期待を超える。"
                "表面的なKPIではなく、ビジネスインパクトに繋がる目的設定を行う。"
            ),
        },
        {
            "id": "target",
            "title": "TARGET｜振り向かせたい人",
            "description": "ターゲット像を具体的に描写する",
            "required_inputs": ["orien_notes"],
            "galante_approach": (
                "デモグラフィックだけでなく、ターゲットの価値観・行動パターン・"
                "隠れた欲求まで深掘りする。「ペルソナ」ではなく「生きた人間」として"
                "描写し、提案全体にリアリティを持たせる。"
            ),
        },
        {
            "id": "from_to",
            "title": "FROM ▶︎ TO｜現状と理想像",
            "description": "施策前後のターゲット・ブランドの変化を明示する",
            "required_inputs": ["orien_notes", "client_name"],
            "galante_approach": (
                "Before/Afterを鮮明に描き、施策のインパクトを可視化する。"
                "感情の変化・行動の変化・認知の変化を具体的に示し、"
                "クライアントが「この未来を実現したい」と思える像を提示する。"
            ),
        },
        {
            "id": "insight",
            "title": "INSIGHT & BENEFIT FRAME｜心を動かすツボ × ブランド価値",
            "description": "ターゲットインサイトとブランド便益の交差点を見つける",
            "required_inputs": ["orien_notes", "client_name", "industry"],
            "galante_approach": (
                "Galanteの提案の核心。ターゲットの「隠れた本音（インサイト）」と"
                "ブランドが提供できる「真の価値」が交差するポイントを発見する。"
                "このインサイトが提案全体を貫く「背骨」となる。"
                "競合が見つけていない切り口で差別化する。"
            ),
        },
        {
            "id": "message",
            "title": "MESSAGE｜最も伝えたい価値",
            "description": "施策全体を貫くコアメッセージを策定する",
            "required_inputs": ["orien_notes", "client_name"],
            "galante_approach": (
                "INSIGHTから導かれる、一言で心を掴むメッセージ。"
                "広告コピーではなく、戦略の本質を凝縮した「提案の魂」。"
                "クライアントの社内で一人歩きするほど明快なものにする。"
            ),
        },
        {
            "id": "success",
            "title": "WHAT DOES SUCCESS LOOK LIKE｜成功の定義",
            "description": "定量・定性両面での成功指標を定義する",
            "required_inputs": ["orien_notes"],
            "galante_approach": (
                "KPIの羅列ではなく、「この施策が大成功したら何が起きるか」を"
                "ストーリーとして描く。定量目標と定性目標の両面から、"
                "クライアントが社内を説得できる材料を提供する。"
            ),
        },
        {
            "id": "budget",
            "title": "BUDGET｜ご予算",
            "description": "予算配分と投資対効果の見通しを提示する",
            "required_inputs": ["orien_notes"],
            "galante_approach": (
                "「費用」ではなく「投資」として提示する。"
                "各施策の費用対効果を明確にし、予算の妥当性を論理的に説明する。"
                "不確かな数値は正直に[要確認]とマークし、信頼を得る。"
            ),
        },
        {
            "id": "schedule",
            "title": "SCHEDULE｜主要マイルストーン",
            "description": "実施スケジュールと主要マイルストーンを提示する",
            "required_inputs": ["orien_notes"],
            "galante_approach": (
                "無理のない現実的なスケジュールを提示しつつ、"
                "スピード感のある実行力をアピールする。"
                "クライアントの意思決定ポイントを明示し、次のアクションを明確にする。"
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Reference Proposals (knowledge base)
# ---------------------------------------------------------------------------
REFERENCE_PROPOSALS = {
    "sns_store_linkage": {
        "doc_id": "1EiM9Ix_C9UTvlG6QiAOGP_jsGYC3t1KU9TbIrMpt8Vo",
        "title": "SNS×店頭連動による売上最大化施策 ご提案書",
        "type": "influencer",
        "industry": "消費財",
        "key_concept": "機能訴求→シーン訴求への転換",
        "sections_summary": {
            "background": "SNS時代の購買行動変化と店頭体験の再定義",
            "insight": "消費者は「商品」ではなく「その商品がある生活シーン」に共感する",
            "from_to": "機能スペック訴求 → 生活シーン共感型コミュニケーション",
            "message": "あなたの日常に、新しい「あたりまえ」を。",
        },
    },
    "ec_growth_strategy": {
        "doc_id": "placeholder_doc_id_ec_growth",
        "title": "EC売上成長戦略 ご提案書",
        "type": "digital",
        "industry": "EC・小売",
        "key_concept": "データドリブン×ブランドストーリー",
        "sections_summary": {
            "background": "EC市場の成熟化とD2Cブランドの台頭",
            "insight": "価格比較ではなく、ブランドの世界観に浸る体験が購買を決める",
            "from_to": "価格競争型EC → ブランド体験型EC",
            "message": "買い物を、体験に変える。",
        },
    },
    "brand_awareness_campaign": {
        "doc_id": "placeholder_doc_id_brand",
        "title": "ブランド認知拡大キャンペーン ご提案書",
        "type": "branding",
        "industry": "全般",
        "key_concept": "認知×共感の同時獲得",
        "sections_summary": {
            "background": "情報過多時代における認知獲得の難しさ",
            "insight": "人は広告を避けるが、共感できるストーリーは自ら探しに行く",
            "from_to": "広告認知 → 共感認知",
            "message": "知られるのではなく、語られるブランドへ。",
        },
    },
}

# ---------------------------------------------------------------------------
# Google Docs Templates
# ---------------------------------------------------------------------------
TEMPLATES = {
    "unified_template": "1B5mVR0jhhLCBIddXZJxfQ7LbM9D3e4EQOSXRxzHHS6s",
}

# ---------------------------------------------------------------------------
# Demo Sample Data
# ---------------------------------------------------------------------------
DEMO_ORIEN_TEXT = """\
【オリエンテーション議事録】
日時: 2026年3月25日 14:00-15:30
クライアント: 株式会社デロンギ・ジャパン
出席者: マーケティング部 田中部長、佐藤課長 / Galante 山田、鈴木

■ 背景・課題
・デロンギの全自動コーヒーマシンの日本市場シェアを拡大したい
・現状はコーヒー愛好家（マニア層）には認知されているが、一般層への浸透が課題
・競合（ネスプレッソ、バルミューダ）が「手軽さ」を訴求し、シェアを伸ばしている
・デロンギの強みは「本格的なイタリアンコーヒーの味わい」と「全自動の利便性」の両立

■ ターゲット
・30-45歳の共働き世帯、世帯年収800万円以上
・品質にこだわりがあるが、忙しくて手間はかけられない層
・カフェには定期的に行くが、家でのコーヒーはインスタントやドリップバッグが中心

■ 予算感
・年間マーケティング予算: 約2億円（デジタル中心）
・今回の施策: 5,000万円〜8,000万円を想定

■ 期待する成果
・ブランド認知度: 現状32% → 目標50%（1年以内）
・EC売上: 前年比150%
・店頭（家電量販店）での指名買い率向上

■ スケジュール感
・提案期限: 4月中旬
・施策開始: 6月（夏のアイスコーヒー需要に合わせたい）
・年末商戦（11-12月）がピーク

■ 特記事項
・田中部長「価格訴求はしたくない。ブランド価値を毀損する」
・佐藤課長「若い世代にも届けたいが、ブランドの格を下げたくない」
・過去に有名タレントを起用したが、ブランド想起には繋がらなかった
"""

DEMO_CLIENT = "デロンギ・ジャパン"
DEMO_INDUSTRY = "家電・コーヒーマシン"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the root application logger."""
    logger = logging.getLogger("galante_ghostwriter")
    if not logger.handlers:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(LOG_DIR / "ghostwriter.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
