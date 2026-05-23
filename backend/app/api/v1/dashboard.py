from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.business import Dashboard
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("")
def list_dashboards(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(Dashboard).filter(Dashboard.status == 1).all()
    return ResponseModel(
        data=[
            {
                "id": d.id,
                "title": d.title,
                "refresh_interval": d.refresh_interval,
                "config_json": d.config_json,
            }
            for d in items
        ]
    )


@router.get("/{dashboard_id}")
def get_dashboard(dashboard_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(Dashboard).filter(Dashboard.id == dashboard_id, Dashboard.status == 1).first()
    if not d:
        return ResponseModel(code=404, message="大屏不存在")
    return ResponseModel(
        data={
            "id": d.id,
            "title": d.title,
            "config_json": d.config_json,
            "refresh_interval": d.refresh_interval,
        }
    )
