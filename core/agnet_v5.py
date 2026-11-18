import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from config import LLM_CONFIG
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage

from tools.read_ops import db_tools
from tools.write_ops import write_tools
from rag.policy_tool import search_policy
from tool_registry import wrap_tools_idempotent

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prompt_path = os.path.join(root_dir, "system_prompt.md")

# =============== 1. 初始化环境 =================
llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    api_key=LLM_CONFIG["api_key"],
    base_url=LLM_CONFIG["base_url"],
    temperature=0
)

# 把所有的工具（查询 + 提交工单）统一注册
all_tools = wrap_tools_idempotent(db_tools + write_tools + [search_policy])
llm_with_tools = llm.bind_tools(all_tools)


# ================= 2. 定义 State =================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ================== 3. 定义节点 ==================
def call_model(state: AgentState):
    messages_with_system = [SystemMessage(content=prompt_path)] + state["messages"]
    response = llm_with_tools.invoke(messages_with_system)
    return {"messages": [response]}


# ================= 4. 定义路由 =================
def route_after_agent(state: AgentState):
    last_msg = state["messages"][-1]
    # 如果模型没有调工具，直接结束当前轮
    if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return "end"

    # 如果有工具调用，直接去执行
    return "execute_tools"


# ================== 5. 建图 ===================
builder = StateGraph(AgentState)

builder.add_node("agent", call_model)
builder.add_node("execute_tools", ToolNode(all_tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "execute_tools": "execute_tools",
        "end": END
    }
)
builder.add_edge("execute_tools", "agent")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# ================= 6. 测试运行 =================
if __name__ == '__main__':
    config = {"configurable": {"thread_id": "user_001"}}

    while True:
        user_input = input("\n user: ")
        if user_input in ["退出", "exit", "quit"]:
            print("再见！")
            break

        inputs = {"messages": [HumanMessage(content=user_input)]}

        # 执行图
        for event in graph.stream(inputs, config=config, stream_mode="values"):
            last_msg = event["messages"][-1]

            # 👇 透视大模型的每一步
            print(f"\n--- [调试] 节点类型: {last_msg.type} ---")

            if last_msg.type == "ai":
                if last_msg.content:
                    print(f"Agent 回复: {last_msg.content}")
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    print(f"Agent 发起了工具调用: {last_msg.tool_calls}")
            elif last_msg.type == "tool":
                print(f"工具 {last_msg.name} 返回: {last_msg.content}")

            if last_msg.type == "ai" and last_msg.content:
                print(f"\n Agent: {last_msg.content}")

            # 只有没有工具调用且有大模型回复时，才打断
            if last_msg.type == "ai" and not getattr(last_msg, "tool_calls", None):
                break