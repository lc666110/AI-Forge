from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    nickname: str = Field(default="AI Forge User", max_length=100)

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if (
            not any(c.isupper() for c in value)
            or not any(c.islower() for c in value)
            or not any(c.isdigit() for c in value)
        ):
            raise ValueError("密码必须包含大小写字母和数字")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    nickname: str
    role: str
    created_at: datetime


class KeySettings(BaseModel):
    openai_api_key: str | None = None
    deepseek_api_key: str | None = None
    qwen_api_key: str | None = None


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", max_length=200)
    model_type: str = "gpt-4o"


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ConversationModelUpdate(BaseModel):
    model_type: str

    @field_validator("model_type")
    @classmethod
    def supported_model(cls, value: str) -> str:
        if value not in {
            "gpt-3.5-turbo",
            "gpt-4o",
            "gpt-5.6",
            "deepseek-v3",
            "deepseek-chat",
            "deepseek-flash",
            "deepseek-v4-pro",
            "qwen-plus",
        }:
            raise ValueError("不支持的模型")
        return value


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    model_type: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    token_usage: int
    created_at: datetime


class ChatRequest(BaseModel):
    conversation_id: int
    content: str = Field(min_length=1, max_length=20000)
    enable_tools: bool = True


class KnowledgeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""


class KnowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    created_at: datetime


class RagChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20000)


def ok(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}
