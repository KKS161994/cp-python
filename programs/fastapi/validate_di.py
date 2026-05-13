from fastapi import FastAPI, Depends

app = FastAPI()
class Database: 
    def get_user(self, user_id:int):
        return {"id": user_id, "name":"shubham"}
    
def get_db():
    return Database()

@app.get("/users/{user_id}")
async def read_user(user_id: int, db:Database = Depends(get_db)):
    return db.get_user(user_id)



    
