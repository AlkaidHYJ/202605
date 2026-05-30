import json
import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.business import AiModel, AiSkill, DigitalAgent
from app.services.skill_executor import execute_skill


def _parse_skill_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    result: list[int] = []
    for item in data:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return result


def _extract_json_object(text: str) -> dict[str, Any] | None:
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S)
    try:
        data = json.loads(content)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass

    last_dict: dict[str, Any] | None = None
    start: int | None = None
    depth = 0
    for idx, ch in enumerate(content):
        if ch == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidate = content[start : idx + 1]
                    try:
                        parsed = json.loads(candidate)
                    except json.JSONDecodeError:
                        parsed = None
                    if isinstance(parsed, dict):
                        last_dict = parsed
                    start = None
    return last_dict


def _read_path(payload: dict[str, Any] | list[Any] | None, path: str | None) -> Any:
    if payload is None or not path:
        return payload
    cursor: Any = payload
    for part in path.split("."):
        if isinstance(cursor, dict):
            cursor = cursor.get(part)
        elif isinstance(cursor, list):
            try:
                cursor = cursor[int(part)]
            except (TypeError, ValueError, IndexError):
                return None
        else:
            return None
    return cursor


def _openai_chat_stream(
    client: httpx.Client,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> str:
    stream_payload = {**payload, "stream": True}
    content_chunks: list[str] = []
    with client.stream("POST", url, json=stream_payload, headers=headers) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("data: "):
                data = line[len("data: ") :].strip()
            else:
                continue
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            delta = (chunk.get("choices") or [{}])[0].get("delta", {}) if isinstance(chunk, dict) else {}
            piece = delta.get("content") or delta.get("reasoning_content") or ""
            if piece:
                content_chunks.append(piece)
    return "".join(content_chunks).strip()


def _openai_chat(
    base_url: str,
    api_key: str,
    model_id: str,
    messages: list[dict[str, Any]],
) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        url = normalized + "/chat/completions"
    else:
        url = normalized + "/v1/chat/completions"
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=120) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices:
            return _openai_chat_stream(client, url, payload, headers)
        return choices[0].get("message", {}).get("content", "").strip()


def _load_agent(db: Session, agent_id: int) -> DigitalAgent:
    agent = (
        db.query(DigitalAgent)
        .filter(DigitalAgent.id == agent_id, DigitalAgent.status == 1)
        .first()
    )
    if not agent:
        raise ValueError("数字员工不存在或未上线")
    return agent


def _load_model(db: Session, model_ref: str | None) -> AiModel:
    model = None
    if model_ref:
        model = db.query(AiModel).filter(AiModel.model_id == model_ref, AiModel.status == 1).first()
    if not model:
        model = (
            db.query(AiModel)
            .filter(AiModel.is_default == 1, AiModel.status == 1)
            .order_by(AiModel.id.desc())
            .first()
        )
    if not model:
        model = db.query(AiModel).filter(AiModel.status == 1).order_by(AiModel.id.desc()).first()
    if not model:
        raise ValueError("暂无可用模型，请先到模型管理新增模型")
    return model


def _load_agent_skills(db: Session, agent: DigitalAgent) -> list[AiSkill]:
    skill_ids = _parse_skill_ids(agent.skill_ids)
    if not skill_ids:
        return []
    skills = db.query(AiSkill).filter(AiSkill.id.in_(skill_ids), AiSkill.status == 1).all()
    skill_map = {skill.id: skill for skill in skills}
    return [skill_map[sid] for sid in skill_ids if sid in skill_map]


def _history_to_text(history_text: str | None) -> str:
    if history_text:
        return history_text.strip()
    return "无"


def _skill_catalog(skills: list[AiSkill]) -> str:
    if not skills:
        return "无"
    parts = []
    for skill in skills:
        param_hint = ""
        if skill.skill_type == 1 and skill.schema_json:
            try:
                config = json.loads(skill.schema_json)
            except json.JSONDecodeError:
                config = None
            if isinstance(config, dict):
                schema = config.get("input_schema") or config.get("parameters")
                if isinstance(schema, dict):
                    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
                    required = set(schema.get("required") or []) if isinstance(schema.get("required"), list) else set()
                    if props:
                        items = [f"{key}{'*' if key in required else ''}" for key in props.keys()]
                        param_hint = f" | 参数: {', '.join(items)}"
        parts.append(
            f"- 技能ID {skill.id}: {skill.skill_name} | 类型 {skill.skill_type} | {skill.description or '无描述'}{param_hint}"
        )
    return "\n".join(parts)


