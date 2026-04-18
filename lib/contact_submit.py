"""お問い合わせの保存（推奨）と SMTP 送信（任意・Secrets 優先）。"""

from __future__ import annotations

import json
import os
import smtplib
import socket
import tempfile
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Streamlit Secrets の [smtp] は dict 風オブジェクトのことがあり、列挙だけではキーが欠ける場合があるため明示する。
_SMTP_SECRET_KEYS = ("host", "port", "user", "password", "from_email", "to_email")
_RESEND_SECRET_KEYS = ("api_key", "from_email", "to_email")


def _secrets_top_level_scalar(sec: Any, key: str) -> str:
    """``st.secrets`` のトップレベルキー（TOML で ``KEY = "..."``）を安全に取得。"""
    if sec is None:
        return ""
    try:
        if key not in sec:
            return ""
        v = sec[key]
        if v is None:
            return ""
        if isinstance(v, (dict, list)):
            return ""
        s = str(v).strip()
        return s
    except Exception:
        return ""


def _office_inbox_from_secrets_dict(sec: Any) -> str:
    """事務局宛先: [contact].to_email → [smtp].to_email → [resend].to_email → Secrets/環境の CONTACT_TO_EMAIL。"""
    inbox = ""
    try:
        if sec and "contact" in sec:
            c = sec["contact"]
            inbox = str(c.get("to_email", "") if hasattr(c, "get") else c["to_email"]).strip()
    except Exception:
        pass
    if not inbox:
        try:
            if sec and "smtp" in sec:
                s = sec["smtp"]
                inbox = str(s.get("to_email", "") if hasattr(s, "get") else s["to_email"]).strip()
        except Exception:
            pass
    if not inbox:
        try:
            if sec and "resend" in sec:
                r = sec["resend"]
                inbox = str(r.get("to_email", "") if hasattr(r, "get") else r["to_email"]).strip()
        except Exception:
            pass
    if not inbox:
        for k in ("CONTACT_TO_EMAIL", "contact_to_email"):
            inbox = _secrets_top_level_scalar(sec, k)
            if inbox:
                break
    if not inbox:
        inbox = (os.environ.get("CONTACT_TO_EMAIL") or "").strip()
    return inbox


def build_smtp_overrides_from_secrets_dict(sec: Any) -> Optional[Dict[str, Any]]:
    """
    ``st.secrets`` 相当のマッピングから ``merge_smtp_settings`` 用の辞書を作る。

    - ``[smtp]`` の各キーは **キー名で直接参照**（イテレーションに依存しない）。
    - ``to_email`` が ``[smtp]`` に無く ``[contact].to_email`` にだけある場合は補完する。
    """
    if sec is None:
        return None
    merged: Dict[str, Any] = {}
    try:
        if "smtp" in sec:
            block = sec["smtp"]
            for k in _SMTP_SECRET_KEYS:
                try:
                    if k not in block:
                        continue
                    v = block[k]
                except Exception:
                    continue
                if v is None:
                    continue
                if isinstance(v, str) and not v.strip():
                    continue
                merged[k] = v
    except Exception:
        pass

    inbox = _office_inbox_from_secrets_dict(sec)
    if inbox and not str(merged.get("to_email") or "").strip():
        merged["to_email"] = inbox

    # トップレベル CONTACT_SMTP_*（Streamlit Secrets で [smtp] テーブルを使わない書き方向け）
    _tl_smtp = (
        ("host", "CONTACT_SMTP_HOST"),
        ("port", "CONTACT_SMTP_PORT"),
        ("user", "CONTACT_SMTP_USER"),
        ("password", "CONTACT_SMTP_PASSWORD"),
        ("from_email", "CONTACT_FROM_EMAIL"),
    )
    for smtp_key, top_key in _tl_smtp:
        if not str(merged.get(smtp_key) or "").strip():
            v = _secrets_top_level_scalar(sec, top_key)
            if v:
                merged[smtp_key] = v

    return merged if merged else None


