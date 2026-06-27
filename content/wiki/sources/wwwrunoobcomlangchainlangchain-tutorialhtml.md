---
type: source
title: "LangChain 教程"
source_type: tutorial
url: https://www.runoob.com/langchain/langchain-tutorial.html
date_accessed: 2026-06-05
tags: [tutorial, runoob, ai-agent]
---

# LangChain 教程

## 基本信息
- **来源**: 菜鸟教程
- **URL**: https://www.runoob.com/langchain/langchain-tutorial.html
- **采集日期**: 2026-06-05
- **章节数**: 2

## 目录
- 概述
- LangChain 简介

---

## 概述

# LangChain 教程

LangChain 是一套用于构建 AI 智能体（AI Agent）和大语言模型（LLM）应用的开发框架。

LangChain 可以帮助开发者快速构建基于 GPT、Claude、Gemini 等大模型的复杂 AI 应用。

LangChain 由 Harrison Chase 于 2022 年 10 月推出，核心目标是：
简化大语言模型应用开发流程
。

LangChain提供统一接口，可连接：大模型、Prompt、向量数据库、工具调用、记忆系统以及 Agent 工作流。

目前 LangChain 已成为最热门的 LLM 应用开发框架之一，广泛应用于：智能聊天机器人、RAG 知识库、文档分析、代码生成、AI 自动化等场景。

## 谁适合阅读本教程？

本教程适合具备 Python 基础，并希望学习 AI 应用开发的开发者。

- 有 Python 基础，想学习 AI 与大语言模型开发的新手
- 想开发 AI 聊天机器人、知识库、Agent 应用的开发者
- 对 GPT、Claude、RAG、向量数据库感兴趣的学习者
- 希望使用 LangChain 快速构建 AI 项目的工程师
- 想从传统开发转向 AI 应用开发的程序员

## 学习本教程前你需要了解

学习本教程前，你需要具备一定 Python 基础，并了解基础 Web 与 API 概念。

- Python 基础：变量、函数、类、模块导入、异常处理
- HTTP 与 API 基础：GET/POST 请求、JSON 数据格式
- Prompt 基础：了解什么是 Prompt 与大语言模型
- 基础数据库知识：了解 SQLite / MySQL 基础操作
- 了解基本命令行操作与 pip 包管理

## LangChain 可以做什么？

- AI 聊天机器人（ChatBot）
- RAG 企业知识库
- PDF 文档问答系统
- AI Agent 自动任务执行
- 代码生成与代码分析
- 多轮对话与上下文记忆
- 联网搜索与工具调用
- 工作流自动化系统

## 第一个 LangChain 程序

以下代码使用 LangChain 调用 OpenAI 模型，并输出 AI 生成内容：

## 实例

运行后，大模型会自动生成关于 Transformer 的解释内容。

## LangChain 核心组件

- LLM：连接 OpenAI、Claude、Gemini 等大模型
- PromptTemplate：管理 Prompt 模板
- Chains：构建多步骤 AI 工作流
- Memory：实现多轮对话记忆
- Tools：调用搜索、数据库、API 等工具
- Agents：让 AI 自动决策与执行任务
- Vector Store：连接向量数据库实现 RAG

## 参考文档

- LangChain 官网：
https://www.langchain.com/
- LangChain Python 文档：
https://python.langchain.com/
- LangChain JavaScript 文档：
https://js.langchain.com/
- LangChain GitHub：
https://github.com/langchain-ai/langchain

---

## LangChain 简介

# LangChain 简介

LangChain 是一个用于构建大语言模型（LLM）应用的 Python 框架。

LangChain 提供统一的接口来连接各种 AI 模型，并支持构建能够自动调用工具、检索知识、记住上下文的智能 Agent。

## LangChain 是什么

简单来说，LangChain 解决了一个核心问题：
让大语言模型能够与外部世界交互
。

原生的 LLM 只能根据训练数据生成文本。但实际应用中，我们需要 AI 能够查询数据库、调用 API、搜索文档、发送邮件。

LangChain 提供了一套标准化的组件来串联这些能力。

组件 | 作用 | 核心功能 | 常见用途
Models（模型） | 连接大语言模型 | 统一模型接口支持多模型切换调用 GPT / Claude / Gemini 等 | 聊天机器人文本生成AI 问答
Prompts（提示词模板） | 管理 Prompt 模板 | Prompt 参数化动态变量替换模板复用 | AI 对话内容生成结构化输出
Document Loader（文档加载） | 读取外部文档数据 | 加载 PDF / TXT / DOCX读取网页与数据库统一文档格式 | 知识库RAG 系统文档问答
Text Splitter（文本切分） | 拆分长文本 | 文本 Chunk 切分控制 Token 长度优化向量检索 | RAG向量数据库长文本处理
Memory（记忆） | 实现上下文记忆 | 保存聊天历史长期记忆对话状态管理 | 聊天机器人AI 助手Agent
Retriever（检索器） | 检索相关知识内容 | 向量搜索语义检索RAG 数据召回 | 企业知识库AI 搜索文档问答
Tools（工具） | 调用外部工具与 API | 搜索互联网数据库查询执行代码 | AI Agent自动化任务数据分析
Output Parser（输出解析器） | 解析模型输出结果 | 结构化输出JSON 解析格式校验 | API 返回自动化系统数据处理
Chains（链） | 组合多个组件形成工作流 | 多步骤执行流程编排组件串联 | 复杂 AI 应用RAG 工作流Agent 系统

