# -*- coding: utf-8 -*-
"""
不動産トレンド情報（信頼ソース中心・拡張前提）

【運用】
- 既定のトレンド行は本ファイル内の CURATED_TREND_ITEMS を編集して追加・更新する。
- 任意で `data/trend_items.json`（配列JSON）を置くと、同一 `id` は上書き・新規 id は追加される。

【将来の自動化拡張ポイント】
- fetch_trend_items(): RSS・公式API・社内DBからの取得をここに集約
- summarize_trend_items(): OpenAI 等の要約API（下記 `_maybe_apply_llm_summaries`）を本番運用向けに調整
- score_trend_items(): 重み・鮮度関数・人気度の正規化をA/Bテストしやすいよう定数化済み

【著作権・利用条件】
- 本文の無断転載は行わず、短い要約＋公式リンクのみとする。
"""

from __future__ import annotations

import json
import math
import os
import re
from datetime import date
from html import escape as html_escape
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# スコアリング重み（表示順の基準）
# ---------------------------------------------------------------------------
RELIABILITY_WEIGHT = 0.4
FRESHNESS_WEIGHT = 0.3
POPULARITY_WEIGHT = 0.3

# 「新着」バッジを付ける日数
NEW_BADGE_DAYS = 14

# セッション内クリック回数の正規化（飽和点）
POPULARITY_CLICK_SATURATION = 48

# 将来: アーカイブ自動化する場合の日数しきい値（現状は未使用・手動 `archived` のみ）
# ARCHIVE_AUTO_DAYS = 120

TREND_POPULARITY_SESSION_KEY = "_lib_trend_popularity_counts"
# UI改修時はキーを上げて CSS を再注入（古い session のみなら一度リロードで可）
TREND_CSS_INJECTED_KEY = "_lib_trend_css_injected_v2"
TREND_LLM_CACHE_KEY = "_lib_trend_llm_summary_cache"

