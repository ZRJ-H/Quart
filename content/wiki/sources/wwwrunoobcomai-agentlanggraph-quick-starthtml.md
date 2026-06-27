---
type: source
title: "LangGraph 入门教程"
source_type: tutorial
url: https://www.runoob.com/ai-agent/langgraph-quick-start.html
date_accessed: 2026-06-05
tags: [tutorial, runoob, ai-agent]
---

# LangGraph 入门教程

## 基本信息
- **来源**: 菜鸟教程
- **URL**: https://www.runoob.com/ai-agent/langgraph-quick-start.html
- **采集日期**: 2026-06-05
- **章节数**: 2

## 目录
- 概述
- AI Agent(智能体) 教程

---

## 概述

# LangGraph 入门教程

LangGraph 是由 LangChain 团队开发的一个
低层级 Agent 编排框架
，专为构建有状态（Stateful）、长时运行的 AI 工作流而设计。

与传统的线性 LLM 调用链不同，LangGraph 将工作流建模为
有向图（Directed Graph）
：

- 节点（Node）
：执行具体操作的函数（如调用 LLM、执行工具、处理数据）
- 边（Edge）
：定义节点之间的流转路径，支持条件分支
- 状态（State）
：在整个工作流中共享并传递的数据
开源地址：
https://github.com/langchain-ai/langgraph
。

> 想象你正在指挥一场交响乐演出：传统的 LLM Chain 就像演奏一首从头到尾的曲子，只能顺序播放；而 LangGraph 则像一位指挥家，可以根据现场观众的反应随时调整演奏顺序，让某个乐章重复，或者跳转到特定段落。它让 AI 工作流拥有了"指挥"的智慧——能够循环、分支、回溯，真正实现复杂的自主决策。

想象你正在指挥一场交响乐演出：传统的 LLM Chain 就像演奏一首从头到尾的曲子，只能顺序播放；而 LangGraph 则像一位指挥家，可以根据现场观众的反应随时调整演奏顺序，让某个乐章重复，或者跳转到特定段落。它让 AI 工作流拥有了"指挥"的智慧——能够循环、分支、回溯，真正实现复杂的自主决策。

### 为什么选择 LangGraph？

下表对比了传统 LLM Chain 与 LangGraph 的主要差异：

特性 | 传统 LLM Chain | LangGraph
工作流结构 | 线性，单向执行 | 图结构，支持循环
状态管理 | 需手动管理 | 内置状态持久化
条件路由 | 实现复杂 | 原生支持
人机协作 | 需要额外开发 | 内置支持 interrupt
多 Agent 协调 | 实现困难 | 一流支持
调试工具 | 有限 | LangGraph Studio

### 适用场景

- 对话机器人
：需要记忆多轮对话上下文
- 自主 Agent
：能够规划、使用工具、迭代思考
- 多 Agent 系统
：多个 AI 协同完成复杂任务
- 审批工作流
：需要人工审核的自动化流程
- 研究助手
：需要多步骤推理和信息检索

## 核心概念

在开始编写代码之前，先理解 LangGraph 的三大核心概念。

### Graph（图）

Graph 是整个工作流的蓝图，定义了 Agent 的完整逻辑结构。它由节点（Nodes）和边（Edges）组成：

```
StateGraph
   |-- Nodes（节点）
   |     |-- node_a
   |     |-- node_b
   |     +-- node_c
   +-- Edges（边）
         |-- START -> node_a
         |-- node_a -> node_b（条件边）
         |-- node_a -> node_c（条件边）
         +-- node_b -> END
```

### State（状态）

State 是贯穿整个图的
共享数据结构
。每个节点可以读取和更新 State，更新后的 State 会传递给下一个节点。

```
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class MyState(TypedDict):
    messages: Annotated[list, add_messages]  # 消息列表（自动追加）
    user_name: str                            # 用户名称
    step_count: int                           # 步骤计数
```

`Annotated[list, add_messages]`
`add_messages`

### Nodes（节点）

节点是普通的 Python 函数，接收当前 State，返回更新后的 State（部分字段）。

```
def my_node(state: MyState) -> dict:
    # 读取状态
    messages = state["messages"]
    
    # 执行操作...
    result = "处理结果"
    
    # 返回更新的字段（不需要返回所有字段）
    return {"messages": [{"role": "ai", "content": result}]}
```

### Edges（边）

边定义节点之间的流转方式：

