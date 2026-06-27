---
type: concept
name: LLM上下文预压缩
category: technical
first_seen: 2026-06-03
last_updated: 2026-06-03
tags: [LLM, Token优化, 上下文压缩, RAG]
---
# LLM上下文预压缩

## 定义
在数据送达LLM之前对工具输出、日志、文件和RAG分块进行智能压缩，可减少60-95%的token消耗但保持答案质量。GitHub项目headroom是该技术的代表性实现，提供库、代理和MCP服务器。该技术代表了一个新范式——不是更大的模型，而是更高效地使用模型。

## 核心要点
- "预压缩"在数据进入LLM上下文窗口前处理
- 减少60-95% token消耗，保持答案质量
- 实现方式：库（SDK）、代理（proxy）、MCP服务器
- headroom（chopratejas/headroom）为代表实现，日增+1,265⭐
- 与RAG（检索增强生成）互补：RAG检索+预压缩优化
- 随着AI Agent大规模部署，token成本成为核心瓶颈

## 相关政策/事件
- [[headroom]] - GitHub Trending +1,265⭐，增长率19%

## 相关概念
- [[AI工具链生态集中爆发]] - 上下游生态
- [[AI算力供需剪刀差]] - 算力成本驱动

## 实际应用
- RAG工作流效率提升
- AI Agent token成本大幅降低
- 长文档处理（法律、医学、金融）
- 多轮对话上下文管理

## 最后更新
- 日期: 2026-06-03
- 更新内容: 首次收录，headroom引领Token优化新范式
