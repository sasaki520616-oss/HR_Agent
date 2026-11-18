from pathlib import Path
from config import EMBED_CONFIG, RAG_CONFIG
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / RAG_CONFIG["docs_dir"]
INDEX_DIR = BASE_DIR / RAG_CONFIG["index_dir"]


# ================= 1. 智能加载器路由 =================
def load_documents_from_dir(directory: Path):
    docs = []
    if not directory.exists():
        print(f"目录不存在: {directory}")
        return docs

    for file_path in directory.glob("**/*"):
        if file_path.is_dir(): continue

        suffix = file_path.suffix.lower()
        try:
            if suffix == ".pdf":
                print(f"正在解析 PDF: {file_path.name}")
                loader = PyPDFLoader(str(file_path))
                docs.extend(loader.load())
            elif suffix in [".docx", ".doc"]:
                print(f"正在解析 Word: {file_path.name}")
                loader = UnstructuredWordDocumentLoader(str(file_path))
                docs.extend(loader.load())
            elif suffix == ".md":
                print(f"正在解析 Markdown: {file_path.name}")
                loader = TextLoader(str(file_path), encoding="utf-8")
                docs.extend(loader.load())
            else:
                print(f"跳过不支持的文件格式: {file_path.name}")
        except Exception as e:
            print(f"解析 {file_path.name} 失败: {e}")

    return docs


# ================= 2. 结构化与语义切片 =================
def split_documents(raw_docs):
    # A. 针对 Markdown 的结构化切分器
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
    )
    # B. 通用递归切分器（用于 PDF/Word，以及 MD 超长段落的兜底）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )

    final_chunks = []

    for doc in raw_docs:
        # 1. 强制提取纯净的文件名（去除绝对路径）作为元数据
        source_name = Path(doc.metadata.get("source", "未知文件")).name

        # 2. 判断如果是 Markdown，走结构化切分
        if source_name.endswith(".md"):
            # 把内容转给 Markdown 专用切分器
            header_splits = md_splitter.split_text(doc.page_content)
            for split in header_splits:
                split.metadata["source"] = source_name
                # 如果某一条还是太长，做二次切分
                chunks = text_splitter.split_documents([split])
                final_chunks.extend(chunks)

        # 3. 如果是 PDF 或 Word，走常规递归切分
        else:
            doc.metadata["source"] = source_name
            # PDF 往往会带很多换行，先做基础清理
            doc.page_content = doc.page_content.replace("\n\n", "\n").strip()
            chunks = text_splitter.split_documents([doc])
            final_chunks.extend(chunks)

    return final_chunks


# ================= 3. 主流程 =================
if __name__ == "__main__":
    print("开始扫描并加载文档...")
    raw_docs = load_documents_from_dir(DOCS_DIR)

    if not raw_docs:
        print("没有找到任何文档，退出。")
        exit(0)

    print(f"共加载 {len(raw_docs)} 页/篇原始文档，开始切片...")
    final_chunks = split_documents(raw_docs)
    print(f"切片完成，共生成 {len(final_chunks)} 个文本块。开始向量化...")

    # 连接本地 Embedding 服务
    embeddings = OpenAIEmbeddings(
        model=EMBED_CONFIG["model_name"],
        base_url=EMBED_CONFIG["base_url"],
        api_key=EMBED_CONFIG["api_key"],
        check_embedding_ctx_length=False
    )

    # 构建 FAISS 并保存
    vectorstore = FAISS.from_documents(final_chunks, embeddings)
    vectorstore.save_local(str(INDEX_DIR))
    print(f"索引构建完成！已保存至 {INDEX_DIR}")