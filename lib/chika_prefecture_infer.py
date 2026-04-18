# -*- coding: utf-8 -*-
"""所在地文字列先頭から都道府県名を推定（公示 CSV の区切りゆれ対策）。"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

import pandas as pd

# 47 都道府県（先頭マッチ・長い語が先に来るよう必要なら調整）
_JP_PREFECTURES: tuple[str, ...] = (
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
    "東京都",
)

_JP_PREF_PATTERN = re.compile("^(" + "|".join(re.escape(p) for p in _JP_PREFECTURES) + ")")


def chika_norm_txt_simple(val: Optional[object]) -> str:
    return unicodedata.normalize("NFKC", str(val).strip())


# 列に略記だけ入っている場合の正規化（フィルタとドロップダウンを一致させる）
_PREF_CANON: dict[str, str] = {
    "京都": "京都府",
    "大阪": "大阪府",
    "東京": "東京都",
}


def canon_prefecture_name(val: object) -> str:
    """NFKC 後、略記なら正式名称に寄せる。"""
    if val is None:
        return ""
    try:
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    t = chika_norm_txt_simple(val)
    if not t or t == "nan":
        return ""
    return _PREF_CANON.get(t, t)


def infer_japanese_prefecture_from_address(text: object) -> str:
    """
    先頭が「○○県／○○府／東京都／北海道」形式ならその文字列を返す。
    NFKC 後に判定する。
    """
    if text is None or (isinstance(text, float) and str(text) == "nan"):
        return ""
    t = chika_norm_txt_simple(text)
    if not t:
        return ""
    m = _JP_PREF_PATTERN.match(t)
    return m.group(1) if m else ""
