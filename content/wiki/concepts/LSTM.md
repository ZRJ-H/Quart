---
type: concept
name: LSTM
category: technical
first_seen: 1997-01-01
last_updated: 2026-05-25
tags: [深度学习, 序列建模, RNN, 架构]
---
# LSTM（长短期记忆网络）

## 定义
长短期记忆网络（Long Short-Term Memory, LSTM）是 RNN 的一种重要变体，通过引入"门控机制"（输入门、遗忘门、输出门）和细胞状态（cell state）来解决 Vanilla RNN 的梯度消失/爆炸问题。在 Transformer 兴起之前，LSTM 是序列建模的事实标准架构。

## 核心要点
- 比 Vanilla RNN 有更强大的更新方程和更好的反向传播动力学
- 通过门控机制选择性记忆/遗忘信息
- 细胞状态（cell state）提供信息的高速公路，让梯度更顺畅地流动
- Karpathy 在 2015 年的文章发现 LSTM 内部有可解释的"神经元"，如引号检测、行长度追踪等
- 多层 LSTM 堆叠是标准做法
- 在 Transformer（2017）之前，LSTM 主导了 NLP 几乎所有任务

## 相关政策/事件
- 1997 年由 Hochreiter & Schmidhuber 提出
- 2014-2017 年在机器翻译、语音识别、文本生成等领域占据主导地位
- 2017 年 Transformer 论文 "Attention Is All You Need" 后逐渐被取代

## 相关概念
- [[RNN（循环神经网络）]] - LSTM 是 RNN 的变体
- [[Attention机制]] - 取代 LSTM 成为序列建模的核心机制
- [[Character-Level Language Model]] - LSTM 的重要应用
- [[LLM训练流水线]] - 现代 LLM 基于 Transformer，但 LSTM 是重要的历史基础

## 相关实体
- [[Andrej-Karpathy]] - 通过文章和 char-rnn 代码推广 LSTM
- [[Ilya-Sutskever]] - Seq2Seq 研究使用 LSTM

## 实际应用
- 字符级和词级语言模型
- 机器翻译（Seq2Seq with LSTM）
- 语音识别
- 时间序列预测

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
