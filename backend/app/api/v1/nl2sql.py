from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.business import Nl2sqlLog
from app.models.system import SysUser
from app.schemas.common import ResponseModel
from app.schemas.nl2sql import Nl2SqlHistoryItem, Nl2SqlQuery, Nl2SqlResult
from app.services.nl2sql_service import run_nl2sql

router = APIRouter()


@router.post("/query", response_model=ResponseModel[Nl2SqlResult])
def query_nl2sql(
    body: Nl2SqlQuery,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    result = run_nl2sql(db, user.id, body.question)
    if "error" in result:
        return ResponseModel(code=400, message=result["error"], data=None)
    return ResponseModel(
        data=Nl2SqlResult(
            sql=result["sql"],
            columns=result["columns"],
            rows=result["rows"],
            interpretation=result["interpretation"],
            chart_type=result["chart_type"],
            log_id=result["log_id"],
        )
    )


@router.get("/history", response_model=ResponseModel[list[Nl2SqlHistoryItem]])
def history(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    logs = (
        db.query(Nl2sqlLog)
        .filter(Nl2sqlLog.user_id == user.id)
        .order_by(Nl2sqlLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return ResponseModel(data=[Nl2SqlHistoryItem.model_validate(x) for x in logs])
