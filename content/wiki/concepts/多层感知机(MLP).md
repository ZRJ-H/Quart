---
type: concept
name: 多层感知机
category: technical
first_seen: 2022-09-12
last_updated: 2026-05-25
tags: [深度学习, 神经网络, 架构]
---
# 多层感知机(MLP)

## 定义
多层感知机（Multi-Layer Perceptron, MLP）是最经典的神经网络架构，由一个输入层、若干隐藏层（每个隐藏层包含神经元和激活函数）和一个输出层组成。相邻层之间为全连接（Fully Connected）。

## 核心要点
- **通用近似定理**：含至少一个隐藏层的 MLP 可以近似任意连续函数
- **标准 MLP 语言模型**（Bengio et al. 2003）：
  - 嵌入层（Embedding）：将离散 token 映射为稠密向量
  - 隐藏层：全连接 + 非线性激活（tanh/ReLU）
  - 输出层：全连接 + Softmax 归一化
- **激活函数**：早期使用 tanh/sigmoid，现代多用 ReLU 及其变体
- 从 MLP 到 Transformer 的演进：注意力机制替代了全连接层对上下文的"融合"
- **"挤压式"处理的局限**：将所有上下文一次性压入单个隐藏层会损失信息，层次化架构（如 WaveNet、Transformer）更优

## 相关概念
- [[反向传播(Backpropagation)]] - MLP 的训练算法
- [[Softmax与交叉熵(Softmax-CrossEntropy)]] - 分类头部的损失
- [[批归一化(BatchNormalization)]] - 稳定 MLP 训练的技术
- [[权重初始化(Weight-Initialization)]] - 影响 MLP 训练效果
- [[WaveNet]] - MLP 的层次化扩展

## 实际应用
- 前深度学习时代 NLP 的主要架构
- 分类、回归任务的基线模型
- Transformer 中的 FFN（Feed-Forward Network）本质上是 MLP

## 最后更新
- 日期: 2026-05-25
- 更新内容: 创建页面，关联 Karpathy Zero to Hero 系列
