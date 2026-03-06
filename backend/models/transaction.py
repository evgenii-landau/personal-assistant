from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB", nullable=False)
    amount_rub = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, default="")
    type = Column(String(10), nullable=False)  # "income" or "expense"
    account = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
