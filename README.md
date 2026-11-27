# HR_Agent：基于 LangGraph 的 HR 助手

这是一个使用 Python、MySQL、DeepSeek API、LangGraph 和 RAG 技术实现的 HR 助手练习项目。项目目前主要用于学习和验证 Agent 工具调用、员工信息查询、制度文档检索，以及通过工单提交和人工审批处理有限的写操作。

> **项目状态说明：** 本 README 按当前仓库代码整理。它区分了已经实现的功能和仍在规划中的功能，不把计划中的能力描述为现有能力。

## 1. 当前已实现的功能

### 1.1 Agent 主流程

- 使用 `ChatOpenAI` 接口调用 DeepSeek 兼容 API。
- 使用 LangGraph `StateGraph` 管理消息状态和执行流程。
- Agent 节点调用模型；模型产生工具调用时，路由到 `ToolNode` 执行工具；工具结果返回后再次进入 Agent 节点。
- 使用 `MemorySaver` 保存进程内的对话状态，并通过 `thread_id` 区分会话。
- 启动时读取 `system_prompt.md` 的正文作为 System Prompt。

### 1.2 MySQL 查询工具

`tools/read_ops.py` 当前注册的查询工具包括：

| 工具 | 用途 |
|---|---|
| `get_current_date` | 获取当前日期 |
| `get_employee_info` | 查询员工部门、岗位和直属领导 |
| `get_employee_contact` | 查询员工电话和邮箱 |
| `get_employee_age` | 查询员工年龄和工龄 |
| `get_department_members` | 查询部门在职员工名单，最多展示 20 人 |
| `get_employee_attendance` | 查询员工指定日期的考勤 |
| `get_employee_attendance_history` | 查询员工指定月份的考勤汇总 |
| `get_department_stats` | 查询部门人数、平均/最大/最小年龄、平均工龄和性别分布 |
| `calculate` | 使用 AST 白名单节点进行基础算术计算 |

部分按姓名查询的员工工具使用 `handle_multiple_matches` 装饰器：先按姓名查找员工；出现重名时返回候选信息；唯一匹配时将工号传给原查询函数。

部门统计由 SQL 聚合完成，不要求模型读取名单后自行计算。部门名单查询使用 `LIMIT 21` 判断是否超过展示上限，并最多返回 20 条。

### 1.3 写操作申请与人工审批系统 (HITL)

`tools/write_ops.py` 提供写操作申请工具（`request_offboard`、`request_update_phone`）。Agent 调用这些工具时**不会直接修改业务表**，而是通过 `submit_change_request()` 生成一条 `PENDING` 状态的工单插入 `change_requests` 表。在插入前，系统会抓取当前数据的 `old_data` 快照，并生成 `idempotency_key` 防重复提交。

工单审批与执行采用**基于状态机的双端解耦架构**（`worker/` 目录）：
当前的设计将“Agent 端申请”与“Worker 端执行”通过字典注册表（策略模式）解耦。这种设计带来了极高的隔离性，但代价是新增一个写操作工具需要同时修改两处代码： 
- 1.在 tools/write_ops.py 中新增提交工单的 @tool 函数。
- 2.在 worker/db_handlers.py 中新增对应的 SQL 执行逻辑，并注册到 action_handlers 字典中。
(未来优化方向：可将具体执行的 SQL 或目标表信息作为元数据直接写在工单的 payload 中，由执行端实现通用的数据变更逻辑，从而免去 Worker 端的代码修改。)

- **审批端 (`worker/review_service.py`)**：常驻轮询 `PENDING` 或 `HOLD` 工单（每次 `LIMIT 10` 遍历）。终端展示原数据快照与目标修改对比，支持操作：(y) 批准、(n) 拒绝、(p) 挂起(HOLD)。审批端仅负责状态流转，不执行具体 SQL。
- **执行端 (`worker/execute_service.py`)**：常驻轮询 `APPROVED` 工单。通过 `UPDATE ... WHERE status = 'APPROVED'` 实现**乐观锁抢单防并发**。执行逻辑通过 `worker/db_handlers.py` 中的**字典注册表（策略模式）**解耦调用，避免 `if/elif` 冗长分支。执行后校验 `cur.rowcount` 防止目标不存在或未更新却标记成功的伪逻辑。成功标记 `EXECUTED`，异常则回滚并标记 `FAILED`。


### 1.4 RAG 制度检索

当前 RAG 流程由 `rag/` 下的三个文件组成：

1. `build_index.py`：扫描文档目录，加载 PDF、Word、Markdown 文件；Markdown 先按标题切分，再使用递归切分器处理过长文本；其他文档使用递归切分器。
2. `embedding_server.py`：通过 FastAPI 暴露兼容 OpenAI Embeddings 格式的 `/v1/embeddings` 接口，使用本地 BGE-M3 模型生成 dense 向量。
3. `policy_tool.py`：加载本地 FAISS 索引，根据问题执行相似度检索，可选按来源文件过滤，并返回检索文本及来源。

当前检索使用 `similarity_search_with_score()`，代码中没有实现 BM25 与向量检索的双路召回。当前 Embedding 服务只返回 BGE-M3 的 dense 向量。

### 1.5 工具测试

当前测试流程由 `tests/` 下的两个文件组成：

1. `test_rag.py`：验证向量检索能否召回正确的制度文档，以及验证**相似度阈值过滤（Threshold Filtering）**能否成功拦截无关问题。
2. `test_tools.py`：验证 MySQL 查询工具的正确性、重名处理逻辑、防注入截断逻辑，以及 AST 安全求值的恶意代码拦截。


