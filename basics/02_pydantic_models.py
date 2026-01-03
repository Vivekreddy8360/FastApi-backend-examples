from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field

app=FastAPI()

class User(BaseModel):
    name:str = Field(..., min_length=3,max_length=20)
    phone:int
    email:str

user_details={}

count_id=1

@app.post('/create')

def create_user(user:User):
    global count_id
    user_details[count_id]=user
    response={
        "message": "User Successfully Created",
        "user_id":count_id,
        "user":user_details[count_id]
    }
    count_id+=1
    return response

@app.get('/users')
def get_users():
    if not user_details:
        raise HTTPException(status_code=404,detail="No Users Found")
    return user_details

@app.get('/user/{user_id}')

def get_single_user(user_id:int):
    if user_id not in user_details:
        raise HTTPException(status_code=404, detail="User Not Found")
    return user_details[user_id]

@app.put('/user/{user_id}')

def update_user(user_id:int,user:User):
    if user_id not in user_details:
        raise HTTPException(status_code=404,detail="User Not Found")
    user_details[user_id]=user

    return {"message": "user updated","user":user}


@app.delete('/user/{user_id}')

def delete_user(user_id:int):
    if user_id not in user_details:
        raise HTTPException(status_code=404,detail="User Not Found")
    delete=user_details.pop(user_id)
    return {"message": "User Deleted","user":delete}