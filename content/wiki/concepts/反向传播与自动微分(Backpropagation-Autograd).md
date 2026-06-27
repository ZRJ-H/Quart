---
type: concept
name: 反向传播与自动微分
category: technical
first_seen: 2022-08-16
last_updated: 2026-05-25
tags: [深度学习, 神经网络, 梯度, 算法]
---
# 反向传播与自动微分

## 定义
**反向传播（Backpropagation）** 是训练神经网络的**核心算法**。它通过链式法则（Chain Rule）从输出反向传播梯度，高效计算损失函数对所有权重的偏导数。**自动微分（Autograd）** 是反向传播的编程实现——自动维护计算图并沿反方向累积梯度。

## 核心要点
- 本质是**链式法则的递归应用**：从输出节点开始，逐层向后求导
- 梯度告诉我们每个参数对损失函数的敏感度——参数往梯度反方向调整即可降低损失
- 计算图中节点被多次使用时，反向传播需累加所有路径的梯度（gradient accumulation）
- **标量级别**的 Autograd（如 micrograd）仅需约 100 行代码即可实现
- **张量级别**的 Autograd（如 PyTorch）需正确处理矩阵乘法和各类操作的形状匹配
- 现代框架（PyTorch/TensorFlow/JAX）自动实现 autograd，但理解底层原理对调试和优化至关重要

## 关键公式
- 链式法则：dz/dx = dz/dy * dy/dx
- 加法节点：梯度直接分发到所有输入
- 乘法节点：局部梯度 = 另一个输入的值
- tanh 激活：局部梯度 = 1 - tanh(x)^2

## 相关政策/事件
- **micrograd** (2020, Karpathy): 100 行标量级 autograd，纯教学目的
- **PyTorch autograd** (2017): 生产级张量自动微分系统
- 深度学习框架演进：从手动写 backward（2010 年左右标准做法）到全自动 autograd

## 相关概念
- [[多层感知机(MLP)]] - 反向传播主要应用的架构
- [[Softmax与交叉熵(Softmax-CrossEntropy)]] - 常见训练损失函数
- [[批归一化(BatchNormalization)]] - 涉及复杂的梯度传播
- [[权重初始化(Weight-Initialization)]] - 影响梯度流动的质量

## 实际应用
- 所有深度学习模型的训练
- GPT、BERT、CNN、RNN 等现代架构均依赖反向传播

## 最后更新
- 日期: 2026-05-25
- 更新内容: 创建页面，关联 Karpathy Zero to Hero 系列
