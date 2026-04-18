from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default="user")  # user / appraiser / admin
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    agreed_tos: Mapped[bool] = mapped_column(Boolean, default=False)
    agreed_privacy: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AppraiserProfile(Base):
    __tablename__ = "appraiser_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    area: Mapped[str] = mapped_column(String(120))
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    bio: Mapped[str] = mapped_column(Text, default="")
    is_accepting: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Request(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    property_type: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(200))
    details: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Proposal(Base):
    __tablename__ = "proposals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    appraiser_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    fee_yen: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="offered")  # offered/accepted/rejected/withdrawn
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount_yen: Mapped[int] = mapped_column(Integer)
    stripe_session_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_payment_intent: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(30), default="created")  # created/paid/failed/refunded
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ScoreEvent(Base):
    __tablename__ = "score_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(20))  # user/appraiser
    actor_id: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(50))
    points: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(200))
    meta: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ConsentLog(Base):
    __tablename__ = "consent_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    consent_type: Mapped[str] = mapped_column(String(30))  # tos/privacy
    version: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)