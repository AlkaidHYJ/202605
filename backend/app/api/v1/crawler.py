from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.business import CrawlerTask, CleaningRule
from app.schemas.common import ResponseModel

router = APIRouter()


class CrawlerTaskCreate(BaseModel):
    task_name: str
    source_url: str
    schedule_cron: str | None = None
    parse_config: str | None = None


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    tasks = db.query(CrawlerTask).order_by(CrawlerTask.created_at.desc()).all()
    return ResponseModel(
        data=[
            {
                "id": t.id,
                "task_name": t.task_name,
                "source_url": t.source_url,
                "status": t.status,
                "schedule_cron": t.schedule_cron,
            }
            for t in tasks
        ]
    )


@router.post("/tasks")
def create_task(body: CrawlerTaskCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    task = CrawlerTask(
        task_name=body.task_name,
        source_url=body.source_url,
        schedule_cron=body.schedule_cron,
        parse_config=body.parse_config,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ResponseModel(data={"id": task.id})


@router.get("/cleaning-rules")
def list_rules(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    rules = db.query(CleaningRule).all()
    return ResponseModel(
        data=[
            {"id": r.id, "rule_name": r.rule_name, "version": r.version, "status": r.status}
            for r in rules
        ]
    )
