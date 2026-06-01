import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin, get_current_user
from app.models.business import CrawlerDocument, CrawlerTask, CleaningRule
from app.schemas.common import ResponseModel
from app.services.crawler_service import clean_markdown, crawl_once

router = APIRouter()


class CrawlerTaskCreate(BaseModel):
    task_name: str
    source_url: str
    schedule_cron: str | None = None
    parse_config: dict | None = None


class CrawlerTaskRunRequest(BaseModel):
    rule_id: int | None = None


class CleaningRuleCreate(BaseModel):
    rule_name: str
    rule_dag: dict | None = Field(default_factory=dict)


class CleaningApplyRequest(BaseModel):
    rule_id: int


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
                "last_run_at": t.last_run_at,
            }
            for t in tasks
        ]
    )


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return ResponseModel(code=404, message="任务不存在")
    db.query(CrawlerDocument).filter(CrawlerDocument.task_id == task_id).delete()
    db.delete(task)
    db.commit()
    return ResponseModel(data={"id": task_id})


@router.post("/tasks/{task_id}/stop")
def stop_task(task_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return ResponseModel(code=404, message="任务不存在")
    task.status = 4
    db.add(task)
    db.commit()
    return ResponseModel(data={"id": task_id, "status": task.status})


@router.post("/tasks")
def create_task(body: CrawlerTaskCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    task = CrawlerTask(
        task_name=body.task_name,
        source_url=body.source_url,
        schedule_cron=body.schedule_cron,
        parse_config=json.dumps(body.parse_config or {}, ensure_ascii=False),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ResponseModel(data={"id": task.id})


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return ResponseModel(code=404, message="任务不存在")
    return ResponseModel(
        data={
            "id": task.id,
            "task_name": task.task_name,
            "source_url": task.source_url,
            "status": task.status,
            "schedule_cron": task.schedule_cron,
            "parse_config": task.parse_config,
            "last_run_at": task.last_run_at,
        }
    )


@router.post("/tasks/{task_id}/run")
async def run_task(
    task_id: int,
    body: CrawlerTaskRunRequest | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return ResponseModel(code=404, message="任务不存在")

    task.status = 1
    task.last_run_at = datetime.utcnow()
    db.add(task)
    db.commit()

    try:
        result = await crawl_once(task.source_url, task.parse_config)
    except Exception as exc:
        task.status = 3
        db.add(task)
        db.commit()
        return ResponseModel(code=500, message=str(exc)[:500])

    if not result.get("success"):
        task.status = 3
        db.add(task)
        db.commit()
        return ResponseModel(code=500, message=result.get("error") or "crawl_failed")

    doc = CrawlerDocument(
        task_id=task.id,
        source_url=task.source_url,
        title=result.get("title"),
        raw_html=result.get("raw_html"),
        extracted_text=result.get("extracted_text"),
        markdown_content=result.get("markdown"),
    )

    if body and body.rule_id:
        rule = db.query(CleaningRule).filter(CleaningRule.id == body.rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="清洗规则不存在")
        cleaned, status, reason = clean_markdown(doc.markdown_content, rule.rule_dag)
        doc.cleaned_markdown = cleaned
        doc.clean_status = status
        doc.clean_reason = reason

    task.status = 2
    db.add(task)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return ResponseModel(data={"document_id": doc.id})


@router.get("/cleaning-rules")
def list_rules(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    rules = db.query(CleaningRule).all()
    return ResponseModel(
        data=[
            {"id": r.id, "rule_name": r.rule_name, "version": r.version, "status": r.status}
            for r in rules
        ]
    )


@router.post("/cleaning-rules")
def create_rule(body: CleaningRuleCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    rule = CleaningRule(
        rule_name=body.rule_name,
        rule_dag=json.dumps(body.rule_dag or {}, ensure_ascii=False),
        status=1,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return ResponseModel(data={"id": rule.id})


@router.post("/tasks/{task_id}/clean")
def apply_rule_to_task(
    task_id: int,
    body: CleaningApplyRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    rule = db.query(CleaningRule).filter(CleaningRule.id == body.rule_id).first()
    if not rule:
        return ResponseModel(code=404, message="清洗规则不存在")
    docs = db.query(CrawlerDocument).filter(CrawlerDocument.task_id == task_id).all()
    if not docs:
        return ResponseModel(code=404, message="无可清洗的数据")
    for doc in docs:
        cleaned, status, reason = clean_markdown(doc.markdown_content, rule.rule_dag)
        doc.cleaned_markdown = cleaned
        doc.clean_status = status
        doc.clean_reason = reason
        db.add(doc)
    db.commit()
    return ResponseModel(data={"count": len(docs)})


@router.get("/tasks/{task_id}/results")
def list_task_results(task_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    docs = (
        db.query(CrawlerDocument)
        .filter(CrawlerDocument.task_id == task_id)
        .order_by(CrawlerDocument.created_at.desc())
        .limit(50)
        .all()
    )
    return ResponseModel(
        data=[
            {
                "id": d.id,
                "title": d.title,
                "source_url": d.source_url,
                "clean_status": d.clean_status,
                "created_at": d.created_at,
            }
            for d in docs
        ]
    )


@router.get("/results/{result_id}")
def get_result(result_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    doc = db.query(CrawlerDocument).filter(CrawlerDocument.id == result_id).first()
    if not doc:
        return ResponseModel(code=404, message="结果不存在")
    return ResponseModel(
        data={
            "id": doc.id,
            "title": doc.title,
            "source_url": doc.source_url,
            "markdown_content": doc.markdown_content,
            "cleaned_markdown": doc.cleaned_markdown,
            "clean_status": doc.clean_status,
            "created_at": doc.created_at,
        }
    )


@router.get("/public-results")
def list_public_results(task_id: int | None = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(CrawlerDocument)
    if task_id:
        query = query.filter(CrawlerDocument.task_id == task_id)
    docs = (
        query
        .order_by(CrawlerDocument.created_at.desc())
        .limit(12)
        .all()
    )
    return ResponseModel(
        data=[
            {
                "id": d.id,
                "title": d.title,
                "source_url": d.source_url,
                "markdown": d.cleaned_markdown or d.markdown_content,
                "markdown_content": d.markdown_content,
                "cleaned_markdown": d.cleaned_markdown,
                "clean_status": d.clean_status,
                "content_length": len((d.cleaned_markdown or d.markdown_content or "")),
                "created_at": d.created_at,
            }
            for d in docs
        ]
    )


@router.get("/public-results-report")
def public_results_report(task_id: int | None = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(CrawlerDocument)
    if task_id:
        query = query.filter(CrawlerDocument.task_id == task_id)
    docs = (
        query
        .order_by(CrawlerDocument.created_at.desc())
        .limit(200)
        .all()
    )
    total = len(docs)
    cleaned = sum(1 for d in docs if d.clean_status == 1)
    lengths = [len((d.cleaned_markdown or d.markdown_content or "")) for d in docs]
    avg_length = int(sum(lengths) / total) if total else 0
    dates = [d.created_at.strftime("%Y-%m-%d") for d in docs if d.created_at]
    date_range = None
    if dates:
        date_range = f"{min(dates)} ~ {max(dates)}"
    return ResponseModel(
        data={
            "total": total,
            "cleaned": cleaned,
            "avg_length": avg_length,
            "date_range": date_range,
        }
    )


@router.get("/public-tasks")
def list_public_tasks(db: Session = Depends(get_db), _=Depends(get_current_user)):
    tasks = db.query(CrawlerTask).order_by(CrawlerTask.created_at.desc()).all()
    return ResponseModel(
        data=[
            {
                "id": task.id,
                "task_name": task.task_name,
                "status": task.status,
                "last_run_at": task.last_run_at,
                "created_at": task.created_at,
            }
            for task in tasks
            if task.status != 4 or task.last_run_at is not None
        ]
    )
