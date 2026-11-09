from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.orm import User, RevokedToken
from utils.jwt import verify_token
from test_jwt import payload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Cannot validate credential", headers={"WWW-Authenticate": "Bearer"})

    payload = verify_token(token)

    if payload.get("type") != "access":
        raise credential_exception

    jti = payload.get("jti")

    revoked_token = db.query(RevokedToken).filter(
        RevokedToken.jti == jti
    ).first()

    if revoked_token:
        raise credential_exception

    user_id = payload.get("sub")

    if not user_id or not user_id.isdigit():
        raise credential_exception

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user or not user.is_active:
        raise credential_exception

    return user


def require_roles(*allowed_roles):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You do not have permission to access this resource")
        return current_user
    return role_checker
