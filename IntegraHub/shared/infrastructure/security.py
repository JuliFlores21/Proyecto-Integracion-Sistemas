import jwt
from fastapi import HTTPException, Header, status
import os

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"

def verify_token(authorization: str = Header(...)):
    """
    Validates JWT token from Authorization header.
    Returns the payload if valid.
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
