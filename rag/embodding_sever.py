import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" # 防下载超时

from fastapi import FastAPI
from pydantic import BaseModel
from FlagEmbedding import BGEM3FlagModel
import uvicorn

app = FastAPI()
print("正在加载 BGE-M3，请稍候...")
model_path = r"E:\rag-project\models\bge-m3"
# 如果后续有了显卡，把 device 改成 'cuda'，use_fp16=True
model = BGEM3FlagModel(model_path, use_fp16=False, device='cpu')

class EmbeddingRequest(BaseModel):
    input: list[str]
    model: str = "bge-m3"

@app.post("/v1/embeddings")
def get_embeddings(req: EmbeddingRequest):
    # 只取稠密向量（Dense），最稳定且兼容性最强
    embeddings = model.encode(req.input, batch_size=12, max_length=8192)['dense_vecs']
    data = [{"object": "embedding", "embedding": emb.tolist(), "index": i} for i, emb in enumerate(embeddings)]
    return {"object": "list", "data": data, "model": req.model, "usage": {"total_tokens": 0}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)