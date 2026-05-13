from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
import jwt
from datetime import datetime, timedelta

app = FastAPI()
security = HTTPBearer()

# Secret key for JWT encoding/decoding
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


def create_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT token for a user"""
    to_encode = {"user_id": user_id}
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ]
) -> dict:
    """Validate JWT token and extract user data"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user_id",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )
    
    return {"user_id": user_id}


def load_user(user_data: Annotated[dict, Depends(validate_token)]) -> dict:
    """Load user details from user_id in token"""
    user_id = user_data["user_id"]
    
    # Mock user database
    users = {
        "user_123": {"user_id": "user_123", "name": "Shubham", "email": "shubham@example.com"},
        "user_456": {"user_id": "user_456", "name": "John", "email": "john@example.com"},
    }
    
    user = users.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    return user


CurrentUserDep = Annotated[dict, Depends(load_user)]


# Endpoint to generate token (for testing)
@app.post("/login")
def login(user_id: str):
    """Generate a JWT token"""
    token = create_token(user_id)
    return {"access_token": token, "token_type": "bearer"}


# Protected endpoint that returns user profile
@app.get("/profile")
def get_profile(user: CurrentUserDep):
    """Get user profile using JWT token"""
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
    }


# Another protected endpoint
@app.get("/me")
def get_current_user_info(user: CurrentUserDep):
    """Get current user info"""
    return {"message": f"Hello {user['name']}", "user": user}
