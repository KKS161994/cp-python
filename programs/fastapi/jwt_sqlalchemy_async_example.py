"""
FastAPI example: JWT authentication + role-based authorization with async SQLAlchemy.

This module demonstrates how to put five common pieces together in one app:
    1. FastAPI              — the web framework that defines HTTP endpoints.
    2. Async SQLAlchemy     — talks to the database without blocking the event loop.
    3. JWT                  — stateless authentication via signed tokens.
    4. Role-based authz     — admin/user roles, with the role embedded in the JWT.
    5. Dependency Injection — FastAPI's `Depends(...)` system to wire things up.

Authentication vs. authorization:
    - **Authentication** (who are you?) → `validate_token` verifies the JWT.
    - **Authorization** (what can you do?) → `require_admin` and inline
      ownership checks gate sensitive endpoints.

Reading order suggested for a beginner:
    - Database setup (engine + session factory + Base)
    - Models (SQLAlchemy `User`, Pydantic `UserCreate` / `UserResponse` / `TokenData`)
    - Middleware (logging + timing every request)
    - JWT helpers (`create_token`, `validate_token`)
    - Authorization (`require_admin`, `RequireAdminDep`, `CurrentTokenDep`)
    - Dependency chain (`get_db` -> `validate_token` -> `load_user_from_db`)
    - Endpoints (`/register`, `/login`, `/profile`, `/users`, ...)

Bootstrapping the first admin:
    `POST /register` always creates a "user". To get an admin you have a few
    options for this demo:
        - Open `test_async.db` with `sqlite3` and run:
              UPDATE users SET role='admin' WHERE user_id='alice';
        - Or temporarily comment out `RequireAdminDep` on
          `PATCH /users/{user_id}/role`, promote one user, then put it back.
    After bootstrapping, admins can promote others via the role endpoint.

Schema note:
    Adding the `role` column changes the schema. Delete `test_async.db`
    before the first run so SQLAlchemy can recreate the `users` table.

Run with:
    uvicorn jwt_sqlalchemy_async_example:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, Integer, select
from sqlalchemy.ext.declarative import declarative_base
from typing import Annotated, AsyncGenerator
import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import asyncio
import time
import logging

# ============= Logging Setup =============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= Database Setup =============
DATABASE_URL = "sqlite+aiosqlite:///./test_async.db"

# create_async_engine() - Creates an ASYNC database connection engine
# The engine manages all database connections and operations
# Think of it as the "connection manager" to your database
engine = create_async_engine(
    DATABASE_URL,           # Connection string: tells where to connect (sqlite file)
    echo=False,             # Set True to print all SQL queries (useful for debugging)
    future=True,            # Use SQLAlchemy 2.0+ behavior (modern syntax)
)

# async_sessionmaker() - Creates a SESSION FACTORY
# This factory creates new database sessions on demand
# Each time you need to query, you get a new session from this factory
# Think of it as a "session vending machine"
AsyncSessionLocal = async_sessionmaker(
    engine,                      # Uses the engine we created above for connections
    class_=AsyncSession,         # Use ASYNC sessions (supports await/async-await)
    expire_on_commit=False,      # Keep objects in memory after commit (don't refresh from DB)
)

# declarative_base() - Creates the BASE CLASS for all ORM models
# All your database models (like User, Post, etc.) inherit from this Base
# The Base tracks all model definitions so SQLAlchemy knows what tables to create
# When you do "Base.metadata.create_all()", it creates tables for all inherited models
Base = declarative_base()


# ============= SQLAlchemy Models =============
class User(Base):
    """ORM model representing a row in the ``users`` table.

    A SQLAlchemy "model" is a Python class that maps to a database table.
    Each class attribute defined with ``Column(...)`` becomes a column.

    Attributes:
        id (int): Auto-incrementing primary key. Database-generated.
        user_id (str): Human-readable unique identifier (e.g. "alice").
            ``unique=True`` enforces uniqueness; ``index=True`` makes lookups fast.
        name (str): User's display name. Not required to be unique.
        email (str): Email address. Unique and indexed for fast lookup.
        password (str): Password. **In production this must be hashed**
            (e.g. with bcrypt/argon2); storing plain text is shown here only
            to keep the example short.

    Example:
        >>> new_user = User(user_id="alice", name="Alice", email="a@b.com", password="x")
        >>> session.add(new_user)
        >>> await session.commit()
    """

    __tablename__ = "users"  # Actual table name created in the database.

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    # Role drives authorization. Defaults to "user"; "admin" gets elevated access.
    # `server_default` adds the default at the SQL level so existing rows backfill.
    role = Column(String, nullable=False, default="user", server_default="user")


# ============= Initialize Database =============
async def init_db() -> None:
    """Create all database tables defined by SQLAlchemy models.

    This walks every class that inherits from ``Base`` (here: just ``User``)
    and issues ``CREATE TABLE IF NOT EXISTS`` for each one. It's safe to call
    on every startup — existing tables are left alone.

    Why ``run_sync``?
        ``Base.metadata.create_all`` is a *synchronous* SQLAlchemy function.
        ``conn.run_sync(...)`` lets us call it safely from async code by
        executing it on a worker thread so it doesn't block the event loop.

    Returns:
        None. The function is awaited purely for its side effect (creating tables).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ============= Pydantic Models =============
