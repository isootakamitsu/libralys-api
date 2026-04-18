"""公的価格変動ダッシュボード（本番 UI）。`app.py` 内ページ用と単体 `streamlit run` 用の両方から呼び出す。"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.chika_data_path import resolve_effective_chika_csv_path
from lib.csv_io import read_csv_japanese, read_csv_japanese_from_bytes
from lib.kokoku_l01_hist_prices import median_yoy_series_from_l01_hist_prices

# Streamlit マルチページ `pages/koji_public_price.py` のファイル名（拡張子なし）と一致させること
KOJI_PUBLIC_PRICE_MULTIPAGE_URL_PATH = "koji_public_price"


def _dummy_series(region_key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(abs(hash(region_key)) % (2**32))
    years = np.arange(2016, 2026, dtype=int)
    idx_pub = 100.0 * np.cumprod(1.0 + rng.normal(0.011, 0.005, len(years)))
    idx_road = 100.0 * np.cumprod(1.0 + rng.normal(0.009, 0.004, len(years)))
    return years, idx_pub, idx_road


def _default_col_index(columns: list, patterns: tuple[str, ...]) -> int:
    """列名にパターンが含まれる最初の列を選ぶ。無ければ 0。"""
    for i, c in enumerate(columns):
        s = str(c)
        for pat in patterns:
            if re.search(pat, s, re.IGNORECASE):
                return i
    return 0


def _looks_like_kokoku_point_csv(df: pd.DataFrame) -> bool:
    """公示地点（L01 系・1 行＝1 地点）っぽいか。"""
    cols = {str(c).strip() for c in df.columns}
    if "L01_006" in cols and "L01_007" in cols:
        return True
    if "latitude" in cols and "longitude" in cols and "change_rate" in cols:
        return True
    return False


def _kokoku_change_rate_series_by_year(
    df: pd.DataFrame, *, stat: str = "median"
) -> tuple[np.ndarray, np.ndarray, str] | None:
    """
    公示地点 CSV: 調査年 L01_005 × 変動率 L01_007 を年次の代表値（既定: 中央値）に集計。
    単年ファイルでも 1 点の系列として返す（None は列不備・有効行なしのとき）。
    """
    d = df.copy()
    d.columns = [str(c).strip() for c in d.columns]
    if "L01_005" not in d.columns or "L01_007" not in d.columns:
        return None
    y = pd.to_numeric(d["L01_005"], errors="coerce")
    r = pd.to_numeric(d["L01_007"], errors="coerce")
    m = y.notna() & r.notna() & np.isfinite(r)
    if not m.any():
        return None
    sub = pd.DataFrame({"_y": y[m], "_r": r[m]})
    if stat == "mean":
        g = sub.groupby("_y", sort=True)["_r"].mean()
    else:
        g = sub.groupby("_y", sort=True)["_r"].median()
    years = g.index.astype(int).values
    vals = g.to_numpy(dtype=float)
    if len(years) == 0:
        return None
    _agg_label = "平均" if stat == "mean" else "中央値"
    note = (
        f"調査年（`L01_005`）ごとに変動率（`L01_007`）の**{_agg_label}**を集計しています。"
        " 地点横断の参考値であり、公式の地価指数・公表統計の代替ではありません。"
    )
    if len(years) == 1:
        note += (
            " **このファイルは調査年が 1 年のみ**のため、グラフは点が 1 つだけです。"
            " 複数年を含む CSV（または複数ファイルを縦結合した CSV）を使うと折れ線になります。"
        )
    return years, vals, note


def render_koji_public_price_dashboard(
    *,
    key_prefix: str = "",
    embedded_in_main_app: bool = False,
) -> None:
    """ダッシュボード本体。`embedded_in_main_app=True` のときは `set_page_config` 済み前提。"""
    if embedded_in_main_app:
        st.title("公的価格変動ダッシュボード")
        st.caption("本サイト内の**本番画面**です（参考分析・補助用途）。")
    else:
        st.title("公的価格変動ダッシュボード（参考）")
        st.caption(
            "本画面は補助分析用です。鑑定評価・価格断定・投資勧誘を行いません。"
            "公式の公示地価・路線価は国土交通省等の公表資料を参照してください。"
        )

    _nav_intro, _nav_site = st.columns(2)
    with _nav_intro:
        if st.button(
            "① 案内ページに戻る",
            key=f"{key_prefix}koji_nav_intro",
            width="stretch",
        ):
            st.switch_page("pages/chika_map_intro.py")
    with _nav_site:
        if st.button(
            "② サイトに戻る",
            key=f"{key_prefix}koji_nav_site",
            width="stretch",
        ):
            st.switch_page("app.py")
    st.markdown("---")

    tab_d, tab_tbl, tab_note = st.tabs(["ダッシュボード", "データ一覧", "留意点"])

    with tab_d:
        _app_root = Path(__file__).resolve().parent.parent
        _kokoku_path, _kokoku_note = resolve_effective_chika_csv_path(_app_root)

        with st.expander("データの種類と L01 列について（地図用 CSV と指数グラフ用 CSV は別です）", expanded=False):
            st.markdown(
                """
