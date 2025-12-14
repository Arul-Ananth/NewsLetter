import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session
from app.database import get_session
from app.config import settings
from app.models.sql import User

# auto_error=False allows the request to proceed even if the token is missing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    # --- DESKTOP MODE BYPASS ---
    if os.environ.get("APP_MODE") == "desktop":
        # Return a dummy "Desktop User" if (1) no token, or (2) token invalid/ignored
        # We generally trust the local user in this mode.
        return User(id=0, email="user@desktop.local", full_name="Desktop User", hashed_password="")
    # ---------------------------

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user