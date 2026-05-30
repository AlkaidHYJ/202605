import json
import re
from datetime import datetime
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


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_time_label(value: datetime | None = None) -> str:
    now = value or datetime.now()
    return now.strftime("%H:%M")


def _stringify_preview(payload: Any, max_len: int = 420) -> str:
    if isinstance(payload, str):
        text = payload
    else:
        try:
            text = json.dumps(payload, ensure_ascii=False, indent=2)
        except Exception:
            text = str(payload)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _detect_weather_theme(text: str) -> str:
    content = text
    if any(key in content for key in ("雪", "霜")):
        return "snowy"
    if any(key in content for key in ("雷", "电", "暴")):
        return "storm"
    if any(key in content for key in ("雨", "阵雨", "小雨", "中雨", "大雨", "暴雨")):
        return "rainy"
    if any(key in content for key in ("雾", "霾")):
        return "foggy"
    if any(key in content for key in ("阴", "多云")):
        return "cloudy"
    if any(key in content for key in ("晴", "日")):
        return "sunny"
    return "clear"


def _safe_json_loads(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _normalize_weather_payload(payload: Any) -> dict[str, Any]:
    payload = _safe_json_loads(payload)
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload.get("data") or {}
    if isinstance(payload, dict):
        return payload
    return {}


def _weather_icon_for(text: str) -> str:
    icon_map = {
        "晴": "☀️",
        "多云": "⛅",
        "阴": "☁️",
        "小雨": "🌧️",
        "中雨": "🌧️",
        "大雨": "⛈️",
        "雷阵雨": "⛈️",
        "小雪": "❄️",
        "中雪": "❄️",
        "大雪": "❄️",
        "雾": "🌫️",
        "霾": "🌫️",
        "晴转多云": "🌤️",
        "多云转晴": "🌤️",
    }
    return icon_map.get(text, "🌤️")


def _weather_bg_class(text: str) -> str:
    bg_map = {
        "晴": "bg-sunny",
        "多云": "bg-cloudy",
        "阴": "bg-cloudy",
        "小雨": "bg-rainy",
        "中雨": "bg-rainy",
        "大雨": "bg-rainy",
        "雷阵雨": "bg-rainy",
        "小雪": "bg-snowy",
        "中雪": "bg-snowy",
        "大雪": "bg-snowy",
        "雾": "bg-cloudy",
        "霾": "bg-cloudy",
        "晴转多云": "bg-sunny",
        "多云转晴": "bg-sunny",
    }
    return bg_map.get(text, "bg-sunny")


def _weather_aqi_class(text: str) -> str:
    aqi_map = {
        "优": "aqi-excellent",
        "良": "aqi-good",
        "轻度": "aqi-light",
        "中度": "aqi-moderate",
        "重度": "aqi-poor",
        "严重": "aqi-poor",
    }
    return aqi_map.get(text, "aqi-good")


def _render_weather_card(item: dict[str, Any]) -> str:
    data = _normalize_weather_payload(item.get("data"))
    args = item.get("args") if isinstance(item.get("args"), dict) else {}
    city = ""
    if isinstance(data.get("city"), str):
        city = data.get("city")
    elif isinstance(args.get("city"), str):
        city = args.get("city")
    elif isinstance(args.get("city"), list) and args.get("city"):
        city = "、".join(str(c) for c in args.get("city") if c)

    info = data.get("info") if isinstance(data.get("info"), list) else []
    today = info[0] if info else {}
    weather_text = str(today.get("weather") or "")
    temp_text = str(today.get("temperature") or "--～--℃")
    wind_text = str(today.get("bearing") or "--级")
    aqi_text = str(today.get("air_quality") or "--")
    icon_text = _weather_icon_for(weather_text)
    bg_class = _weather_bg_class(weather_text)
    aqi_class = _weather_aqi_class(aqi_text)

    forecast_items = []
    for day in info:
        day_label = _escape_html(str(day.get("Time") or "--"))
        day_weather = str(day.get("weather") or "")
        day_icon = _weather_icon_for(day_weather)
        day_temp = _escape_html(str(day.get("temperature") or "--～--℃"))
        day_wind = _escape_html(str(day.get("bearing") or "--"))
        raw_aqi = str(day.get("air_quality") or "--")
        day_aqi = _escape_html(raw_aqi)
        day_aqi_class = _weather_aqi_class(raw_aqi)
        forecast_items.append(
            "<div class=\"forecast-item\">"
            f"<span class=\"forecast-day\">{day_label}</span>"
            f"<span class=\"forecast-icon\">{_escape_html(day_icon)}</span>"
            f"<span class=\"forecast-temp\">{day_temp}</span>"
            f"<span class=\"forecast-wind\">{day_wind}</span>"
            f"<span class=\"forecast-aqi {day_aqi_class}\">{day_aqi}</span>"
            "</div>"
        )

    city_text = _escape_html(city or "天气")
    weather_text_safe = _escape_html(weather_text or "天气")
    temp_text_safe = _escape_html(temp_text)
    wind_text_safe = _escape_html(wind_text)
    aqi_text_safe = _escape_html(aqi_text)

    return (
        "<div class=\"weather-sim\">"
        "<style>"
        ".weather-sim{font-family:'Noto Sans SC',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}"
        ".weather-sim .weather-card{border-radius:24px;padding:24px 26px;position:relative;overflow:hidden;color:#fff;" 
        "box-shadow:0 20px 40px -18px rgba(15,23,42,0.45);border:1px solid rgba(255,255,255,0.25);}"
        ".weather-sim .weather-backdrop{position:absolute;inset:0;background:radial-gradient(circle at 20% 20%,rgba(255,255,255,0.18),transparent 60%);opacity:.9;}"
        ".weather-sim .weather-content{position:relative;display:grid;gap:14px;}"
        ".weather-sim .city-header{display:flex;align-items:center;gap:10px;}"
        ".weather-sim .city-icon{font-size:22px;}"
        ".weather-sim .city-name{font-size:22px;font-weight:700;text-shadow:0 2px 12px rgba(15,23,42,0.35);}"
        ".weather-sim .current-weather{text-align:center;display:grid;gap:8px;}"
        ".weather-sim .weather-main-icon{font-size:52px;}"
        ".weather-sim .current-temp{font-size:40px;font-weight:300;}"
        ".weather-sim .current-desc{font-size:16px;opacity:.92;}"
        ".weather-sim .current-details{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;}"
        ".weather-sim .detail-item{display:flex;align-items:center;gap:6px;font-size:12px;background:rgba(255,255,255,0.18);" 
        "padding:6px 12px;border-radius:999px;}"
        ".weather-sim .forecast-title{font-size:12px;letter-spacing:2px;opacity:.7;text-transform:uppercase;}"
        ".weather-sim .forecast-list{display:grid;gap:10px;}"
        ".weather-sim .forecast-item{display:flex;align-items:center;padding:12px 14px;background:rgba(255,255,255,0.12);" 
        "border-radius:14px;gap:10px;}"
        ".weather-sim .forecast-day{width:42px;font-weight:600;}"
        ".weather-sim .forecast-icon{font-size:22px;}"
        ".weather-sim .forecast-temp{flex:1;font-size:13px;font-weight:600;}"
        ".weather-sim .forecast-wind{font-size:12px;opacity:.85;}"
        ".weather-sim .forecast-aqi{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600;}"
        ".weather-sim .aqi-excellent{background:linear-gradient(135deg,#4ade80,#22c55e);}"
        ".weather-sim .aqi-good{background:linear-gradient(135deg,#a3e635,#84cc16);}"
        ".weather-sim .aqi-light{background:linear-gradient(135deg,#fbbf24,#f59e0b);}"
        ".weather-sim .aqi-moderate{background:linear-gradient(135deg,#fb923c,#f97316);}"
        ".weather-sim .aqi-poor{background:linear-gradient(135deg,#f87171,#ef4444);}"
        ".weather-sim .bg-sunny{background:linear-gradient(135deg,#667eea 0%,#764ba2 50%,#f093fb 100%);}"
        ".weather-sim .bg-cloudy{background:linear-gradient(135deg,#4a5568 0%,#718096 50%,#a0aec0 100%);}"
        ".weather-sim .bg-rainy{background:linear-gradient(135deg,#2d3748 0%,#4a5568 50%,#553c9a 100%);}"
        ".weather-sim .bg-snowy{background:linear-gradient(135deg,#a0aec0 0%,#cbd5e0 50%,#e2e8f0 100%);}"
        "</style>"
        f"<div class=\"weather-card {bg_class}\">"
        "<div class=\"weather-backdrop\"></div>"
        "<div class=\"weather-content\">"
        "<div class=\"city-header\">"
        "<span class=\"city-icon\">📍</span>"
        f"<span class=\"city-name\">{city_text}</span>"
        "</div>"
        "<div class=\"current-weather\">"
        f"<span class=\"weather-main-icon\">{_escape_html(icon_text)}</span>"
        f"<div class=\"current-temp\">{temp_text_safe}</div>"
        f"<div class=\"current-desc\">{weather_text_safe}</div>"
        "<div class=\"current-details\">"
        f"<div class=\"detail-item\"><span>💨</span><span>{wind_text_safe}</span></div>"
        f"<div class=\"detail-item\"><span>🌿</span><span>{aqi_text_safe}</span></div>"
        "</div>"
        "</div>"
        "<div class=\"forecast-section\">"
        "<div class=\"forecast-title\">未来预报</div>"
        "<div class=\"forecast-list\">"
        f"{''.join(forecast_items)}"
        "</div>"
        "</div>"
        "</div>"
        "</div>"
        "</div>"
    )


def _render_generic_card(item: dict[str, Any]) -> str:
    title = _escape_html(str(item.get("skill_name") or "技能"))
    status = "成功" if item.get("success") else "失败"
    status_class = "success" if item.get("success") else "failure"
    payload = item.get("data") if item.get("success") else (item.get("error") or item.get("response"))
    body = _escape_html(_stringify_preview(payload))
    provider = _escape_html(str(item.get("provider") or ""))
    time_text = _escape_html(_format_time_label())
    source = f"来源: {provider} · {time_text}" if provider else f"时间: {time_text}"
    return (
        "<div class=\"skill-card\">"
        f"<div class=\"skill-title\">{title}</div>"
        f"<div class=\"skill-subtitle {status_class}\">{status}</div>"
        f"<pre class=\"skill-body\">{body}</pre>"
        f"<div class=\"skill-meta\">{source}</div>"
        "</div>"
    )


def _render_skill_results_html(skill_results: list[dict[str, Any]]) -> str | None:
    if not skill_results:
        return None
    cards = []
    for item in skill_results:
        name = str(item.get("skill_name") or "").lower()
        if item.get("skill_id") == 5 or "weather" in name or "天气" in name:
            cards.append(_render_weather_card(item))
        else:
            cards.append(_render_generic_card(item))
    return "".join(cards)


def _maybe_extract_html_reply(text: str) -> str | None:
    if not text:
        return None
    candidate = text.strip()
    if "<" not in candidate or ">" not in candidate:
        return None
    return candidate


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
        '{"reply":"给用户看的简短自然回复(建议用HTML片段)","skill_calls":[{"skill_id":1,"args":{}}]}\n'
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
                "provider": result.get("provider"),
                "args": args,
                "data": result.get("data"),
                "response": result.get("response"),
            })
        except Exception as exc:
            skill_results.append({
                "skill_id": skill.id,
                "skill_name": skill.skill_name,
                "success": False,
                "provider": "error",
                "args": args,
                "error": str(exc),
            })

    final_reply = reply_seed
    if skill_results:
        final_reply = _skill_results_to_reply(skill_results)

    if not final_reply:
        final_reply = _fallback_reply(agent, user_message, skill_results)

    reply_html = _render_skill_results_html(skill_results)
    if not reply_html:
        reply_html = _maybe_extract_html_reply(reply_seed)

    return {
        "agent_id": agent.id,
        "agent_name": agent.agent_name,
        "model_id": model.model_id,
        "model_name": model.model_name,
        "reply": final_reply,
        "reply_html": reply_html,
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