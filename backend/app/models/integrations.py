from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.auth import Base, generate_uuid


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)  # facebook, instagram, whatsapp, google_sheets, ai_voice
    status: Mapped[str] = mapped_column(String(20), default="not_connected")  # not_connected, connected, error
    external_account_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
