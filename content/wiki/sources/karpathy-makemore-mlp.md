---
type: source
title: "Building makemore Part 2: MLP"
source_type: youtube
url: https://www.youtube.com/watch?v=TCH_1BHY58I
date_accessed: 2026-05-25
date_published: 2022-09-12
tags: [youtube, Andrej Karpathy, Neural Networks Zero to Hero, MLP, 深度学习]
---
# Building makemore Part 2: MLP

> 本系列第 3 部分，属于 **Neural Networks: Zero to Hero** 系列。建议先观看 [[karpathy-makemore-part1]]。

## 摘要
基于 **多层感知机（MLP）** 实现字符级语言模型，参考 Bengio et al. 2003 论文。MLP 使用多个前序字符作为上下文（block_size=3），通过嵌入层、隐藏层、输出层的架构预测下一个字符。相比 bigram 模型（仅 1 字符上下文），MLP 能捕捉更长距离依赖。

还系统介绍了机器学习基础概念：学习率调优、超参数、数据划分、过拟合与欠拟合。

## 关键要点
- **嵌入（Embedding）**：将字符映射为低维稠密向量，通过索引或 one-hot 乘以嵌入矩阵 C 实现
- **MLP 架构**：嵌入 -> 展平(view/cat) -> 隐藏层(线性+tanh) -> 输出层 -> Softmax -> 交叉熵损失
- **PyTorch view**：不复制内存，仅改变张量视图，比 cat 更高效
- **交叉熵损失**：`F.cross_entropy(logits, targets)` 融合 log-softmax 和 NLL，更稳定更高效
- **数值稳定性**：手动 Softmax 时 logits 过大会溢出；PyTorch 内置实现会减去最大值
- **学习率搜索**：在 1e-3 到 1 之间指数扫描，绘制 loss-LR 曲线找最优范围
- **Train/Dev/Test 划分**：80%/10%/10%，防止过拟合导致的虚假评估
- **Mini-batch SGD**：每次随机采样 32 个样本，更快但方向有噪声
- **学习率衰减**：训练后期降低学习率，帮助收敛

## 相关实体
- [[Andrej-Karpathy]] - 讲师/作者
- [[PyTorch]] - 实现框架

## 相关概念
- [[多层感知机(MLP)]] - 本视频的核心架构
- [[字符级语言模型(Character-Level-Language-Model)]] - 应用场景
- [[反向传播(Backpropagation)]] - 训练算法
- [[Softmax与交叉熵(Softmax-CrossEntropy)]] - 损失函数
- [[权重初始化(Weight-Initialization)]] - 初始化策略

## 个人思考
Bengio 2003 MLP 语言模型论文是 NLP 里程碑，奠定了嵌入 + 隐藏层 + Softmax 的标准范式。本视频将 20 年前的经典工作以实操方式呈现。

## 参考资料
- Bengio et al. 2003: https://www.jmlr.org/papers/volume3/bengio03a/bengio03a.pdf
- 系列笔记本: https://github.com/karpathy/nn-zero-to-hero/blob/master/lectures/makemore/makemore_part2_mlp.ipynb
