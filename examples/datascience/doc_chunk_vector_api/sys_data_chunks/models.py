import hashlib
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.declarative import declarative_base

now = datetime.now
VEC_DIMENSIONS = 1024

BaseModel: type = declarative_base()


class DataStorageModel(BaseModel):
    """Chunck storage"""

    __tablename__ = "chunk_data_storage"
    __table_args__ = (
        UniqueConstraint(
            "document", "chunk_index", name="doc_chunk_constrain"
        ),
    )

    id = Column(PgUUID, default=uuid.uuid4, primary_key=True)
    document = Column(Unicode, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Unicode, nullable=False, default="")
    vec = Column(Vector(VEC_DIMENSIONS), nullable=True, default=None)
    created = Column(DateTime(timezone=False), default=now, nullable=False)
    filled = Column(DateTime(timezone=False), nullable=True, default=None)
    tags = Column(JSONB, default="[]", nullable=True)
