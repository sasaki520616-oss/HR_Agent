import os
from dotenv import load_dotenv, find_dotenv

# 1. 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_INDEX_DIR = os.path.join(BASE_DIR, "data", "faiss_index")  # FAISS索引路径
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")                # 文档路径
SYSTEM_PROMPT_PATH = os.path.join(BASE_DIR, "system_prompt.md")  # 系统提示词

load_dotenv(find_dotenv())  # 其他环境配置


# 2. 数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "connection_timeout": int(os.getenv("DB_CONN_TIMEOUT", 5)) # 超时
}

if not DB_CONFIG["password"]:
    raise ValueError(
        f"找不到数据库密码。当前配置：DB_HOST={DB_CONFIG['host']},"
        f"DB_USER={DB_CONFIG['user']},DB_NAME={DB_CONFIG['database']},"
    )

# 3. 大模型配置
LLM_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY"),
    "base_url": os.getenv("DEEPSEEK_BASE_URL"),
    "model": os.getenv("DEEPSEEK_MODEL")
}

# 4. RAG 与 Embedding 配置
EMBED_CONFIG = {
    "model_name": os.getenv("EMBED_MODEL_NAME"),
    "base_url": os.getenv("EMBED_BASE_URL"),
    "api_key": os.getenv("EMBED_API_KEY")
}

RAG_CONFIG = {
    "docs_dir": os.getenv("RAG_DOCS_DIR"),
    "index_dir": os.getenv("RAG_INDEX_DIR"),
    "chunk_size": int(os.getenv("RAG_CHUNK_SIZE")),
    "chunk_overlap": int(os.getenv("RAG_CHUNK_OVERLAP")),
    "top_k": int(os.getenv("RAG_TOP_K"))
}