from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.models.system import SysUser
from app.schemas.auth import LoginRequest, UserCreate, UserOut
from app.schemas.common import ResponseModel, TokenResponse

router = APIRouter()


@router.post("/login", response_model=ResponseModel[TokenResponse])
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(SysUser).filter(SysUser.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != 1:
        raise HTTPException(status_code=403, detail="账号已禁用")
    token = create_access_token(user.id, {"is_admin": user.is_admin})
    return ResponseModel(
        data=TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username,
            real_name=user.real_name,
            is_admin=user.is_admin,
        )
    )


@router.post("/register", response_model=ResponseModel[TokenResponse])
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(SysUser).filter(SysUser.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = SysUser(
        username=body.username,
        password_hash=hash_password(body.password),
        real_name=body.real_name,
        dept_id=body.dept_id,
        is_admin=0,
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, {"is_admin": user.is_admin})
    return ResponseModel(
        data=TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username,
            real_name=user.real_name,
            is_admin=user.is_admin,
        )
    )


@router.get("/me", response_model=ResponseModel[UserOut])
def me(user: SysUser = Depends(get_current_user)):
    return ResponseModel(data=UserOut.model_validate(user))
