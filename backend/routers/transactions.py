from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.deps import get_current_user
from backend.models.user import User
from backend.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionOut
from backend.services.transaction_service import (
    create_transaction,
    list_transactions,
    get_transaction,
    update_transaction,
    delete_transaction,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_transaction(db, current_user.id, data)


@router.get("/", response_model=List[TransactionOut])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_transactions(db, current_user.id)


@router.get("/{txn_id}", response_model=TransactionOut)
def get_one(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = get_transaction(db, current_user.id, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.put("/{txn_id}", response_model=TransactionOut)
def update(
    txn_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = update_transaction(db, current_user.id, txn_id, data)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not delete_transaction(db, current_user.id, txn_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
