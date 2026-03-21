from fastapi import HTTPException
from sqlmodel import Session

from backend.common.config import AppMode, AuthMode, settings
from backend.common.models.sql import UsageLog, UserWallet


def check_funds(session: Session, user_id: int):
    if settings.APP_MODE == AppMode.DESKTOP or settings.auth_mode() == AuthMode.TRUSTED_LAN:
        return None

    wallet = session.get(UserWallet, user_id)
    if not wallet or wallet.balance <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits. Please top up.")
    return wallet


def process_transaction(session: Session, user_id: int, topic: str, input_tok: int, output_tok: int):
    if settings.APP_MODE == AppMode.DESKTOP or settings.auth_mode() == AuthMode.TRUSTED_LAN:
        return {"deducted": 0, "remaining": "Unlimited"}

    cost = input_tok + (output_tok * 3)

    wallet = session.get(UserWallet, user_id)
    if wallet:
        wallet.balance -= cost
        session.add(wallet)

    log = UsageLog(
        user_id=user_id,
        topic=topic,
        input_tokens=input_tok,
        output_tokens=output_tok,
        total_cost=cost,
    )

    session.add(log)
    session.commit()

    remaining = wallet.balance if wallet else 0
    return {"deducted": cost, "remaining": remaining}
