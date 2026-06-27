---
type: concept
name: microgpt
category: technical
first_seen: 2026-02-12
last_updated: 2026-05-25
tags: [GPT, LLM, Karpathy, 极简实现, 深度学习]
---
# microgpt

## 定义
Karpathy 开发的极简 GPT 实现——一个单一文件、200 行纯 Python、零外部依赖，完整实现从数据集加载到模型推理的 GPT 训练流程。这是 Karpathy 多年致力于简化 LLM 的集大成之作（micrograd → makemore → nanogpt → microgpt）。

## 核心要点
- 200 行 Python 代码实现完整 GPT：数据集、分词器、自动求导、GPT-2 架构、Adam 优化器、训练循环、推理循环
- 仅 4,192 个参数（对比 GPT-2 的 16 亿）
- 字符级分词器，词汇量仅 27（26 字母 + BOS 特殊标记）
- 手写 Value 类实现 autograd，算法与 PyTorch 的 loss.backward() 同源
- 显式 KV Cache 训练（通常仅在推理中使用）
- 使用 32,000 个人名作为数据集演示
- 训练 1000 步后能生成类似人名的文本
- 同时作为艺术三联画在 karpathy.art 出售

## 相关政策/事件
- Karpathy 的简化 LLM 系列：micrograd（自动求导）→ makemore（生成模型）→ nanogpt（GPT 实现）→ microgpt（极简 GPT）
- 2026 年 2 月发布，被称为"LLM 的本质"

## 相关概念
- [[LLM训练流水线]] - microgpt 覆盖完整训练流程
- [[Tokenization]] - 使用的字符级分词
- [[Agentic-Engineering]] - microgpt 作为教育工具在 Agent 时代的价值
- [[缩放定律]] - microgpt 的微小参数规模形成对比

## 相关实体
- [[Andrej-Karpathy]] - 创建者
- [[Eureka-Labs]] - 所属公司

## 实际应用
- 作为 LLM 教育的教学工具
- 作为 Agent 环境下可审查的"小型化"知识产物
- 验证 GPT 架构的算法本质

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
