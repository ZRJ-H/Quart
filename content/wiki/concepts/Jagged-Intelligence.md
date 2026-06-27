---
type: concept
name: Jagged Intelligence
category: technical
first_seen: 2026-04-30
last_updated: 2026-05-25
tags: [AI, LLM, 能力分析, Karpathy]
---
# Jagged Intelligence

## 定义
Karpathy 提出的 LLM 能力分析框架，描述模型能力尖峰（capability spike）的不均匀分布特征。模型能力不是平滑提升的，而是在可验证的、被训练关注的数据域上出现尖峰，在其他领域表现异常。

## 核心要点
- **核心公式**：能力尖峰 ≈ 可验证性 x 训练关注度 x 数据覆盖 x 经济价值
- 模型没有"说明书"——它们是预训练混合、RL 环境、基准压力、产品优先级和经济激励的产物
- 典型例子：
  - 模型能重构 100,000 行代码库，但告诉你"50 米远的洗车店应该走路去"
  - 象棋能力：GPT-3.5 到 GPT-4 大幅提升，部分原因是训练集中加入了大量象棋数据
- 对创始人的启示：你的任务是否在模型的"轨道"上？如果在可验证且被充分训练的区域内，模型会表现优秀；否则可能在基础问题上失败
- 需要探索模型的能力分布，必要时通过微调或自有 RL 环境补齐短板

## 相关政策/事件
- 2026 年 4 月 Karpathy 在 Sequoia Ascent 2026 上阐述此框架
- 与 [[Verifiability (AI)]] 概念紧密相连

## 相关概念
- [[Verifiability (AI)]] - Jagged Intelligence 的核心驱动因素
- [[Agentic-Engineering]] - 需要理解和适应 Jagged Intelligence 来构建设计
- [[Animals-vs-Ghosts]] - 解释 Jagged Intelligence 的理论框架

## 相关实体
- [[Andrej-Karpathy]] - 提出者
- [[OpenAI]] - 以 ChatGPT/Codex 为典型观察对象

## 实际应用
- 评估 AI 产品的能力边界
- 指导模型选型和定制策略
- 设计 Agent 工作流时避开模型的薄弱区域

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
