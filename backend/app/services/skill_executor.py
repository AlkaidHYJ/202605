import ast
import contextlib
import io
import json
import sys
import types
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models.business import AiModel, AiSkill


_ALLOWED_IMPORTS = {
    "collections",
    "datetime",
    "functools",
    "httpx",
    "itertools",
    "json",
    "math",
    "operator",
    "random",
    "re",
    "request",
    "requests",
    "statistics",
    "uuid",
}

_SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "Exception": Exception,
    "float": float,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "KeyError": KeyError,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "reversed": reversed,
    "round": round,
    "RuntimeError": RuntimeError,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "TypeError": TypeError,
    "ValueError": ValueError,
    "zip": zip,
}


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


def _get_config_value(cfg: dict[str, Any], key: str) -> Any:
    value = cfg.get(key)
    if value is not None:
        return value
    nested = cfg.get("skill_package")
    if isinstance(nested, dict):
        value = nested.get(key)
        if value is not None:
            return value
    return None


def _extract_skill_md(cfg: dict[str, Any]) -> str | None:
    skill_md = _get_config_value(cfg, "skill_md")
    if isinstance(skill_md, str) and skill_md.strip():
        return skill_md.strip()
    package_content = _get_config_value(cfg, "skill_package_content")
    if isinstance(package_content, str) and package_content.strip():
        return package_content.strip()
    package = cfg.get("skill_package")
    if isinstance(package, str) and package.strip():
        return package.strip()
    return None


def _compile_sandbox(code: str) -> ast.AST:
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module_name = ""
            if isinstance(node, ast.ImportFrom):
                module_name = (node.module or "").split(".")[0]
            for alias in node.names:
                current_name = module_name or alias.name.split(".")[0]
                module_name = current_name
                if module_name not in _ALLOWED_IMPORTS:
                    raise ValueError(f"sandbox 禁止导入模块: {module_name}")
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValueError("sandbox 禁止使用 global/nonlocal")
    return tree


def _safe_import(name: str, globals=None, locals=None, fromlist=(), level=0):
    module_name = name.split(".")[0]
    if module_name not in _ALLOWED_IMPORTS:
        raise ValueError(f"sandbox 禁止导入模块: {module_name}")
    if module_name in {"request", "requests"}:
        return _get_requests_shim(module_name)
    return __import__(name, globals, locals, fromlist, level)


def _get_requests_shim(module_name: str) -> types.ModuleType:
    shim = sys.modules.get(module_name)
    if shim is not None:
        return shim

    shim = types.ModuleType(module_name)

    def _request(method: str, url: str, **kwargs: Any):
        return httpx.request(method, url, **kwargs)

    def _get(url: str, **kwargs: Any):
        return httpx.get(url, **kwargs)

    def _post(url: str, **kwargs: Any):
        return httpx.post(url, **kwargs)

    def _put(url: str, **kwargs: Any):
        return httpx.put(url, **kwargs)

    def _delete(url: str, **kwargs: Any):
        return httpx.delete(url, **kwargs)

    def _head(url: str, **kwargs: Any):
        return httpx.head(url, **kwargs)

    def _patch(url: str, **kwargs: Any):
        return httpx.patch(url, **kwargs)

    shim.request = _request
    shim.get = _get
    shim.post = _post
    shim.put = _put
    shim.delete = _delete
    shim.head = _head
    shim.patch = _patch
    shim.Session = httpx.Client
    shim.Client = httpx.Client
    shim.HTTPError = httpx.HTTPError
    shim.Response = httpx.Response
    sys.modules[module_name] = shim
    return shim


def _run_python_sandbox(code: str, args: dict[str, Any]) -> tuple[Any, str]:
    tree = _compile_sandbox(code)
    _get_requests_shim("request")
    _get_requests_shim("requests")
    namespace: dict[str, Any] = {
        "__builtins__": {**_SAFE_BUILTINS, "__import__": _safe_import},
        "args": args,
        "context": args,
        "payload": args,
    }
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exec(compile(tree, "<skill_sandbox>", "exec"), namespace, namespace)
        entrypoint = next(
            (namespace.get(name) for name in ("main", "execute", "run") if callable(namespace.get(name))),
            None,
        )
        if entrypoint is None:
            if "result" in namespace:
                result = namespace["result"]
            else:
                raise ValueError("function skill 需要定义 main(args) / execute(args) / run(args)")
        else:
            result = entrypoint(args)
    return result, stdout.getvalue().strip()


def _load_model(db: Session, model_ref: int | None) -> AiModel:
    model = None
    if model_ref:
        model = db.query(AiModel).filter(AiModel.id == model_ref, AiModel.status == 1).first()
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


def _openai_chat(base_url: str, api_key: str, model_id: str, message: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        url = normalized + "/chat/completions"
    else:
        url = normalized + "/v1/chat/completions"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "").strip()


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


def execute_skill(
    skill: AiSkill,
    args: dict[str, Any] | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    args = args or {}
    config = _normalize_config(skill)
    runtime = config["runtime"]
    response_cfg = config["response"]
    raw_cfg = config["raw"]

    function_code = _get_config_value(raw_cfg, "function_code")
    if skill.skill_type == 1 and isinstance(function_code, str) and function_code.strip():
        result, logs = _run_python_sandbox(function_code, args)
        return {
            "success": True,
            "skill_id": skill.id,
            "skill_name": skill.skill_name,
            "provider": "python",
            "request": {"args": args},
            "response": {"stdout": logs},
            "data": result,
        }

    if skill.skill_type == 2:
        skill_md = _extract_skill_md(raw_cfg)
        if not skill_md:
            raise ValueError("skill 类型缺少 SKILL.md 内容")
        if db is None:
            return {
                "success": True,
                "skill_id": skill.id,
                "skill_name": skill.skill_name,
                "provider": "skill",
                "request": {"args": args},
                "response": {"body": skill_md},
                "data": skill_md,
            }
        model = _load_model(db, skill.model_id)
        prompt = (
            "你正在执行一个 skill 技能包。请严格遵循 SKILL.md 的规则并结合输入完成任务。"
            "如果 SKILL.md 对输出格式有要求，请严格遵守。"
            "请直接返回可给用户展示的最终结果，不要输出分析过程。\n\n"
            f"SKILL.md 内容:\n{skill_md}\n\n"
            f"输入参数:\n{json.dumps(args, ensure_ascii=False, indent=2)}"
        )
        answer = _openai_chat(
            model.base_url,
            model.api_key,
            model.model_id,
            prompt,
        )
        return {
            "success": True,
            "skill_id": skill.id,
            "skill_name": skill.skill_name,
            "provider": "skill",
            "request": {"args": args},
            "response": {"model_id": model.model_id, "body": answer},
            "data": answer,
        }

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
