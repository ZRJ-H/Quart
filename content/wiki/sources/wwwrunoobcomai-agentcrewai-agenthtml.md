---
type: source
title: "CrewAI 构建智能体"
source_type: tutorial
url: https://www.runoob.com/ai-agent/crewai-agent.html
date_accessed: 2026-06-05
tags: [tutorial, runoob, ai-agent]
---

# CrewAI 构建智能体

## 基本信息
- **来源**: 菜鸟教程
- **URL**: https://www.runoob.com/ai-agent/crewai-agent.html
- **采集日期**: 2026-06-05
- **章节数**: 2

## 目录
- 概述
- AI Agent(智能体) 教程

---

## 概述

# CrewAI 制作智能体

CrewAI 是一个多智能体协作的开源框架，专门用于编排和协调多个 AI Agent 进行协作。

CrewAI 可以把一个复杂任务，拆成多个角色，各自负责一部分，通过流程协作完成。

对比理解：

- 单 Agent
：一个大模型，从头干到尾
- CrewAI
：产品经理 + 工程师 + 分析师 + 编辑，各司其职
CrewAI 是一个协调、管理和框架化 AI Agent 的工具，它基于 LangChain 和 Pydantic 构建，用于促进角色扮演、自治和协作的 Agent 团队。

- Crew（团队）
： 一个由多个
Agent
组成的项目组。
`Agent`
- Agent（成员）
： 团队中的个体，每个都有明确的
role
（角色）、
goal
（目标）和
backstory
（背景故事）。
`role`
`goal`
`backstory`
- Task（任务）
： 需要团队完成的具体工作。一个
Crew
包含多个有序或并行的
Task
，并分配给合适的
Agent
。
`Crew`
`Task`
`Agent`
- Process（流程）
： 定义团队的工作流程，例如是顺序执行还是同时执行任务。
简单来说，crewAI 提供了一个结构化的方式来定义谁（Agent）在什么流程（Process）下，完成哪些事（Task），最终达成团队目标。

下面的流程图清晰地展示了 crewAI 框架中各个核心组件是如何协同工作的：

流程始于定义具备特定角色和目标的智能体（Agent），然后为其创建具体的任务（Task）。

接着，将这些智能体及其任务组建成一个团队（Crew），并为团队选择协同工作的流程（Process），如顺序执行或并行执行。最终，团队按照既定流程执行所有任务，产出最终结果。

## 环境搭建与安装

开始构建前，我们需要准备好开发环境。

### 前置条件

Python 版本要求：

- 必须
：Python ≥ 3.10 且 < 3.14
- 可以在终端输入
python --version
来检查，不满足版本范围，后续问题会非常多，不建议硬扛
`python --version`
CrewAI 使用
UV
做依赖和包管理，目的只有一个：
让多 Agent 项目更稳定，不被环境问题拖垮

UV 入门教程参考：
UV - Python 包与环境管理工具
。

API 密钥：

crewAI 本身不提供 AI 模型，它需要连接像 OpenAI 的 GPT、Anthropic 的 Claude 等大语言模型。

### 安装 crewAI

打开你的终端或命令行工具，使用 pip 命令安装 crewAI 包。

```
# 正常安装
pip install crewai
# 其他依赖
pip install langchain
pip install openai


# 如果安装慢，可以使用国内镜像安装
pip install crewai -i https://mirrors.aliyun.com/pypi/simple/
pip install langchain -i https://mirrors.aliyun.com/pypi/simple/
pip install openai -i https://mirrors.aliyun.com/pypi/simple/
```

如果希望使用 crewAI 内置的一些高级工具（如网络搜索），可以安装额外的依赖项：

```
# 正常安装
pip install 'crewai[tools]'

# 如果安装慢，可以使用国内镜像安装
pip install 'crewai[tools]' -i https://mirrors.aliyun.com/pypi/simple/
```

国内我们可以采用 DeepSeek 大模型来测试，如果还没有需要先去
https://platform.deepseek.com/api_keys
创建一个 API key。

DeepSeek 的 API 文档参考：
https://api-docs.deepseek.com/zh-cn/
。

安装完成后，创建一个新的 Python 文件，例如
my_first_crew.py
，并导入必要的库。

`my_first_crew.py`
CrewAI 的 LLM 对第三方模型（包括 DeepSeek）底层必须通过 LiteLLM，使用前我们需要先安装：

```
pip install -U litellm
```

## 实例

接下来，就会开始执行任务，输出相关信息：

完成后就会把输出的内容写入到  python_data_cleaning_blog.md 文件中。

以下是代码中相关属性的说明。

### LLM（模型层）关键属性

