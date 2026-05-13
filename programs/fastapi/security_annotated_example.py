from fastapi import FastAPI, Depends, HTTPException
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


@app.get("/profile")
def get_profile(
    user: CurrentUserDep,
):
    return {
        "user_id": user["user_id"],
        "name": "Shubham",
    }