**このタブの折れ線グラフ**は「**年 × 指数**」の**時系列テーブル**用です（例: `year` と `公示地価指数` の列）。

**`data/kokoku/2026.csv` のような公示地点データ**は「**1 行＝1 地点**」で、**年次の指数列ではありません**。  
地図・地点フィルタは **案内 `chika_map_intro` → 地図ダッシュボード** を使ってください（読込パスは `CHIKA_CSV_PATH` / Secrets と同じ解決ルールです）。

国交省 L01 形式でよく使う列の例（地点 CSV）:

| 列 | 意味の例 |
|----|-----------|
| **L01_001〜004** | 地点番号の構成要素（**年や指数ではない**） |
| **L01_022** | 地域コード等 |
| **L01_005** | **調査年**（同一 CSV に複数年があれば、`L01_007` を年次で集計できます） |
| **L01_006** | 価格（円/㎡） |
| **L01_007** | 変動率（%）・地点ごとの前年比 |
| **L01_056 以降** | 国土数値情報では **昭和58年（1983）〜の年次単価（円/㎡）** が続く構成です（CSV によって列が数列ずれることがあります）。アプリは `L01_006` と一致する列からずれを推定し、**年別単価から前年比（%）**を算出できます。 |
| **L01_024** | 所在 |
| **L01_027** | 用途 |
"""
            )
            if _kokoku_note:
                st.info(_kokoku_note)
            st.caption(f"地図ページと同じ既定パス（参考）: `{_kokoku_path}`")

        up = st.file_uploader(
            "任意：指数時系列 CSV（列例: year, koji_index）※路線価指数は不要なら下のチェックを外す",
            type=["csv"],
            help="時系列指数用: 年列＋指数列。公示地点 L01 は年別単価列から前年比を算出するか、L01_007 を調査年別に集計します。",
            key=f"{key_prefix}koji_file",
        )
        use_repo_csv = st.checkbox(
            "リポジトリ既定の公示地価 CSV を読み込む（地点一覧・地図用ファイル）",
            value=False,
            key=f"{key_prefix}koji_use_repo_csv",
            help="地図ページと同じパス解決。年別単価列があればそこから前年比（中央値）を優先。無ければ L01_007 を調査年別に集計します。",
        )
        show_road = st.checkbox(
            "路線系指数も表示する",
            value=False,
            key=f"{key_prefix}koji_show_road",
        )
        region = st.selectbox(
            "エリア区分（ダミー用）",
            ["全国イメージ", "首都圏イメージ", "近畿イメージ"],
            key=f"{key_prefix}koji_region",
        )

        df_raw: pd.DataFrame | None = None
        if use_repo_csv and _kokoku_path.is_file():
            try:
                df_raw = read_csv_japanese(_kokoku_path)
                st.caption(f"読込: `{_kokoku_path}`")
            except Exception as e:
                st.error(f"既定パスからの読み込みに失敗しました: {e}")
        elif use_repo_csv:
            st.warning(f"既定パスのファイルがありません: `{_kokoku_path}`")

        if up is not None:
            try:
                df_raw = read_csv_japanese_from_bytes(up.getvalue())
            except Exception as e:
                st.error(f"アップロード CSV の読み込みに失敗しました: {e}")
                df_raw = None

        chart_kind: str = "dummy"
        kokoku_from_hist_prices = False

        if df_raw is not None and _looks_like_kokoku_point_csv(df_raw):
            hist_yoy = median_yoy_series_from_l01_hist_prices(df_raw)
            if hist_yoy is not None:
                years, idx_pub, kokoku_note = hist_yoy
                idx_road = np.full(len(years), np.nan)
                chart_kind = "kokoku_pct"
                kokoku_from_hist_prices = True
                st.success(
                    "公示地点 CSV の **年別単価列（L01_056 付近〜）** から前年比を算出し、"
                    "**地点ごとの中央値**を年次でグラフにしました。"
                )
                st.info(kokoku_note)
            else:
                kokoku_agg = _kokoku_change_rate_series_by_year(df_raw, stat="median")
                if kokoku_agg is not None:
                    years, idx_pub, kokoku_note = kokoku_agg
                    idx_road = np.full(len(years), np.nan)
                    chart_kind = "kokoku_pct"
                    st.success(
                        "公示地点 CSV から **調査年 × 変動率（L01_007）の中央値** を集計してグラフにしました。"
                    )
                    st.info(kokoku_note)
                else:
                    st.warning(
                        "読み込んだ CSV は **公示地点一覧** に見えますが、"
                        "年別単価からの前年比推定にも `L01_005`/`L01_006` 照合にも失敗し、"
                        "`L01_007` の集計もできませんでした。地図は **chika_map_intro** から開いてください。"
                    )
                    years, idx_pub, idx_road = _dummy_series(region)
                    chart_kind = "dummy"
                    st.info("グラフは **ダミーデータ** に切り替えました。")
        elif df_raw is not None:
            try:
                cols = list(df_raw.columns)
                iy = _default_col_index(cols, (r"年|年度|year|西暦",))
                ik = _default_col_index(cols, (r"公示|地価|koji",))
                ir = _default_col_index(cols, (r"路線|road",))
                if ir == ik and len(cols) > 1:
                    ir = min(1, len(cols) - 1)

                c1, c2 = st.columns(2)
                with c1:
                    col_y = st.selectbox(
                        "年の列",
                        options=cols,
                        index=iy,
                        key=f"{key_prefix}koji_csv_y",
                    )
                with c2:
                    col_k = st.selectbox(
                        "公示系指数の列",
                        options=cols,
                        index=ik,
                        key=f"{key_prefix}koji_csv_k",
                    )
                col_r = ""
                if show_road:
                    col_r = st.selectbox(
                        "路線系指数の列",
                        options=cols,
                        index=ir,
                        key=f"{key_prefix}koji_csv_r",
                    )

                years = pd.to_numeric(df_raw[col_y], errors="coerce").dropna().astype(int).values
                idx_pub = pd.to_numeric(df_raw[col_k], errors="coerce").ffill().bfill().to_numpy()
                n = min(len(years), len(idx_pub))
                years, idx_pub = years[:n], idx_pub[:n]
                if show_road and col_r:
                    idx_road = pd.to_numeric(df_raw[col_r], errors="coerce").ffill().bfill().to_numpy()[:n]
                    n = min(n, len(idx_road))
                    years, idx_pub, idx_road = years[:n], idx_pub[:n], idx_road[:n]
                else:
                    idx_road = np.full(n, np.nan)
                chart_kind = "index"
                st.success(f"CSV を読み込みました（{n} 行）。")
            except Exception as e:
                st.error(f"CSV の解釈に失敗しました: {e}")
                years, idx_pub, idx_road = _dummy_series(region)
                chart_kind = "dummy"
                st.info("ダミーデータにフォールバックしました。")
        else:
            years, idx_pub, idx_road = _dummy_series(region)
            chart_kind = "dummy"
            st.info("CSV 未指定のため **ダミーデータ** を表示しています。")

        if chart_kind == "kokoku_pct":
            if kokoku_from_hist_prices:
                pub_name = "公示地点・前年比（単価履歴→中央値）"
                fig_title = "公示地点・前年比の推移（年別単価から算出、地点ごとの中央値、%）"
            else:
                pub_name = "公示地点・変動率（中央値）"
                fig_title = "公示地点・変動率の年次推移（調査年ごとの中央値、%）"
        else:
            pub_name = "公示系指数"
            fig_title = "指数の推移（イメージ／アップロード値）"

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=years,
                y=idx_pub,
                name=pub_name,
                mode="lines+markers",
                line=dict(color="#C9A24D", width=2),
            )
        )
        if show_road and chart_kind != "kokoku_pct":
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=idx_road,
                    name="路線系指数",
                    mode="lines+markers",
                    line=dict(color="#0ea5e9", width=2),
                )
            )
        fig.update_layout(
            title=fig_title,
            height=460,
            paper_bgcolor="#F7F5F2",
            plot_bgcolor="#F7F5F2",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig, width="stretch")

        if chart_kind == "kokoku_pct" and len(idx_pub) >= 1:
            y_last = int(years[-1])
            _lbl = "前年比（単価から）" if kokoku_from_hist_prices else "変動率（L01_007 等）"
            st.metric(f"{y_last}年・{_lbl}（地点の中央値）", f"{idx_pub[-1]:+.2f}%")
            if len(idx_pub) >= 2:
                y_prev = int(years[-2])
                st.metric(
                    f"{y_last}年と{y_prev}年の前年比・中央値の差（pt）",
                    f"{idx_pub[-1] - idx_pub[-2]:+.2f}",
                )
        elif len(idx_pub) > 1:
            yoy_pub = (idx_pub[-1] / idx_pub[-2] - 1.0) * 100.0
            if show_road and len(idx_road) > 1:
                yoy_road = (idx_road[-1] / idx_road[-2] - 1.0) * 100.0
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("公示系・直近前年比", f"{yoy_pub:+.2f}%")
                with m2:
                    st.metric("路線系・直近前年比", f"{yoy_road:+.2f}%")
                with m3:
                    st.metric("差（pt）", f"{yoy_pub - yoy_road:+.2f}")
            else:
                st.metric("公示系・直近前年比", f"{yoy_pub:+.2f}%")

    with tab_tbl:
        rng = np.random.default_rng(42)
        prefs = ["北海道", "宮城", "東京", "神奈川", "愛知", "大阪", "福岡"]
        rows = [
            {
                "都道府県（例）": p,
                "公示YoY%（ダミー）": round(float(rng.normal(1.2, 0.9)), 2),
                "路線YoY%（ダミー）": round(float(rng.normal(0.9, 0.7)), 2),
            }
            for p in prefs
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption("表はサンプルです。CSV を利用する場合はダッシュボードタブで取り込みください。")

    with tab_note:
        note_extra = ""
        if embedded_in_main_app:
            note_extra = "- 本画面はサイト本体と**同一セッション**で動作します（別ポートの単体起動とは状態を共有しません）。\n"
        else:
            note_extra = "- 本スクリプトは `app.py`（会社サイト用）と**別ポート**で起動してください。\n"
        st.markdown(
            f"""
- **ダミーデータ**および**サンプル表**は説明用であり、実務判断の根拠にできません。  
- **公示地価・路線価**の公式値は国土交通省・都道府県等の公表を参照してください。  
- CSV 取り込みは列の数値化のみ行います。単位・指数定義の整合は利用者側で確認してください。  
{note_extra}"""
        )
