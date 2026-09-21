from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001_initial"; down_revision = None; branch_labels = None; depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("users", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("nickname", sa.String(100), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("openai_api_key", sa.Text()), sa.Column("deepseek_api_key", sa.Text()), sa.Column("qwen_api_key", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("conversations", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("model_type", sa.String(50), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table("messages", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("token_usage", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_table("knowledge_bases", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_knowledge_bases_user_id", "knowledge_bases", ["user_id"])
    op.create_table("documents", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("knowledge_base_id", sa.BigInteger(), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False), sa.Column("file_name", sa.String(255), nullable=False), sa.Column("file_size", sa.BigInteger(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_documents_knowledge_base_id", "documents", ["knowledge_base_id"])
    op.create_table("vector_store", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("chunk_index", sa.Integer(), nullable=False), sa.Column("embedding", Vector(1536), nullable=False))
    op.create_index("ix_vector_store_document_id", "vector_store", ["document_id"])

def downgrade():
    for table in ["vector_store", "documents", "knowledge_bases", "messages", "conversations", "users"]: op.drop_table(table)