def build_resend_overrides_from_secrets_dict(sec: Any) -> Optional[Dict[str, Any]]:
    """
    ``[resend]`` から Resend API 用の辞書を作る（HTTPS・Streamlit Cloud で SMTP より通りやすい）。

    必須は ``api_key``。``to_email`` は ``[contact].to_email`` 等で補完可。
    """
    if sec is None:
        return None
    merged: Dict[str, Any] = {}
    try:
        if "resend" in sec:
            block = sec["resend"]
            for k in _RESEND_SECRET_KEYS:
                try:
                    if k not in block:
                        continue
                    v = block[k]
                except Exception:
                    continue
                if v is None:
                    continue
                if isinstance(v, str) and not v.strip():
                    continue
                merged[k] = v
    except Exception:
        pass

    inbox = _office_inbox_from_secrets_dict(sec)
    if inbox and not str(merged.get("to_email") or "").strip():
        merged["to_email"] = inbox

    # トップレベル（公式例に近い ``RESEND_API_KEY = "re_..."`` 形式）
    if not str(merged.get("api_key") or "").strip():
        for k in ("RESEND_API_KEY", "resend_api_key"):
            v = _secrets_top_level_scalar(sec, k)
            if v:
                merged["api_key"] = v
                break
    if not str(merged.get("from_email") or "").strip():
        for k in ("RESEND_FROM_EMAIL", "resend_from_email"):
            v = _secrets_top_level_scalar(sec, k)
            if v:
                merged["from_email"] = v
                break

    return merged if str(merged.get("api_key") or "").strip() else None


