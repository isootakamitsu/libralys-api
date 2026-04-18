"""ブラウザ内の shisanhyo 系メインデモ用 DCF／直接還元の参照画面（参考分析）。"""

from __future__ import annotations

import streamlit as st
import pandas as pd


def render_shisanhyo_embedded_dcf_dashboard(*, show_page_anchor: bool = False) -> None:
    """入力タブ＋結果タブで DC／DCF を試せる簡易ダッシュボード。

    既定ではアンカーなし（ツール体験デモ内での利用を想定）。ページ埋め込み時のみ True。
    """
    if show_page_anchor:
        st.markdown(
            '<div id="embedded_dcf_dash_anchor" style="scroll-margin-top:5.5rem;"></div>',
            unsafe_allow_html=True,
        )
    st.caption(
        "参考分析用のブラウザ内ダッシュボードです。前提を変えてインプット／アウトプットの流れを体感できます。"
    )

    tab_in, tab_out, tab_note = st.tabs(["入力", "結果（DCF／DC）", "留意点"])

    with tab_in:
        st.subheader("基本条件")
        c1, c2 = st.columns(2)
        with c1:
            area = st.number_input(
                "賃貸面積（㎡）",
                min_value=0.0,
                value=1000.0,
                step=10.0,
                key="sh_emb_dcf_area",
            )
            rent_pm = st.number_input(
                "市場賃料単価（円/㎡・月）",
                min_value=0.0,
                value=3000.0,
                step=50.0,
                key="sh_emb_dcf_rent",
            )
            occ = st.number_input(
                "稼働率（%）",
                min_value=0.0,
                max_value=100.0,
                value=95.0,
                step=0.5,
                key="sh_emb_dcf_occ",
            )
        with c2:
            opex_ratio = st.number_input(
                "運営費率（%：EGI比）",
                min_value=0.0,
                max_value=100.0,
                value=25.0,
                step=0.5,
                key="sh_emb_dcf_opex",
            )
            capex_y = st.number_input(
                "年間CapEx（円）",
                min_value=0.0,
                value=5_000_000.0,
                step=100_000.0,
                key="sh_emb_dcf_capex",
            )
            other_deduction_y = st.number_input(
                "その他控除（年額・円）※任意",
                min_value=0.0,
                value=0.0,
                step=100_000.0,
                key="sh_emb_dcf_other",
            )

        st.subheader("利回り・DCF条件（r−g 構造）")
        c3, c4 = st.columns(2)
        with c3:
            cap_rate = st.number_input(
                "Going-in Cap Rate（%）",
                min_value=0.1,
                max_value=30.0,
                value=4.5,
                step=0.1,
                key="sh_emb_dcf_caprate",
            )
            disc_r = st.number_input(
                "割引率 r（%）",
                min_value=0.1,
                max_value=30.0,
                value=5.5,
                step=0.1,
                key="sh_emb_dcf_r",
            )
            growth_g = st.number_input(
                "長期成長率 g（%）",
                min_value=-5.0,
                max_value=10.0,
                value=1.0,
                step=0.1,
                key="sh_emb_dcf_g",
            )
        with c4:
            hold_years = st.number_input(
                "保有期間（年）",
                min_value=1,
                max_value=30,
                value=10,
                step=1,
                key="sh_emb_dcf_years",
            )
            exit_cap = st.number_input(
                "Exit Cap Rate（%）",
                min_value=0.1,
                max_value=30.0,
                value=5.0,
                step=0.1,
                key="sh_emb_dcf_exitcap",
            )
            sale_cost_ratio = st.number_input(
                "売却費用率（%）※任意",
                min_value=0.0,
                max_value=10.0,
                value=1.5,
                step=0.1,
                key="sh_emb_dcf_salecost",
            )

        st.subheader("ER（簡易）")
        st.caption("PML 等を価格にどう織り込むかは案件ルール次第です。ここでは最小限の控除表示のみ行います。")
        c5, c6 = st.columns(2)
        with c5:
            pml = st.number_input(
                "PML（%）",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.5,
                key="sh_emb_dcf_pml",
            )
        with c6:
            er_reserve_y = st.number_input(
                "ER由来の追加準備金（年額・円）※任意",
                min_value=0.0,
                value=0.0,
                step=100_000.0,
                key="sh_emb_dcf_erreserve",
            )

        run = st.button("DCF／DC を計算（参考）", type="primary", key="sh_emb_dcf_run", width="stretch")
        if run:
            st.session_state["sh_emb_dcf_inputs"] = {
                "area": float(area),
                "rent_pm": float(rent_pm),
                "occ": float(occ),
                "opex_ratio": float(opex_ratio),
                "capex_y": float(capex_y),
                "other_deduction_y": float(other_deduction_y),
                "cap_rate": float(cap_rate),
                "disc_r": float(disc_r),
                "growth_g": float(growth_g),
                "hold_years": int(hold_years),
                "exit_cap": float(exit_cap),
                "sale_cost_ratio": float(sale_cost_ratio),
                "pml": float(pml),
                "er_reserve_y": float(er_reserve_y),
            }
            st.success("「結果」タブに出力しました。タブを切り替えてご確認ください。")

    with tab_out:
        if "sh_emb_dcf_inputs" not in st.session_state:
            st.info("左の「入力」タブで条件を設定し、「計算」ボタンを押してください。")
        else:
            inp = st.session_state["sh_emb_dcf_inputs"]
            gpi = inp["area"] * inp["rent_pm"] * 12.0
            egi = gpi * (inp["occ"] / 100.0)
            opex = egi * (inp["opex_ratio"] / 100.0)
            noi = egi - opex
            ncf0 = noi - inp["capex_y"] - inp["other_deduction_y"] - inp["er_reserve_y"]
            dc_value = ncf0 / (inp["cap_rate"] / 100.0) if inp["cap_rate"] > 0 else 0.0

            years = inp["hold_years"]
            r = inp["disc_r"] / 100.0
            g = inp["growth_g"] / 100.0
            exit_cap = inp["exit_cap"] / 100.0

            cash = []
            for t in range(1, years + 1):
                cf = ncf0 * ((1 + g) ** (t - 1))
                pv = cf / ((1 + r) ** t)
                cash.append((t, cf, pv))

            ncf_next = ncf0 * ((1 + g) ** years)
            terminal = ncf_next / exit_cap if exit_cap > 0 else 0.0
            terminal_net = terminal * (1 - inp["sale_cost_ratio"] / 100.0)
            terminal_pv = terminal_net / ((1 + r) ** years)
            dcf_value = sum(pv for _, _, pv in cash) + terminal_pv
            theo_cap = inp["disc_r"] - inp["growth_g"]

            st.subheader("主要結果（参考）")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("NOI（年額）", f"¥{noi:,.0f}")
            with m2:
                st.metric("NCF（年額）", f"¥{ncf0:,.0f}")
            with m3:
                st.metric("r−g（理論Cap）", f"{theo_cap:.2f}%")

            st.divider()
            m4, m5 = st.columns(2)
            with m4:
                st.success(f"直接還元価格（DC）：¥{dc_value:,.0f}")
                st.caption("NCF ÷ CapRate による参考値")
            with m5:
                st.success(f"DCF価格：¥{dcf_value:,.0f}")
                st.caption("年次CFの現在価値＋復帰価格の現在価値")

            diff = dcf_value - dc_value
            st.subheader("DC と DCF の差異（説明用）")
            st.write(f"差額：¥{diff:,.0f}")
            if dc_value > 0 and abs(diff) / dc_value < 0.05:
                st.info("概ね整合（乖離5%以内）。前提に大きな矛盾は見えにくい水準です。")
            elif diff > 0:
                st.info("DCF が高い：成長前提（g）や Exit 条件が価格を押し上げている可能性があります。")
            else:
                st.info("DCF が低い：割引率（r）や Exit Cap、売却費用等が価格を押し下げている可能性があります。")

            st.subheader("r−g 整合チェック")
            st.write(f"理論Cap（r−g）：{theo_cap:.2f}% / 入力 Cap：{inp['cap_rate']:.2f}%")
            if abs(theo_cap - inp["cap_rate"]) > 1.0:
                st.warning("Cap と r−g の乖離が大きい（±1.0%超）。説明・補正・例外判断の整理が必要です。")
            else:
                st.success("Cap と r−g は概ね整合しています。")

            st.subheader("ER（PML）簡易チェック")
            st.write(f"PML：{inp['pml']:.1f}%")
            if inp["pml"] >= 20.0:
                st.warning("PML が高水準です。保険・修繕・割引率（リスクプレミアム）等の整理が必要になりやすいです。")
            else:
                st.success("PML は相対的に落ち着いた水準（ただし物件特性に依存）です。")

            st.subheader("年次キャッシュフロー（参考）")
            df = pd.DataFrame(cash, columns=["年", "NCF（年額）", "PV"])
            st.dataframe(df, width="stretch", hide_index=True)

    with tab_note:
        st.write(
            """
- 本画面は参考分析です。正式な鑑定評価・コンサルティングは、資料確認・現地調査・市場分析に基づいて行います。  
- DCF は前提依存性が高いため、賃料・稼働率・運営費・CapEx・r・g・Exit 等を「固定して説明」することが重要です。  
- ローカルで動かす **フル版** アプリは、より実務に近い画面・データ連携を想定しています。
"""
        )
