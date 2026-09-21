import ast
import json
import operator
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from openai import AsyncOpenAI, DefaultAsyncHttpxClient

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decrypt_secret
from app.models import User

MODELS = {
    "gpt-3.5-turbo": ("openai", "https://api.openai.com/v1"),
    "gpt-4o": ("openai", "https://api.openai.com/v1"),
    "gpt-5.6": ("openai", "https://api.openai.com/v1"),
    "deepseek-chat": ("deepseek", "https://api.deepseek.com"),
    "deepseek-v3": ("deepseek", "https://api.deepseek.com"),
    "deepseek-flash": ("deepseek", "https://api.deepseek.com"),
    "deepseek-v4-pro": ("deepseek", "https://api.deepseek.com"),
    "qwen-plus": ("qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
}


def client_for(user: User, model: str) -> tuple[AsyncOpenAI, str]:
    provider, base_url = MODELS.get(model, ("openai", "https://api.openai.com/v1"))
    encrypted = getattr(user, f"{provider}_api_key", None)
    key = decrypt_secret(encrypted)
    if not key:
        raise AppError(f"请先在设置页配置 {provider} API Key", 400, 400)
    actual_model = "deepseek-v4-pro" if model in {"deepseek-v3", "deepseek-chat"} else model
    return (
        AsyncOpenAI(
            api_key=key,
            base_url=base_url,
            http_client=DefaultAsyncHttpxClient(trust_env=False),
        ),
        actual_model,
    )


ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def calculate(expression: str):
    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPS:
            return ALLOWED_OPS[type(node.op)](evaluate(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPS:
            return ALLOWED_OPS[type(node.op)](evaluate(node.left), evaluate(node.right))
        raise ValueError("仅支持基础算术表达式")

    return evaluate(ast.parse(expression, mode="eval").body)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算基础数学表达式",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "查询指定时区当前时间",
            "parameters": {
                "type": "object",
                "properties": {"timezone": {"type": "string", "default": "Asia/Shanghai"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索网页获取最新信息",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


async def run_tool(name: str, args: dict):
    if name == "calculator":
        return str(calculate(args["expression"]))
    if name == "current_time":
        timezone_name = args.get("timezone") or "Asia/Shanghai"
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"无效时区：{timezone_name}") from exc
        return datetime.now(timezone).isoformat()
    if name == "web_search":
        if not settings.tavily_api_key:
            return "网页搜索未配置 TAVILY_API_KEY"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": settings.tavily_api_key, "query": args["query"], "max_results": 5},
            )
            response.raise_for_status()
            return json.dumps(response.json().get("results", []), ensure_ascii=False)
    return "未知工具"


async def stream_completion(
    user: User, model: str, messages: list[dict], enable_tools: bool = True
):
    client, actual_model = client_for(user, model)
    if enable_tools:
        first = await client.chat.completions.create(
            model=actual_model, messages=messages, tools=TOOLS, tool_choice="auto"
        )
        answer = first.choices[0].message
        if answer.tool_calls:
            messages.append(answer.model_dump(exclude_none=True))
            for call in answer.tool_calls:
                args = json.loads(call.function.arguments)
                yield {"type": "tool_start", "name": call.function.name, "input": args}
                output = await run_tool(call.function.name, args)
                yield {"type": "tool_end", "name": call.function.name, "output": output}
                messages.append({"role": "tool", "tool_call_id": call.id, "content": output})
    stream = await client.chat.completions.create(
        model=actual_model, messages=messages, stream=True
    )
    async for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        if text:
            yield {"type": "token", "content": text}
