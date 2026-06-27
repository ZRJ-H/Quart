---
type: concept
name: Self-Attention
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [attention, transformer, 神经网络, NLP]
---
# Self-Attention

## 定义
Self-Attention（自注意力机制）是 Transformer 架构的核心计算单元。它允许序列中的每个 token 通过加权求和的方式"关注"其他所有 token，权重由 token 间的相似度决定。在自回归语言模型中，使用因果掩码（causal mask）确保每个 token 只能关注其左侧的 token。

## 核心要点
- 每个 token 发射三个向量：Query（查询）、Key（键）、Value（值）
- 注意力分数 = Query 与所有 Key 的点积 → softmax 归一化 → 加权求和 Value
- 数学表达：Attention(Q,K,V) = softmax(QK^T/√d_k) V
- 缩放因子 √d_k 防止点积随维度增大而过大，导致 softmax 梯度消失
- 因果掩码（causal/autoregressive mask）：上三角矩阵设为 -inf，确保无法看到未来 token
- 多头注意力（Multi-Head Attention）：并行运行多个注意力头，拼接结果，捕捉不同子空间的关系
- QKV 合并计算 + split 是多头注意力的高效实现方式（Karpathy GPT-2 复现中使用）
- 计算复杂度 O(n² d)，n=序列长度，d=特征维度——长序列时计算开销极大
- Karpathy 用下三角矩阵（tril）乘法的技巧实现高效的批量因果注意力计算

## 相关概念
- [[Transformer]] - Self-Attention 所属的架构
- [[GPT]] - 使用因果自注意力的模型
- [[GPT-2]] - Self-Attention 在 GPT-2 中的具体参数

## 实际应用
暂无

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建，基于 Karpathy Zero to Hero 系列视频
