from datetime import datetime

from pydantic import BaseModel, Field


class Nl2SqlQuery(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class Nl2SqlResult(BaseModel):
    sql: str
    columns: list[str]
    rows: list[dict]
    interpretation: str
    chart_type: str = "table"
    log_id: int


class Nl2SqlHistoryItem(BaseModel):
    id: int
    question: str
    generated_sql: str | None
    status: int
    created_at: datetime

    class Config:
        from_attributes = True
