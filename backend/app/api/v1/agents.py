import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.redis_client import redis_client
from app.core.security import get_current_user
from app.models.business import AiModel, AiSkill, DigitalAgent
from app.models.system import SysUser
from app.schemas.common import ResponseModel
from app.services.agent_runtime import generate_agent_reply

router = APIRouter()


class AgentChatRequest(BaseModel):
    agent_id: int
    message: str


@router.get("")
def list_agents(db: Session = Depends(get_db), _=Depends(get_current_user)):
    agents = db.query(DigitalAgent).filter(DigitalAgent.status == 1).all()
    default_model = (
        db.query(AiModel)
        .filter(AiModel.is_default == 1, AiModel.status == 1)
        .order_by(AiModel.id.desc())
        .first()
    )
    model_refs = [agent.model_id for agent in agents if agent.model_id]
    model_map = {
        model.model_id: model
        for model in db.query(AiModel).filter(AiModel.model_id.in_(model_refs)).all()
    }
    skill_ids: list[int] = []
    for agent in agents:
        if not agent.skill_ids:
            continue
        try:
            skill_ids.extend(int(item) for item in json.loads(agent.skill_ids))
        except Exception:
            continue
    skill_map = {skill.id: skill for skill in db.query(AiSkill).filter(AiSkill.id.in_(skill_ids)).all()} if skill_ids else {}

    def _parse_agent_skill_ids(raw: str | None) -> list[int]:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except Exception:
            return []
        if not isinstance(parsed, list):
            return []
        result: list[int] = []
        for item in parsed:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return result

    return ResponseModel(
        data=[
            {
                "id": a.id,
                "agent_name": a.agent_name,
                "persona": a.persona,
                "skill_ids": a.skill_ids,
                "model_id": a.model_id,
                "model_name": (
                    model_map.get(a.model_id).model_name
                    if a.model_id and model_map.get(a.model_id)
                    else (default_model.model_name if default_model else None)
                ),
                "skill_names": [
                    skill_map[skill_id].skill_name
                    for skill_id in _parse_agent_skill_ids(a.skill_ids)
                    if skill_id in skill_map
                ],
            }
            for a in agents
        ]
    )


@router.post("/chat")
def agent_chat(
    body: AgentChatRequest,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    agent = (
        db.query(DigitalAgent)
        .filter(DigitalAgent.id == body.agent_id, DigitalAgent.status == 1)
        .first()
    )
    if not agent:
        raise HTTPException(404, "数字员工不存在或未上线")

    ctx_key = f"agent:ctx:{user.id}:{body.agent_id}"
    history = redis_client.lrange(ctx_key, 0, -1) or []
    history_text = "\n".join(history)
    result = generate_agent_reply(db, agent.id, body.message, history_text=history_text)
    reply = result["reply"]
    redis_client.rpush(ctx_key, f"user:{body.message}", f"assistant:{reply}")
    redis_client.ltrim(ctx_key, -settings.IM_CONTEXT_ROUNDS * 2, -1)

    return ResponseModel(
        data={
            "reply": reply,
            "reply_html": result.get("reply_html"),
            "context_rounds": len(history) // 2 + 1,
            "model_name": result.get("model_name"),
            "skill_results": result.get("skill_results", []),
        }
    )
