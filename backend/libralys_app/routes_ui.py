# ============================================================
# UI Routes
# ============================================================

from fastapi import APIRouter, Query
from .ui_build import build_ui_top

router = APIRouter(prefix="/api/ui", tags=["ui"])

@router.get("/top")
def ui_top(lang: str = Query("ja")):
    return build_ui_top(lang)