- 普通边
：固定路径，
node_a -> node_b
`node_a -> node_b`
- 条件边
：根据 State 动态路由，
node_a -> node_b 或 node_c
`node_a -> node_b 或 node_c`
- 起始边
：
START -> 第一个节点
`START -> 第一个节点`
- 结束边
：
某节点 -> END
`某节点 -> END`

## 环境搭建

### 安装依赖

使用国内镜像安装 LangGraph 和相关依赖：

```
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows

# 安装 LangGraph 和 LangChain
pip install langgraph langchain langchain-openai python-dotenv -i https://mirrors.aliyun.com/pypi/simple/

# 可选：安装开发工具
pip install langgraph-cli jupyter -i https://mirrors.aliyun.com/pypi/simple/
```

### 配置 API Key

在项目根目录创建
.env
文件，同时配置 OpenAI 和 DeepSeek：

`.env`
```
# .env 文件内容

# OpenAI 配置（国外用户）
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek 配置（国内用户推荐）
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

`https://api.deepseek.com`

### 验证安装

```
import langgraph
print(f"LangGraph 版本: {langgraph.__version__}")
```

## 第一个 LangGraph 程序

让我们从最简单的例子开始——一个只有两个节点的线性工作流。

## 实例

运行结果：

```
[greet_node] 收到消息: 世界
[process_node] 处理消息: 你好！世界

最终结果: {'message': '你好！世界', 'processed': True}
```

### 可视化图结构

在 Jupyter Notebook 中可以直接可视化图结构：

```
# 在 Jupyter Notebook 中可视化
from IPython.display import Image
Image(graph.get_graph().draw_mermaid_png())

# 或者打印 Mermaid 格式
print(graph.get_graph().draw_mermaid())
```

## State 状态管理

### 使用 TypedDict 定义状态

```
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 消息历史（add_messages reducer 自动追加而非覆盖）
    messages: Annotated[list, add_messages]
    
    # 普通字段（直接覆盖）
    user_id: str
    session_id: str
    
    # 可选字段
    error: Optional[str]
    
    # 计数器（使用 operator.add 作为 reducer）
    retry_count: Annotated[int, lambda x, y: x + y]
```

### 使用 Pydantic 定义状态（推荐用于生产）

```
from pydantic import BaseModel, Field
from typing import Annotated
from langgraph.graph.message import add_messages

class ProductionState(BaseModel):
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    user_id: str = ""
    confidence_score: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True
```

### MessagesState（内置快捷状态）

LangGraph 提供了内置的
MessagesState
，专为对话场景设计：

`MessagesState`
```
from langgraph.graph import MessagesState

# MessagesState 等价于:
# class MessagesState(TypedDict):
#     messages: Annotated[list[AnyMessage], add_messages]

# 直接使用，无需自定义
builder = StateGraph(MessagesState)
```

## Nodes 节点

### 普通函数节点

```
def simple_node(state: AgentState) -> dict:
    # 读取状态
    last_message = state["messages"][-1]
    
    # 执行操作
    response = f"收到: {last_message.content}"
    
    # 返回部分状态更新
    return {
        "messages": [{"role": "assistant", "content": response}]
    }
```

### LLM 调用节点

## 实例

### 异步节点

```
import asyncio

async def async_node(state: AgentState) -> dict:
    """异步节点，适合 I/O 密集型操作"""
    # 模拟异步操作（如 API 调用、数据库查询）
    await asyncio.sleep(0.1)
    
    result = await some_async_api_call(state["messages"][-1].content)
    return {"messages": [{"role": "assistant", "content": result}]}

# 使用异步图
result = await graph.ainvoke({"messages": [...]})
```

### 使用类作为节点

```
class RouterNode:
    def __init__(self, llm, system_prompt: str):
        self.llm = llm
        self.system_prompt = system_prompt
    
    def __call__(self, state: AgentState) -> dict:
        """类实例可以作为节点使用"""
        messages = [
            SystemMessage(content=self.system_prompt),
            *state["messages"]
        ]
        response = self.llm.invoke(messages)
        return {"messages": [response]}

# 添加类节点
router = RouterNode(llm, "你是一个专业的路由助手。")
builder.add_node("router", router)
```

## Edges 边与条件路由

### 普通边

```
# 固定路径：node_a 完成后始终执行 node_b
builder.add_edge("node_a", "node_b")

# 结束：node_a 完成后图结束
builder.add_edge("node_a", END)
```

