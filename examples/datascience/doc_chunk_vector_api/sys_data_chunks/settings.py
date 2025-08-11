from pydantic import Field
from pydantic_settings.main import BaseSettings

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv("dev.env")


class ServerSettings(BaseSettings):
    pool_size: int = Field(env="PARALLEL_REQUESTS", default=8)
    pool_class: str = Field(env="POOL_CLASS", default="concurrent.futures.ThreadPoolExecutor")
    wait_limit: float = Field(env="WAIT_LIMIT", default=50)
    chunk_size: int = Field(env="CHUNK_SIZE_LIMIT", default=160)
    db_connection: str = Field(env="DB_CONNECTION", default="")
    model_name: str = Field(env="MODEL_NAME", default="ai-forever/ru-en-RoSBERTa")
    sql_debug: bool = Field(env="SQL_DEBUG", default=False)
    debug_use: bool = Field(env="DEBUG", default=False)
    tolerance: int = Field(env="TOLERANCE_CHUNK_SIZE_DIFF", default=10)  # 10% default
    source_doc_label: str = Field(env="SOURCE_DOC_LABEL", default="Source article:")
