from fastapi import FastAPI,Depends , HTTPException
from sqlmodel import SQLModel,create_engine,Session , select
from contextlib import asynccontextmanager
from typing import Annotated
from models import User, CreateUser

DATABASE_URL = "sqlite:///./user.db"
engine= create_engine(DATABASE_URL,echo=True)

@asynccontextmanager
async def lifespan(app:FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app=FastAPI(lifespan=lifespan)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep= Annotated[Session,Depends(get_session)]


@app.post('/createuser')

def create_user(user:CreateUser,session:SessionDep):
    new_user=User.model_validate(user)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.get('/users',response_model=list[User])

def get_users(session:SessionDep):
    users=session.exec(select(User)).all()
    if not users:
        raise HTTPException(status_code=404,detail="User not found")
    
    return users


@app.get('/users/{user_id}',response_model=User)

def get_single_user(user_id:int,session:SessionDep):
    user=session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404,detail="User Not Found")
    return user


@app.put('/users/{user_id}',response_model=User)

def update_user(user_id:int,update:CreateUser,session:SessionDep):
    user = session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404,detail="User Not Found")
    
    user.name=update.name
    user.phone=update.phone
    user.email=update.email

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.delete('/users/{user_id}')

def delete_user(user_id:int,session:SessionDep):
    user=session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404,detail="User Not Found")
    session.delete(user)
    session.commit()
    return {"message":"user deleted Successfully"}