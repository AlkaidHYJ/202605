import json
from typing import Any

import httpx

from app.models.business import AiSkill


def _replace_token(value: str, args: dict[str, Any]) -> str:
    result = value
    for key, arg in args.items():
        result = result.replace("{" + key + "}", str(arg))
    return result


def _render_template(template: Any, args: dict[str, Any]) -> Any:
    if isinstance(template, str):
        return _replace_token(template, args)
    if isinstance(template, dict):
        return {k: _render_template(v, args) for k, v in template.items()}
    if isinstance(template, list):
        return [_render_template(v, args) for v in template]
    return template


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
            except (ValueError, IndexError):
                return None
        else:
            return None
    return cursor


def _normalize_config(skill: AiSkill) -> dict[str, Any]:
    if not skill.schema_json:
        raise ValueError("skill.schema_json 为空，无法执行")
    try:
        cfg = json.loads(skill.schema_json)
    except json.JSONDecodeError as exc:
        raise ValueError("skill.schema_json 不是合法 JSON") from exc
    if not isinstance(cfg, dict):
        raise ValueError("skill.schema_json 必须是 JSON 对象")
    runtime = cfg.get("runtime") if isinstance(cfg.get("runtime"), dict) else {}
    response = cfg.get("response") if isinstance(cfg.get("response"), dict) else {}
    return {
        "runtime": runtime,
        "response": response,
        "raw": cfg,
    }


def execute_skill(skill: AiSkill, args: dict[str, Any] | None = None) -> dict[str, Any]:
    args = args or {}
    config = _normalize_config(skill)
    runtime = config["runtime"]
    response_cfg = config["response"]

    provider = str(runtime.get("provider", "http")).lower()
    if provider != "http":
        raise ValueError(f"暂不支持 provider={provider}")

    method = str(runtime.get("method", "GET")).upper()
    url = runtime.get("url")
    if not url:
        raise ValueError("runtime.url 不能为空")

    timeout_seconds = int(runtime.get("timeout_seconds", 10))
    query_template = runtime.get("query_template") or {}
    body_template = runtime.get("body_template") or {}
    headers_template = runtime.get("headers_template") or {}

    query = _render_template(query_template, args)
    body = _render_template(body_template, args)
    headers = _render_template(headers_template, args)

    if method == "GET":
        body = None

    with httpx.Client(timeout=timeout_seconds) as client:
        resp = client.request(method, url, params=query, json=body, headers=headers)

    try:
        body_json = resp.json()
    except ValueError:
        body_json = None

    success = resp.status_code < 400
    if body_json is not None:
        code_path = response_cfg.get("success_code_path")
        code_expect = response_cfg.get("success_code_equals")
        if code_path:
            code_actual = _read_path(body_json, code_path)
            if code_expect is not None:
                success = success and code_actual == code_expect

    data_path = response_cfg.get("data_path")
    normalized_data = _read_path(body_json, data_path) if body_json is not None and data_path else body_json
    if normalized_data is None and isinstance(body_json, dict):
        normalized_data = body_json.get("data")
        if normalized_data is None and "content" in body_json:
            normalized_data = body_json.get("content")

    return {
        "success": success,
        "skill_id": skill.id,
        "skill_name": skill.skill_name,
        "provider": provider,
        "request": {
            "method": method,
            "url": url,
            "query": query,
            "body": body,
        },
        "response": {
            "status_code": resp.status_code,
            "body": body_json if body_json is not None else resp.text,
        },
        "data": normalized_data,
    }
