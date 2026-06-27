---
type: concept
name: LLM训练流水线
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [LLM, 训练, AI, 预训练, 后训练]
---
# LLM训练流水线

## 定义
大型语言模型从原始互联网数据到可用对话助手的完整构建流程，包含数据收集与预处理、Token化、预训练（Next Token Prediction）、后训练（SFT + RLHF）等核心阶段。

## 核心要点
- 数据来源以Common Crawl为主（270亿网页），经多阶段过滤（URL过滤/文本提取/去重）
- 预训练：在百万级token批次上同时优化Next Token Prediction，每次参数更新降低损失值
- 后训练三阶段：SFT（学会对话格式）→ 奖励模型训练（拟合人类偏好）→ RL（基于奖励优化）
- 基础模型（pretrained base model）拥有世界知识但不会对话，对话能力在后训练阶段获得
- 训练需要大规模GPU集群（数千张GPU训练数月），个人电脑不可行

## 相关实体
- [[Andrej-Karpathy]] - 系统讲解训练流水线的AI研究者

## 相关概念
- [[Tokenization]] - 流水线第一步
- [[后训练(Post-training)]] - SFT+RLHF阶段
- [[RLHF与奖励模型]] - 人类反馈驱动的优化

## 实际应用
暂无

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