### 条件边

条件边是 LangGraph 的核心功能，根据当前 State 动态决定下一步。

```
def route_after_llm(state: AgentState) -> str:
    """
    路由函数：根据 LLM 的最新输出决定走哪条路径
    返回值必须是已注册节点名称或 END
    """
    last_message = state["messages"][-1]
    
    # 如果 LLM 请求使用工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # 否则结束
    return END

# 添加条件边
builder.add_conditional_edges(
    "llm",              # 源节点
    route_after_llm,    # 路由函数
    {
        "tools": "tool_executor",   # 返回 "tools" 时 -> tool_executor 节点
        END: END                    # 返回 END 时 -> 结束
    }
)
```

### 并行执行（Fan-out）

```
# 从一个节点并行分叉到多个节点
builder.add_edge("start_node", "branch_a")
builder.add_edge("start_node", "branch_b")
builder.add_edge("start_node", "branch_c")

# 多个节点汇聚到一个节点（Fan-in）
builder.add_edge("branch_a", "merge_node")
builder.add_edge("branch_b", "merge_node")
builder.add_edge("branch_c", "merge_node")
```

### 完整条件路由示例

## 实例

运行结果示例：

```
用户: 北京今天天气怎么样？
助手: 很抱歉，我没有实时天气数据。不过北京现在是春季，建议您出门时关注天气预报...
--------------------------------------------------

用户: 帮我写一个 Python 快速排序
助手: 好的，下面是一个 Python 实现的快速排序算法：

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    ...
--------------------------------------------------

用户: 你好，介绍一下你自己
助手: 你好！我是一个 AI 助手，很高兴为你服务。我可以帮你回答各种问题...
--------------------------------------------------

用户: 再见啦！
助手: 再见！期待下次与你交流。
--------------------------------------------------
```

`END`

## 构建对话机器人

现在用所学知识构建一个支持多轮对话的机器人。这个机器人能够记住对话上下文，实现连续的交互体验。

## 实例

运行结果示例：

```
你: 你好，我叫小明
助手: 你好，小明！很高兴认识你。有什么我可以帮助你的吗？

你: 我想学习 Python 编程
助手: 太好了！Python 是一门很适合初学者的编程语言。我可以帮你从基础开始：
1. 首先了解变量和数据类型
2. 学习条件语句和循环
3. 掌握函数的定义和使用
你想从哪个部分开始呢？

你: 你还记得我叫什么吗？
助手: 当然记得，你叫小明！你刚才说想学习 Python 编程，我们可以继续这个话题。

你: 退出
再见！
```

## 工具调用 - ReAct Agent

让 Agent 具备使用外部工具的能力是 LangGraph 最强大的特性之一。
ReAct
（Reason + Act）是最常见的 Agent 模式：LLM 思考 -> 选择工具 -> 执行工具 -> 观察结果 -> 继续思考。

### 定义工具

首先定义 Agent 可以使用的工具：

```
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """搜索网络获取最新信息。
    
    Args:
        query: 搜索关键词
    
    Returns:
        搜索结果摘要
    """
    # 实际项目中替换为真实搜索 API
    return f"关于 '{query}' 的搜索结果：这是模拟的搜索结果..."

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。
    
    Args:
        expression: 数学表达式，如 '2 + 2' 或 '100 * 0.8'
    
    Returns:
        计算结果
    """
    import ast
    import operator
    
    # 安全的运算符映射
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    def safe_eval(node):
        if isinstance(node, ast.Expression):
            return safe_eval(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            return ops[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = safe_eval(node.operand)
            return ops[type(node.op)](operand)
        else:
            raise ValueError(f"不支持的表达式类型: {type(node)}")
    
    try:
        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。
    
    Args:
        city: 城市名称
    
    Returns:
        天气信息
    """
    # 实际项目中替换为真实天气 API
    return f"{city} 今日天气：晴，温度 22C，湿度 60%"

tools = [search_web, calculate, get_weather]
```

`eval()`
`eval()`

### 构建 ReAct Agent

## 实例

### 流式输出工具调用过程

```
# 流式观察 Agent 的每一步
for chunk in graph.stream(
    {"messages": [HumanMessage(content="搜索 LangGraph 的最新特性")]},
    stream_mode="updates"
):
    for node_name, updates in chunk.items():
        print(f"\n=== 节点: {node_name} ===")
        for msg in updates.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"  -> 调用工具: {tc['name']}({tc['args']})")
            else:
                print(f"  -> 输出: {msg.content[:200] if msg.content else '(无内容)'}")
```

