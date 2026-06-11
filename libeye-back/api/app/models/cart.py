from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class CartSession(Base):
    __tablename__ = "cart_sessions"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="PENDING")  # PENDING, PROCESSING, SUCCESS, FAILED
    image_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("CartItem", back_populates="session", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("cart_sessions.id", ondelete="CASCADE"))
    title = Column(String, nullable=True)
    call_number = Column(String, nullable=False)
    shelf_location = Column(String, nullable=True)
    display_order = Column(Integer, nullable=False)  # 사서가 서가에 꽂아야 할 최적의 순서

    session = relationship("CartSession", back_populates="items")
