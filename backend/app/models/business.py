from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CrawlerTask(Base):
    __tablename__ = "crawler_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    parse_config: Mapped[str | None] = mapped_column(Text, comment="JSON解析配置")
    schedule_cron: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[int] = mapped_column(Integer, default=0, comment="0待运行 1运行中 2成功 3失败")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CleaningRule(Base):
    __tablename__ = "cleaning_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_dag: Mapped[str] = mapped_column(Text, comment="JSON DAG规则编排")
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[int] = mapped_column(Integer, default=0, comment="0草稿 1已发布")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DigitalAgent(Base):
    __tablename__ = "digital_agent"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False)
    persona: Mapped[str | None] = mapped_column(Text)
    model_id: Mapped[str | None] = mapped_column(String(64))
    skill_ids: Mapped[str | None] = mapped_column(Text, comment="JSON Skill列表")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="0测试 1上线")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Nl2sqlLog(Base):
    __tablename__ = "nl2sql_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(Text)
    result_rows: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1成功 0失败 2拦截")
    error_msg: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Dashboard(Base):
    __tablename__ = "dashboard"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_interval: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1已发布 0草稿")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DataAsset(Base):
    __tablename__ = "data_asset"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    source_table: Mapped[str | None] = mapped_column(String(128))
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AiModel(Base):
    __tablename__ = "ai_model"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_type: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    api_key: Mapped[str] = mapped_column(String(512), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    is_default: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AiSkill(Base):
    __tablename__ = "ai_skill"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    skill_type: Mapped[int] = mapped_column(Integer, default=1, comment="1 function 2 skill")
    description: Mapped[str | None] = mapped_column(Text)
    schema_json: Mapped[str | None] = mapped_column(Text, comment="JSON schema or function spec")
    model_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
