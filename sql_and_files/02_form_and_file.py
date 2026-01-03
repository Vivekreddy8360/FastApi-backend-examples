from fastapi import FastAPI,Depends , HTTPException , Form,UploadFile ,File

from sqlmodel import SQLModel,create_engine,Session , select
from contextlib import asynccontextmanager
from typing import Annotated
from models import User, CreateUser
import os
import os, shutil
#from fastapi import 

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

UPLOADS_DIRS = "uploads"
os.makedirs(UPLOADS_DIRS,exist_ok=True)

@app.post("/createuser")

def usercreate(
    session:SessionDep,
    name:str=Form(...),
    phone:int=Form(...),
    email:str=Form(),
    file:UploadFile=File(...)
    ):


    user_data={"name":name,"phone":phone,"email":email}
    validated=CreateUser.model_validate(user_data)

    file_path= os.path.join(UPLOADS_DIRS,file.filename)
    with open(file_path,"wb") as f:
        shutil.copyfileobj(file.file,f)

    user=User(**validated.model_dump(),file_path=f"{UPLOADS_DIRS}/{file.filename}")
    session.add(user)
    session.commit()
    session.refresh(user)

    return user

