---
type: source
title: "Building makemore Part 3: Activations & Gradients, BatchNorm"
source_type: youtube
url: https://www.youtube.com/watch?v=P6sfmUTpUmc
date_accessed: 2026-05-25
date_published: 2022-10-04
tags: [youtube, Andrej Karpathy, Neural Networks Zero to Hero, BatchNorm, 深度学习]
---
# Building makemore Part 3: Activations & Gradients, BatchNorm

> 本系列第 4 部分，属于 **Neural Networks: Zero to Hero** 系列。建议先观看 [[karpathy-makemore-mlp]]。

## 摘要
深入 MLP 内部，详细审视激活值和梯度的统计特性，以及不当缩放的后果。核心主题：(1) Softmax "过度自信"导致初始 loss 远高于预期；(2) tanh 层饱和导致梯度消失；(3) Kaiming 权重初始化；(4) **Batch Normalization**。

## 关键要点
- **Softmax 初始化诊断**：初始 loss 应为 -ln(1/27)=3.29，过高说明 logits 过大导致"过度自信地犯错"
- **tanh 饱和**：激活值集中在 +/-1 尾部时，局部梯度 (1-t^2) 趋近于 0，梯度被"杀死"
- **Dead Neuron**：若神经元对所有样本都饱和，则永远学不到东西
- **Kaiming Init**：权重初始化为 N(0, gain/root(fan_in))，tanh 的 gain=5/3
- **批归一化（Batch Normalization, 2015）**：
  - 对每个 mini-batch 标准化激活值
  - 引入可学习的 gamma 和 beta，允许网络恢复表达能力
  - 降低对初始化的敏感度，使深层网络训练更稳定
  - 缺点：耦合 batch 内样本，训练/推理行为不同
- 正确初始化使 val loss 从 2.17 改善至 2.10

## 相关实体
- [[Andrej-Karpathy]] - 讲师/作者
- [[PyTorch]] - 实现框架

## 相关概念
- [[批归一化(BatchNormalization)]] - 本视频的核心技术
- [[权重初始化(Weight-Initialization)]] - Kaiming 初始化
- [[多层感知机(MLP)]] - 基础架构
- [[反向传播(Backpropagation)]] - 梯度分析的基础

## 个人思考
本视频是"深度学习诊断实践"的最佳入门。核心观点：框架虽然自动处理反向传播，但激活值和梯度的统计特性仍需手动监控。BatchNorm 的设计哲学——"既然我们希望分布良好，为什么不直接强制标准化"——在深度学习中反复出现。

## 参考资料
- Kaiming Init 论文: https://arxiv.org/abs/1502.01852
- BatchNorm 论文: https://arxiv.org/abs/1502.03167
- PyTorch Internals: http://blog.ezyang.com/2019/05/pytorch-internals/
