from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from backend.server.database import get_session
from backend.server.models.sql import User, UserWallet
from backend.server.models.schemas import UserSignup, UserLogin, Token
from backend.server.services.auth_utils import get_password_hash, verify_password, create_access_token

router = APIRouter(tags=["Auth"])

@router.post("/signup", status_code=201)
def signup(user_data: UserSignup, session: Session = Depends(get_session)):
    # 1. Check existing
    statement = select(User).where(User.email == user_data.email)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Email exists")
    
    # 2. Create User
    new_user = User(
        email=user_data.email, 
        full_name=user_data.full_name, 
        hashed_password=get_password_hash(user_data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # 3. Create Wallet (Free Credits)
    wallet = UserWallet(user_id=new_user.id, balance=50)
    session.add(wallet)
    session.commit()
    
    return {"message": "User created", "user_id": new_user.id}

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user_data.email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}