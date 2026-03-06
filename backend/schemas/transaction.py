from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    amount: float
    currency: str = "RUB"
    category: str
    description: str = ""
    type: str  # "income" or "expense"
    account: str = ""


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    account: Optional[str] = None


class TransactionOut(BaseModel):
    id: int
    user_id: int
    amount: float
    currency: str
    amount_rub: float
    category: str
    description: str
    type: str
    account: str
    created_at: datetime

    model_config = {"from_attributes": True}