属性 | 示例值 | 作用 | 错误后果
model | deepseek/deepseek-v4-flash | LiteLLM 规范写法：服务商/模型名 | 少了deepseek/会直接报LLM Provider NOT provided
api_key | sk-xxxxx | 模型鉴权 | 为空或错误直接 401 / LLM Failed
api_base | https://api.deepseek.com/v1 | DeepSeek API 地址 | 根据具体模型的地址来
temperature | 0.7 | 控制输出随机性 | 过高内容发散，过低文本僵硬

`model`
`deepseek/deepseek-v4-flash`
`服务商/模型名`
`deepseek/`
`LLM Provider NOT provided`
`api_key`
`sk-xxxxx`
`api_base`
`https://api.deepseek.com/v1`
`temperature`
`0.7`

### Agent（智能体）关键属性

属性 | 作用 | 本质
role | Agent 的"身份标签" | 写进 system prompt
goal | 当前 Agent 的核心目标 | 决定回答方向
backstory | 行为约束与风格 | 稳定输出质量
llm | 使用哪个模型 | 必须显式绑定
verbose | 打印执行过程 | 仅影响日志
allow_delegation | 是否允许转派任务 | 极易踩坑

`role`
`goal`
`backstory`
`llm`
`verbose`
`allow_delegation`

### researcher（研究员）

属性 | 值 | 设计意图
allow_delegation | False | 防止无限拆任务
goal | 找资料 + 给代码 | 输出是"原料"

`allow_delegation`
`False`
`goal`

### writer（写作）

属性 | 值 | 风险
allow_delegation | True | 可能触发 delegate 再研究
context | [research_task] | 已有输入，其实不需要再 delegate

`allow_delegation`
`True`
`context`
`[research_task]`
结论
顺序流水线中，写作 Agent
应关闭 delegation
，否则容易二次委托失败。

### Task（任务）关键属性

Task 通用字段:

属性 | 作用 | 关键点
description | 实际发给 LLM 的任务文本 | 越具体越稳
agent | 谁来执行 | 必须唯一
expected_output | 结果约束 | 不强制，但强烈建议
context | 依赖的上游任务 | 顺序执行核心

`description`
`agent`
`expected_output`
`context`
research_task:

属性 | 说明
agent=researcher | 绑定研究员
无context | 第一阶段任务
输出 | 结构化研究内容

`agent=researcher`
`context`
write_task:

属性 | 说明
context=[research_task] | 强制读取研究结果
agent=writer | 只做整理与表达
输出 | 最终 Markdown 文本

`context=[research_task]`
`agent=writer`

### Crew（执行器）关键属性

属性 | 示例值 | 作用 | 错误后果
agents | [researcher, writer] | 所有可用 Agent | 少一个直接报错
tasks | [research_task, write_task] | 执行队列 | 顺序按列表
process | Process.sequential | 执行策略 | 并行会打乱依赖
verbose | True | 日志开关 | 只能是 bool

`agents`
`[researcher, writer]`
`tasks`
`[research_task, write_task]`
`process`
`Process.sequential`
`verbose`
`True`

### kickoff() 与输出结构

表达式 | 类型 | 用途
crew.kickoff() | CrewOutput | 执行结果容器
result.raw | str | 最终文本输出
result.tasks_output | list/dict | 每个 Task 的输出
result.token_usage | dict | 统计信息

`crew.kickoff()`
`CrewOutput`
`result.raw`
`str`
`result.tasks_output`
`result.token_usage`

## crewai 命令

我们可以使用
crewai
命令生成完整工程结构：

```
crewai create crew <项目名>
```

例如我们创建一个项目 runoob-agent-test，还行以下命令：

```
crewai create crew runoob-agent-test
```

接下来出现以下内容，可以先选择大模型的提供商：

```
Creating folder runoob_agent_test...
Cache expired or not found. Fetching provider data from the web...
Downloading  [####################################]  1102019/56339
Select a provider to set up:
1. openai
2. anthropic
3. gemini
4. nvidia_nim
5. groq
6. huggingface
7. ollama
8. watson
9. bedrock
10. azure
11. cerebras
12. sambanova
13. other
q. Quit
```

本章节，我们就选 DeepSeek，先输入 13 选 other，然后可以鼠标滚动看下 DeepSeek 在 23，输入序号 23 即可：

如果你有其他模型的 API key ，根据序号选择即可。

完成后，可以看到生成的目录如下：

项目结构说明:

```
my_project/
├── .env                # 环境变量（API Key）
├── pyproject.toml      # 项目依赖声明
├── README.md
└── src/
    └── my_project/
        ├── main.py     # 程序入口
        ├── crew.py     # Crew 与 Agent 的核心逻辑
        ├── tools/      # 自定义工具
        └── config/
            ├── agents.yaml  # Agent 定义
            └── tasks.yaml   # Task 定义
```

