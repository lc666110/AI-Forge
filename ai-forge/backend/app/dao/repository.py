from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, KnowledgeBase, Message


async def owned_conversation(
    db: AsyncSession, conversation_id: int, user_id: int
) -> Conversation | None:
    return await db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )


async def recent_messages(db: AsyncSession, conversation_id: int, limit: int = 20) -> list[Message]:
    rows = (
        await db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
    ).all()
    return list(reversed(rows))


async def owned_knowledge(
    db: AsyncSession, knowledge_id: int, user_id: int
) -> KnowledgeBase | None:
    return await db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_id, KnowledgeBase.user_id == user_id
        )
    )


async def delete_conversation(db: AsyncSession, conversation_id: int, user_id: int) -> bool:
    result = await db.execute(
        delete(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )
    await db.commit()
    return bool(result.rowcount)