# ---------------------------------------------------------------------------
# 【ここを編集】信頼性の高いソースのトレンド行（手動メンテ）
# 各項目は title/summary は自サイト用の短い説明（1〜2行）に留める。
# ---------------------------------------------------------------------------
CURATED_TREND_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "mlit-land-building-stats",
        "source_key": "MLIT",
        "source_url": "https://www.mlit.go.jp/statistics/",
        "published_date": "2026-04-01",
        "title_ja": "国土交通省｜土地・建物・住宅に関する統計（不動産価格指数等）",
        "title_en": "MLIT — Land, building & housing statistics (incl. price indices)",
        "summary_ja": "公示地価・不動産価格指数・土地取引等の公表一覧への入口。住宅・土地の価格動向を公的統計で確認する際の起点として利用可能。",
        "summary_en": "Official entry point for published land and housing statistics including price-related indices. Use as a neutral baseline for market context.",
        "category": "住宅",
        "reliability_score": 1.0,
        "popularity_score": 0.72,
        "reliability_tier": "公的",
        "archived": False,
        "use_llm_summary": False,
    },
    {
        "id": "mlit-press-releases",
        "source_key": "MLIT",
        "source_url": "https://www.mlit.go.jp/report/press/",
        "published_date": "2026-03-20",
        "title_ja": "国土交通省｜報道発表（土地・住宅・不動産関連の公式ニュース）",
        "title_en": "MLIT — Press releases (land, housing & real estate)",
        "summary_ja": "土地・住宅・都市政策等に関する報道発表の公式一覧。最新の制度・統計公表の確認に向く一次情報源。",
        "summary_en": "Official press-release index for land, housing and urban policy—useful for first-party updates on statistics and policy notices.",
        "category": "住宅",
        "reliability_score": 1.0,
        "popularity_score": 0.68,
        "reliability_tier": "公的",
        "archived": False,
        "use_llm_summary": False,
    },
    {
        "id": "miki-office-rent",
        "source_key": "SANKI",
        "source_url": "https://www.e-miki.com/rent/",
        "published_date": "2026-03-28",
        "title_ja": "三鬼商事｜オフィスマーケット（賃料・空室等の市況整理）",
        "title_en": "Miki Shoji — Office market (rent & vacancy context)",
        "summary_ja": "主要ビル市場の賃料・空室動向を月次で整理したオフィス市況レポート群への導線。需給・賃料トレンドの把握に向く。",
        "summary_en": "Monthly office market materials focused on rent and vacancy trends—suited for supply/demand and rent trajectory reviews.",
        "category": "オフィス",
        "reliability_score": 0.88,
        "popularity_score": 0.78,
        "reliability_tier": "業界",
        "archived": False,
        "use_llm_summary": False,
    },
    {
        "id": "japan-reit-portal",
        "source_key": "JREIT",
        "source_url": "https://www.japan-reit.com/",
        "published_date": "2026-04-05",
        "title_ja": "JAPAN-REIT.COM｜J-REITの指数・開示・話題の整理ポータル",
        "title_en": "JAPAN-REIT.COM — J-REIT indices, disclosures & topics",
        "summary_ja": "東証REIT指数の概況、銘柄ニュース、コラム等へ分類アクセス可能。取得・譲渡・決算トレンドの素早い把握の補助として利用。",
        "summary_en": "Structured access to index moves, issuer news and columns—supporting quick scans of acquisition, disposal and earnings-related themes.",
        "category": "J-REIT",
        "reliability_score": 0.82,
        "popularity_score": 0.74,
        "reliability_tier": "業界",
        "archived": False,
        "use_llm_summary": False,
    },
    {
        "id": "japan-reit-topics",
        "source_key": "JREIT",
        "source_url": "https://www.japan-reit.com/topic/",
        "published_date": "2026-04-02",
        "title_ja": "JAPAN-REIT.COM｜銘柄ニュース（開示・話題の年次インデックス）",
        "title_en": "JAPAN-REIT.COM — Ticker news index",
        "summary_ja": "銘柄別の開示・話題を時系列で辿れるインデックス。ポートフォリオ銘柄のイベント確認の出発点として利用可能。",
        "summary_en": "Ticker-level news index for time-ordered scanning—useful as a starting point for issuer-specific event checks.",
        "category": "J-REIT",
        "reliability_score": 0.82,
        "popularity_score": 0.62,
        "reliability_tier": "業界",
        "archived": False,
        "use_llm_summary": False,
    },
    {
        "id": "cbre-japan-insights",
        "source_key": "CBRE",
        "source_url": "https://www.cbre.co.jp/insights/",
        "published_date": "2026-03-15",
        "title_ja": "CBRE｜Japan Insights（オフィス・投資・各セクターのレポート入口）",
        "title_en": "CBRE — Japan insights (multi-sector reports)",
        "summary_ja": "大手仲介の調査レポート・コメントへの入口。オフィス需給、投資マーケット等の業界整理を参照する際の二次ソースとして位置づけ可能。",
        "summary_en": "Gateway to broker research and commentary—position as secondary industry context alongside primary official statistics.",
        "category": "商業",
        "reliability_score": 0.78,
        "popularity_score": 0.58,
        "reliability_tier": "業界",
        "archived": False,
        "use_llm_summary": False,
    },
    # アーカイブ例（運用時は `archived: True` で過去枠へ）
    {
        "id": "mlit-legacy-sample-archived",
        "source_key": "MLIT",
        "source_url": "https://www.mlit.go.jp/",
        "published_date": "2025-08-01",
        "title_ja": "（アーカイブ例）国土交通省トップ｜報道発表・統計の再探索",
        "title_en": "(Archive sample) MLIT top — press & statistics",
        "summary_ja": "過去に掲載していた案内の置き場所例。運用では古いトピックを `archived: True` にして整理する。",
        "summary_en": "Placeholder for retired highlights; keep stale items under archived for clarity.",
        "category": "住宅",
        "reliability_score": 1.0,
        "popularity_score": 0.35,
        "reliability_tier": "公的",
        "archived": True,
        "use_llm_summary": False,
    },
]

