from datetime import datetime
from sqlalchemy.orm import Session
from .models import AuditLog

def audit(db: Session, actor_user_id: int, action: str, meta: str = ""):
    db.add(AuditLog(actor_user_id=actor_user_id, action=action, meta=meta))
    db.commit()