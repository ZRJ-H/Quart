---
type: source
title: "RAG 与知识检索"
source_type: tutorial
url: https://www.runoob.com/ai-agent/retrieval-augmented-generation.html
date_accessed: 2026-06-05
tags: [tutorial, runoob, ai-agent]
---

# RAG 与知识检索

## 基本信息
- **来源**: 菜鸟教程
- **URL**: https://www.runoob.com/ai-agent/retrieval-augmented-generation.html
- **采集日期**: 2026-06-05
- **章节数**: 2

## 目录
- 概述
- AI Agent(智能体) 教程

---

## 概述

# RAG 与知识检索

RAG（Retrieval-Augmented Generation，检索增强生成）是目前最主流的 LLM 落地架构之一。

RAG 的核心思想是：
让 LLM 在回答问题时，先从外部知识库中检索相关内容，再基于检索结果生成回答
，而不是仅依赖模型训练时记住的知识。

这解决了 LLM 的两个核心痛点：知识截止日期（模型不知道训练后发生的事）和幻觉问题（模型在不确定时会编造答案）。

## RAG 基础原理

一个完整的 RAG 系统由两条流水线组成：
离线索引流水线
（将文档预处理存入向量库）和
在线查询流水线
（接收用户问题、检索、生成）。

离线阶段将原始文档切分成小块，通过 Embedding 模型转换为向量，存入向量数据库。

在线阶段将用户问题同样转换为向量，从数据库中找到最相近的文档块，拼接成上下文交给 LLM 生成答案。

下图展示了 RAG 的完整请求流程：

## 数据预处理与文档切分（Chunking）

### 前置挑战：复杂文档解析

在进行切分前，RAG 往往面临着
格式解析
的挑战。特别是 PDF、Word 或扫描件中的表格、图片和多栏排版，普通的文本提取极易造成语义错乱。

目前行业主流方案是引入
文档解析引擎
（如 LlamaParse、Unstructured）或多模态大模型，将复杂图文转换为结构化的 Markdown，为后续高质量切分打下基础。

### 文档切分策略

文档切分是 RAG 效果的基础，切分粒度直接影响检索质量。块太大会引入噪声，块太小会丢失上下文。常用策略如下：

切分策略 | 适用场景 | 优点 | 缺点
固定大小切分 | 通用文本 | 实现简单，速度快 | 可能切断语义完整的句子
递归字符切分 | 结构化文本（Markdown、代码） | 优先按段落、句子等语义边界切分 | 实现略复杂，需设定合理的分隔符列表
语义切分 (Semantic) | 长文档、书籍 | 利用 Embedding 计算相邻句子的相似度，自动寻找语义转折点切分 | 计算成本高，预处理速度慢
父子文档检索(Small-to-Big) | 全面覆盖场景 | 用"小块"进行高精度向量检索，命中后返回对应的"大块"（父文档）给 LLM，兼顾了检索精度和上下文完整性。 | 数据库设计和维护成本翻倍

> 实践中常在切分时加入
重叠（overlap）
，即相邻块之间共享若干字符，防止重要信息在边界处被截断。典型配置：块大小 512 tokens，重叠 50~100 tokens。

实践中常在切分时加入
重叠（overlap）
，即相邻块之间共享若干字符，防止重要信息在边界处被截断。典型配置：块大小 512 tokens，重叠 50~100 tokens。

## 实例：使用 LangChain 进行递归切分

## 向量检索

### Embedding 模型

Embedding 模型负责将文本转换为稠密向量（通常是 768 或 1536 维的浮点数数组）。语义相近的文本在向量空间中距离更近，这正是相似度检索的数学基础。

常用 Embedding 模型对比：

模型 | 维度 | 适用语言 | 特点
text-embedding-3-small（OpenAI） | 1536 | 多语言 | 性价比高，适合大规模索引
text-embedding-3-large（OpenAI） | 3072 | 多语言 | 精度最高，成本较高
BAAI/bge-m3 | 1024 | 中英文 | 开源，中文效果优秀，支持多语言
sentence-transformers/all-MiniLM-L6-v2 | 384 | 英文 | 体积小，速度快，适合本地极轻量部署

`text-embedding-3-small`
`text-embedding-3-large`
`BAAI/bge-m3`
`sentence-transformers/all-MiniLM-L6-v2`

### 相似度计算与 ANN 算法