class LoginRequest(BaseModel):
    """Schema for the JSON body of ``POST /login``.

    Keeping credentials in the JSON body (not the URL) avoids leaking them
    into server access logs, browser history, and ``Referer`` headers.

    Attributes:
        user_id (str): The user's unique identifier.
        password (str): The user's plain-text password, checked against the
            stored value. (In production this would be checked against a
            hash, not stored plain text.)
    """

    user_id: str
    password: str


class UserCreate(BaseModel):
    """Schema for the JSON body of the ``POST /register`` endpoint.

    Pydantic models describe the *shape* of data. FastAPI uses this class to:
        1. Parse the incoming JSON request body.
        2. Validate that all required fields are present and have the right type.
        3. Return a clear 422 error automatically if validation fails.

    Note:
        Notice this class has no ``password`` hashing — it's just a data
        contract. Hashing happens in the endpoint logic.

    Attributes:
        user_id (str): Unique human-friendly user identifier.
        name (str): Display name.
        email (str): Email address.
        password (str): Plain-text password from the client; should be hashed
            before being stored in production.
    """

    user_id: str
    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    """Schema for user data sent back to clients.

    Deliberately omits sensitive fields like ``password``. FastAPI will
    automatically serialize this model to JSON when an endpoint returns it.

    Attributes:
        id (int): Database primary key.
        user_id (str): Human-friendly unique identifier.
        name (str): Display name.
        email (str): Email address.
        role (str): Authorization role — ``"user"`` or ``"admin"``.
    """

    id: int
    user_id: str
    name: str
    email: str
    role: str

    class Config:
        """Pydantic configuration.

        ``from_attributes = True`` (Pydantic v2) lets us construct a
        ``UserResponse`` directly from a SQLAlchemy ``User`` ORM object, by
        reading attributes rather than dict keys. Without it, Pydantic would
        only accept ``dict``-like inputs.
        """

        from_attributes = True


