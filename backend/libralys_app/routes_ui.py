# ============================================================
# UI Routes（将来の /api/ui/* をここへ）
# GET /api/ui/top は backend/main.py の get_ui_top に統一
# ============================================================

from fastapi import APIRouter

router = APIRouter(prefix="/api/ui", tags=["ui"])