def merge_smtp_settings(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Streamlit Secrets（``overrides``）を最優先し、未設定キーだけ環境変数 CONTACT_* で補完する。

    キー: host, port, user, password, to_email, from_email
    """
    out: Dict[str, str] = {}

    def put(key: str, val: Any) -> None:
        if val is None:
            return
        s = str(val).strip()
        if s:
            out[key] = s

    if overrides:
        put("host", overrides.get("host"))
        put("port", overrides.get("port"))
        put("user", overrides.get("user"))
        put("password", overrides.get("password"))
        put("to_email", overrides.get("to_email"))
        put("from_email", overrides.get("from_email"))

    if "host" not in out:
        put("host", os.environ.get("CONTACT_SMTP_HOST"))
    if "port" not in out:
        put("port", os.environ.get("CONTACT_SMTP_PORT"))
    if "user" not in out:
        put("user", os.environ.get("CONTACT_SMTP_USER"))
    if "password" not in out:
        put("password", os.environ.get("CONTACT_SMTP_PASSWORD"))
    if "to_email" not in out:
        put("to_email", os.environ.get("CONTACT_TO_EMAIL"))
    if "from_email" not in out:
        put("from_email", os.environ.get("CONTACT_FROM_EMAIL"))

    return out


def merge_resend_settings(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Secrets（overrides）優先。未設定は環境変数 RESEND_* / CONTACT_TO_EMAIL で補完。"""
    out: Dict[str, str] = {}

    def put(key: str, val: Any) -> None:
        if val is None:
            return
        s = str(val).strip()
        if s:
            out[key] = s

    if overrides:
        put("api_key", overrides.get("api_key"))
        put("from_email", overrides.get("from_email"))
        put("to_email", overrides.get("to_email"))

    if "api_key" not in out:
        put("api_key", os.environ.get("RESEND_API_KEY"))
    if "from_email" not in out:
        put("from_email", os.environ.get("RESEND_FROM_EMAIL"))
    if "to_email" not in out:
        put("to_email", os.environ.get("CONTACT_TO_EMAIL"))

    return out


def resend_ready(settings: Dict[str, str]) -> bool:
    """Resend は api_key・送信元・宛先が揃えば送信可能。"""
    return bool(
        (settings.get("api_key") or "").strip()
        and (settings.get("from_email") or "").strip()
        and (settings.get("to_email") or "").strip()
    )


def smtp_ready(settings: Dict[str, str]) -> bool:
    """Gmail 等は host・宛先・ユーザー・アプリパスワードが揃って初めて送信可能。"""
    if not settings.get("host") or not settings.get("to_email"):
        return False
    if not (settings.get("user") or "").strip():
        return False
    if not (settings.get("password") or "").strip():
        return False
    return True


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _resolve_contact_log_path(app_dir: Path) -> Tuple[Path, Optional[str]]:
    """
    記録先パスを返す。Streamlit Cloud 等でアプリ直下が読み取り専用のときは temp にフォールバック。

    Returns
    -------
    path
        JSONL の絶対パス
    warning
        フォールバック利用時に UI へ出す警告文、なければ None
    """
    primary = (app_dir / "data" / "contact_inquiries.jsonl").resolve()
    try:
        primary.parent.mkdir(parents=True, exist_ok=True)
        with primary.open("a", encoding="utf-8"):
            pass
        return primary, None
    except OSError:
        pass

    fallback = Path(tempfile.gettempdir()) / "library_contact_inquiries" / "contact_inquiries.jsonl"
    try:
        fallback.parent.mkdir(parents=True, exist_ok=True)
        with fallback.open("a", encoding="utf-8"):
            pass
    except OSError as exc:
        raise OSError(
            f"お問い合わせの保存先を確保できませんでした（アプリ配下・一時フォルダの両方で失敗）: {exc}"
        ) from exc

    warn = (
        "サーバー上でアプリフォルダへ書き込めないため、**一時領域**に記録しました（ホスト再起動等で失われる可能性があります）。"
        "確実な受付には **Streamlit Cloud の Secrets に [smtp] を設定**しメール通知を有効にしてください。"
    )
    return fallback, warn


def _build_email_body(record: Dict[str, Any]) -> str:
    lines = [
        "ライブラリーズ お問い合わせフォームより",
        "",
        f"相談種別: {record.get('purpose', '')}",
        f"お名前: {record.get('name', '')}",
        f"メール: {record.get('email', '')}",
        f"電話: {record.get('tel', '') or '（未入力）'}",
        f"所在地: {record.get('address', '') or '（未入力）'}",
        "",
        "【ご相談内容】",
        record.get("message", ""),
        "",
        f"受付日時: {record.get('submitted_at', '')}",
    ]
    return "\n".join(lines)


def _try_smtp(record: Dict[str, Any], settings: Dict[str, str]) -> Tuple[bool, str]:
    host = settings.get("host", "")
    to_addr = settings.get("to_email", "")
    if not host or not to_addr:
        return False, "SMTPホストまたは宛先メールが未設定です"

    port_raw = settings.get("port", "587")
    try:
        port = int(port_raw)
    except ValueError:
        port = 587

    user = (settings.get("user", "") or "").strip()
    password = "".join((settings.get("password", "") or "").split())
    from_addr = (settings.get("from_email") or user or to_addr).strip()

    msg = EmailMessage()
    purpose = str(record.get("purpose", "")).replace("\r", " ").replace("\n", " ")[:200]
    msg["Subject"] = f"[ライブラリーズ] お問い合わせ {purpose}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(_build_email_body(record))
    reply = (record.get("email") or "").strip()
    if reply:
        msg["Reply-To"] = reply

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=45) as smtp:
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=45) as smtp:
                smtp.starttls()
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
        return True, "通知メールを送信しました"
    except socket.timeout as exc:
        return (
            False,
            f"SMTP接続がタイムアウトしました（{exc}）。ホスト・ポート、ファイアウォール、"
            "Streamlit Cloud からの外向き SMTP 可否を確認してください。",
        )
    except OSError as exc:
        if "timed out" in str(exc).lower():
            return (
                False,
                f"SMTP接続がタイムアウトしました（{exc}）。ネットワークまたはポート（587/465）を確認してください。",
            )
        return False, f"SMTP通信エラー: {exc}"
    except Exception as exc:
        hint = ""
        err = str(exc).lower()
        if "535" in str(exc) or "badcredentials" in err or "username and password" in err:
            hint = (
                "（Gmailの場合: `user` は完全なメールアドレス、`password` は必ず「アプリパスワード」16文字。"
                "通常ログインパスワードは不可。2段階認証オン後に再発行し、コピペミス・前後空白を確認。"
                "それでも失敗する場合は port を 465 にし host=smtp.gmail.com で SSL も試してください。）"
            )
        return False, f"SMTPエラー: {exc}{hint}"


