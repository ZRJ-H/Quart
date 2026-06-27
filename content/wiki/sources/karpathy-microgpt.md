---
type: source
title: "microgpt"
source_type: article
url: https://karpathy.github.io/2026/02/12/microgpt/
date_accessed: 2026-05-25
date_published: 2026-02-12
tags: [article, karpathy, blog, LLM, GPT, 深度学习]
---
# microgpt

## 摘要
Karpathy 发布 microgpt——一个仅 200 行纯 Python、零依赖、完整实现 GPT 训练和推理的单一文件。这是 Karpathy 多年简化 LLM 到极致项目（micrograd、makemore、nanogpt）的集大成之作，同时作为艺术品以三联画形式在他的艺术商店销售。文章逐行指导读者理解每个组件：数据集、分词器、自动求导引擎、GPT-2 风格神经网络架构、Adam 优化器、训练循环和推理循环。

## 关键要点
- 200 行纯 Python 实现完整 GPT，零外部依赖
- 使用 32,000 个人名作为数据集，每个名字视为一个"文档"
- 字符级分词器（26 个字母 + BOS 特殊标记，共 27 个词汇）
- 手写 Value 类实现自动求导（autograd），与 PyTorch 的 loss.backward() 算法同源
- 模型架构迷你版 GPT-2：嵌入层、多头自注意力、MLP 层、RMSNorm（替代 LayerNorm）、ReLU（替代 GeLU）
- 仅 4,192 个参数（对比 GPT-2 的 16 亿、现代 LLM 的数千亿）
- 显式使用 KV Cache 进行训练（通常仅在推理中使用）
- Adam 优化器 + 线性学习率衰减
- 训练 1000 步后能生成类似人名的文本

## 相关概念
- [[microgpt]] - Karpathy 的极致简化 GPT 实现
- [[Tokenization]] - 字符级分词器
- [[LLM训练流水线]] - 完整的训练流程
- [[缩放定律]] - 对比 GPT-2 和现代 LLM 的参数规模

## 相关实体
- [[Andrej-Karpathy]] - 作者
- [[Eureka-Labs]] - Karpathy 的教育 AI 公司

## 个人思考
microgpt 体现了 Karpathy 一贯的教育哲学：通过极简实现揭示复杂系统的核心本质。200 行代码覆盖了从数据准备到模型推理的完整流程，是理解 Transformer 架构的绝佳教学工具。文章也展示了"工程简化"与"艺术表达"的交汇——代码本身作为艺术品出售。