class TokenResponse(BaseModel):
    """Response shape for ``POST /login``.

    Attributes:
        access_token (str): The signed JWT to send back in
            ``Authorization: Bearer <token>`` headers.
        token_type (str): Always ``"bearer"`` — follows the OAuth2 convention
            so generic clients (Swagger UI, Postman) know how to use it.
    """

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic "the operation succeeded" response.

    Used for endpoints whose only meaningful output is a confirmation string
    (e.g. delete operations).

    Attributes:
        message (str): Human-readable confirmation message.
    """

    message: str


class UserActionResponse(BaseModel):
    """Response wrapper for endpoints that return a message + the user.

    Used by ``/register`` and ``/me`` where we want to echo back both a
    friendly message *and* the user record the action affected.

    Attributes:
        message (str): Human-readable message ("User registered successfully",
            "Hello Alice", ...).
        user (UserResponse): The relevant user record.
    """

    message: str
    user: UserResponse


# ============= FastAPI Setup with Middleware =============
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
]

app = FastAPI(middleware=middleware)
security = HTTPBearer()

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


# ============= Custom Middleware =============
@app.middleware("http")
async def log_and_time_middleware(request: Request, call_next):
    """Log each HTTP request and measure how long it took to handle.

    Middleware is a function that runs *around* every request: it sees the
    request on the way in and the response on the way out. Useful for
    cross-cutting concerns like logging, auth, CORS, metrics, etc.

    Args:
        request: The incoming ``Request`` object (method, URL, headers, ...).
        call_next: A callable that forwards the request to the next middleware
            (or to the actual endpoint) and returns a ``Response``. You must
            ``await`` it.

    Returns:
        The ``Response`` returned by ``call_next``, with two extra headers
        added: ``X-Request-ID`` and ``X-Process-Time``.

    Raises:
        Exception: Re-raises whatever the endpoint raised, after logging it.
    """
    request_id = f"{time.time()}"
    start_time = time.time()
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(
            f"[{request_id}] Completed in {process_time:.4f}s - "
            f"Status: {response.status_code}"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] Error after {process_time:.4f}s: {str(e)}")
        raise


# ============= Startup / Shutdown Events =============
@app.on_event("startup")
async def startup() -> None:
    """Run once when the FastAPI app starts.

    Used here to create database tables before any request arrives.
    The ``@app.on_event("startup")`` decorator registers this function with
    FastAPI; you don't call it yourself.
    """
    logger.info("🚀 Starting up application...")
    await init_db()
    logger.info("✅ Database initialized")


@app.on_event("shutdown")
async def shutdown() -> None:
    """Run once when the FastAPI app is shutting down.

    Disposes the SQLAlchemy engine, which closes the underlying connection
    pool cleanly so the database doesn't see abandoned connections.
    """
    logger.info("🛑 Shutting down application...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


# ============= Dependency to get DB Session with Generator =============
# This is a FastAPI dependency that provides a database session
# Used as: db: DbSession in endpoint functions
# FastAPI automatically injects this dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session to an endpoint, then clean it up.

    This is a FastAPI **dependency**. You declare ``db: AsyncSession = Depends(get_db)``
    in an endpoint, and FastAPI does the following automatically:

        1. Calls this function.
        2. Runs everything up to ``yield session`` (the "setup" phase).
        3. Passes ``session`` into your endpoint as the ``db`` argument.
        4. After your endpoint returns, resumes this function past the ``yield``
           (the "teardown" phase) — commit on success, rollback on error,
           and always close the session.

    Why ``yield`` instead of ``return``?
        A function with ``yield`` is a **generator**. FastAPI uses generator
        dependencies to know where to hand control to the endpoint and where
        to come back for cleanup — much like a context manager.

    Yields:
        AsyncSession: A fresh database session, scoped to a single request.

    Raises:
        Exception: Any exception raised inside the endpoint is re-raised here
            after the session is rolled back, so FastAPI's error handlers can
            still see it.
    """
    # Create new async session from the factory
    async with AsyncSessionLocal() as session:
        try:
            # Log session creation
            logger.debug("📊 Creating new DB session")
            
            # YIELD the session to the endpoint function
            # Execution pauses here until endpoint finishes
            yield session
            
            # After endpoint finishes (if no error), commit changes
            await session.commit()
            logger.debug("✅ DB session committed")
        except Exception as e:
            # If endpoint raised exception, rollback all changes
            await session.rollback()
            logger.error(f"❌ DB session error: {str(e)}")
            raise
        finally:
            # ALWAYS close the session, even if error occurred
            await session.close()
            logger.debug("🔒 DB session closed")


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ============= JWT Functions =============
class TokenData(BaseModel):
    """Decoded contents of a JWT.

    This is the "thin user" representation we pull *out of* the token,
    without touching the database. Useful when you just need to know who
    is calling and what their role is.

    Attributes:
        user_id (str): Unique user identifier (the JWT's ``user_id`` claim).
        role (str): Authorization role ("user" / "admin"), embedded at login.
    """

    user_id: str
    role: str



