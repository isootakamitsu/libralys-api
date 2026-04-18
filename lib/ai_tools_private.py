"""AIツール「フル版」パス・起動コマンドは公開リポに含めず、Secrets のみで上書きする。"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

def _secrets_ai_tools_private_root() -> Dict[str, Any] | None:
    try:
        root = st.secrets.get("ai_tools_private", None)
    except Exception:
        return None
    if root is None:
        return None
    if hasattr(root, "to_dict"):
        return dict(root.to_dict())
    if isinstance(root, dict):
        return dict(root)
    return None


def _normalize_cmd_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [str(x).strip() for x in val if str(x).strip()]
    s = str(val).strip()
    return [s] if s else []


def merge_ai_tool_private_overrides(base_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    公開メタデータ（名称・説明・key_slug 等）に、``st.secrets["ai_tools_private"][key_slug]`` をマージする。

    Secrets 例（``secrets.toml``）::

        [ai_tools_private.ai03]
        path = "C:/顧客限定/AI鑑定評価書作成_Ver1.0"
        run_cmds = ["streamlit run app.py"]
        setup_cmds = ["pip install -r requirements.txt"]

    未設定のツールは ``private_full_launch_available=False``（フル版起動・コマンド表示は出さない）。
    """
    priv_root = _secrets_ai_tools_private_root()
    out: List[Dict[str, Any]] = []
    for raw in base_projects:
        p = copy.deepcopy(raw)
        slug = str(p.get("key_slug") or "").strip()
        block: Dict[str, Any] | None = None
        if priv_root and slug:
            b = priv_root.get(slug)
            if isinstance(b, dict):
                block = dict(b)
            elif hasattr(b, "to_dict"):
                block = dict(b.to_dict())

        if block:
            path_s = str(block.get("path") or "").strip()
            if path_s:
                p["path"] = Path(path_s)
            rc = block.get("run_cmds")
            if rc is None and block.get("run_cmd"):
                rc = block.get("run_cmd")
            cmds = _normalize_cmd_list(rc)
            if cmds:
                p["run_cmds"] = cmds
            sc = block.get("setup_cmds")
            if sc is None and block.get("setup_cmd"):
                sc = block.get("setup_cmd")
            su = _normalize_cmd_list(sc)
            if su:
                p["setup_cmds"] = su

        path_ok = p.get("path") is not None and str(p.get("path", "")).strip() != ""
        if path_ok:
            path_ok = Path(p["path"]).is_dir()  # type: ignore[arg-type]
        run_ok = bool(p.get("run_cmds"))
        p["private_full_launch_available"] = bool(path_ok and run_ok)

        out.append(p)

    return out
