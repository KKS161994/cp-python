from fastapi import Depends, FastAPI, HTTPException, Header

app = FastAPI()

def get_current_user(authorization: str | None = Header(default=None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing token")
    if authorization != "Bearer valid-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": "u_123"}

@app.get("/profile")
def get_profile(user=Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "name": "Shubham"
    }