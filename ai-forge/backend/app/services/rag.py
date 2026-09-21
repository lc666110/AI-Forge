import io

from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, VectorStore
from app.services.ai import client_for


def extract_text(filename: str, content: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
    if name.endswith(".docx"):
        return "\n".join(p.text for p in DocxDocument(io.BytesIO(content)).paragraphs)
    if name.endswith((".txt", ".md", ".markdown")):
        return content.decode("utf-8", errors="ignore")
    raise ValueError("仅支持 PDF、DOCX、TXT、Markdown")


async def index_document(db: AsyncSession, user, document: Document, raw: bytes):
    text = extract_text(document.file_name, raw)
    chunks = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120).split_text(text)
    client, _ = client_for(user, "gpt-4o")
    for start in range(0, len(chunks), 50):
        batch = chunks[start : start + 50]
        vectors = await client.embeddings.create(model="text-embedding-3-small", input=batch)
        db.add_all(
            [
                VectorStore(
                    document_id=document.id,
                    content=chunk,
                    chunk_index=start + i,
                    embedding=vectors.data[i].embedding,
                )
                for i, chunk in enumerate(batch)
            ]
        )
    document.status = "ready"
    await db.commit()


async def retrieve(db: AsyncSession, user, knowledge_id: int, question: str, limit: int = 5):
    client, _ = client_for(user, "gpt-4o")
    embedding = (
        (await client.embeddings.create(model="text-embedding-3-small", input=[question]))
        .data[0]
        .embedding
    )
    distance = VectorStore.embedding.cosine_distance(embedding)
    rows = (
        await db.execute(
            select(VectorStore, Document)
            .join(Document)
            .where(Document.knowledge_base_id == knowledge_id)
            .order_by(distance)
            .limit(limit)
        )
    ).all()
    return [
        {"content": vector.content, "document": doc.file_name, "chunk": vector.chunk_index}
        for vector, doc in rows
    ]
