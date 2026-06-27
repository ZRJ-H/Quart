---
type: source
title: "Building makemore Part 4: Becoming a Backprop Ninja"
source_type: youtube
url: https://www.youtube.com/watch?v=q8SA3rM6ckI
date_accessed: 2026-05-25
date_published: 2022-10-11
tags: [youtube, Andrej Karpathy, Neural Networks Zero to Hero, 反向传播, 深度学习]
---
# Building makemore Part 4: Becoming a Backprop Ninja

> 本系列第 5 部分，属于 **Neural Networks: Zero to Hero** 系列。建议先观看 [[karpathy-makemore-batchnorm]]。

## 摘要
去掉 PyTorch autograd 的 `loss.backward()`，**手动**对整个 2 层 MLP（含 BatchNorm）进行反向传播。手动推导交叉熵损失、线性层、tanh、BatchNorm、嵌入表的梯度。训练的是**张量级别**的反向传播直觉——与 micrograd（标量级别）不同，这里需要在矩阵维度上正确实现链式法则。

配套 Colab 练习，建议先自己尝试实现再对照答案。

## 关键要点
- **反向传播是"渗漏的抽象"（leaky abstraction）**：理解底层原理对调试现代神经网络至关重要
- **关键操作的反向传播公式**：
  - 交叉熵 -> dlogprobs = -1/N（正确位置）/ 0（其他）
  - Log -> dprobs = dlogprobs / probs
  - Softmax 需要处理广播和 max 索引回溯
  - 矩阵乘法 Y = XW + B -> dX = dY W^T, dW = X^T dY, dB = sum(dY, axis=0)
  - BatchNorm -> 需要处理均值和方差的反向传播
  - Embedding -> 将梯度通过 scatter/one-hot 分散回正确位置
- **形状一致性检查**：梯度张量的形状必须与对应参数张量完全相同
- 维度分析法比记忆公式更可靠

## 相关实体
- [[Andrej-Karpathy]] - 讲师/作者
- [[PyTorch]] - 仅用 Tensor 做矩阵运算（去掉 autograd）

## 相关概念
- [[反向传播(Backpropagation)]] - 手动实现的练习
- [[自动微分(Autograd)]] - 被去掉的自动微分层
- [[多层感知机(MLP)]] - 被反向传播的网络
- [[批归一化(BatchNormalization)]] - 包含的层
- [[Softmax与交叉熵(Softmax-CrossEntropy)]] - 损失函数

## 个人思考
从标量到张量级别的反向传播是一个重要的认知跃迁。最大的启发：通过维度匹配就能推导出正确的梯度公式——不需要记忆，只需要知道输入/输出的形状。BatchNorm 的反向传播确实是系列中最复杂的部分。

## 参考资料
- Yes you should understand backprop: https://karpathy.medium.com/yes-you-should-understand-backprop-e2f06eab496b
- 练习 Colab: https://colab.research.google.com/drive/1WV2oi2fh9XXyldh02wupFQX0wh5ZC-z-?usp=sharing
