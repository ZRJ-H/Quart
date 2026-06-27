---
type: concept
name: Softmax与交叉熵
category: technical
first_seen: 2022-09-07
last_updated: 2026-05-25
tags: [深度学习, 损失函数, 分类]
---
# Softmax与交叉熵损失

## 定义
**Softmax** 将实数向量（logits）映射为概率分布：p_i = exp(l_i) / sum(exp(l_j))。**交叉熵损失（Cross-Entropy Loss）** 衡量模型预测分布与真实分布的差异。对分类任务，二者的组合是标准输出层设计。

## 核心要点
- **负对数似然（Negative Log Likelihood, NLL）**：语言模型的标准损失函数
  - Loss = -1/N * sum(log(p_correct))
  - 理想情况下概率为 1，log(1)=0，loss=0
  - 最坏情况下概率趋近 0，log(0) 趋近 -inf
- **数值稳定性**：
  - 手动实现 Softmax 时，logits 过大会导致 e^100 溢出
  - 解决方法：减去每行的最大值，使最大值为 0
  - PyTorch 的 `F.cross_entropy` 内部自动处理此问题
- Softmax 输出的和为 1，是一个有效的概率分布
- 交叉熵损失 = -sum(y * log(p))，对于 one-hot 标签等价于 NLL

## 反向传播
- 交叉熵 + Softmax 的组合梯度形式简洁：dloss/dlogits = probs - y (one-hot)
- 这是 PyTorch 使用 fused kernel 高效实现的原因之一

## 相关概念
暂无

## 实际应用
- 所有多分类问题的标准输出层
- 语言模型的生成头部（预测下一个 token）
- 图像分类网络的最后一层

## 最后更新
- 日期: 2026-05-25
- 更新内容: 创建页面，关联 Karpathy Zero to Hero 系列