# Create a digitally signed token that proves user identity
def create_token(
    user_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT (JSON Web Token) for the given user.

    A JWT is just a string of the form ``header.payload.signature``. The
    payload is plain JSON (anyone can read it!) but the signature is
    generated with ``SECRET_KEY``, so the server can detect tampering.

    Embedding ``role`` directly in the token means later requests can be
    authorized without a database lookup — at the cost of staleness:
    role changes do not take effect until the user logs in again.

    Args:
        user_id: Identifier to embed in the token. We'll later read this back
            to know *who* is making a request.
        role: Authorization role ("user" or "admin") embedded as a claim so
            ``validate_token`` can return it without a DB round-trip.
        expires_delta: How long the token should remain valid. If ``None``,
            defaults to 1 hour. The ``| None`` syntax (Python 3.10+) means
            "either a ``timedelta`` or ``None``".

    Returns:
        The encoded JWT as a string, ready to send back to the client. The
        client typically stores it and sends it back in the
        ``Authorization: Bearer <token>`` header on later requests.

    Example:
        >>> token = create_token("alice", "user", expires_delta=timedelta(minutes=15))
    """
    to_encode: dict = {"user_id": user_id, "role": role}

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ]
) -> TokenData:
    """Verify the incoming JWT and return its decoded payload.

    Used as a FastAPI dependency. Any endpoint that does
    ``Depends(validate_token)`` will only run if the request carried a valid
    ``Authorization: Bearer <token>`` header.

    The ``Annotated[...]`` type hint is how you attach metadata to a parameter
    type in modern Python (3.9+). Here it says: "this parameter is an
    ``HTTPAuthorizationCredentials`` object, and FastAPI should obtain it by
    calling ``Depends(security)``" — that's how ``security = HTTPBearer()``
    plugs into this function.

    Args:
        credentials: Automatically supplied by FastAPI. ``credentials.credentials``
            is the raw token string from the ``Authorization`` header.

    Returns:
        A ``TokenData`` carrying both ``user_id`` and ``role`` (the role is
        embedded at login, so authorization checks don't need a DB lookup).

    Raises:
        HTTPException: 401 if the token is missing required claims, has
            expired, or fails signature verification.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("user_id")
        role: str | None = payload.get("role")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user_id",
            )
        if role is None:
            # Older tokens issued before the role claim existed will hit this.
            # Force the user to log in again to mint a token with a role.
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing role (please log in again)",
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

    return TokenData(user_id=user_id, role=role)


async def load_user_from_db(
    token: TokenData = Depends(validate_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Look up the authenticated user in the database.

    This dependency chains two other dependencies, which is what makes
    FastAPI's DI system so powerful:

        HTTPBearer (security)
              ↓ produces credentials
        validate_token(credentials)
              ↓ produces TokenData (user_id + role)
        load_user_from_db(token, db)
              ↓ produces User
        <your endpoint>(user: User)

    Any endpoint that asks for ``CurrentUserDep`` triggers this whole chain.
    Use ``CurrentUserDep`` when you need the *full* user row (e.g. email,
    DB id). Use ``CurrentTokenDep`` when you only need ``user_id`` / ``role``
    and want to skip the database round-trip.

    Args:
        token: Provided by ``validate_token`` after it verifies the JWT.
        db: Provided by ``get_db`` — an async SQLAlchemy session.

    Returns:
        The ``User`` ORM object loaded from the database.

    Raises:
        HTTPException: 404 if no matching user row exists. (A valid token
            whose user has since been deleted will hit this case.)
    """
    result = await db.execute(
        select(User).where(User.user_id == token.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


# Type alias for authenticated user dependency
# Automatically validates JWT and loads user from DB
CurrentUserDep = Annotated[User, Depends(load_user_from_db)]
# Lightweight version: just the decoded token payload (no DB hit).
CurrentTokenDep = Annotated[TokenData, Depends(validate_token)]


# ============= Authorization =============
def require_admin(token: TokenData = Depends(validate_token)) -> TokenData:
    """Dependency that allows the request through only for admin users.

    Authorization (what you're allowed to do) sits *on top of* authentication
    (proving who you are). This dependency first reuses ``validate_token`` to
    confirm the request carries a valid JWT, then inspects the embedded role
    claim. Non-admins are rejected with HTTP 403 (Forbidden) — note the
    distinction from 401 (Unauthorized), which means "I don't know who you
    are." Here we *do* know who you are; you just don't have permission.

    Args:
        token: Decoded JWT payload, supplied by ``validate_token``.

    Returns:
        The same ``TokenData``, so admin endpoints can still see ``user_id``
        (e.g. for audit logging).

    Raises:
        HTTPException: 403 if the caller's role isn't ``"admin"``.
    """
    if token.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required",
        )
    return token


# Type alias: declare `actor: RequireAdminDep` in an endpoint to gate it
# behind the admin check.
RequireAdminDep = Annotated[TokenData, Depends(require_admin)]


# ============= Endpoints =============

@app.post("/register")
async def register(user_data: UserCreate, db: DbSession) -> UserActionResponse:
    """Create a new user account.

    Steps:
        1. Reject the request if a user with the same ``user_id`` or ``email``
           already exists.
        2. Create a new ``User`` row and commit it.
        3. Return a clean ``UserResponse`` (password is *not* echoed back).

    Args:
        user_data: Parsed and validated JSON body (FastAPI builds this from
            the incoming request using the ``UserCreate`` schema).
        db: Async SQLAlchemy session injected by ``get_db``.

    Returns:
        dict: ``{"message": str, "user": UserResponse}``.

    Raises:
        HTTPException: 400 if a user with the same ``user_id`` or ``email``
            is already registered.
    """
    # Check if user already exists (user_id OR email must be unique)
    result = await db.execute(
        select(User).where(
            (User.user_id == user_data.user_id) | (User.email == user_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists",
        )
    
    # Simulate async I/O operation (e.g., sending email verification)
    await asyncio.sleep(0.1)
    
    # Create new User instance (not saved to DB yet)
    new_user = User(
        user_id=user_data.user_id,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,  # TODO: Hash this in production!
    )
    
    # Save to database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserActionResponse(
        message="User registered successfully",
        user=UserResponse.model_validate(new_user),
    )


@app.post("/login")
async def login(credentials: LoginRequest, db: DbSession) -> TokenResponse:
    """Authenticate a user and return a JWT.

    Credentials are read from the **JSON request body** — FastAPI knows to do
    this because ``credentials`` is typed as a Pydantic model (``LoginRequest``).
    Any non-Pydantic, non-``Depends`` parameter would instead be taken from
    the query string, which is why we wrap them in a model.

    Example request:
        ``POST /login`` with body ``{"user_id": "alice", "password": "secret"}``.

    Args:
        credentials: Parsed and validated JSON body containing ``user_id`` and
            ``password``.
        db: Async SQLAlchemy session injected by ``get_db``.

    Returns:
        TokenResponse: A bearer JWT. The client should send the token back on
        subsequent requests via ``Authorization: Bearer <access_token>``.

    Raises:
        HTTPException: 401 if the user doesn't exist or the password is wrong.
    """
    # Query database for user with this user_id
    result = await db.execute(
        select(User).where(User.user_id == credentials.user_id)
    )
    user = result.scalar_one_or_none()

    # Verify password is correct
    if not user or user.password != credentials.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )
    
    # Simulate async I/O (e.g., logging, audit trail)
    await asyncio.sleep(0.05)
    
    # Generate JWT token for this user (embed role for authorization).
    token = create_token(user.user_id, user.role)
    return TokenResponse(access_token=token)


@app.get("/profile")
async def get_profile(user: CurrentUserDep) -> UserResponse:
    """Return the profile of the currently authenticated user.

    Requires a valid JWT. The ``user`` parameter is automatically populated
    by the ``CurrentUserDep`` dependency chain (JWT → user_id → User row).

    The ``-> UserResponse`` annotation tells FastAPI to coerce whatever we
    return into a ``UserResponse`` before serializing. Because ``UserResponse``
    has ``from_attributes = True``, returning the SQLAlchemy ``User`` ORM
    object directly works — Pydantic reads its attributes.

    Args:
        user: The authenticated ``User`` ORM object.

    Returns:
        UserResponse: Filtered, JSON-safe view of the user.
    """
    # Simulate async work
    await asyncio.sleep(0.05)

    return user  # FastAPI converts to UserResponse via the return annotation.


@app.get("/me")
async def get_me(user: CurrentUserDep) -> UserActionResponse:
    """Return a friendly greeting plus the current user's data.

    Args:
        user: The authenticated ``User`` (injected by ``CurrentUserDep``).

    Returns:
        UserActionResponse: Message + the user record.
    """
    await asyncio.sleep(0.05)

    return UserActionResponse(
        message=f"Hello {user.name}",
        user=UserResponse.model_validate(user),
    )


@app.get("/users")
async def list_all_users(
    actor: RequireAdminDep, db: DbSession
) -> list[UserResponse]:
    """List every user in the database (admin only).

    Protected by the ``RequireAdminDep`` dependency — any non-admin caller
    is rejected with HTTP 403 before this function body runs.

    Args:
        actor: The admin caller's decoded token (unused here, but commonly
            passed to audit logging).
        db: Async SQLAlchemy session injected by ``get_db``.

    Returns:
        list[UserResponse]: One entry per user. Passwords are not included.
    """
    result = await db.execute(select(User))
    users = result.scalars().all()

    return [UserResponse.model_validate(user) for user in users]


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str, actor: CurrentTokenDep, db: DbSession
) -> MessageResponse:
    """Delete a user by their ``user_id``.

    Authorization rule: the caller must be either
        - an **admin** (can delete anyone), or
        - the **owner** of the account (``actor.user_id == user_id``).

    The ``{user_id}`` segment in the route is a **path parameter** — FastAPI
    matches it from the URL (e.g. ``DELETE /users/alice``) and passes it in
    as the ``user_id`` function argument.

    Args:
        user_id: The unique identifier of the user to delete (from the URL).
        actor: The caller's decoded JWT (token payload only — no DB lookup).
        db: Async SQLAlchemy session injected by ``get_db``.

    Returns:
        dict: ``{"message": "User deleted successfully"}``.

    Raises:
        HTTPException: 403 if the caller is neither an admin nor the owner.
        HTTPException: 404 if no user with that ``user_id`` exists.
    """
    if actor.role != "admin" and actor.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own account",
        )

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    await db.delete(user)
    await db.commit()

    return MessageResponse(message="User deleted successfully")


class RoleChange(BaseModel):
    """Body schema for ``PATCH /users/{user_id}/role``.

    Attributes:
        role (str): New role to assign. Must be ``"user"`` or ``"admin"``.
    """

    role: str


@app.patch("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    body: RoleChange,
    actor: RequireAdminDep,
    db: DbSession,
) -> UserResponse:
    """Promote or demote a user (admin only).

    Authorization rule: only admins may change roles (``RequireAdminDep``).
    Extra guard: admins cannot demote themselves — useful safety rail so the
    last admin can't accidentally lock everyone out.

    Note:
        Because the role is embedded in the JWT, the affected user keeps
        their old role *until they log in again*. This is the staleness
        tradeoff of putting claims in the token instead of reading them
        from the DB on every request.

    Args:
        user_id: The target user's identifier (from the URL).
        body: JSON body with the new ``role``.
        actor: The admin caller's decoded token (injected).
        db: Async SQLAlchemy session injected by ``get_db``.

    Returns:
        UserResponse: The updated user record.

    Raises:
        HTTPException: 400 if ``role`` isn't a recognised value.
        HTTPException: 403 if an admin tries to demote themselves.
        HTTPException: 404 if the target user doesn't exist.
    """
    if body.role not in {"user", "admin"}:
        raise HTTPException(
            status_code=400,
            detail="role must be 'user' or 'admin'",
        )

    if actor.user_id == user_id and body.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admins cannot demote themselves",
        )

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    user.role = body.role
    await db.commit()
    await db.refresh(user)

    return user  # Coerced to UserResponse by the return annotation.
