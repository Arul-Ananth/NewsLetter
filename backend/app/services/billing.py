import os  # <--- Import OS to check environment variables
from fastapi import HTTPException
from sqlmodel import Session
from app.models.sql import UserWallet, UsageLog


def check_funds(session: Session, user_id: int):
    # --- SKIP FOR DESKTOP APP ---
    if os.environ.get("APP_MODE") == "desktop":
        return None  # Return None means "Allowed" in this context
    # ----------------------------

    wallet = session.get(UserWallet, user_id)
    if not wallet or wallet.balance <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits. Please top up.")
    return wallet


def process_transaction(session: Session, user_id: int, topic: str, input_tok: int, output_tok: int):
    # --- SKIP FOR DESKTOP APP ---
    if os.environ.get("APP_MODE") == "desktop":
        return {"deducted": 0, "remaining": "Unlimited"}
    # ----------------------------

    # Pricing Strategy: Output is 3x more expensive
    cost = input_tok + (output_tok * 3)

    # Update Wallet
    wallet = session.get(UserWallet, user_id)
    if wallet:
        wallet.balance -= cost
        session.add(wallet)

    # Log Transaction
    log = UsageLog(
        user_id=user_id,
        topic=topic,
        input_tokens=input_tok,
        output_tokens=output_tok,
        total_cost=cost
    )

    session.add(log)
    session.commit()

    remaining = wallet.balance if wallet else 0
    return {"deducted": cost, "remaining": remaining}