### 运行你的 Crew

进入项目根目录：

```
cd my_project
```

锁定并安装依赖：

```
crewai install
```

运行：

```
crewai run
```

或直接：

```
python src/my_project/main.py
```

### 配置 API 密钥

为了安全起见，不建议将 API Key 直接写在代码里，我们可以将其设置为环境变量。

在代码中设置（仅用于测试）
：

```
import os
os.environ["OPENAI_API_KEY"] = "你的-openai-api-key-here"
```

推荐方式：使用
.env
文件

`.env`
在项目根目录创建一个名为
.env
的文件。

`.env`
在文件中写入：
OPENAI_API_KEY=你的-openai-api-key-here

`OPENAI_API_KEY=你的-openai-api-key-here`
在 Python 代码中，使用
python-dotenv
包来加载。

`python-dotenv`
安装命令：

```
pip install python-dotenv
```

接下来在代码中载入：

```
from dotenv import load_dotenv
load_dotenv() # 这会自动加载 .env 文件中的变量
# 现在 os.environ["OPENAI_API_KEY"] 就已经有了值
```

## 核心组件详解与实战

现在，让我们像组建公司一样，一步步创建我们的 AI 团队，我们将模拟一个技术博客创作团队。

### 第一步：定义智能体 (Agent)

Agent
是你的团队成员。创建时需要定义几个关键属性：

`Agent`

参数 | 说明 | 示例
role | 代理的角色或职位。 | 资深技术作家
goal | 代理的最终目标。 | 创作深入浅出、实用的技术教程
backstory | 角色的背景故事，用于塑造其行为和语气。 | 你是一位拥有10年全栈开发经验的开发者，热爱分享，擅长将复杂概念简单化。
llm | 指定代理使用的大语言模型。 | ChatOpenAI(model="gpt-4", temperature=0.7)
verbose | 设置为True时，会输出代理的详细思考过程。 | True(调试时很有用)
allow_delegation | 是否允许此代理将任务委托给其他代理。 | True

`资深技术作家`
`创作深入浅出、实用的技术教程`
`你是一位拥有10年全栈开发经验的开发者，热爱分享，擅长将复杂概念简单化。`
`ChatOpenAI(model="gpt-4", temperature=0.7)`
`True`
`True`
`True`
让我们创建两个代理：一个
研究员
和一个
作家
。

## 实例

### 第二步：创建任务 (Task)

Task
是具体的工作项，需要分配给
Agent
去完成。关键属性包括：

`Task`
`Agent`

参数 | 说明 | 示例
description | 对任务的清晰描述。 | 研究 "Python异步编程asyncio" 在 2023 年后的核心应用场景和最佳实践。
agent | 负责执行此任务的Agent对象。 | researcher
expected_output | 对任务产出物的详细描述。 | 一份结构化的研究报告，包含概述、3-4个核心应用场景、2-3个代码片段示例以及总结。

`研究 "Python异步编程asyncio" 在 2023 年后的核心应用场景和最佳实践。`
`Agent`
`researcher`
`一份结构化的研究报告，包含概述、3-4个核心应用场景、2-3个代码片段示例以及总结。`
我们为研究员和作家各创建一个任务。

## 实例

注意
write_task
中的
context=[research_task]
，这建立了任务间的依赖关系，意味着作家需要等研究员完成任务后才能开始工作。

`write_task`
`context=[research_task]`

### 第三步：组建团队与设置流程 (Crew & Process)

现在，将
Agent
和
Task
组装成
Crew
，并定义他们的工作
Process
。

`Agent`
`Task`
`Crew`
`Process`

## 实例

crewAI 主要支持两种流程：

- Process.sequential
： 任务按在列表中的顺序依次执行。适合有严格依赖关系的流水线作业。
`Process.sequential`
- Process.hierarchical
： 配合一个管理者（Manager）Agent，由它来协调和分配任务。适合更复杂、动态的协作场景。
`Process.hierarchical`

### 第四步：执行任务并获取结果

一切就绪，启动你的 AI 团队！

## 实例

运行你的 Python 脚本 (
python my_first_crew.py
)。由于我们设置了
verbose=True
和
verbose=2
，你将在终端看到每个 Agent 的思考过程和任务执行日志，最后看到生成的博客文章。

`python my_first_crew.py`
`verbose=True`
`verbose=2`

## 进阶技巧：为 Agent 配备工具 (Tools)

crewAI 可以让
Agent
调用外部
Tool
，如搜索网络、查询数据库、执行计算等。

`Agent`
`Tool`
以下示例为研究员配备
网络搜索
和
计算
工具：

## 实例

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
