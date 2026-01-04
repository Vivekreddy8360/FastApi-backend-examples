from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, create_engine, Session, select
from contextlib import asynccontextmanager
from typing import Annotated
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from .models import User, CreateUser, Token, UserResponse

# ------------------ DATABASE ------------------
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, echo=True)

# ------------------ LIFESPAN ------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

# ------------------ APP ------------------
app = FastAPI(lifespan=lifespan)

# ------------------ STATIC FILES (IMAGES) ------------------
# ONE-TIME CONFIGURATION
app.mount("/images", StaticFiles(directory="images"), name="images")

# ------------------ DB SESSION ------------------
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# ------------------ AUTH / JWT ------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expire_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expire_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep
):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = session.exec(
        select(User).where(User.email == email)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# ------------------ PASSWORD ------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ------------------ REGISTER ------------------
@app.post("/register")
def register(session: SessionDep, user_data: CreateUser):
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

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

# ------------------ LOGIN ------------------
@app.post("/login", response_model=Token)
def login(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ------------------ PROFILE ------------------
@app.get("/profile", response_model=UserResponse)
def profile(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
