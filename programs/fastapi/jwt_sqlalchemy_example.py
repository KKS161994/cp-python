from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Annotated
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

# ============= Database Setup =============
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============= SQLAlchemy Models =============
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # In production, use hashed passwords


Base.metadata.create_all(bind=engine)


# ============= Pydantic Models =============
class UserCreate(BaseModel):
    user_id: str
    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    user_id: str
    name: str
    email: str
    
    class Config:
        from_attributes = True


# ============= FastAPI Setup =============
app = FastAPI()
security = HTTPBearer()

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


# ============= Dependency to get DB Session =============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


# ============= JWT Functions =============
def create_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create JWT token"""
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
) -> str:
    """Validate JWT token and return user_id"""
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
    
    return user_id


def load_user_from_db(
    user_id: str = Depends(validate_token),
    db: Session = Depends(get_db),
) -> User:
    """Load user from database"""
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    return user


CurrentUserDep = Annotated[User, Depends(load_user_from_db)]


# ============= Endpoints =============

@app.post("/register")
def register(user_data: UserCreate, db: DbSession):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.user_id == user_data.user_id) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists",
        )
    
    # Create new user
    new_user = User(
        user_id=user_data.user_id,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,  # In production, hash this!
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user": UserResponse.from_orm(new_user)}


@app.post("/login")
def login(user_id: str, password: str, db: DbSession):
    """Login and get JWT token"""
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user or user.password != password:  # In production, use bcrypt!
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )
    
    token = create_token(user.user_id)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/profile")
def get_profile(user: CurrentUserDep):
    """Get current user profile"""
    return {
        "id": user.id,
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
    }


@app.get("/me")
def get_me(user: CurrentUserDep):
    """Get current user info"""
    return {"message": f"Hello {user.name}", "user": UserResponse.from_orm(user)}


@app.get("/users")
def list_all_users(db: DbSession):
    """List all users (public endpoint)"""
    users = db.query(User).all()
    return [UserResponse.from_orm(user) for user in users]
