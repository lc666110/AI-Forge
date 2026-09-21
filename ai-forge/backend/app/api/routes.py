import json

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_user, current_user
from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import (
    create_token,
    decode_token,
    encrypt_secret,
    hash_password,
    verify_password,
)
from app.dao.repository import (
    delete_conversation,
    owned_conversation,
    owned_knowledge,
    recent_messages,
)
from app.models import Conversation, Document, KnowledgeBase, Message, User, VectorStore
from app.schemas.common import (
    ChatRequest,
    ConversationCreate,
    ConversationModelUpdate,
    ConversationUpdate,
    KeySettings,
    KnowledgeCreate,
    LoginRequest,
    RagChatRequest,
    RefreshRequest,
    RegisterRequest,
    UserOut,
    ok,
)
from app.services.ai import stream_completion
from app.services.rag import index_document, retrieve

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await db.scalar(select(User).where(User.email == body.email.lower())):
        raise AppError("邮箱已注册", 409, 409)
    user = User(
        email=body.email.lower(), password_hash=hash_password(body.password), nickname=body.nickname
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return ok(
        {
            "user": UserOut.model_validate(user).model_dump(mode="json"),
            "tokens": {
                "access_token": create_token(user.id),
                "refresh_token": create_token(user.id, "refresh"),
            },
        }
    )


@router.post("/auth/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise AppError("邮箱或密码错误", 401, 401)
    return ok(
        {
            "user": UserOut.model_validate(user).model_dump(mode="json"),
            "access_token": create_token(user.id),
            "refresh_token": create_token(user.id, "refresh"),
        }
    )


@router.post("/auth/refresh")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        user_id = decode_token(body.refresh_token, "refresh")
    except Exception:
        raise AppError("刷新令牌无效", 401, 401) from None
    if not await db.get(User, user_id):
        raise AppError("用户不存在", 401, 401)
    return ok(
        {"access_token": create_token(user_id), "refresh_token": create_token(user_id, "refresh")}
    )


@router.get("/users/me")
async def me(user: User = Depends(current_user)):
    return ok(UserOut.model_validate(user).model_dump(mode="json"))


@router.put("/users/me/keys")
async def save_keys(
    body: KeySettings, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    for name, value in body.model_dump().items():
        if value is not None:
            setattr(user, name, encrypt_secret(value))
    await db.commit()
    return ok(message="API Key 已加密保存")


@router.get("/conversations")
async def conversations(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
        )
    ).all()
    return ok(
        [
            {
                "id": x.id,
                "title": x.title,
                "model_type": x.model_type,
                "created_at": x.created_at,
                "updated_at": x.updated_at,
            }
            for x in rows
        ]
    )


@router.post("/conversations")
async def create_conversation(
    body: ConversationCreate, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    item = Conversation(user_id=user.id, **body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ok({"id": item.id, "title": item.title, "model_type": item.model_type})


@router.patch("/conversations/{conversation_id}")
async def rename_conversation(
    conversation_id: int,
    body: ConversationUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await owned_conversation(db, conversation_id, user.id)
    if not item:
        raise AppError("会话不存在", 404, 404)
    item.title = body.title
    await db.commit()
    return ok(message="已重命名")


@router.patch("/conversations/{conversation_id}/model")
async def change_model(
    conversation_id: int,
    body: ConversationModelUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await owned_conversation(db, conversation_id, user.id)
    if not item:
        raise AppError("会话不存在", 404, 404)
    item.model_type = body.model_type
    await db.commit()
    return ok(message="模型已切换")


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(
    conversation_id: int, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    if not await delete_conversation(db, conversation_id, user.id):
        raise AppError("会话不存在", 404, 404)
    return ok(message="已删除")


@router.get("/conversations/{conversation_id}/messages")
async def messages(
    conversation_id: int, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    if not await owned_conversation(db, conversation_id, user.id):
        raise AppError("会话不存在", 404, 404)
    rows = (
        await db.scalars(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
        )
    ).all()
    return ok(
        [
            {
                "id": x.id,
                "role": x.role,
                "content": x.content,
                "token_usage": x.token_usage,
                "created_at": x.created_at,
            }
            for x in rows
        ]
    )


@router.post("/chat/stream")
async def chat(
    body: ChatRequest, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    conversation = await owned_conversation(db, body.conversation_id, user.id)
    if not conversation:
        raise AppError("会话不存在", 404, 404)
    history = await recent_messages(db, conversation.id)
    db.add(Message(conversation_id=conversation.id, role="user", content=body.content))
    await db.commit()
    prompt = [{"role": x.role, "content": x.content} for x in history] + [
        {"role": "user", "content": body.content}
    ]

    async def events():
        full = ""
        try:
            async for event in stream_completion(
                user, conversation.model_type, prompt, body.enable_tools
            ):
                if event["type"] == "token":
                    full += event["content"]
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            db.add(Message(conversation_id=conversation.id, role="assistant", content=full))
            await db.commit()
            yield 'data: {"type":"done"}\n\n'
        except Exception as exc:
            yield f"data: {json.dumps({'type':'error','message':str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/knowledge-bases")
async def list_knowledge(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.scalars(
            select(KnowledgeBase)
            .where(KnowledgeBase.user_id == user.id)
            .order_by(KnowledgeBase.id.desc())
        )
    ).all()
    return ok(
        [
            {"id": x.id, "name": x.name, "description": x.description, "created_at": x.created_at}
            for x in rows
        ]
    )


@router.post("/knowledge-bases")
async def create_knowledge(
    body: KnowledgeCreate, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    item = KnowledgeBase(user_id=user.id, **body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ok({"id": item.id, "name": item.name, "description": item.description})


@router.post("/knowledge-bases/{knowledge_id}/documents")
async def upload_document(
    knowledge_id: int,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await owned_knowledge(db, knowledge_id, user.id):
        raise AppError("知识库不存在", 404, 404)
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise AppError("文件不能超过20MB")
    document = Document(
        knowledge_base_id=knowledge_id, file_name=file.filename or "unknown", file_size=len(raw)
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    try:
        await index_document(db, user, document, raw)
    except Exception:
        document.status = "failed"
        await db.commit()
        raise
    return ok({"id": document.id, "file_name": document.file_name, "status": document.status})


@router.post("/knowledge-bases/{knowledge_id}/chat/stream")
async def rag_chat(
    knowledge_id: int,
    body: RagChatRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await owned_knowledge(db, knowledge_id, user.id):
        raise AppError("知识库不存在", 404, 404)
    sources = await retrieve(db, user, knowledge_id, body.question)
    context = "\n\n".join(f"[{i+1}] {x['document']}: {x['content']}" for i, x in enumerate(sources))
    prompt = [
        {
            "role": "system",
            "content": "仅基于提供的资料回答。使用[1]格式标注引用；资料不足时明确说明。",
        },
        {"role": "user", "content": f"资料：\n{context}\n\n问题：{body.question}"},
    ]

    async def events():
        yield f"data: {json.dumps({'type':'sources','sources':sources}, ensure_ascii=False)}\n\n"
        async for event in stream_completion(user, "gpt-4o", prompt, False):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/admin/stats")
async def stats(_: User = Depends(admin_user), db: AsyncSession = Depends(get_db)):
    users = await db.scalar(select(func.count()).select_from(User))
    conversations = await db.scalar(select(func.count()).select_from(Conversation))
    knowledge = await db.scalar(select(func.count()).select_from(KnowledgeBase))
    vectors = await db.scalar(select(func.count()).select_from(VectorStore))
    return ok(
        {
            "users": users,
            "conversations": conversations,
            "knowledge_bases": knowledge,
            "vector_chunks": vectors,
        }
    )
