---
type: source
title: "Building makemore Part 5: Building a WaveNet"
source_type: youtube
url: https://www.youtube.com/watch?v=t3YJ5hKiMQ0
date_accessed: 2026-05-25
date_published: 2022-11-21
tags: [youtube, Andrej Karpathy, Neural Networks Zero to Hero, WaveNet, CNN, 深度学习]
---
# Building makemore Part 5: Building a WaveNet

> 本系列第 6 部分（完结篇），属于 **Neural Networks: Zero to Hero** 系列。建议先观看 [[karpathy-makemore-backprop]]。

## 摘要
将 2 层 MLP 扩展为树状架构，最终到达类似 **DeepMind WaveNet (2016)** 的层次化卷积架构。WaveNet 原本用于生成原始音频，但其核心设计——**逐步融合上下文信息**——同样适用于字符语言模型。

还介绍了如何将代码重构为类似 PyTorch `torch.nn` 的模块化架构，以及真实的深度学习开发流程。

## 关键要点
- **层次化融合**：逐层两两融合（字符->双字组->四字组->八字组），形成树状结构
- **上下文窗口扩展**：block_size=3 提升到 8 后，val loss 从 2.10 降至 2.02
- **模块化重构**：封装 Embedding/Flatten 模块，使用 Sequential 容器
- **BatchNorm 3D Bug**：当输入变为 BxTxC 时，原始 BatchNorm 只在 dim=0 归一化，需要改为 dim=(0,1)
- **PyTorch Linear 的 Batch 特性**：接受任意形状输入，只在最后维度做矩阵乘法
- 在等参数预算下，层次化架构与扁平 MLP 性能接近
- 增大容量后，val loss 突破 **2.0**（达 1.993）
- **因果空洞卷积**本质上是将外层 for 循环移到 CUDA kernel 内部，同时利用节点复用提升效率

## 相关实体
- [[Andrej-Karpathy]] - 讲师/作者
- [[DeepMind]] - 发表了 WaveNet 论文
- [[PyTorch]] - 实现框架

## 相关概念
- [[WaveNet]] - 本视频构建的架构
- [[多层感知机(MLP)]] - 扩展的起点
- [[批归一化(BatchNormalization)]] - 需要适配 3D 输入
- [[反向传播(Backpropagation)]] - 训练算法

## 个人思考
本视频是系列的自然收尾。展示了两个重要洞察：(1) 深度学习开发中 90% 时间花在追踪张量形状和调试边界条件上；(2) 从扁平 MLP 到层次化卷积架构的演进本质是**先验知识的融入**——信息应该逐步而非一次性融合。

## 参考资料
- WaveNet 论文 (DeepMind 2016): https://arxiv.org/abs/1609.03499
- 系列笔记本: https://github.com/karpathy/nn-zero-to-hero/blob/master/lectures/makemore/makemore_part5_cnn1.ipynb
