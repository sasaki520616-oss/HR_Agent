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

### 1.3 写操作申请与工单审批

`tools/write_ops.py` 当前提供两个写操作申请工具：

- `request_offboard`：提交员工离职申请。
- `request_update_info`：提交员工联系方式修改申请。

这两个工具调用 `submit_change_request()`，向 `change_requests` 表插入工单记录，并生成幂等键。它们的职责是**提交申请，不直接修改员工业务数据**。

`worker/execute_service.py` 是独立的人工审批执行脚本。当前实现会查询一次 `PENDING` 工单，逐条通过终端 `input()` 等待人工输入：

- 批准后，根据当前支持的动作执行员工状态或电话更新，并更新工单状态。
- 拒绝后，将工单状态更新为 `REJECTED`。
- 执行异常时回滚当前事务，并尝试将工单标记为 `FAILED`。

**当前 Worker 是一次性、交互式处理脚本，不是持续运行的后台轮询服务。** 当前代码也没有实现 Agent/Worker 使用不同数据库账号的读写权限隔离。

### 1.4 RAG 制度检索

当前 RAG 流程由 `rag/` 下的三个文件组成：

1. `build_index.py`：扫描文档目录，加载 PDF、Word、Markdown 文件；Markdown 先按标题切分，再使用递归切分器处理过长文本；其他文档使用递归切分器。
2. `embodding_sever.py`：通过 FastAPI 暴露兼容 OpenAI Embeddings 格式的 `/v1/embeddings` 接口，使用本地 BGE-M3 模型生成 dense 向量。
3. `policy_tool.py`：加载本地 FAISS 索引，根据问题执行相似度检索，可选按来源文件过滤，并返回检索文本及来源。

当前检索使用 `similarity_search_with_score()`，代码中没有实现 BM25 与向量检索的双路召回。当前 Embedding 服务只返回 BGE-M3 的 dense 向量。

## 2. 项目目录

```text
HR_Agent/
├── core/
│   └── agnet_v5.py             # LangGraph Agent 主程序
├── tools/
│   ├── read_ops.py             # MySQL 查询工具、部门统计、AST 计算器
│   ├── write_ops.py            # 写操作申请工具、工单创建
│   └── utils.py                # 数据库连接、员工重名处理
├── worker/
│   └── execute_service.py      # 人工审批及工单执行脚本
├── rag/
│   ├── build_index.py          # 文档加载、切分、向量化和 FAISS 索引构建
│   ├── embodding_sever.py      # BGE-M3 FastAPI Embedding 服务
│   └── policy_tool.py          # FAISS 制度检索工具
├── config.py                   # 环境变量和路径配置
├── system_prompt.md            # Agent 系统提示词
├── requirements.txt            # Python 依赖
└── README.md
```

注：`agnet.py` 和 `embodding_sever.py` 是当前仓库中的实际文件名，暂时保留原名，避免文档路径与代码不一致。

## 3. 环境配置

建议在项目根目录创建 `.env` 文件。下面是变量名称示例，请按自己的环境填写，不要将真实密钥提交到 Git 仓库。

```dotenv
# MySQL
DB_HOST=127.0.0.1
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_database
DB_CONN_TIMEOUT=5

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Embedding 服务客户端配置
EMBED_MODEL_NAME=bge-m3
EMBED_BASE_URL=http://127.0.0.1:8080/v1
EMBED_API_KEY=EMPTY

# RAG 路径及检索参数（相对于项目根目录）
RAG_DOCS_DIR=data/docs
RAG_INDEX_DIR=data/faiss_index
RAG_CHUNK_SIZE=600
RAG_CHUNK_OVERLAP=100
RAG_TOP_K=3
```

`config.py` 会读取上述变量。当前 `build_index.py` 中切片长度和重叠长度实际写为 `600` 和 `100`；虽然配置文件读取了 `RAG_CHUNK_SIZE`、`RAG_CHUNK_OVERLAP`，但当前构建脚本尚未使用这两个配置项。

## 4. 安装与运行

先创建并激活 Python 虚拟环境，再安装依赖：

```bash
pip install -r requirements.txt
```

运行前需要准备：

- 已创建并配置好项目使用的 MySQL 数据库及相关表。
- `.env` 中的数据库、DeepSeek 和 Embedding 配置正确。
- 本地 BGE-M3 模型文件可用。
- `rag/embodding_sever.py` 中的 `model_path` 当前是写死的 Windows 路径 `E:\rag-project\models\bge-m3`，在其他机器运行前需要改成实际模型路径。

建议按以下顺序操作：

**第一步：启动 Embedding 服务**

```bash
python -m rag.embodding_sever
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
python -m core.agnet_v5
```

输入问题即可进行交互，输入 `exit`、`quit` 或 `退出` 结束。

**第四步：处理待审批工单**

在另一个终端执行：

```bash
python -m worker.execute_service
```

当前脚本会读取当时已有的待审批工单，并在终端逐条询问是否批准。它不会持续监听新工单；有新申请时，需要再次运行脚本。

## 5. 当前未实现或需要完善的部分

以下内容属于后续规划，不应视为当前版本已经具备的功能：

- `tool_registry` 已废弃，当前 Agent 直接合并查询工具、写操作工具和 RAG 工具列表。
- 工资扣款申请工具尚未实现。
- Agent 与 Worker 的数据库读写权限隔离尚未实现；当前公共连接函数使用同一套 `DB_CONFIG`。
- Worker 尚未改造成持续运行的轮询服务，也没有实现并发抢单/任务锁机制。worker审批通过后agent直接修改sql表，需要再加一个人工审查修改是否正确，防止脏数据
- RAG 尚未实现 BM25 与向量检索双路召回及融合排序。
- `RAG_CHUNK_SIZE` 和 `RAG_CHUNK_OVERLAP` 配置尚未接入切片逻辑。
- Embedding 模型路径目前写死在 `embodding_sever.py` 中，尚未统一由配置管理。
- 当前仓库未包含数据库建表 SQL、自动化测试和独立评估脚本；部署时需要自行准备数据库结构并进行验证。
- FAISS 加载使用 `allow_dangerous_deserialization=True`，只应加载可信来源、自己构建的本地索引文件。

## 6. 安全与使用边界

- Agent 的写操作工具只负责创建工单，不应向用户声称业务数据已经修改。
- 当前人工审批脚本和 Agent 仍使用同一套数据库连接配置，因此不能将当前实现描述为数据库层面的读写权限隔离。
- 请勿将 `.env`、API Key、数据库密码、员工真实个人信息或未经脱敏的业务数据提交到公开仓库。
- 当前项目是学习和验证用途的实现。投入真实企业环境前，还需要完善权限隔离、审批身份认证、并发控制、审计日志、异常恢复和自动化测试。
