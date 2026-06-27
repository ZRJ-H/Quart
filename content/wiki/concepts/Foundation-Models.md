---
type: concept
name: Foundation Models
category: technical
first_seen: 2022-03-14
last_updated: 2026-05-25
tags: [AI, LLM, 预训练, 基础模型]
---
# Foundation Models

## 定义
"基础模型"（Foundation Model）指在大规模数据上预训练的通用 AI 模型（如 GPT、CLIP），可以被轻量级微调、提示工程或蒸馏后，应用于众多下游任务。这一概念由斯坦福 HAI 在 2021 年提出，Karpathy 在 2022 年的 Lecun1989 复现文章中将其作为关键趋势展开。

## 核心要点
- 与 "从零训练" 范式形成对比：绝大多数应用不再需要从零训练神经网络
- 仅由少数机构（如 OpenAI、Google、Meta）训练基础模型
- 大多数应用通过以下方式实现：
  - 轻量级微调（fine-tuning）部分网络层
  - 提示工程（prompt engineering）
  - 知识蒸馏（distillation）到更小的专用推理网络
- Karpathy 预测此趋势将持续加强
- 极端外推：2055 年你直接向"神经网络巨脑"说英语来执行任务，而非自己训练

## 相关政策/事件
- 2021 年 Stanford HAI 提出 "Foundation Model" 术语
- Karpathy 2022 年在 [[karpathy-lecun1989]] 文章中将其与 LeNet 时代对比
- 2026 年的 Agent 时代，基础模型 + Agent 已成为主流工作方式

## 相关概念
- [[缩放定律]] - 基础模型的基础——规模扩大带来能力涌现
- [[LLM训练流水线]] - 基础模型的训练过程
- [[Software-3.0]] - 基础模型作为编程平台
- [[Jagged-Intelligence]] - 基础模型的能力分布特征

## 相关实体
- [[OpenAI]] - GPT 系列基础模型
- [[Yann-LeCun]] - 从早期 CNN 到基础模型范式的见证者

## 实际应用
- ChatGPT / Claude / Gemini 等对话 AI
- 通过 API 使用预训练模型构建应用
- Agent 基于基础模型进行推理和操作

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
