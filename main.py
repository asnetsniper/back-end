# main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.middleware.cors import CORSMiddleware
from models import User  # 从 models.py 中导入 Item 模型

# MySQL数据库连接配置
DATABASE_URL = "mysql+mysqlconnector://root:sonny123@localhost:3306/test"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Pydantic模型
class UserCreate(BaseModel):
    name: str
    email: str
    @validator('email')
    def check_email(cls, v):
        if '@' not in v:
            raise ValueError('Email must contain @ symbol')
        return v
class UserRead(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

# 创建表
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可根据需要指定允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 路由
@app.post("/api/users/", response_model=UserRead)
def create_user(user: UserCreate, db=Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists or invalid data")
    return db_user

@app.get("/api/users/", response_model=List[UserRead])
def read_users(skip: int = 0, limit: int = 10, db=Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users
class UserIdRequest(BaseModel):
    user_id: int

@app.post("/api/users/get_by_id/", response_model=UserRead)
def get_user_by_id(request: UserIdRequest, db=Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
    