`ToolNode`
`tools_condition`
`ToolNode`
`tools_condition`

## Human-in-the-Loop 人机协作

LangGraph 原生支持在工作流执行过程中暂停，等待人工审核或输入。这对于需要人工确认的敏感操作非常有用。

### 使用 interrupt 暂停执行

```
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver

def sensitive_action_node(state: MessagesState) -> dict:
    """执行敏感操作前请求人工审批"""
    last_msg = state["messages"][-1].content
    
    # 暂停图的执行，等待人工决策
    human_decision = interrupt({
        "question": "是否批准执行以下操作？",
        "action": last_msg,
        "risk_level": "中等"
    })
    
    if human_decision == "approve":
        return {"messages": [{"role": "assistant", "content": "操作已批准并执行完毕。"}]}
    else:
        return {"messages": [{"role": "assistant", "content": "操作已取消。"}]}

# 必须使用 checkpointer 才能支持 interrupt
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

### 完整的审批工作流

## 实例

### 在边上设置断点

```
# 另一种方式：在编译时指定断点
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["sensitive_node"],   # 执行该节点前暂停
    # interrupt_after=["review_node"],     # 执行该节点后暂停
)
```

`checkpointer`
`interrupt`

## 持久化内存

LangGraph 提供了内置的状态持久化机制，让 Agent 能够跨会话记住对话历史。

### 内存存储（适合开发测试）

```
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 使用 thread_id 区分不同会话
config_user_a = {"configurable": {"thread_id": "user-alice"}}
config_user_b = {"configurable": {"thread_id": "user-bob"}}

# Alice 的对话
graph.invoke({"messages": [HumanMessage(content="我叫 Alice")]}, config=config_user_a)
graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config=config_user_a)
# Agent 能记住：你叫 Alice

# Bob 的对话完全独立
graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config=config_user_b)
# Agent 不知道 Bob 的名字（不同 thread_id）
```

### SQLite 持久化存储（适合本地项目）

```
# 安装依赖
# pip install langgraph-checkpoint-sqlite

from langgraph.checkpoint.sqlite import SqliteSaver

# 数据持久化到文件，程序重启后对话历史仍存在
with SqliteSaver.from_conn_string("./chat_memory.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": "persistent-chat"}}
    
    # 第一次运行
    graph.invoke({"messages": [HumanMessage(content="我叫张三")]}, config=config)
    
    # 程序重启后再次运行，记忆仍然存在
    result = graph.invoke(
        {"messages": [HumanMessage(content="你还记得我叫什么吗？")]},
        config=config
    )
```

### 查看对话历史

```
# 获取某个 thread 的完整状态历史
history = list(graph.get_state_history(config))

for snapshot in history:
    print(f"时间: {snapshot.created_at}")
    print(f"消息数: {len(snapshot.values['messages'])}")
    print("---")

# 获取当前状态
current_state = graph.get_state(config)
print(f"当前消息数: {len(current_state.values['messages'])}")
```

`thread_id`

## 多 Agent 系统

LangGraph 擅长协调多个专门化的 Agent 协同工作。通过将复杂任务分解给不同的专家 Agent，可以实现更强大的问题解决能力。

### 主从架构（Supervisor Pattern）

## 实例

### 子图（Subgraph）

将复杂子流程封装为子图，在主图中复用：

```
# 将复杂子流程封装为子图，在主图中复用
sub_builder = StateGraph(MessagesState)
sub_builder.add_node("step1", step1_node)
sub_builder.add_node("step2", step2_node)
sub_builder.add_edge(START, "step1")
sub_builder.add_edge("step1", "step2")
sub_builder.add_edge("step2", END)
sub_graph = sub_builder.compile()

# 在主图中使用子图
main_builder = StateGraph(MessagesState)
main_builder.add_node("preprocessing", preprocess_node)
main_builder.add_node("sub_workflow", sub_graph)  # 直接使用编译好的子图
main_builder.add_node("postprocessing", postprocess_node)

main_builder.add_edge(START, "preprocessing")
main_builder.add_edge("preprocessing", "sub_workflow")
main_builder.add_edge("sub_workflow", "postprocessing")
main_builder.add_edge("postprocessing", END)

