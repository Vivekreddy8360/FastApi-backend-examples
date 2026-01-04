from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, create_engine, Session, select
from contextlib import asynccontextmanager
from typing import Annotated
from passlib.context import CryptContext

from .models import User, CreateUser ,LoginUser  # make sure class names are correct

DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, echo=True)

# ------------------ LIFESPAN ------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

# ------------------ DB SESSION ------------------
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# ------------------ AUTH ------------------
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"   # ✅ fixed spelling
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ------------------ REGISTER ------------------
@app.post("/register")
def register(
    session: SessionDep,
    user_data: CreateUser
):
    # check if user already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


@app.post("/login")
def login(session: SessionDep, login_user: LoginUser):
    user = session.exec(
        select(User).where(User.email == login_user.email)
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    if not verify_password(login_user.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    return user

