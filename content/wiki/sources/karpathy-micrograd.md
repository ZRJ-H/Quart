---
type: source
title: "The spelled-out intro to neural networks and backpropagation: building micrograd"
source_type: youtube
url: https://www.youtube.com/watch?v=VMj-3S1tku0
date_accessed: 2026-05-25
date_published: 2022-08-16
tags: [youtube, Andrej Karpathy, Neural Networks Zero to Hero, 深度学习, 反向传播]
---
# The spelled-out intro to neural networks and backpropagation: building micrograd

> 本系列第 1 部分，属于 **Neural Networks: Zero to Hero** 系列。

## 摘要
Karpathy 从零开始逐步构建 **micrograd**——一个仅约 100 行 Python 的标量级自动微分引擎。本视频从头讲解反向传播（backpropagation）和神经网络训练的本质：如何使用链式法则（chain rule）计算损失函数对网络权重的梯度，并通过梯度下降优化。整个教学核心是**不依赖任何深度学习框架**，仅用 Python 标量运算演示神经网络训练的全部细节。

micrograd 虽然只是一个教学工具（不适用于生产环境），但它揭示了 PyTorch、JAX 等现代框架底层自动微分引擎的核心原理——所有张量操作、计算图构建、反向传播本质上都是链式法则的递归应用。

## 关键要点
- **micrograd** 是一个标量级的 autograd 引擎（约 100 行代码），完整实现了反向传播
- 反向传播本质上是**链式法则的递归应用**：从输出节点开始，逐层向后求导
- 神经网络只是一类特殊的数学表达式，反向传播适用于任意数学表达式，不限于神经网络
- 梯度（gradient）告诉我们每个参数对损失函数的敏感度
- 通过梯度下降可以迭代地调整权重以最小化损失函数
- 计算图中节点被多次使用时，其梯度等于所有反向路径的梯度之和
- 完整的神经网络库（nn）仅需约 50 行额外代码即可构建在 micrograd 之上
- 从 micrograd 到现代框架的唯一区别是将标量打包为张量以实现并行计算

## 相关实体
- [[Andrej-Karpathy]] - 讲师/作者
- [[PyTorch]] - 类比对象，说明生产级框架的核心原理

## 相关概念
- [[反向传播(Backpropagation)]] - 本视频的核心主题
- [[自动微分(Autograd)]] - micrograd 实现的引擎类型
- [[多层感知机(MLP)]] - 视频末尾构建的神经网络架构

## 个人思考
这是目前网络上最深入浅出的反向传播教学视频之一。亮点在于从极限定义出发理解导数，然后用手工方式一步步走通整个计算图的反向传播过程，最后将一切抽象为 100 行代码。

## 参考资料
- micrograd GitHub: https://github.com/karpathy/micrograd
- 系列笔记本: https://github.com/karpathy/nn-zero-to-hero/tree/master/lectures/micrograd