检索的核心是度量距离。最常用的是
余弦相似度（Cosine Similarity）
，它计算两个向量的夹角余弦值，值域 [-1, 1]，越接近 1 越相似。此外还有点积（Dot Product）和欧氏距离（L2 Distance）。

为了在百万级向量中实现毫秒级检索，数据库通常采用
近似最近邻（ANN）算法
（如
HNSW
、IVF）。HNSW 是目前最主流的算法，它通过构建多层跳跃图网络，牺牲极少的精度换取了数量级的搜索速度提升。

## Advanced RAG (进阶架构)

基础架构（Naive RAG）常面临检索不准确、冗余信息多导致"上下文淹没"等问题。Advanced RAG 通过
预检索优化 → 检索融合 → 后检索优化
的三段式架构予以解决。

### 1、预检索：查询优化

用户的原始问题往往表达不够精确：

- 查询改写（Query Rewriting）
：用 LLM 将口语化提问改写为规范化的检索词。
- HyDE（Hypothetical Document Embedding）
：让 LLM 先"盲猜"一个假设性答案，由于生成的答案通常比原问题包含更多行业术语，用这个假设答案的向量去检索，往往能召回更高质量的文档。

### 2、混合检索（Hybrid Search）

将
向量检索
（懂语义，容错率高）与
关键词检索
（BM25，匹配度高）的结果按权重融合。这在遇到专有名词、产品型号、代码片段时尤为重要，因为传统的向量检索容易在特定的专有名词上"翻车"。

### 3、后检索优化：重排序（Reranking）

这是一个
粗排 → 精排
的两阶段设计。向量检索虽然快，但打分不够精确。重排序（Reranking）会引入
Cross-Encoder 模型
（如 `bge-reranker`），将"问题"和"文档"成对输入模型进行联合推理打分。它的运算量大，只负责精选 Top-20 到 Top-5。

## 实例：重排序流程伪代码

### 4、Self-RAG 与 CRAG（修正式 RAG）

加入自我反思机制。例如 CRAG（Corrective RAG）在拿到检索结果后，先由 LLM 充当"评委"打分。如果本地知识库查无此文或质量极低，系统会自动触发 Web Search（如 Google API）作为补充，大幅降低幻觉。

## GraphRAG：知识图谱 + 检索融合

传统 RAG 将知识库当作独立的文本碎片，无法回答诸如"找到所有同时由现任 CEO 创办且市值超千亿的公司"这类需要
跨文档、多跳推理
的复杂问题。
GraphRAG
引入知识图谱（Knowledge Graph），将实体和关系显式建模。

### GraphRAG 核心步骤

- 知识构建
：离线阶段使用 LLM 从文档提取三元组（主体、关系、客体），写入 Neo4j 等图数据库。
- 双路检索
：针对提问中的实体，不仅做传统的向量检索，同时在图谱中触发图遍历（Graph Traversal），提取多跳关系链。
- 图文融合生成
：将向量检索找回的"片段"与图检索找回的"路径结构"拼装进 Prompt，使得 LLM 既具备全局视野又掌握具体细节。

## 技术与数据库选型建议

数据库/工具选型 | 类型 | 推荐落地场景
Pinecone / Zilliz Cloud | 全托管云服务 | 开箱即用，不想维护基础设施。搭配 Cohere Rerank + GPT-4o 是最快商用的方案。
Qdrant | 开源 + 托管 | Rust 编写，内存管理优秀，性能极高。适合企业级私有化部署。
Weaviate / Elasticsearch | 开源 + 托管 | 自带极其成熟的 BM25 + 向量混合检索（Hybrid Search），专有名词较多的场景首选。
Milvus | 开源分布式 | 适合十亿至百亿级别的超大规模企业级检索平台。
Chroma / FAISS | 本地库/嵌入式 | 极轻量，无需部署独立服务。非常适合本地开发、个人知识库项目验证。

## RAG 评估指标（RAGAS 框架）

RAG 系统的评估不能仅凭直觉，主流使用
RAGAS
框架，从"检索"和"生成"两个维度进行自动化量化测试：

- Context Recall（检索召回率）
：标准答案中的信息有多少比例能被检索到。
- Context Precision（检索精确率）
：检索到的文档中有多少比例是真正相关的。
- Faithfulness（忠实度/幻觉指标）
：生成的答案是否都有检索出的文档支撑。
- Answer Relevance（答案相关性）
：生成的答案是否真正回答了用户的问题，避免答非所问。

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
