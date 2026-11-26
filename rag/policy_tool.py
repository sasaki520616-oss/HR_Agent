from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool

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


@tool
def search_policy(query: str) -> str:
    """..."""
    search_kwargs = {"k": RAG_CONFIG.get("top_k", 3)}
    docs_with_scores = _vectorstore.similarity_search_with_score(query, **search_kwargs)

    if not docs_with_scores:
        return f"未检索到与 '{query}' 相关的制度..."

    THRESHOLD = 0.6

    valid_docs = []
    for doc, score in docs_with_scores:
        if score < THRESHOLD:
            valid_docs.append(doc)

    if not valid_docs:
        return f"知识库中未找到与 '{query}' 相关的公司制度。请直接告知用户无法回答，严禁编造。"

    results = []
    for doc in valid_docs:
        source = doc.metadata.get("source", "未知文件")
        results.append(f"[来源: {source}]\n{doc.page_content}")

    return "\n\n---\n\n".join(results)