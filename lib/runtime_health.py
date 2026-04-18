"""デプロイ後の動作確認用（機密値は表示しない）。"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from lib.chika_data_path import (
    describe_chika_csv_config_source,
    get_chika_data_csv_path,
    resolve_effective_chika_csv_path,
)
from lib.contact_submit import (
    build_resend_overrides_from_secrets_dict,
    build_smtp_overrides_from_secrets_dict,
    merge_resend_settings,
    merge_smtp_settings,
    resend_ready,
    smtp_ready,
)


def _git_short_sha(base: Path) -> str:
    if not (base / ".git").exists():
        return "（.git なし … Streamlit Cloud 等のビルド成果物想定）"
    try:
        proc = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "（取得失敗）"


def _smtp_overrides_from_secrets() -> Optional[Dict[str, Any]]:
    """app.py の build_smtp_overrides_for_submit と同等の辞書（診断用）。"""
    try:
        sec = getattr(st, "secrets", None)
        return build_smtp_overrides_from_secrets_dict(sec)
    except Exception:
        return None


def _contact_to_from_secrets() -> str:
    try:
        sec = getattr(st, "secrets", None)
        if sec is None:
            return "（Secrets なし）"
        if "contact" in sec and str(sec["contact"].get("to_email") or "").strip():
            return "設定あり（[contact].to_email）"
        if "smtp" in sec and str(sec["smtp"].get("to_email") or "").strip():
            return "設定あり（[smtp].to_email）"
        if "resend" in sec and str(sec["resend"].get("to_email") or "").strip():
            return "設定あり（[resend].to_email）"
    except Exception:
        pass
    return "未設定（メールソフトリンク用の宛先が出ません）"


def collect_health_report(base_dir: Path) -> List[tuple[str, str]]:
    """(ラベル, 説明) のリスト。パスワード等は出さない。"""
    base_dir = base_dir.resolve()
    rows: List[tuple[str, str]] = []

    rows.append(("アプリルート", str(base_dir)))
    rows.append(("Git コミット（短縮）", _git_short_sha(base_dir)))

    primary = get_chika_data_csv_path(base_dir)
    effective, fb_note = resolve_effective_chika_csv_path(base_dir)
    rows.append(("地図CSV（設定の出所）", describe_chika_csv_config_source(base_dir)))
    rows.append(("地図CSV（主設定パス）", str(primary)))
    try:
        ok_p = primary.is_file() and primary.stat().st_size > 0
        rows.append(("主設定CSVの状態", "存在・非空" if ok_p else "見つからないか空"))
    except OSError as e:
        rows.append(("主設定CSVの状態", f"確認エラー: {e}"))

    rows.append(("地図CSV（実際に読むパス）", str(effective)))
    try:
        ok_e = effective.is_file() and effective.stat().st_size > 0
        sz = effective.stat().st_size if ok_e else 0
        rows.append(("実効CSVの状態", f"OK（{sz:,} bytes）" if ok_e else "読めません"))
    except OSError as e:
        rows.append(("実効CSVの状態", f"エラー: {e}"))

    if fb_note:
        rows.append(("CSV フォールバック", fb_note))

    bundled_font = base_dir / "fonts" / "NotoSansJP-VF.ttf"
    rows.append(
        (
            "カード用フォント",
            f"同梱あり: {bundled_font.name}" if bundled_font.is_file() else "同梱なし（画像内日本語が化ける可能性）",
        )
    )

    ov = _smtp_overrides_from_secrets()
    merged = merge_smtp_settings(ov)
    smtp_ok = smtp_ready(merged)
    rows.append(
        (
            "SMTP（自動メール）",
            "Secrets 設定で送信可能な項目が揃っています"
            if smtp_ok
            else "未充足（host / user / password / to_email を Secrets の [smtp] で確認）",
        )
    )
    try:
        sec = getattr(st, "secrets", None)
        rov = build_resend_overrides_from_secrets_dict(sec) if sec is not None else None
    except Exception:
        rov = None
    r_merged = merge_resend_settings(rov)
    resend_ok = resend_ready(r_merged)
    rows.append(
        (
            "Resend API（自動メール・HTTPS）",
            "api_key / from_email / to_email が揃っています（Cloud 推奨）"
            if resend_ok
            else "未設定（[resend] またはトップレベル RESEND_API_KEY / RESEND_FROM_EMAIL・宛先 CONTACT_TO_EMAIL）",
        )
    )
    if merged.get("host"):
        rows.append(("SMTP ホスト", merged["host"]))
    rows.append(("事務局宛（リンク用）", _contact_to_from_secrets()))

    ce = (os.environ.get("CONTACT_TO_EMAIL") or "").strip()
    if ce:
        rows.append(("環境変数 CONTACT_TO_EMAIL", "設定あり（SMTP宛の補完に使用）"))

    return rows


def render_sidebar_health(base_dir: Path) -> None:
    """サイドバー用コンパクト診断。"""
    st.caption("この端末で実際に読み込んでいるパス・設定の充足状況です（パスワードは表示しません）。")
    for label, text in collect_health_report(base_dir):
        st.markdown(f"**{label}**")
        st.code(text, language="text")
