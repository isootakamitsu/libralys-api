"""国交省系・公示地価 CSV（L01_xxx 列 + lon/lat）を pydeck 用の必須列に正規化する。

Streamlit Cloud（pandas+PyArrow 文字列）対策: 本モジュールは StringAccessor ``.str.*`` を使わず
``object`` 列 + ``re`` / ``map`` で処理する（ArrowInvalid 回避）。
デプロイ確認用: ``import`` 群の直後に ``_KOKOKU_NORM_NO_PANDAS_STR = 1`` があること。
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from lib.chika_prefecture_infer import canon_prefecture_name, infer_japanese_prefecture_from_address

_KOKOKU_NORM_NO_PANDAS_STR = 1

_REQUIRED = [
    "latitude",
    "longitude",
    "standard_no",
    "address",
    "prefecture",
    "city",
    "use_type",
    "price_current",
    "price_prev",
    "change_rate",
]


def _norm_colnames(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def looks_like_kokoku_l01_format(df: pd.DataFrame) -> bool:
    """L01 コード列と lon/lat を持つ公示地価系 CSV かどうか。"""
    if df is None or df.empty:
        return False
    cols = set(_norm_colnames(df).columns)
    return (
        "L01_006" in cols
        and "L01_007" in cols
        and ("lon" in cols or "LON" in cols or "longitude" in cols)
        and ("lat" in cols or "LAT" in cols or "latitude" in cols)
        and (
            ("L01_024" in cols and "L01_027" in cols)
            or ("L01_022" in cols and "L01_025" in cols)
        )
    )


def _zseries(d: pd.DataFrame, key: str) -> pd.Series:
    if key not in d.columns:
        return pd.Series("", index=d.index)
    return d[key].apply(lambda x: "" if pd.isna(x) else str(x).strip())


def _as_object_str_series(s: pd.Series) -> pd.Series:
    """
    PyArrow バックエンドの文字列列では ``.str.contains(..., regex=True)`` 等が
    ``pyarrow.lib.ArrowInvalid`` になることがあるため、Python str の object 列にそろえる。
    """
    a = s.fillna("")
    return pd.Series(["" if x is None else str(x) for x in a.tolist()], index=a.index, dtype=object)


# pandas / PyArrow の str.contains(regex=True) を使わず所在地らしさを判定する
_KOKOKU_ADDR_PREF_RE = re.compile(r"(?:北海道|東京都|大阪府|京都府|[\u4e00-\u9fff]{2}県)")


def _cell_looks_like_kokoku_address(val: object) -> bool:
    if val is None:
        return False
    try:
        if pd.isna(val):
            return False
    except (TypeError, ValueError):
        pass
    t = str(val)
    if "\u3000" in t:
        return True
    return _KOKOKU_ADDR_PREF_RE.search(t) is not None


def _address_looks_like_mask(s: pd.Series) -> pd.Series:
    """各行が公示の「所在地」列らしいか（Arrow の regex 経路を完全に回避）。"""
    idx = s.index
    vals = s.fillna("").tolist()
    return pd.Series([_cell_looks_like_kokoku_address(v) for v in vals], index=idx, dtype=bool)


def _address_series(d: pd.DataFrame) -> pd.Series:
    """
    所在地文字列。
    国交省系の標準では L01_024 が「北海道　札幌市…」形式。
    pandas が false/01101 で列ずれした場合は L01_022 が数値化され L01_024 に所在地が入るため、
    L01_024 に全角スペースや都道府県パターンがあれば L01_024 を優先する。
    """
    d = _norm_colnames(d)
    if "L01_024" not in d.columns:
        return _zseries(d, "L01_022")
    s24 = _as_object_str_series(d["L01_024"])
    looks_like_addr = _address_looks_like_mask(s24)
    if looks_like_addr.mean() > 0.3:
        return s24
    return _zseries(d, "L01_022")


def _use_type_series(d: pd.DataFrame) -> pd.Series:
    """用途区分。標準は L01_027（例: 住宅）。列ずれフォールバックで L01_025。"""
    d = _norm_colnames(d)
    if "L01_027" in d.columns:
        u = _as_object_str_series(d["L01_027"])
        if u.map(len).mean() > 0:
            return u
    return _zseries(d, "L01_025")


def normalize_kokoku_l01_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """L01 + lon/lat 形式の DataFrame を必須列名の DataFrame に変換（ベクトル化）。"""
    d = _norm_colnames(df)

    lon_col = "lon" if "lon" in d.columns else ("LON" if "LON" in d.columns else "longitude")
    lat_col = "lat" if "lat" in d.columns else ("LAT" if "LAT" in d.columns else "latitude")

    addr = _as_object_str_series(_address_series(d))

    # 全角スペースのみでなく半角スペース・タブ区切りにも対応（公式 CSV の揺れ対策）
    _addr_1sep = addr.astype(object).map(lambda t: re.sub(r"[\t \u3000]+", "\u3000", str(t)))
    _zen = "\u3000"
    _pref_parts: list[str] = []
    _rest_parts: list[str] = []
    for t in _addr_1sep.tolist():
        ts = str(t)
        if _zen in ts:
            a, b = ts.split(_zen, 1)
            _pref_parts.append(a)
            _rest_parts.append(b)
        else:
            _pref_parts.append("")
            _rest_parts.append(ts)
    pref = pd.Series(_pref_parts, index=d.index, dtype=object)
    rest_s = pd.Series(_rest_parts, index=d.index, dtype=object)

    # split で都道府県が取れない行は所在地先頭から 47 都道府県を推定（京都府など 0 件フィルタの防止）
    pstrip = pref.map(lambda x: str(x).strip())
    inf = addr.map(infer_japanese_prefecture_from_address)
    pref = _as_object_str_series(pstrip.where(pstrip != "", inf))
    pref = pref.map(canon_prefecture_name)

    _re_city_a = re.compile(r"^(.+?市.+?区)")
    _re_city_b = re.compile(r"^(.+?(?:市|区|町|村))")

    def _extract_city(rest: str) -> str:
        t = str(rest)
        m = _re_city_a.match(t)
        if m:
            return m.group(1)
        m = _re_city_b.match(t)
        if m:
            return m.group(1)
        return t[:48] if t else ""

    city = rest_s.map(_extract_city)

    z = lambda k: _zseries(d, k)
    standard_no = z("L01_001") + "-" + z("L01_002") + "-" + z("L01_003") + "-" + z("L01_004")
    if "L01_022" in d.columns:
        standard_no = standard_no + "-" + z("L01_022")
    standard_no = standard_no.map(lambda x: str(x).strip("-"))

    cur = pd.to_numeric(d["L01_006"], errors="coerce")
    rate = pd.to_numeric(d["L01_007"], errors="coerce")
    denom = 1.0 + rate / 100.0
    prev = np.where(np.isfinite(cur) & np.isfinite(rate) & (denom != 0.0), cur / denom, np.nan)

    out = pd.DataFrame(
        {
            "latitude": pd.to_numeric(d[lat_col], errors="coerce"),
            "longitude": pd.to_numeric(d[lon_col], errors="coerce"),
            "standard_no": standard_no,
            "address": addr,
            "prefecture": _as_object_str_series(pref),
            "city": _as_object_str_series(city),
            "use_type": _use_type_series(d),
            "price_current": cur,
            "price_prev": prev,
            "change_rate": rate,
        },
        index=d.index,
    )
    return out[_REQUIRED]
