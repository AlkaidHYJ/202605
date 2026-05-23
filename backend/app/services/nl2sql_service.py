"""NL2SQL 生成与安全沙箱（仅允许 SELECT）"""
import re
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.business import Nl2sqlLog


FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)


def validate_select_only(sql: str) -> tuple[bool, str]:
    stripped = sql.strip().rstrip(";")
    if not stripped.upper().startswith("SELECT"):
        return False, "仅允许执行 SELECT 查询"
    if FORBIDDEN_KEYWORDS.search(stripped):
        return False, "SQL 包含禁止的关键字"
    if ";" in stripped:
        return False, "不允许多语句执行"
    return True, ""


def mock_generate_sql(question: str) -> str:
    """占位：对接 LLM 网关前使用规则生成示例 SQL"""
    q = question.lower()
    if "销售" in question or "sale" in q:
        return "SELECT region, SUM(amount) AS total FROM sales GROUP BY region LIMIT 100"
    if "用户" in question or "user" in q:
        return "SELECT id, username, created_at FROM sys_user WHERE status = 1 LIMIT 100"
    return "SELECT 1 AS demo_value, '示例数据' AS label LIMIT 10"


def execute_sql_sandbox(db: Session, sql: str) -> tuple[list[str], list[dict], str]:
    start = time.time()
    if time.time() - start > settings.NL2SQL_TIMEOUT_SECONDS:
        raise TimeoutError("查询超时")

    result = db.execute(text(sql))
    columns = list(result.keys())
    rows_raw = result.fetchmany(settings.NL2SQL_MAX_ROWS)
    rows = [dict(zip(columns, row)) for row in rows_raw]
    interpretation = f"共返回 {len(rows)} 条记录（最多 {settings.NL2SQL_MAX_ROWS} 条）"
    return columns, rows, interpretation


def run_nl2sql(
    db: Session, user_id: int, question: str
) -> dict[str, Any]:
    generated = mock_generate_sql(question)
    ok, err = validate_select_only(generated)
    log = Nl2sqlLog(
        user_id=user_id,
        question=question,
        generated_sql=generated,
        status=1 if ok else 2,
        error_msg=err if not ok else None,
    )
    if not ok:
        db.add(log)
        db.commit()
        db.refresh(log)
        return {"error": err, "log_id": log.id}

    try:
        columns, rows, interpretation = execute_sql_sandbox(db, generated)
        log.result_rows = len(rows)
        db.add(log)
        db.commit()
        db.refresh(log)
        return {
            "sql": generated,
            "columns": columns,
            "rows": rows,
            "interpretation": interpretation,
            "chart_type": "bar" if len(columns) == 2 and len(rows) <= 20 else "table",
            "log_id": log.id,
        }
    except Exception as exc:
        log.status = 0
        log.error_msg = str(exc)[:500]
        db.add(log)
        db.commit()
        db.refresh(log)
        return {"error": str(exc), "log_id": log.id}
