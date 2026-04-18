"""公示地価 L01 CSV の年次単価列（L01_056 付近〜）から、地点別前年比の中央値時系列を求める。

国土数値情報の属性定義では L01_056 が昭和58年（1983）の単価、以降の列が年次単価となるが、
CSV によっては列が数列ずれるため、`L01_005`（調査年）と `L01_006`（当年単価）の一致列から
列オフセットを推定する。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# 国土数値情報 L01 テンプレート（例: v3.0）に基づく対応
_HIST_FIRST_YEAR = 1983  # 昭和58年（S58 単価列に相当する暦年）
_HIST_OFFICIAL_FIRST_COL_NUM = 56  # L01_056 = S58 公示価格


def infer_l01_hist_price_col_offset(df: pd.DataFrame) -> int | None:
    """
    `L01_006`（公示価格）と数値が一致する列が、仕様上の当年列から何列ずれているか推定する。
    一致行数が十分あるときだけオフセットを返す。推定不能なら None。
    """
    d = df
    if "L01_005" not in d.columns or "L01_006" not in d.columns:
        return None
    ty = pd.to_numeric(d["L01_005"], errors="coerce").dropna()
    if ty.empty:
        return None
    survey_year = int(ty.mode().iloc[0])
    official_nn = _HIST_OFFICIAL_FIRST_COL_NUM + (survey_year - _HIST_FIRST_YEAR)
    tgt = pd.to_numeric(d["L01_006"], errors="coerce").to_numpy()
    n = len(d)
    if n == 0:
        return None
    best_off, best_cnt = 0, -1
    for off in range(-3, 16):
        nn = official_nn + off
        c = f"L01_{nn:03d}"
        if c not in d.columns:
            continue
        colv = pd.to_numeric(d[c], errors="coerce").to_numpy()
        if colv.shape != tgt.shape:
            continue
        cnt = int(
            np.sum(
                np.isfinite(tgt)
                & np.isfinite(colv)
                & (tgt > 0)
                & (np.abs(tgt - colv) <= 0.5),
            )
        )
        if cnt > best_cnt:
            best_cnt, best_off = cnt, off
    if best_cnt < max(30, int(n * 0.05)):
        return None
    return best_off


def _iter_hist_year_columns(df: pd.DataFrame, offset: int, *, max_calendar_year: int) -> list[tuple[int, str]]:
    """暦年昇順の (year, column_name)。単価でない列（内部コード等）で打ち切る。"""
    out: list[tuple[int, str]] = []
    # 当年単価列のオフセットぶん、L01_056 から右へずれた先が実際の S58 単価列になりうる
    nn = _HIST_OFFICIAL_FIRST_COL_NUM + offset
    while nn <= 220:
        c = f"L01_{nn:03d}"
        if c not in df.columns:
            break
        y = _HIST_FIRST_YEAR + (nn - _HIST_OFFICIAL_FIRST_COL_NUM - offset)
        if y > max_calendar_year:
            break
        ser = pd.to_numeric(df[c], errors="coerce")
        med = float(np.nanmedian(ser.to_numpy()))
        if not np.isfinite(med):
            nn += 1
            continue
        if med > 5e11:
            break
        out.append((y, c))
        nn += 1
    out.sort(key=lambda x: x[0])
    return out


def median_yoy_series_from_l01_hist_prices(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, str] | None:
    """
    各地点について隣接する暦年の単価から前年比（%）を計算し、その中央値を暦年（変化後の年）ごとに集計。

    Returns:
        (years_end, yoy_pct_median, note) または推定・計算不能時 None。
        years_end[i] は (year-1 → year) の変化を表す終端年。
    """
    d = df.copy()
    d.columns = [str(c).strip() for c in d.columns]
    offset = infer_l01_hist_price_col_offset(d)
    if offset is None:
        return None
    sy = pd.to_numeric(d["L01_005"], errors="coerce").dropna()
    if sy.empty:
        return None
    max_cal_year = int(sy.max())
    pairs = _iter_hist_year_columns(d, offset, max_calendar_year=max_cal_year)
    if len(pairs) < 2:
        return None
    year_to_col = {y: c for y, c in pairs}
    years_sorted = sorted(year_to_col.keys())
    years_end: list[int] = []
    yoys: list[float] = []
    for y in years_sorted:
        y0 = y - 1
        if y0 not in year_to_col:
            continue
        c0, c1 = year_to_col[y0], year_to_col[y]
        p0 = pd.to_numeric(d[c0], errors="coerce").to_numpy(dtype=float)
        p1 = pd.to_numeric(d[c1], errors="coerce").to_numpy(dtype=float)
        mask = np.isfinite(p0) & np.isfinite(p1) & (p0 > 0) & (p1 > 0)
        if not np.any(mask):
            continue
        pct = (p1[mask] / p0[mask] - 1.0) * 100.0
        years_end.append(y)
        yoys.append(float(np.nanmedian(pct)))
    if not years_end:
        return None
    note = (
        f"**年別単価**（仕様上は `L01_056`＝{_HIST_FIRST_YEAR}年相当から続く列）と `L01_006` の照合で"
        f" **列オフセット {offset:+d}** を推定し、各地点の**前年比（%）**を求めたうえで**中央値**を年ごとに集計しています。"
        " 新設地点など前年単価がない行は除きます。公表の `L01_007` や公式指数とは一致しない場合があります。"
    )
    return np.array(years_end, dtype=int), np.array(yoys, dtype=float), note
