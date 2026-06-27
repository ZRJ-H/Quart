---
type: concept
name: 系统1与系统2思维(LLM)
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [LLM, 思维模型, Thinking, System1, System2]
---

# 系统1与系统2思维(LLM)

## 定义
源自丹尼尔·卡尼曼《思考，快与慢》的认知框架，被Karpathy引入LLM领域：当前LLM只有"系统1"（快速直觉响应），缺乏"系统2"（缓慢理性思考）。将时间转换为准确率是LLM的重要发展方向。

## 核心要点
- **系统1（System 1）**：快速、直觉、自动化的思维。当前LLM的默认模式——输入tokens后立即生成下一个token，每个token生成时间大致相同
- **系统2（System 2）**：缓慢、理性、有意识的思维。需要多步推理、回溯、假设检验——当前LLM缺乏此能力
- **LLM的现状**：像"火车轨道"一样单向推进（chunk chunk chunk），无法在回答前"思考"
- **未来方向**：将时间（推理token数量）转化为准确率——模型应该能够在回答前花30分钟"思考"
- **LLM系统2的形态**：树状思维（Tree of Thoughts）、自我反思（Self-Reflection）、重新表述（Rephrasing）等多步推理策略
- 后来出现的推理模型（如o1、DeepSeek R1）通过强化学习部分实现了"系统2"——模型学会了在输出最终答案前进行内部推理

## 相关概念
- [[思维链推理(Chain-of-Thought)]] - 系统2的一种实现形式
- [[推理模型]] - 通过RL获得"系统2"能力的模型
- [[LLM即操作系统]] - Karpathy的LLM类比框架

## 实际应用
暂无

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
