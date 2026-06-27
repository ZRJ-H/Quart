---
type: concept
name: Transformer
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [attention, self-attention, 神经网络架构, deep learning]
---
# Transformer

## 定义
Transformer 是一种基于自注意力机制（Self-Attention）的神经网络架构，由 Google 在 2017 年论文 "Attention is All You Need" 中提出。它完全摒弃了循环和卷积，仅依靠注意力机制在序列元素间建立依赖关系，成为现代大语言模型（LLM）的基础架构。

## 核心要点
- "Attention is All You Need"（2017）是 Transformer 的开山论文
- 原始 Transformer = 编码器（Encoder）+ 解码器（Decoder），用于机器翻译
- GPT 系列 = Decoder-only 变体（移除编码器和交叉注意力）
- 核心组件：多头自注意力（Multi-Head Self-Attention）、位置编码、前馈网络（FFN/MLP）、残差连接、层归一化（LayerNorm）
- Token 间通信通过注意力机制完成，每个 token 独立通过 FFN 做特征变换
- 残差流：残差连接在梯度反向传播时提供干净的通道，是训练深度 Transformer 的关键
- Self-attention 的计算复杂度为 O(n²)（n 为序列长度），是 Transformer 的主要计算瓶颈
- GPT-2 引入了 Pre-normalization（LayerNorm 移到 attention/FFN 之前），提高训练稳定性

## Transformer 架构演进

| 变体 | 年份 | 核心改动 | 代表模型 |
|------|------|----------|----------|
| 原始 Transformer | 2017 | Encoder-Decoder 结构 | 机器翻译 |
| GPT | 2018 | Decoder-only | GPT-1/2/3/4 |
| BERT | 2018 | Encoder-only | BERT, RoBERTa |
| GPT-2 | 2019 | Pre-normalization, GELU | GPT-2 |
| Llama | 2023 | RoPE, SwiGLU, RMSNorm | Llama 1/2/3 |

## 相关概念
- [[GPT]] - Decoder-only Transformer
- [[Self-Attention]] - Transformer 的核心计算机制
- [[GPT-2]] - Transformer 在 GPT 系列中的具体实现

## 实际应用
暂无

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建，基于 Karpathy Zero to Hero 系列视频
