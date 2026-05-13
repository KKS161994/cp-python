from fastapi import FastAPI,Depends,Header,HTTPException

app = FastAPI()

def get_current_user(
        authorisation: str|None = Header(default= None)
):
    if authorisation is None:
        raise HTTPException(
            status_code=401
            detail= "Missing authorisation details"
            )
    return {"token":authorisation}


@app.get("/profile")
def get_profile(user = Depends(get_current_user)):
    return user
    