SOURCE_KEY_TO_GROUP = {
    "MLIT": "kokudo",
    "SANKI": "sanki",
    "JREIT": "reit",
    "CBRE": "other",
    "OTHER": "other",
}

VALID_CATEGORIES = ("住宅", "オフィス", "商業", "J-REIT")

# 用途別 expander 見出し用（英語UI）
_CATEGORY_LABEL_EN: Dict[str, str] = {
    "住宅": "Residential",
    "オフィス": "Office",
    "商業": "Commercial",
    "J-REIT": "J-REIT",
}


def category_display_name(category: str, lang: str) -> str:
    """用途別トレンドの見出しに使うカテゴリ表示名。"""
    if lang == "en":
        return _CATEGORY_LABEL_EN.get(str(category), str(category))
    return str(category)


def get_featured_trend(sorted_active_items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """スコア順に並んだアクティブ一覧から注目1件を返す（無ければ None）。"""
    if not sorted_active_items:
        return None
    return sorted_active_items[0]


def group_trends_by_category(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """category ごとに分類（VALID_CATEGORIES 順で走査しやすいよう全キーを用意）。"""
    buckets: Dict[str, List[Dict[str, Any]]] = {c: [] for c in VALID_CATEGORIES}
    for row in items:
        c = str(row.get("category", "住宅"))
        if c not in buckets:
            c = "住宅"
        buckets[c].append(row)
    return buckets


def split_archive_by_month(archived_items: List[Dict[str, Any]]) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """アーカイブを年月降順の (YYYY-MM, rows) リストで返す。"""
    by_month: Dict[str, List[Dict[str, Any]]] = {}
    for row in archived_items:
        ym = row["_pub_date"].strftime("%Y-%m")
        by_month.setdefault(ym, []).append(row)
    out: List[Tuple[str, List[Dict[str, Any]]]] = []
    for ym in sorted(by_month.keys(), reverse=True):
        rows = sorted(by_month[ym], key=lambda x: (-x["_pub_date"].toordinal(), str(x["id"])))
        out.append((ym, rows))
    return out


def _normalize_trend_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    JSON 手編集で混入しがちなキーの空白・全角空白・連続空白を正規化する。
    同一正規キーへの衝突時は、非空でより長い文字列を優先（要約の欠損取り込み用）。
    """
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if not isinstance(k, str):
            continue
        nk = k.strip().replace("\ufeff", "").replace("\u3000", " ").replace("\u00a0", " ")
        nk = re.sub(r"\s+", "_", nk.strip())
        nk = re.sub(r"_+", "_", nk)
        if nk not in out:
            out[nk] = v
            continue
        ov = out[nk]
        if isinstance(ov, str) and isinstance(v, str):
            a, b = ov.strip(), v.strip()
            if not a and b:
                out[nk] = v
            elif a and b and len(b) > len(a):
                out[nk] = v
        elif (ov in (None, "", [], {})) and v not in (None, "", [], {}):
            out[nk] = v
    return out


def _trend_scalar_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, dict)):
        try:
            return json.dumps(v, ensure_ascii=False)
        except TypeError:
            return str(v).strip()
    return str(v).strip()


def fetch_trend_items(base_dir: Path) -> List[Dict[str, Any]]:
    """手動配列＋任意JSONをマージして生データを返す（将来は外部取得をここに接続）。"""
    merged: Dict[str, Dict[str, Any]] = {}
    for row in CURATED_TREND_ITEMS:
        rid = str(row.get("id", "")).strip()
        if rid:
            merged[rid] = _normalize_trend_row_keys(dict(row))
    json_path = base_dir / "data" / "trend_items.json"
    if json_path.is_file():
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                for row in raw:
                    if isinstance(row, dict):
                        row = _normalize_trend_row_keys(dict(row))
                        rid = str(row.get("id", "")).strip()
                        if rid:
                            base = _normalize_trend_row_keys(dict(merged.get(rid, {})))
                            base.update(row)
                            merged[rid] = base
        except (OSError, json.JSONDecodeError):
            pass
    return list(merged.values())


def normalize_trend_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """キー欠損を埋め、日付を正規化する。"""
    out: List[Dict[str, Any]] = []
    for raw in items:
        row = _normalize_trend_row_keys(dict(raw))
        row.setdefault("id", re.sub(r"\W+", "-", str(row.get("title_ja", "item"))).strip("-").lower()[:48] or "item")
        row.setdefault("source_key", "OTHER")
        row.setdefault("source_url", "https://www.mlit.go.jp/")
        row.setdefault("published_date", date.today().isoformat())
        row.setdefault("title_ja", "（タイトル未設定）")
        row.setdefault("title_en", row["title_ja"])
        row.setdefault("summary_ja", "")
        row.setdefault("summary_en", row.get("summary_ja", ""))
        row["title_ja"] = _trend_scalar_str(row.get("title_ja", "")) or "（タイトル未設定）"
        row["title_en"] = _trend_scalar_str(row.get("title_en", "")) or row["title_ja"]
        row["summary_ja"] = _trend_scalar_str(row.get("summary_ja", ""))
        row["summary_en"] = _trend_scalar_str(row.get("summary_en", "")) or row["summary_ja"]
        cat = str(row.get("category", "住宅"))
        if cat not in VALID_CATEGORIES:
            cat = "住宅"
        row["category"] = cat
        row.setdefault("reliability_score", 0.75)
        row.setdefault("popularity_score", 0.55)
        row.setdefault("reliability_tier", "その他")
        row.setdefault("archived", False)
        row.setdefault("use_llm_summary", False)
        # published_date を date 型にも保持（ソート安定化）
        try:
            row["_pub_date"] = date.fromisoformat(str(row["published_date"])[:10])
        except ValueError:
            row["_pub_date"] = date.today()
            row["published_date"] = row["_pub_date"].isoformat()
        out.append(row)
    return out


def _resolve_openai_api_key() -> str:
    k = os.getenv("OPENAI_API_KEY", "").strip()
    if k:
        return k
    try:
        import streamlit as st

        sec = getattr(st, "secrets", None)
        if sec is None:
            return ""
        if "OPENAI_API_KEY" in sec:
            return str(sec["OPENAI_API_KEY"]).strip()
        o = sec.get("openai")
        if isinstance(o, dict) and o.get("api_key"):
            return str(o["api_key"]).strip()
    except Exception:
        return ""
    return ""


def _llm_one_line_summary(
    *,
    title: str,
    category: str,
    source_key: str,
    lang: str,
    api_key: str,
) -> Optional[str]:
    """OpenAI Chat Completions による1〜2行要約（requests 利用・失敗時は None）。"""
    try:
        import requests
    except ImportError:
        return None
    system = (
        "You are a concise real-estate analyst assistant. Output 1-2 short neutral sentences in the target language. "
        "No hype, no investment advice, no quoted article text."
    )
    user = (
        f"Language: {lang}\n"
        f"Source type: {source_key}\n"
        f"Category: {category}\n"
        f"Topic title: {title}\n"
        "Summarize what a professional appraiser would use this official/industry source for."
    )
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "max_tokens": 120,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=25,
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text.replace("\n", " ").strip() or None
    except Exception:
        return None


def summarize_trend_items(items: List[Dict[str, Any]], *, lang: str) -> List[Dict[str, Any]]:
    """
    要約の付与・上書き。
    - 既定: 手動の summary_ja / summary_en を使用（安定運用）
    - use_llm_summary=True かつ API キーあり: LLM要約を試行（セッションキャッシュ）
    """
    api_key = _resolve_openai_api_key()
    try:
        import streamlit as st

        cache: Dict[str, str] = st.session_state.setdefault(TREND_LLM_CACHE_KEY, {})
    except Exception:
        cache = {}

    out: List[Dict[str, Any]] = []
    for row in items:
        r = dict(row)
        title = r["title_ja"] if lang == "ja" else r.get("title_en") or r["title_ja"]
        sum_key = "summary_ja" if lang == "ja" else "summary_en"
        if r.get("use_llm_summary") and api_key:
            ck = f"{r['id']}:{lang}"
            if ck not in cache:
                generated = _llm_one_line_summary(
                    title=title,
                    category=r["category"],
                    source_key=r["source_key"],
                    lang="Japanese" if lang == "ja" else "English",
                    api_key=api_key,
                )
                if generated:
                    cache[ck] = generated
            if ck in cache:
                r[sum_key] = cache[ck]
        if not (r.get(sum_key) or "").strip():
            r[sum_key] = r.get("summary_ja") or r.get("summary_en") or ""
        r["summary"] = r["summary_ja"] if lang == "ja" else r.get("summary_en", "")
        out.append(r)
    return out


def _freshness_score(pub: date, today: date) -> float:
    age = max(0, (today - pub).days)
    if age <= 7:
        return 1.0
    if age <= 30:
        return 0.88
    if age <= 90:
        return 0.72
    return max(0.25, 0.72 - min(0.47, (age - 90) / 400.0))


def _merged_popularity(row: Dict[str, Any], session_clicks: int) -> float:
    base = float(row.get("popularity_score", 0.55))
    base = max(0.0, min(1.0, base))
    if POPULARITY_CLICK_SATURATION <= 0:
        norm = 0.0
    else:
        norm = min(1.0, math.log1p(max(0, session_clicks)) / math.log1p(POPULARITY_CLICK_SATURATION))
    # 閲覧ログが無い初期状態でも、編集上の人気度を活かす
    return max(0.0, min(1.0, 0.55 * base + 0.45 * norm))


def score_trend_items(items: List[Dict[str, Any]], *, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """鮮度・（静的＋セッション）人気度を反映し display_score を付与。"""
    try:
        import streamlit as st

        pop_map: Dict[str, int] = st.session_state.setdefault(TREND_POPULARITY_SESSION_KEY, {})
    except Exception:
        pop_map = {}
    tday = today or date.today()
    scored: List[Dict[str, Any]] = []
    for row in items:
        r = dict(row)
        pub = r.get("_pub_date")
        if not isinstance(pub, date):
            pub = date.today()
        rel = max(0.0, min(1.0, float(r.get("reliability_score", 0.7))))
        fresh = _freshness_score(pub, tday)
        clicks = int(pop_map.get(str(r["id"]), 0))
        pop = _merged_popularity(r, clicks)
        r["freshness_score"] = fresh
        r["popularity_score_effective"] = pop
        r["display_score"] = (
            RELIABILITY_WEIGHT * rel + FRESHNESS_WEIGHT * fresh + POPULARITY_WEIGHT * pop
        )
        scored.append(r)
    scored.sort(
        key=lambda x: (-float(x["display_score"]), -x["_pub_date"].toordinal(), str(x["id"])),
    )
    return scored


def _source_label(row: Dict[str, Any], lang: str) -> str:
    key = row.get("source_key", "OTHER")
    if lang == "en":
        return {
            "MLIT": "MLIT (Japan)",
            "SANKI": "Miki Shoji",
            "JREIT": "JAPAN-REIT.COM",
            "CBRE": "CBRE",
            "OTHER": "Other",
        }.get(str(key), "Other")
    return {
        "MLIT": "国土交通省",
        "SANKI": "三鬼商事",
        "JREIT": "JAPAN-REIT.COM",
        "CBRE": "CBRE",
        "OTHER": "その他",
    }.get(str(key), "その他")


def _inject_trend_css_once() -> None:
    try:
        import streamlit as st
    except ImportError:
        return
    if st.session_state.get(TREND_CSS_INJECTED_KEY):
        return
    st.session_state[TREND_CSS_INJECTED_KEY] = True
    st.markdown(
        """
<style>
/* 不動産トレンド：既存テーマと干渉しにくいようスコープを lib-trend- で統一 */
.lib-trend-wrap { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans JP", sans-serif; color: #0f172a; }
.lib-trend-note { font-size: 0.88rem; color: #475569; line-height: 1.65; margin: 0 0 1rem 0; }
.lib-trend-subhead { font-size: 0.95rem; font-weight: 700; color: #0f1c2e; margin: 1.25rem 0 0.65rem 0; letter-spacing: 0.02em; }
.lib-trend-filters { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; align-items: flex-end; }
.lib-trend-card-stack { display: flex; flex-direction: column; gap: 1rem; margin: 0.35rem 0 0.5rem 0; }
.lib-trend-card {
  border: 1px solid rgba(15, 28, 46, 0.12);
  border-radius: 12px;
  padding: 1.1rem 1.15rem;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
  box-sizing: border-box;
  width: 100%;
  margin-bottom: 1rem;
}
.lib-trend-card:last-child { margin-bottom: 0; }
.lib-trend-card--featured {
  border-color: rgba(15, 28, 46, 0.28);
  background: linear-gradient(165deg, #f8fafc 0%, #ffffff 45%, #fafbfc 100%);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
  padding: 1.2rem 1.25rem;
}
.lib-trend-card--spotlight {
  border-color: rgba(15, 28, 46, 0.22);
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 55%);
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
}
.lib-trend-badges { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.45rem; }
.lib-trend-badge {
  display: inline-block; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em;
  padding: 0.2rem 0.45rem; border-radius: 4px; text-transform: uppercase;
}
.lib-trend-badge--new { background: #0f172a; color: #fff; }
.lib-trend-badge--tier-ko { background: #ecfdf5; color: #065f46; }
.lib-trend-badge--tier-gy { background: #eff6ff; color: #1e40af; }
.lib-trend-badge--tier-oth { background: #f4f4f5; color: #3f3f46; }
.lib-trend-card-title { font-size: 1.05rem; font-weight: 700; line-height: 1.5; margin: 0 0 0.55rem 0; color: #0f1c2e; }
.lib-trend-card-sum { font-size: 0.9rem; line-height: 1.72; color: #334155; margin: 0 0 0.75rem 0; }
.lib-trend-meta { font-size: 0.78rem; color: #64748b; line-height: 1.5; margin: 0; }
.lib-trend-score { font-size: 0.72rem; color: #94a3b8; margin-top: 0.35rem; }
.lib-trend-list { display: flex; flex-direction: column; gap: 0.65rem; }
.lib-trend-row {
  display: grid; grid-template-columns: minmax(0, 2.2fr) minmax(0, 3fr) auto;
  gap: 0.75rem; align-items: start;
  padding: 0.75rem 0.85rem; border: 1px solid rgba(15, 28, 46, 0.08); border-radius: 8px; background: #fff;
}
@media (max-width: 768px) {
  .lib-trend-row { grid-template-columns: 1fr; }
}
.lib-trend-row-title { font-weight: 650; font-size: 0.95rem; margin: 0; color: #0f1c2e; }
.lib-trend-archive-month { font-size: 0.85rem; font-weight: 700; color: #475569; margin: 0.75rem 0 0.35rem 0; }
</style>
        """,
        unsafe_allow_html=True,
    )


def _tier_badge_class(tier: str) -> str:
    t = str(tier)
    if t == "公的":
        return "lib-trend-badge lib-trend-badge--tier-ko"
    if t == "業界":
        return "lib-trend-badge lib-trend-badge--tier-gy"
    return "lib-trend-badge lib-trend-badge--tier-oth"


def _render_official_link(*, label: str, url: str, use_wide: bool, widget_key: str) -> None:
    """
    公式URLを開く（components.html の window.open は iframe 制約で失敗しやすいため link_button 優先）。
    古い Streamlit では link_button 未対応のため markdown リンクにフォールバックする。
    """
    import streamlit as st

    if not (url.startswith("http://") or url.startswith("https://")):
        return
    try:
        st.link_button(label, url, key=widget_key, use_container_width=use_wide)
    except TypeError:
        try:
            st.link_button(label, url, use_container_width=use_wide)
        except TypeError:
            st.markdown(
                f'<p class="lib-trend-wrap" style="margin:0.35rem 0 0 0;">'
                f'<a href="{html_escape(url)}" target="_blank" rel="noopener noreferrer">'
                f"{html_escape(label)}</a></p>",
                unsafe_allow_html=True,
            )


def render_real_estate_trends_section(
    *,
    base_dir: Path,
    t: Callable[[str], str],
    lang: str,
    render_section_title: Callable[..., None],
) -> None:
    """
    Streamlit 上に「不動産トレンド情報」を描画。
    t: app.py の i18n 関数（キー不足時はキーそのまま返す想定）
    """
    import streamlit as st

    _inject_trend_css_once()

    raw = fetch_trend_items(base_dir)
    items = normalize_trend_items(raw)
    items = summarize_trend_items(items, lang=lang)
    items = score_trend_items(items)

    # 見出し「不動産トレンド情報」の直下に置く（サブタイトル本文は下のアコーディオンへ）
    render_section_title(
        title_jp=t("trend_section_title"),
        title_en="",
        subtitle="",
    )
    # ① リード文・注意書きはアコーディオンで初期閉じ
    with st.expander(t("trend_notes_expander"), expanded=False):
        st.markdown(t("trend_section_sub"))
        st.markdown(t("trend_legal_note"))

    # ④ 絞り込みは見出しブロックの下へ（2列でコンパクトに）
    _f1, _f2 = st.columns(2)
    with _f1:
        cat_filter = st.selectbox(
            t("trend_filter_category"),
            options=[
                t("trend_cat_all"),
                "住宅",
                "オフィス",
                "商業",
                "J-REIT",
            ],
            key="lib_trend_filter_category",
        )
    with _f2:
        src_filter = st.selectbox(
            t("trend_filter_source"),
            options=[
                t("trend_src_all"),
                t("trend_src_kokudo"),
                t("trend_src_sanki"),
                t("trend_src_reit"),
                t("trend_src_other"),
            ],
            key="lib_trend_filter_source",
        )

    def _pass_filters(row: Dict[str, Any]) -> bool:
        if cat_filter != t("trend_cat_all") and row.get("category") != cat_filter:
            return False
        g = SOURCE_KEY_TO_GROUP.get(str(row.get("source_key")), "other")
        if src_filter == t("trend_src_kokudo") and g != "kokudo":
            return False
        if src_filter == t("trend_src_sanki") and g != "sanki":
            return False
        if src_filter == t("trend_src_reit") and g != "reit":
            return False
        if src_filter == t("trend_src_other") and g != "other":
            return False
        return True

    active_all = [r for r in items if not r.get("archived")]
    archived = [r for r in items if r.get("archived")]
    active = [r for r in active_all if _pass_filters(r)]
    archived_f = [r for r in archived if _pass_filters(r)]

    if not active and not archived_f:
        st.info(t("trend_empty"))
        return

    today = date.today()
    spotlight = active[:3]
    rest = active[3:]

    st.markdown(f'<div class="lib-trend-wrap"><p class="lib-trend-note"><b>{t("trend_spotlight_heading")}</b></p></div>', unsafe_allow_html=True)
    if spotlight:
        cols = st.columns(min(3, len(spotlight)))
        for i, row in enumerate(spotlight):
            with cols[i]:
                _render_trend_card(
                    row,
                    lang=lang,
                    t=t,
                    spotlight=True,
                    today=today,
                )
    else:
        st.caption(t("trend_spotlight_empty"))

    # ③ 用途別トレンド一覧は外側アコーディオンで初期閉じ（中身は従来どおりカード行）
    if rest:
        with st.expander(t("trend_by_use_heading"), expanded=False):
            for row in rest:
                _render_trend_row(row, lang=lang, t=t, today=today)
    else:
        st.caption(t("trend_list_empty"))

    # アーカイブ（月別見出し・折りたたみ）
    if archived_f:
        st.markdown("---")
        with st.expander(t("trend_archive_expander"), expanded=False):
            by_month: Dict[str, List[Dict[str, Any]]] = {}
            for row in sorted(archived_f, key=lambda x: (-x["_pub_date"].toordinal(), x["id"])):
                ym = row["_pub_date"].strftime("%Y-%m")
                by_month.setdefault(ym, []).append(row)
            for ym in sorted(by_month.keys(), reverse=True):
                st.markdown(
                    f'<div class="lib-trend-wrap"><p class="lib-trend-archive-month">{t("trend_archive_month_prefix")} {ym}</p></div>',
                    unsafe_allow_html=True,
                )
                for row in by_month[ym]:
                    _render_trend_row(row, lang=lang, t=t, today=today, compact=True)


def _render_trend_card(
    row: Dict[str, Any],
    *,
    lang: str,
    t: Callable[[str], str],
    spotlight: bool,
    today: date,
) -> None:
    import streamlit as st

    title = row["title_ja"] if lang == "ja" else row.get("title_en") or row["title_ja"]
    summary = row.get("summary") or ""
    pub: date = row["_pub_date"]
    age_days = (today - pub).days
    new_badge = age_days <= NEW_BADGE_DAYS
    tier = str(row.get("reliability_tier", ""))
    card_cls = "lib-trend-card lib-trend-card--spotlight" if spotlight else "lib-trend-card"
    new_html = f'<span class="lib-trend-badge lib-trend-badge--new">NEW</span>' if new_badge else ""
    tier_html = f'<span class="{_tier_badge_class(tier)}">{html_escape(tier)}</span>'
    cat_html = f'<span class="lib-trend-badge lib-trend-badge--tier-oth">{html_escape(row["category"])}</span>'
    # スコア行は変数にまとめてから f-string に埋め込む（.format 内の :.2f と f-string の {} が衝突し SyntaxError になるのを防ぐ）
    score_line = t("trend_score_caption").format(score=float(row["display_score"]))
    st.markdown(
        f"""
<div class="lib-trend-wrap {card_cls}">
  <div class="lib-trend-badges">{new_html}{tier_html}{cat_html}</div>
  <p class="lib-trend-card-title">{html_escape(title)}</p>
  <p class="lib-trend-card-sum">{html_escape(summary)}</p>
  <p class="lib-trend-meta">{html_escape(_source_label(row, lang))} · {html_escape(pub.isoformat())}</p>
  <p class="lib-trend-score">{html_escape(score_line)}</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    url = str(row.get("source_url", ""))
    _render_official_link(
        label=t("trend_open_official"),
        url=url,
        use_wide=True,
        widget_key=f"lib_trend_link_sp_{row['id']}",
    )


def _render_trend_row(
    row: Dict[str, Any],
    *,
    lang: str,
    t: Callable[[str], str],
    today: date,
    compact: bool = False,
) -> None:
    import streamlit as st

    title = row["title_ja"] if lang == "ja" else row.get("title_en") or row["title_ja"]
    summary = row.get("summary") or ""
    pub: date = row["_pub_date"]
    age_days = (today - pub).days
    new_badge = age_days <= NEW_BADGE_DAYS
    new_html = f'<span class="lib-trend-badge lib-trend-badge--new">NEW</span> ' if new_badge else ""
    tier = str(row.get("reliability_tier", ""))
    tier_badge = f'<span class="{_tier_badge_class(tier)}">{html_escape(tier)}</span> '
    score_html = ""
    if not compact:
        score_html = (
            f'<p class="lib-trend-score">'
            f'{html_escape(t("trend_score_caption").format(score=float(row["display_score"])))}'
            f"</p>"
        )
    left = f"""
<div class="lib-trend-wrap">
  <p class="lib-trend-row-title">{new_html}{html_escape(title)}</p>
  <p class="lib-trend-meta">{tier_badge}{html_escape(_source_label(row, lang))} · {html_escape(pub.isoformat())} · {html_escape(row["category"])}</p>
  {score_html}
</div>
    """
    mid = f'<div class="lib-trend-wrap"><p class="lib-trend-card-sum" style="margin:0">{html_escape(summary)}</p></div>'
    st.markdown(
        f'<div class="lib-trend-row">{left}<div>{mid}</div><div></div></div>',
        unsafe_allow_html=True,
    )
    url = str(row.get("source_url", ""))
    _render_official_link(
        label=t("trend_open_official"),
        url=url,
        use_wide=True,
        widget_key=f"lib_trend_link_row_{row['id']}",
    )

