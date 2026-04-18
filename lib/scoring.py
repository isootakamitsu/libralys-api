from datetime import datetime
from math import exp
from sqlalchemy.orm import Session
from .models import ScoreEvent

SCORE_WEIGHTS = {
    "deal": +8,
    "cancel_pre": -6,
    "cancel_post": -16,
    "cancel_after_delivery": -22,
    "refund": -12,
    "no_pay": -30,
    "good_response": +2,
    "late_response": -3,
}
HALF_LIFE_DAYS = 180
LAMBDA = 0.693 / HALF_LIFE_DAYS

def add_score(db: Session, actor_type: str, actor_id: int, event_type: str):
    pts = SCORE_WEIGHTS.get(event_type, 0)
    db.add(ScoreEvent(actor_type=actor_type, actor_id=actor_id, event_type=event_type, points=pts))
    db.commit()

def calc_score(db: Session, actor_type: str, actor_id: int):
    base = 60.0
    now = datetime.utcnow()
    rows = db.query(ScoreEvent).filter_by(actor_type=actor_type, actor_id=actor_id).all()
    score = base
    for r in rows:
        age = (now - r.created_at).days
        w = exp(-LAMBDA * age)
        score += r.points * w
    score = max(0.0, min(100.0, score))
    label = "A" if score >= 80 else "B" if score >= 60 else "C"
    return round(score, 1), label