main_graph = main_builder.compile()
```

## LangGraph Studio 可视化调试

LangGraph Studio 是官方提供的可视化开发环境，让你实时查看 Agent 的执行过程，大幅提升开发和调试效率。

### 安装 LangGraph CLI

```
pip install langgraph-cli -i https://mirrors.aliyun.com/pypi/simple/
```

### 创建项目配置文件

在项目根目录创建
langgraph.json
配置文件：

`langgraph.json`
```
{
  "dependencies": ["."],
  "graphs": {
    "my_agent": "./my_agent.py:graph"
  },
  "env": ".env"
}
```

### 启动开发服务器

```
langgraph dev
```

启动后访问
http://localhost:8123
即可在浏览器中使用 LangGraph Studio。

`http://localhost:8123`

### Studio 主要功能

- 实时可视化
：图形化展示节点执行过程，直观了解工作流状态
- 状态检查
：在任意节点暂停查看当前 State，方便排查问题
- 时间旅行
：回放历史执行步骤，追踪每一步的状态变化
- 热重载
：修改代码后自动更新图结构，无需重启服务

## 最佳实践与常见问题

### 最佳实践

状态设计要点

- 保持 State 精简，只包含必要字段
- 为复杂字段定义明确的 reducer（如
add_messages
）
`add_messages`
- 使用 Pydantic 模型在生产环境中验证状态类型
- 避免在 State 中存储过大的对象，考虑使用外部存储
节点设计要点

- 每个节点职责单一，便于测试和复用
- 节点函数应该是幂等的（相同输入产生相同输出）
- 避免在节点中直接修改传入的 state，而是返回新值
- 合理使用异步节点处理 I/O 密集型操作
错误处理

```
def robust_node(state: AgentState) -> dict:
    try:
        result = risky_operation(state)
        return {"messages": [result], "error": None}
    except Exception as e:
        return {
            "error": str(e),
            "messages": [{"role": "assistant", "content": f"操作失败: {e}"}]
        }
```

避免无限循环

```
def route_with_limit(state: AgentState) -> str:
    # 设置最大重试次数，防止无限循环
    if state.get("retry_count", 0) >= 3:
        return END
    
    if needs_retry(state):
        return "retry_node"
    return END
```

### 常见问题 FAQ

Q1：节点返回值格式不对怎么办？

```
# 错误：直接修改 state 对象
def bad_node(state):
    state["messages"].append(...)  # 不要直接修改
    return state

# 正确：返回需要更新的字段
def good_node(state):
    return {"messages": [new_message]}  # 只返回变更字段
```

Q2：如何在节点之间传递临时数据？

将临时数据加入 State 定义，或使用下划线前缀约定为内部字段：

```
from typing import TypedDict

class PublicState(TypedDict):
    messages: list  # 对外暴露

class PrivateState(TypedDict):
    messages: list
    _internal_cache: dict  # 以下划线开头约定为内部使用
```

Q3：如何调试节点执行过程？

```
# 使用 stream 模式观察每个节点的输出
for event in graph.stream(initial_state, stream_mode="updates"):
    for node_name, state_update in event.items():
        print(f"\n[节点: {node_name}]")
        print(f"更新: {state_update}")
```

Q4：StateGraph 和 MessageGraph 的区别？

MessageGraph
是早期版本的 API，功能较为受限。现在推荐统一使用
StateGraph
，它更灵活、功能更完善。如需处理消息，使用
StateGraph(MessagesState)
或自定义包含
messages
字段的 State。

`MessageGraph`
`StateGraph`
`StateGraph(MessagesState)`
`messages`
`MessageGraph`
`StateGraph`

## 总结

本文系统介绍了 LangGraph 框架的核心概念和实战应用。LangGraph 通过图结构的工作流编排，让开发者能够构建具备循环、分支、状态持久化能力的复杂 AI Agent。相比传统的线性 LLM Chain，LangGraph 在处理需要多步推理、人机协作、多 Agent 协同的场景时具有显著优势。

概念 | 说明 | 关键代码
StateGraph | 有向图工作流引擎，LangGraph 的核心 | StateGraph(MyState)
State | 节点间共享的状态数据结构 | TypedDict+Annotated
Nodes | 执行具体操作的函数节点 | builder.add_node()
Edges | 节点间的流转路径，支持条件分支 | add_edge()/add_conditional_edges()
ReAct Agent | 推理+行动的循环模式 | ToolNode+tools_condition
Human-in-Loop | 人工审批与介入机制 | interrupt()+Command(resume=)
持久化 | 会话记忆与状态保存 | MemorySaver/SqliteSaver
多 Agent | 多专家协作系统 | Supervisor Pattern