def submit_contact(
    app_dir: Path,
    payload: Dict[str, Any],
    smtp_overrides: Optional[Dict[str, Any]] = None,
    resend_overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Optional[str], bool, Optional[str]]:
    """
    可能なら ``data/contact_inquiries.jsonl`` に追記し、
    **Resend（HTTPS）** または **SMTP** が揃っていれば事務局へ通知する（Resend を優先）。

    Returns
    -------
    ok, message, extra_warn, email_sent, storage_note
        storage_note … 記録ファイルのパスやフォールバック説明（任意で UI に表示）
    """
    import html as html_stdlib
    import re

    import requests

    def _post_resend(rec: Dict[str, Any], rs: Dict[str, str]) -> Tuple[bool, str]:
        """Resend API（requests.post）。成功時メッセージは「送信成功」。"""
        api_key = (rs.get("api_key") or "").strip()
        to_email = (rs.get("to_email") or "").strip()
        raw_from = (rs.get("from_email") or "").strip()
        if not api_key or not to_email or not raw_from:
            return False, "Resend の api_key / from_email / to_email が未設定です"

        m = re.search(r"<([^>]+)>", raw_from)
        from_email = (m.group(1).strip() if m else raw_from).strip()

        plain = _build_email_body(rec)
        html_content = f"<pre>{html_stdlib.escape(plain)}</pre>"

        json_body: Dict[str, Any] = {
            "from": f"お問い合わせ <{from_email}>",
            "to": [to_email],
            "subject": "お問い合わせが届きました",
            "html": html_content,
        }
        reply_addr = (rec.get("email") or "").strip()
        if reply_addr:
            json_body["reply_to"] = reply_addr

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=json_body,
                timeout=45,
            )
        except requests.RequestException as exc:
            return False, f"Resend 通信エラー: {exc}"

        if response.status_code not in (200, 201):
            return False, f"Resend API エラー: {response.text}"

        return True, "送信成功"

    record = {
        **payload,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }
    settings = merge_smtp_settings(smtp_overrides)
    resend_settings = merge_resend_settings(resend_overrides)

    log_path: Optional[Path] = None
    storage_note: Optional[str] = None
    fallback_warn: Optional[str] = None

    try:
        log_path, fallback_warn = _resolve_contact_log_path(app_dir)
        _append_jsonl(log_path, record)
        storage_note = f"記録先: `{log_path}`"
    except OSError as exc:
        # ファイル不可でも Resend / SMTP があればメールのみで受付成功とする（Cloud 向け）
        mail_errors: list[str] = []
        if resend_ready(resend_settings):
            ok_r, det_r = _post_resend(record, resend_settings)
            if ok_r:
                return (
                    True,
                    "送信成功",
                    None,
                    True,
                    f"※ ファイル保存エラー: {exc}",
                )
            mail_errors.append(det_r)
        if smtp_ready(settings):
            ok_smtp, det_s = _try_smtp(record, settings)
            if ok_smtp:
                return (
                    True,
                    "お問い合わせをメールで送信しました。（サーバーへのファイル記録は利用できませんでした）",
                    None,
                    True,
                    f"※ ファイル保存エラー: {exc}",
                )
            mail_errors.append(det_s)
        if mail_errors:
            return (
                False,
                f"ファイル保存に失敗し、メール送信も失敗しました: {exc} / {'；'.join(mail_errors)}",
                None,
                False,
                None,
            )
        return False, f"送信データの保存に失敗しました: {exc}", None, False, None

    base_ok = "お問い合わせを受け付け、内容を記録しました。"

    if fallback_warn:
        storage_note = f"{storage_note}\n\n{fallback_warn}" if storage_note else fallback_warn

    send_failures: list[str] = []

    if resend_ready(resend_settings):
        ok_r, det_r = _post_resend(record, resend_settings)
        if ok_r:
            return True, "送信成功", None, True, storage_note
        send_failures.append(det_r)

    if smtp_ready(settings):
        ok_s, det_s = _try_smtp(record, settings)
        if ok_s:
            return True, f"{base_ok} {det_s}", None, True, storage_note
        send_failures.append(det_s)

    if not resend_ready(resend_settings) and not smtp_ready(settings):
        hint = (
            "※ **自動メールはまだ届きません。** メール送信（**[resend]** の Resend API または **[smtp]**）が未設定のため、"
            "サーバーから事務局への通知メールは送信されていません。"
            "Streamlit Cloud の **Secrets** に `[resend]`（HTTPS・推奨）または `[smtp]` を設定するか、"
            "下の「メールソフトで送る」をご利用ください。"
        )
        return True, base_ok, hint, False, storage_note

    joined = "；".join(send_failures)
    return True, base_ok, f"※ 記録は保存済みですが、メール送信に失敗しました（{joined}）", False, storage_note
