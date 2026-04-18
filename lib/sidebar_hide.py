# -*- coding: utf-8 -*-
"""
Streamlit の左サイドバーを CSS で非表示・非操作にする。

st.sidebar 上のウィジェットは **Python 側では従来どおり実行**されるため、
app.py のページ selectbox や NAV_PENDING による session 同期は変えずに維持できる
（ユーザーはサイドバーをクリックできないだけ）。

注意: pages/chika_pydeck_dashboard.py のようにフィルタをサイドバーだけに置いている画面は、
非表示のままではその UI が使えなくなる。必要なら main 列へ移す。
"""

from __future__ import annotations

import streamlit as st

_HIDE_SIDEBAR_CSS = """
<style>
/* サイドバー本体：非表示・クリック不能（st.sidebar の実行と session は維持） */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
  display: none !important;
  width: 0 !important;
  min-width: 0 !important;
  max-width: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
  visibility: hidden !important;
}
[data-testid="collapsedControl"] {
  display: none !important;
  pointer-events: none !important;
  visibility: hidden !important;
}
/* メイン列の左余白（環境によってはサイドバー分が残るため） */
[data-testid="stAppViewContainer"] section.main,
section[data-testid="stMain"] {
  margin-left: 0 !important;
}
</style>
"""


def inject_hidden_sidebar_css() -> None:
    """各スクリプトの先頭付近で毎回呼ぶ（Streamlit の再描画後もスタイルが効くように）。"""
    st.markdown(_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