`StateGraph(MyState)`
`TypedDict`
`Annotated`
`builder.add_node()`
`add_edge()`
`add_conditional_edges()`
`ToolNode`
`tools_condition`
`interrupt()`
`Command(resume=)`
`MemorySaver`
`SqliteSaver`

### 推荐学习路径

---

## AI Agent(智能体) 教程

# AI Agent(智能体) 教程

AI Agent 称为智能体，本质是自动执行任务的程序，核心在于让模型不只回答问题，而是按步骤完成动作。

AI Agent（人工智能代理）
是一个能够感知环境、进行决策并执行行动，以达成特定目标的智能软件实体，它不仅仅是回答问题的聊天机器人，更是能够动手做事的智能执行者。

Agent = LLM (大脑) + Planning (规划) + Tool use (执行) + Memory (记忆)。

快速体验 0 代码，一句话生成应用：
https://www.miaoda.cn/
。

## 谁适合阅读本教程？

- 想使用 AI 自动化日常任务的人
- 对编程不熟但想用 AI 做实际工作的新人
- 已会基本电脑操作、但对 Agent/工作流 等概念零基础的人
- 想把 AI 从聊天提升到真正干活的人

## 课程内容

## 什么是 Agent？

Agent 就是一个能干活的智能助手。

Agent = LLM (大脑) + Planning (规划) + Tool use (执行) + Memory (记忆)。

学习 Agent 需要思维转变： 从
对话框问答
进化为
目标驱动的任务执行
。

传统的软件程序遵循固定的指令流程：
输入 → 处理 → 输出
，而 AI Agent 则更像一个有自主性的
员工
，它能够：

- 理解任务目标
：明白你想要什么结果
- 制定计划
：思考如何达成目标
- 使用工具
：调用各种资源和 API
- 自我调整
：根据反馈优化策略
- 持续执行
：直到完成任务或遇到无法解决的问题
类比理解：

- 传统程序 = 自动售货机：投币 → 按按钮→ 出商品
- AI Agent = 私人助理：告诉需求 → 助理规划 → 完成任务并汇报

## AI Agent 结构组成

结构由三块组成:

- 目标：
明确任务意图
- 逻辑：
按规则拆成可执行步骤
- 工具：
通过代码或 API 让步骤落地
运行方式:

- 接收输入
- 判断当前任务
- 调用对应工具执行
- 返回结果
- 保留必要上下文
- 支持多轮连续操作
- 遇阻时调整执行步骤
与普通大模型的差异点:

- 普通大模型：生成文本
- Agent：生成行动并执行行动，能完成实际工作
举例：

- 给出目标：如 "规划三天北京行程，预算 5000"。
- 自动检索机票、酒店与价格。
- 自动收集景点信息并做对比。
- 自动生成可执行行程表。
- 具备条件时可继续执行预订操作。

## AI Agent 的工作原理：一个简单的代码示例

让我们通过一个 Python 伪代码示例，直观感受一下 AI Agent 的工作流程。假设我们要创建一个能自动查询天气并给出穿衣建议的简单 Agent。

## 实例

代码解读
：

- WeatherAgent
类定义了一个简单的 Agent 框架。
`WeatherAgent`
- tools
字典定义了 Agent 可以使用的两种"工具"（函数）。
`tools`
- run
方法是核心流程：它
解析
用户指令，
规划
出需要调用
get_weather_api
和
generate_advice
两个工具，然后
按顺序执行
，并将中间结果存入
memory
，最后
输出
整合后的答案。
`run`
`get_weather_api`
`generate_advice`
`memory`

## 学习资源

Google 5 天智能体课程：
https://www.kaggle.com/learn-guide/5-day-agents

微软的课程：
https://github.com/microsoft/ai-agents-for-beginners

Hello-Agents：
https://github.com/datawhalechina/hello-agents

500 个智能体案例：
https://github.com/ashishpatel26/500-AI-Agents-Projects

智能体资源库：
https://github.com/NirDiamant/GenAI_Agents

HF 智能体课程：
https://github.com/huggingface/agents-course
