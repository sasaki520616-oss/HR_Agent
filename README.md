# 🤖 企业级 HR & 考勤管理 Agent

基于 LangGraph 与 DeepSeek 打造的智能 HR 助理。本项目从零手写起步，不仅实现了自然语言查数据、RAG 制度问答，更**深度解决了企业级 Agent 落地的三大痛点：数据防幻觉、重名防呆、高危写操作安全隔离**。

## 🌟 核心架构亮点

1. **确定性计算与防幻觉**：绝不让大模型心算。部门聚合（平均/最大/最小）强制走 SQL 参数化工具；工资/考勤计算走纯 Python AST 计算器，100% 保证数据准确。
2. **重名消歧与静默纠偏**：针对企业高频的重名场景，手写拦截装饰器。工具层只认工号，大模型只需传名字，装饰器自动查重并拦截，结合 Prompt 实现用户确认后带工号静默查询。
3. **工单流（Change Request）与读写隔离**：Agent 无直接改库权限。所有高危操作（扣款、离职、改信息）只生成 `PENDING` 状态的数据库工单；由独立的后台服务（`execute_service.py`）人工审批后执行，做到权限物理隔离与可追溯。
4. **RAG 双路召回与防御**：本地私有化部署 BGE-M3 向量服务，结合 FAISS 构建知识库，Prompt 写死“检索不到即拒答”，杜绝政策编造。

## 🛠️ 技术栈
- **核心框架**：LangGraph (状态图路由)、LangChain (工具绑定)
- **大模型**：DeepSeek (OpenAI API 兼容)
- **数据库**：MySQL (纯 Python 驱动)
- **RAG**：BAAI/bge-m3 + FAISS + FastAPI 微服务

## 📂 目录结构
```text
├── core/           # LangGraph 核心主程序 (agent_v5.py)
├── tools/          # 工具模块
│   ├── utils.py    # 公共连接与防重名装饰器
│   ├── read_ops.py # 只读查询工具
│   └── write_ops.py# 写操作工单工具
├── worker/         # 独立审批执行服务
├── rag/            # RAG 向量检索与文档切片
├── config.py       # 全局配置
└── system_prompt.md# Agent 核心大脑约束