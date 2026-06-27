---
type: concept
name: 权重初始化
category: technical
first_seen: 2022-10-04
last_updated: 2026-05-25
tags: [深度学习, 神经网络, 训练技术]
---
# 权重初始化

## 定义
权重初始化决定了神经网络在训练开始前的参数状态。不当的初始化会导致梯度消失/爆炸或模型"过度自信地犯错"。Kaiming He 等人（2015）提出的 **Kaiming 初始化**是目前最通用的初始化方法。

## 核心要点
- **Softmax 初始化**：输出 logits 应接近 0 或相等，使初始概率分布接近均匀
  - 初始 loss 应约等于 -ln(1/vocab_size)，若远高于此则需调整
- **tanh/ReLU 初始化**：隐藏层激活值不应集中在饱和区域
  - tanh 饱和 => 梯度消失 (1-t^2 接近 0)
  - ReLU 死区 => 梯度完全为 0
- **Kaiming Init 公式**：权重 ~ N(0, gain/root(fan_in))
  - tanh 的 gain = 5/3
  - ReLU 的 gain = root(2)
  - Linear 的 gain = 1
- **PyTorch 实现**：`torch.nn.init.kaiming_normal_` 或 `kaiming_uniform_`
- 正确初始化 vs 错误初始化：小模型相差不大，深层网络差异显著
- 现代技术（BatchNorm、Residual Connections、Adam 优化器）大幅降低了对精确初始化的依赖

## 相关概念
- [[批归一化(BatchNormalization)]] - 降低初始化敏感度
- [[反向传播(Backpropagation)]] - 初始化影响梯度流动
- [[多层感知机(MLP)]] - 初始化主要的应用场景

## 实际应用
- 任何深度神经网络的训练起点
- 尤其重要：深层 CNN、Transformer、ResNet

## 最后更新
- 日期: 2026-05-25
- 更新内容: 创建页面，关联 Karpathy Zero to Hero 系列