## 2. 项目目录

```text
HR_Agent/
├── core/
│   └── agent.py             # LangGraph Agent 主程序
├── tests/
│   ├── test_rag.py             # RAG 检索层测试
│   └── test_tools.py           # 工具层测试
├── tools/
│   ├── read_ops.py             # MySQL 查询工具、部门统计、AST 计算器
│   ├── write_ops.py            # 写操作申请工具、工单创建
│   └── utils.py                # 数据库连接、员工重名处理
├── worker/
│   ├── review_service.py       # 人工审批终端（状态流转，支持 HOLD 挂起）
│   ├── execute_service.py      # 后台执行器（乐观锁抢单，事务更新）
│   └── db_handlers.py          # 策略模式处理函数（具体业务 SQL 隔离）
├── rag/
│   ├── build_index.py          # 文档加载、切分、向量化和 FAISS 索引构建
│   ├── embedding_server.py     # BGE-M3 FastAPI Embedding 服务
│   └── policy_tool.py          # FAISS 制度检索工具
├── config.py                   # 环境变量和路径配置
├── system_prompt.md            # Agent 系统提示词
├── requirements.txt            # Python 依赖
└── README.md
```

## 3. 环境配置

建议在项目根目录创建 `.env` 文件。下面是变量名称示例，请按自己的环境填写，不要将真实密钥提交到 Git 仓库。

```dotenv
# 1. MySQL配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=your_database
DB_CONN_TIMEOUT=5

# 1.1 Agent 只读账号
AGENT_DB_USER=your_db_user
AGENT_DB_PASSWORD=your_db_password

# 1.2 Worker 管理账号
WORKER_DB_USER=your_db_user
WORKER_DB_PASSWORD=your_db_password

# 2. DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 3. Embedding 服务客户端配置
EMBED_MODEL_NAME=bge-m3
EMBED_BASE_URL=http://127.0.0.1:8080/v1
EMBED_API_KEY=EMPTY

# 4. RAG 路径及检索参数
RAG_DOCS_DIR=data/docs
RAG_INDEX_DIR=data/faiss_index
RAG_CHUNK_SIZE=600
RAG_CHUNK_OVERLAP=100
RAG_TOP_K=3
```

## 4. 安装与运行

先创建并激活 Python 虚拟环境，再安装依赖：

```bash
python -3.11 -m venv .venv
pip install -r requirements.txt
```

运行前需要准备：

- 运行前请先执行 init.sql 创建表结构,并配置好项目使用的 MySQL 数据库及相关表。
- `.env` 中的数据库、DeepSeek 和 Embedding 配置正确。
- 本地 BGE-M3 模型文件可用。

建议按以下顺序操作：

**第一步：启动 Embedding 服务**

```bash
python -m rag.embedding_server
```

服务默认监听 `0.0.0.0:8080`，Embedding 客户端配置的 API 地址应与实际服务地址对应。

**第二步：构建 FAISS 索引**

将支持的制度文件放入 `RAG_DOCS_DIR` 指定的目录，然后执行：

```bash
python -m rag.build_index
```

构建完成后，索引保存到 `RAG_INDEX_DIR` 指定的位置。Agent 启动时会在导入 `policy_tool.py` 时加载该索引，因此首次运行 Agent 前应先完成索引构建。

**第三步：启动 Agent**

```bash
python -m core.agent
```

输入问题即可进行交互，输入 `exit`、`quit` 或 `退出` 结束。

**第四步：处理待审批工单**

在另外两个终端分别执行（按需启动）：

```bash
python -m worker.review_service
python -m worker.execute_service
```

**第五步：工具测试**
```bash
python -m tests.test_tools
python -m tests.test_rag
```

## 5. 当前未实现或需要完善的部分

以下内容属于后续规划，不应视为当前版本已经具备的功能：
- **HOLD 状态的长期死锁风险**：若员工一直不处理 HOLD 工单，系统不会自动清理。后续可增加 `review_count` 字段，超限时自动流转或告警。
- **审批交互终端化**：当前审批仅在终端进行 `input()` 交互，尚未接入 Web UI 或企业微信/飞书审批卡片，未来可做异步通知改造。
- **RAG** 尚未实现 BM25 与向量检索双路召回及融合排序。
- **MemorySaver** 是存在于内存的短期记忆模块，并发能力差，可能导致内存爆炸，未实现持久化存储机制。
- **FAISS** 加载使用 `allow_dangerous_deserialization=True`，只应加载可信来源、自己构建的本地索引文件。

## 6. 安全与使用边界

- **最小权限隔离**：Agent 数据库账号仅拥有 `SELECT` 和 `INSERT` 权限，无法直接修改业务表数据；后台 Worker 拥有修改权限，仅通过安全流转的工单执行变更。
- **数据审计与快照**：提交修改申请时自动留存 `old_data` 原数据快照，审批端可直观对比修改前后差异，避免误批，也为未来实现“一键回滚”提供数据基础。
- **并发与防重防御**：写操作使用 `idempotency_key` 幂等键防止大模型重复提交；执行端基于数据库乐观锁（状态流转校验）实现防并发抢单，防止多进程重复消费。
- **数据与隐私保护**：请勿将 `.env`、API Key、数据库密码、员工真实个人信息或未经脱敏的业务数据提交到公开仓库。
- **边界说明**：当前项目为学习和验证用途，虽已实现基础的状态机与并发防御，但投入真实企业环境前，仍需完善审批身份认证（如 SSO）、分布式锁（如 Redis）、审计日志落库及自动化集成测试。