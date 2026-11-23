from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import Optional

from config import EMBED_CONFIG, RAG_CONFIG

BASE_DIR = Path(__file__).parent.parent
INDEX_DIR = BASE_DIR / RAG_CONFIG["index_dir"]

_embeddings = OpenAIEmbeddings(
    model=EMBED_CONFIG["model_name"],
    base_url=EMBED_CONFIG["base_url"],
    api_key=EMBED_CONFIG["api_key"],
    check_embedding_ctx_length=False
)

_vectorstore = FAISS.load_local(
    str(INDEX_DIR),
    _embeddings,
    allow_dangerous_deserialization=True
)


def search_policy(query: str, source_filter: Optional[str] = None) -> str:
    """检索公司制度文档（员工手册、考勤制度、报销规定等）。
    当用户询问公司规章制度、员工福利、考勤请假等问题时，必须调用此工具。

    Args:
        query: 用户关于公司制度的具体问题，尽量保留关键词。
        source_filter: 可选参数。如果用户明确指明了要查哪份文档，请传入文档名（例如："员工手册.md"）。
    """
    search_kwargs = {"k": RAG_CONFIG.get("top_k", 3)}
    if source_filter:
        search_kwargs["filter"] = {"source": source_filter}

    docs_with_scores = _vectorstore.similarity_search_with_score(query, **search_kwargs)

    if not docs_with_scores:
        return f"未检索到与 '{query}' 相关的制度。请直接告知用户暂无相关规定，严禁编造。"

    results = []
    for doc, score in docs_with_scores:
        source = doc.metadata.get("source", "未知文件")
        results.append(f"[来源: {source}]\n{doc.page_content}")

    return "\n\n---\n\n".join(results)