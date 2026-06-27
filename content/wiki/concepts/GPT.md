---
type: concept
name: GPT
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [LLM, Transformer, 自回归模型, OpenAI]
---
# GPT

## 定义
GPT（Generative Pre-trained Transformer）是一种基于 Transformer 解码器架构的自回归语言模型。由 OpenAI 提出，核心思想是大规模无监督预训练 + 有监督微调。GPT 系列模型是 ChatGPT 的基础技术栈。

## 核心要点
- GPT = Generative（生成式）+ Pre-trained（预训练）+ Transformer（架构）
- 自回归（autoregressive）：逐个 token 预测下一个 token，生成序列
- 只有 Transformer 解码器（decoder-only），没有编码器（encoder），与原始 Transformer 不同
- 因果掩码（causal mask）：每个 token 只能关注其左侧的 token，不能看到未来
- 三阶段训练：预训练（next token prediction）→ SFT（指令微调）→ RLHF（人类偏好对齐）
- GPT-1（2018, 117M）、GPT-2（2019, 最高1.5B）、GPT-3（2020, 175B）、GPT-4（2023）等迭代
- 缩放定律（Scaling Laws）：模型参数、数据量、计算量同步扩大时，性能持续提升

## 相关概念
- [[Transformer]] - GPT 的基础架构
- [[Self-Attention]] - GPT 的核心机制
- [[GPT-2]] - GPT 系列的具体实现版本
- [[Tokenization]] - GPT 使用的分词方案
- [[Byte-Pair-Encoding]] - GPT 使用的 BPE 分词算法
- [[缩放定律]] - GPT 系列的规模扩展规律

## 相关实体
- [[OpenAI]] - GPT 系列模型的开发者
- [[Andrej-Karpathy]] - 著名 GPT 教学和开源实现者
- [[nanoGPT]] - Karpathy 的 GPT 开源实现

## 实际应用
- ChatBot（ChatGPT、Copilot 等）
- 代码生成（GitHub Copilot 基于 GPT 架构）
- 文本补全和写作辅助
- 多模态扩展（GPT-4V 增加视觉理解）

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建，基于 Karpathy Zero to Hero 系列视频
