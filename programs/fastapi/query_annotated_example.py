from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

app = FastAPI()
security = HTTPBearer()


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ]
):
    token = credentials.credentials

    if token != "valid-token":
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    return {
        "user_id": "u_123"
    }


CurrentUserDep = Annotated[
    dict,
    Depends(get_current_user),
]


# ✅ RECOMMENDED (Annotated for everything)
@app.get("/items/")
def get_items(
    skip: Annotated[int, Query(0)],
    limit: Annotated[int, Query(10)],
    user: CurrentUserDep,
):
    return {
        "skip": skip,
        "limit": limit,
        "user": user,
    }


# ⚠️ MIXED (Annotated only for complex stuff) - Less consistent
@app.get("/items-mixed/")
def get_items_mixed(
    user: CurrentUserDep,  # Annotated - required, must come first
    skip: int = Query(0),
    limit: int = Query(10),
):
    return {
        "skip": skip,
        "limit": limit,
        "user": user,
    }
