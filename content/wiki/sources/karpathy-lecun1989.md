---
type: source
title: "Deep Neural Nets: 33 years ago and 33 years from now"
source_type: article
url: https://karpathy.github.io/2022/03/14/lecun1989/
date_accessed: 2026-05-25
date_published: 2022-03-14
tags: [article, karpathy, blog, 深度学习, 历史, LeNet]
---
# Deep Neural Nets: 33 years ago and 33 years from now

## 摘要
Karpathy 复现了 Yann LeCun 等人 1989 年的经典论文"Backpropagation Applied to Handwritten Zip Code Recognition"（公认最早的端到端反向传播神经网络实际应用），以此作为案例研究来审视深度学习在 33 年间的进步轨迹，并展望未来 33 年。

## 关键要点
- **1989 年网络规格**：仅 9,760 个参数、64K MACs、1K 激活值、4 层卷积网络，在 SUN-4/260 工作站上训练 3 天
- **复现结果**：在 MNIST 子集上测试误差 4.09%（与原论文 5.00% 接近，但数据有差异）
- **33 年进步指标**：
  - 数据集规模扩大 ~100,000,000 倍（像素数据量）
  - 模型参数扩大 ~1,000,000 倍
  - 计算速度提升 ~3,000 倍（MacBook Air M1 vs SUN-4/260）
- **"时间旅行"优化实验**：
  - MSE → Softmax + Cross-Entropy：大幅改善训练
  - SGD → AdamW：小幅改善
  - 数据增广（平移 1px）：测试误差降至 2.19%
  - 添加 Dropout + ReLU：测试误差降至 1.59%（错误减少 60%）
  - 扩大训练集 7 倍 + 现代技术：测试误差降至 1.25%
- **核心洞察**：宏观上 33 年没有太大变化——仍在做端到端可微神经网络，用反向传播和 SGD 优化
- **对 2055 年的预测**：
  - 模型和数据集比今天大 10,000,000 倍
  - 今天的模型可以在个人设备上 1 分钟训练完成
  - 从零训练特定任务的模型正在过时，被微调/提示工程/蒸馏取代
  - 最终极形式：用自然语言向"神经网络巨脑"下达指令

## 相关概念
- [[LeNet]] - 1989 年论文中的早期卷积神经网络
- [[Foundation-Models]] - GPT 等基础模型
- [[缩放定律]] - 规模扩大带来的性能提升
- [[神经网络训练配方]] - 现代优化技巧

## 相关实体
- [[Andrej-Karpathy]] - 作者/复现者
- [[Yann-LeCun]] - 原始论文作者
- [[OpenAI]] - GPT、CLIP 等基础模型开发者
- [[Yann-LeCun]] - 1989 年论文作者，深度学习先驱

## 个人思考
这篇文章巧妙地用"时间旅行"思维实验展示了深度学习领域的真实进步轨迹。最令人震惊的不是技术变化有多大，而是"没怎么变"——1989 年的论文放在今天仍然像一个现代深度学习论文的缩小版。Karpathy 对 2055 年的外推暗示：未来的 AI 开发将主要是与巨型预训练模型对话，而非从零训练。这个预测在 2026 年的 Agent 时代已经部分成真。
