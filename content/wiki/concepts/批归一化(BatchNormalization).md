---
type: concept
name: 批归一化
category: technical
first_seen: 2022-10-04
last_updated: 2026-05-25
tags: [深度学习, 神经网络, 训练技术]
---
# 批归一化(Batch Normalization)

## 定义
批归一化（Batch Normalization, BatchNorm）由 Ioffe & Szegedy 于 2015 年提出，是深度学习中最重要的规范化技术之一。它对每个 mini-batch 的激活值进行标准化（减去均值除以标准差），然后通过可学习的缩放（gamma）和偏移（beta）参数恢复表达能力。

## 核心要点
- **核心操作**：BN(x) = gamma * (x - mean)/std + beta
- mean 和 std 在训练时由当前 batch 计算，推理时使用全局移动平均
- gamma 和 beta 是可学习参数，通过反向传播更新
- **三大优势**：
  - 大幅降低对权重初始化的敏感度
  - 允许使用更大的学习率
  - 对深层网络训练起到稳定作用
- **缺点与陷阱**：
  - 训练和推理行为不同，需注意切换 `model.eval()`
  - 耦合 batch 内样本——batch size 过小时估计不准
  - 输入维度变化时（如 2D->3D），需要在正确维度上做归一化
  - 与残差连接、LayerNorm 相比，在 Transformer 中已较少使用

## 相关政策/事件
- **BatchNorm 论文** (Ioffe & Szegedy, 2015, Google): 开创性的规范化技术
- **LayerNorm** (Ba et al., 2016): 在 Transformer 中替代 BatchNorm
- **GroupNorm** (Wu & He, 2018): 适用于小 batch size 的场景

## 相关概念
- [[反向传播(Backpropagation)]] - BatchNorm 的反向传播较复杂
- [[多层感知机(MLP)]] - BatchNorm 常见的应用场景
- [[权重初始化(Weight-Initialization)]] - BatchNorm 降低了对初始化的依赖

## 实际应用
- 现代 CNN 的标准组件
- MLP 和部分 RNN 架构中使用
- Transformer 中已被 LayerNorm 取代

## 最后更新
- 日期: 2026-05-25
- 更新内容: 创建页面，关联 Karpathy Zero to Hero 系列
