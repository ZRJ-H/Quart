---
type: concept
name: RNN（循环神经网络）
category: technical
first_seen: 2015-05-21
last_updated: 2026-05-25
tags: [深度学习, 序列建模, NLP, RNN]
---
# RNN（循环神经网络）

## 定义
循环神经网络（Recurrent Neural Network）是一类专门处理序列数据的神经网络架构，通过维护内部隐藏状态（hidden state），使得网络的输出不仅依赖于当前输入，还依赖于过去所有输入的历史。RNN 理论上图灵完备，可以模拟任意程序。

## 核心要点
- 核心能力：处理输入和/或输出为序列的数据，灵感来自"运行固定程序处理输入和内部变量"
- Vanilla RNN 更新公式：h_t = tanh(W_hh * h_{t-1} + W_xh * x_t)
- RNN 可以堆叠为多层结构，每层接收上层的输出作为输入
- "训练普通神经网络是优化函数，训练循环神经网络是优化程序"
- 实践中多使用 LSTM（长短期记忆网络）而非 Vanilla RNN，因为 LSTM 的更新方程和反向传播动力学更好
- 在 Transformer 兴起之前，RNN/LSTM 是 NLP 和序列建模的主导架构

## 相关政策/事件
- 2015 年 Karpathy 发表 "The Unreasonable Effectiveness of RNNs"，极大推动了 RNN 的普及
- 2014 年 Sutskever 等人发表 "Sequence to Sequence Learning with Neural Networks"
- RNN 推动了深度学习的序列建模革命

## 相关概念
- [[LSTM]] - 最常用的 RNN 变体
- [[Attention机制]] - 解决 RNN 长距离依赖问题的重要创新（Karpathy 在 2015 年即预言其重要性）
- [[Character-Level Language Model]] - RNN 的重要应用

## 相关实体
- [[Andrej-Karpathy]] - RNN 普及的重要推动者
- [[Ilya-Sutskever]] - Seq2Seq 论文作者
- [[DeepMind]] - Neural Turing Machines 论文

## 实际应用
- 机器翻译（Seq2Seq）
- 语音识别
- 文本生成（字符级和词级）
- 图像描述（Image Captioning）
- 视频分类

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
