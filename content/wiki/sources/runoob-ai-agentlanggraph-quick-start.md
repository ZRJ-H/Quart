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
- **类型**: 技术教程

## 概述
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
想象你正在指挥一场交响乐演出：传统的 LLM Chain 就像演奏一首从头到尾的曲子，只能顺序播放；而 Lang

## 目录
- 概述
- AI Agent(智能体) 教程

## 相关实体
- [[AI Agent生态]] - 主要教程内容
- [[Claude Code生态]] - 相关工具
- [[OpenCode]] - 相关工具
- [[Skills生态]] - 相关概念

## 相关概念
- [[AI Agent生态]] - 教程主题
- [[多智能体编排]] - CrewAI/LangGraph 内容
- [[RAG]] - RAG 教程内容
- [[向量数据库]] - 向量数据库教程内容

## 个人思考
菜鸟教程提供了系统化的 AI Agent 学习路径，从基础概念到实际应用，适合作为入门参考资料。



## 完整内容
- [[wwwrunoobcomai-agentlanggraph-quick-starthtml]] - 完整教程内容
- 文件位置: wwwrunoobcomai-agentlanggraph-quick-starthtml.md

## 最后更新
- 日期: 2026-06-05
- 更新内容: 首次收录
