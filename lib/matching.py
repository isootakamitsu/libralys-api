from sqlalchemy.orm import Session
from .models import AppraiserProfile, User

def recommend_appraisers(db: Session, location_text: str, limit: int = 10):
    # 超簡易：住所文字列に area が含まれる鑑定士を優先、受託中(is_accepting)のみ
    all_profiles = db.query(AppraiserProfile).filter_by(is_accepting=True).all()
    scored = []
    for p in all_profiles:
        score = 0
        if p.area and p.area in (location_text or ""):
            score += 10
        score += min(10, p.experience_years // 3)  # 経験を少し加点
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]