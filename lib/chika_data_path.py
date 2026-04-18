"""地価公示 pydeck 用 CSV のパス解決。

優先順位:
1. 環境変数 ``CHIKA_CSV_PATH``（絶対パス、またはアプリルートからの相対パス）
2. Streamlit Secrets の **トップレベル** ``CHIKA_CSV_PATH``（Cloud の Secrets UI にそのまま貼れる）
3. Streamlit Secrets の ``[chika] csv_path``
4. 既定: ``<アプリルート>/data/kokoku/2026.csv``

※ Streamlit Community Cloud では Secrets が OS の環境変数に自動注入されないため、
  ``CHIKA_CSV_PATH`` を Secrets に書いた場合は本モジュールが ``st.secrets`` から読みます。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Tuple


def _app_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_under_root(path_str: str, root: Path) -> Path:
    s = path_str.strip()
    q = Path(s)
    return q.resolve() if q.is_absolute() else (root / q).resolve()


def _secrets_get_str(sec: Any, key: str) -> str:
    if sec is None:
        return ""
    try:
        if hasattr(sec, "get"):
            raw = sec.get(key)
        else:
            raw = sec[key]
        return str(raw or "").strip()
    except Exception:
        return ""


def _chika_csv_path_from_secrets(sec: Any, root: Path) -> Optional[Path]:
    """Secrets から csv パス文字列を得て Path にする。該当なしは None。"""
    top = _secrets_get_str(sec, "CHIKA_CSV_PATH")
    if top:
        return _resolve_under_root(top, root)
    try:
        if "chika" not in sec:
            return None
        ch = sec["chika"]
        rel = _secrets_get_str(ch, "csv_path")
        if rel:
            return _resolve_under_root(rel, root)
    except Exception:
        return None
    return None


def get_chika_data_csv_path(app_root: Optional[Path] = None) -> Path:
    """
    公示地価マップ用 CSV の絶対パスを返す。

    Parameters
    ----------
    app_root
        リポジトリ直下（``app.py`` があるディレクトリ）。未指定時は本ファイルから自動算出。
    """
    root = (app_root or _app_root()).resolve()

    env_override = os.environ.get("CHIKA_CSV_PATH", "").strip()
    if env_override:
        return _resolve_under_root(env_override, root)

    try:
        import streamlit as st

        sec = getattr(st, "secrets", None)
        if sec is not None:
            p = _chika_csv_path_from_secrets(sec, root)
            if p is not None:
                return p
    except Exception:
        pass

    return (root / "data" / "kokoku" / "2026.csv").resolve()


def describe_chika_csv_config_source(app_root: Optional[Path] = None) -> str:
    """診断用: どの設定が主パスに効いているか（機密・パス値は出さない）。"""
    root = (app_root or _app_root()).resolve()
    if os.environ.get("CHIKA_CSV_PATH", "").strip():
        return "環境変数 CHIKA_CSV_PATH"
    try:
        import streamlit as st

        sec = getattr(st, "secrets", None)
        if sec is not None:
            if _secrets_get_str(sec, "CHIKA_CSV_PATH"):
                return "Secrets の CHIKA_CSV_PATH（トップレベル）"
            if "chika" in sec and _secrets_get_str(sec["chika"], "csv_path"):
                return "Secrets の [chika].csv_path"
    except Exception:
        pass
    return "既定（リポジトリの data/kokoku/2026.csv）"


def resolve_effective_chika_csv_path(app_root: Optional[Path] = None) -> Tuple[Path, Optional[str]]:
    """
    設定どおりのパスが無いとき、リポジトリ同梱の代替 CSV を探す。

    Returns
    -------
    path
        読み込みに使う絶対パス（見つからない場合は主設定パス＝存在しない可能性あり）
    note
        代替利用時に UI へ出す説明文。不要なら None。
    """
    primary = get_chika_data_csv_path(app_root)
    root = (app_root or _app_root()).resolve()

    def _usable(p: Path) -> bool:
        try:
            return p.is_file() and p.stat().st_size > 0
        except OSError:
            return False

    if _usable(primary):
        return primary.resolve(), None

    alternates = [
        root / "data" / "chika_kouji_points.csv",
        root / "data" / "kokoku" / "2026.csv",
    ]
    for alt in alternates:
        if _usable(alt):
            return alt.resolve(), (
                f"主設定の CSV が見つからないため、代替ファイルを使用しています: `{alt.as_posix()}`"
            )

    return primary.resolve(), None
