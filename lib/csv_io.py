"""CSV 読み込み（日本語環境向け: UTF-8 優先、Shift_JIS / CP932 フォールバック）。"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

import pandas as pd

# UTF-8 系 → Windows 系 → 旧来の日本語 CSV（euc-jp / JIS）まで順に試す
DEFAULT_JP_ENCODINGS: tuple[str, ...] = (
    "utf-8-sig",
    "utf-8",
    "cp932",
    "shift_jis",
    "euc_jp",
    "iso2022_jp",
)


def read_csv_japanese(path: Union[str, Path], **kwargs: Any) -> pd.DataFrame:
    """ローカルパスの CSV を複数 encoding で順に試行する。"""
    p = Path(path)
    last_err: Optional[UnicodeDecodeError] = None
    for enc in DEFAULT_JP_ENCODINGS:
        try:
            return pd.read_csv(p, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            last_err = e
    raise UnicodeDecodeError(
        "utf-8", b"", 0, 1, f"CSV を判別できませんでした（試行: {DEFAULT_JP_ENCODINGS}）"
    ) from last_err


def read_csv_japanese_from_fileobj(fileobj: BinaryIO, **kwargs: Any) -> pd.DataFrame:
    """アップロード済みファイルオブジェクト用。"""
    pos = fileobj.tell()
    try:
        raw = fileobj.read()
    finally:
        fileobj.seek(pos)
    return read_csv_japanese_from_bytes(raw, **kwargs)


def read_csv_japanese_from_bytes(data: bytes, **kwargs: Any) -> pd.DataFrame:
    """バイト列から CSV を読む（アップロード CSV 向け）。"""
    last_err: Optional[UnicodeDecodeError] = None
    for enc in DEFAULT_JP_ENCODINGS:
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            last_err = e
    raise UnicodeDecodeError(
        "utf-8", b"", 0, 1, f"CSV を判別できませんでした（試行: {DEFAULT_JP_ENCODINGS}）"
    ) from last_err