def _fallback_reply(agent: DigitalAgent, user_message: str, skill_results: list[dict[str, Any]]) -> str:
    if skill_results:
        snippets = []
        for item in skill_results:
            if item.get("success"):
                payload = item.get("data")
            else:
                payload = item.get("error") or item.get("response") or "调用失败"
            text = json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
            snippets.append(f"{item.get('skill_name', '技能')}: {text[:300]}")
        return f"我已调用技能，结果如下：{'；'.join(snippets)}"
    return f"【{agent.agent_name}】已收到：{user_message}"


def _skill_results_to_reply(skill_results: list[dict[str, Any]]) -> str:
    success_items = [item for item in skill_results if item.get("success")]
    if not success_items:
        return ""
    if len(success_items) == 1:
        data = success_items[0].get("data")
        if isinstance(data, str):
            return data.strip()
        return json.dumps(data, ensure_ascii=False, indent=2)
    parts: list[str] = []
    for item in success_items:
        data = item.get("data")
        if isinstance(data, str):
            content = data.strip()
        else:
            content = json.dumps(data, ensure_ascii=False)
        parts.append(f"{item.get('skill_name', '技能')}: {content}")
    return "\n".join(parts)


def generate_agent_reply(
    db: Session,
    agent_id: int,
    user_message: str,
    history_text: str | None = None,
) -> dict[str, Any]:
    agent = _load_agent(db, agent_id)
    model = _load_model(db, agent.model_id)
    skills = _load_agent_skills(db, agent)

    transcript = _history_to_text(history_text)
    skill_catalog = _skill_catalog(skills)

    planner_prompt = (
        f"你是数字员工【{agent.agent_name}】。\n"
        f"人设：{agent.persona or '企业数字员工'}。\n"
        "请基于上下文判断是否需要调用技能。\n"
        "如果需要调用技能，只输出 JSON，格式如下：\n"
        '{"reply":"给用户看的简短自然回复","skill_calls":[{"skill_id":1,"args":{}}]}\n'
        "如果不需要调用技能，skill_calls 为空数组。\n"
        "不要输出 Markdown，不要输出多余解释。\n\n"
        f"最近对话：\n{transcript}\n\n"
        f"当前用户消息：\n{user_message}\n\n"
        f"可用技能：\n{skill_catalog}"
    )

    try:
        planner_raw = _openai_chat(
            model.base_url,
            model.api_key,
            model.model_id,
            [
                {"role": "system", "content": "你是严谨的数字员工编排器，只输出符合要求的结果。"},
                {"role": "user", "content": planner_prompt},
            ],
        )
    except Exception:
        planner_raw = ""

    planner_data = _extract_json_object(planner_raw) or {}
    reply_seed = str(planner_data.get("reply") or planner_raw or "").strip()
    skill_calls = planner_data.get("skill_calls") if isinstance(planner_data.get("skill_calls"), list) else []

    skill_results: list[dict[str, Any]] = []
    for call in skill_calls:
        if not isinstance(call, dict):
            continue
        try:
            skill_id = int(call.get("skill_id"))
        except (TypeError, ValueError):
            continue
        skill = next((item for item in skills if item.id == skill_id), None)
        if not skill:
            skill_results.append({"skill_id": skill_id, "skill_name": f"技能{skill_id}", "success": False, "error": "技能不在当前员工可用列表中"})
            continue
        args = call.get("args") if isinstance(call.get("args"), dict) else {}
        try:
            result = execute_skill(skill, args, db=db)
            skill_results.append({
                "skill_id": skill.id,
                "skill_name": skill.skill_name,
                "success": result.get("success", False),
                "data": result.get("data"),
                "response": result.get("response"),
            })
        except Exception as exc:
            skill_results.append({
                "skill_id": skill.id,
                "skill_name": skill.skill_name,
                "success": False,
                "error": str(exc),
            })

    final_reply = reply_seed
    if skill_results:
        final_reply = _skill_results_to_reply(skill_results)

    if not final_reply:
        final_reply = _fallback_reply(agent, user_message, skill_results)

    return {
        "agent_id": agent.id,
        "agent_name": agent.agent_name,
        "model_id": model.model_id,
        "model_name": model.model_name,
        "reply": final_reply,
        "skill_results": skill_results,
    }


def build_history_text(lines: list[str]) -> str:
    return "\n".join(lines).strip()


def find_mentioned_agents(content: str, agents: list[DigitalAgent]) -> list[DigitalAgent]:
    matched: list[tuple[int, DigitalAgent]] = []
    for agent in agents:
        token = f"@{agent.agent_name}"
        index = content.find(token)
        if index >= 0:
            matched.append((index, agent))
    return [agent for _, agent in sorted(matched, key=lambda item: item[0])]