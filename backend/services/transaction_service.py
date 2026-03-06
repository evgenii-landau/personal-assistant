from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.transaction import Transaction
from backend.schemas.transaction import TransactionCreate, TransactionUpdate


def create_transaction(db: Session, user_id: int, data: TransactionCreate) -> Transaction:
    txn = Transaction(
        user_id=user_id,
        amount=data.amount,
        currency=data.currency,
        amount_rub=data.amount,  # caller responsible for conversion before posting
        category=data.category,
        description=data.description,
        type=data.type,
        account=data.account,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def list_transactions(db: Session, user_id: int) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_transaction(db: Session, user_id: int, txn_id: int) -> Optional[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.id == txn_id, Transaction.user_id == user_id)
        .first()
    )


def update_transaction(
    db: Session, user_id: int, txn_id: int, data: TransactionUpdate
) -> Optional[Transaction]:
    txn = get_transaction(db, user_id, txn_id)
    if not txn:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(db: Session, user_id: int, txn_id: int) -> bool:
    txn = get_transaction(db, user_id, txn_id)
    if not txn:
        return False
    db.delete(txn)
    db.commit()
    return True


def get_dashboard(db: Session, user_id: int) -> dict:
    """Return aggregate analytics for the authenticated user.

    balance         — sum of all-time amount_rub (income positive, expense negative)
    monthly_income  — sum of income transactions in the current calendar month
    monthly_expenses — sum of expense transactions in the current calendar month
    transaction_count — number of transactions in the current calendar month
    """
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # All-time balance: income adds, expense subtracts
    balance_row = (
        db.query(
            func.coalesce(
                func.sum(
                    func.case(
                        (Transaction.type == "income", Transaction.amount_rub),
                        else_=-Transaction.amount_rub,
                    )
                ),
                0.0,
            )
        )
        .filter(Transaction.user_id == user_id)
        .one()
    )

    # Current-month income
    income_row = (
        db.query(func.coalesce(func.sum(Transaction.amount_rub), 0.0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.created_at >= month_start,
        )
        .one()
    )

    # Current-month expenses
    expense_row = (
        db.query(func.coalesce(func.sum(Transaction.amount_rub), 0.0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.created_at >= month_start,
        )
        .one()
    )

    # Current-month transaction count
    count_row = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= month_start,
        )
        .one()
    )

    return {
        "balance": round(balance_row[0], 2),
        "monthly_income": round(income_row[0], 2),
        "monthly_expenses": round(expense_row[0], 2),
        "transaction_count": count_row[0],
    }
