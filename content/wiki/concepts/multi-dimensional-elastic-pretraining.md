---
type: concept
name: 多维弹性预训练
category: technical
first_seen: 2026-05-13
last_updated: 2026-05-13
tags: [ai, training, efficiency, baidu]
---
# 多维弹性预训练（Multi-Dimensional Elastic Pretraining）

## 定义
百度文心大模型 5.1 引入的预训练范式，通过动态采样机制同时优化不同参数规模的子模型，实现"一次训练生成多种规模模型"，将训练成本降至同规模模型 6%。

## 核心要点
- **三大维度**：弹性深度（Elastic Depth）、弹性专家容量（Elastic Expert Capacity）、弹性稀疏度（Elastic Sparsity）
- **一次训练多模型**：无需为每种参数规模独立训练
- **成本革命**：预训练成本仅为同规模模型的 6%
- **能力无损**：基础效果在同规模模型中领先

## 相关政策/事件
- 百度 Create 2026 AI 开发者大会（2026-05-13）正式宣布

## 相关概念
- 模型压缩
- 知识蒸馏
- MoE（混合专家模型）

## 实际应用
- 大模型降本增效
- 多规模模型快速部署
- 国产大模型 API 定价竞争力

## 最后更新
- 日期: 2026-05-13
- 更新内容: 首次创建
