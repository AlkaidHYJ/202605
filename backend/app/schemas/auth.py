from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: str | None = None
    dept_id: int | None = None
    is_admin: int = 0


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    real_name: str | None = None
    dept_id: int | None = None
    status: int | None = None
    is_admin: int | None = None


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str | None
    dept_id: int | None
    status: int
    is_admin: int

    class Config:
        from_attributes = True