- 统一模型接口
- 支持多模型切换
- 调用 GPT / Claude / Gemini 等
- 聊天机器人
- 文本生成
- AI 问答
- Prompt 参数化
- 动态变量替换
- 模板复用
- AI 对话
- 内容生成
- 结构化输出
- 加载 PDF / TXT / DOCX
- 读取网页与数据库
- 统一文档格式
- 知识库
- RAG 系统
- 文档问答
- 文本 Chunk 切分
- 控制 Token 长度
- 优化向量检索
- RAG
- 向量数据库
- 长文本处理
- 保存聊天历史
- 长期记忆
- 对话状态管理
- 聊天机器人
- AI 助手
- Agent
- 向量搜索
- 语义检索
- RAG 数据召回
- 企业知识库
- AI 搜索
- 文档问答
- 搜索互联网
- 数据库查询
- 执行代码
- AI Agent
- 自动化任务
- 数据分析
- 结构化输出
- JSON 解析
- 格式校验
- API 返回
- 自动化系统
- 数据处理
- 多步骤执行
- 流程编排
- 组件串联
- 复杂 AI 应用
- RAG 工作流
- Agent 系统
从技术角度看，LangChain 是一个模块化的 LLM 应用开发框架，它包含三个层次：

层次 | 说明 | 包名
核心抽象层 | 定义模型、工具、消息等基础接口 | langchain-core
用户接口层 | 提供 init_chat_model、create_agent 等高阶 API | langchain
集成层 | 连接 OpenAI、Anthropic、Ollama 等第三方服务 | langchain-openai 等

## 为什么选择 LangChain

如果你只是调用一次模型 API，直接用 HTTP 请求就够了。但当你需要构建一个完整的 AI 应用时，LangChain 提供了以下优势：

能力 | 描述 | 适用场景
模型统一接口 | 一套代码切换 OpenAI / Anthropic / DeepSeek 等模型 | 多模型对比测试、成本优化
Agent 架构 | 模型自动决定何时调用工具，形成思考-行动循环 | 自动化任务、智能客服
中间件系统 | 在模型调用前后插入自定义逻辑（重试、缓存、过滤） | 生产环境的可靠性保障
结构化输出 | 让模型按指定格式返回 JSON，方便程序解析 | 数据提取、表单填充
记忆与持久化 | 内置对话记忆和跨会话存储能力 | 多轮对话、用户偏好记忆
生态丰富 | 数百个第三方集成，覆盖主流模型和工具 | 快速接入各类服务

## LangChain 能做什么

以下是 LangChain 最典型的应用场景：

### 智能聊天机器人

具备多轮对话记忆，能调用外部工具（查天气、查订单、发邮件）的聊天助手。

### RAG 知识库问答

将私有文档（PDF、网页、数据库）向量化存储，让模型能够基于这些文档回答问题，附带引用来源。

### Agent 自动化助手

模型自主规划任务步骤，按需调用不同的工具，完成复杂的多步操作，如"帮我整理上周的销售数据并生成报告"。

### 数据提取与分析

从非结构化文本中提取结构化信息（如从合同扫描件中提取关键字段），或让模型生成数据分析结论。

## LangChain 与 LangGraph 的关系

很多初学者会困惑这两个库的区别。简单来说：

对比维度 | LangChain | LangGraph
定位 | 高层 Agent 框架，开箱即用 | 底层工作流引擎，精细控制
上手难度 | 低，10 行代码创建 Agent | 中高，需理解图（Graph）概念
适用场景 | 标准 Agent 应用、快速原型 | 复杂多步骤工作流、多 Agent 协作
关系 | LangChain 的 create_agent() 底层构建在 LangGraph 之上

> 本教程聚焦于 LangChain。如果你刚开始学习，从 LangChain 入手是正确的选择。当你需要更精细的流程控制时，再深入 LangGraph。

本教程聚焦于 LangChain。如果你刚开始学习，从 LangChain 入手是正确的选择。当你需要更精细的流程控制时，再深入 LangGraph。

## 准备工作

在开始学习之前，你只需要具备以下基础：

- Python 基础语法（函数、类、类型注解）
- 能够使用 pip 安装 Python 包
- 了解基本的命令行操作
- 有一个大模型 API Key（OpenAI、Anthropic 等均可）
> 本教程的代码示例在 Python 3.10+ 环境下测试通过。

本教程的代码示例在 Python 3.10+ 环境下测试通过。
