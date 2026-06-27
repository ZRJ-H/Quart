---
type: concept
name: 2-bit KV Cache量化
category: technical
first_seen: 2026-06-05
last_updated: 2026-06-05
tags: [LLM, 推理优化, KV Cache, 量化, OSCAR]
---
# 2-bit KV Cache量化

## 定义
将大语言模型（LLM）推理中的键值缓存（KV Cache）量化至约2.28bits的新技术方案，可将显存占用降低约8倍，同时推理吞吐量提升约7倍。OSCAR方案性能超越TurboQuant。

## 核心要点
- **量化目标**: KV Cache量化至约2.28bits
- **性能提升**: 显存占用降低约8倍，推理吞吐量提升约7倍
- **代表方案**: OSCAR（超越TurboQuant）
- **提出方**: Together AI、悉尼大学、UIUC联合研究

## 相关政策/事件
- 2026-06-05: OSCAR 2-bit KV Cache量化方案发布，显存降低8倍吞吐量提升7倍
- 标志LLM推理部署成本大幅下降的新方向

## 相关概念
- 大模型推理优化 - KV Cache量化是关键优化方向
- AI推理部署成本 - 显存瓶颈的主要解决方案
- AI Token成本优化 - 成本优化的互补技术

## 相关实体
- Together AI
- OSCAR

## 实际应用
- 降低LLM推理部署的GPU显存需求
- 使大模型在消费级硬件上运行成为可能
- 显著降低AI服务运营成本

## 最后更新
- 日期: 2026-06-05
- 更新内容: 首次创建，记录OSCAR 2-bit KV Cache量化突破
