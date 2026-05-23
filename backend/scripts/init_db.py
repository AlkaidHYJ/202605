"""初始化数据库与演示数据"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import *
from app.services import im_service


def seed():
    db = SessionLocal()
    try:
        if db.query(SysUser).filter(SysUser.username == "admin").first():
            print("数据已存在，跳过初始化")
            return

        dept = SysDept(parent_id=0, dept_name="总部", sort_order=0)
        db.add(dept)
        db.flush()

        admin = SysUser(
            username="admin",
            password_hash=hash_password("admin123"),
            real_name="系统管理员",
            dept_id=dept.id,
            is_admin=1,
        )
        user = SysUser(
            username="user01",
            password_hash=hash_password("user123"),
            real_name="业务用户",
            dept_id=dept.id,
            is_admin=0,
        )
        db.add_all([admin, user])
        db.flush()

        db.add_all(
            [
                ImSensitiveWord(word="违禁词示例", level=1, category="阻断"),
                ImSensitiveWord(word="审计词示例", level=2, category="审计"),
            ]
        )

        agent = DigitalAgent(
            agent_name="数据分析师小智",
            persona="专注企业数据洞察与报表解读",
            model_id="default-llm",
            skill_ids='["nl2sql","report"]',
            status=1,
        )
        db.add(agent)

        dashboard = Dashboard(
            title="经营概览大屏",
            config_json='{"widgets":[{"type":"kpi","title":"今日销售额","value":1280000}]}',
            refresh_interval=60,
            status=1,
        )
        db.add(dashboard)

        db.commit()
        im_service.reload_sensitive_words(db)
        print("初始化完成")
        print("  管理员: admin / admin123")
        print("  业务用户: user01 / user123")
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed()
