---
type: source
title: "Let's build GPT: from scratch, in code, spelled out."
source_type: youtube
url: https://www.youtube.com/watch?v=kCc8FmEb1nY
date_accessed: 2026-05-25
date_published: 2023-01-17
tags: [youtube, Andrej Karpathy, GPT, Transformer, Zero to Hero]
---
# Let's build GPT: from scratch, in code, spelled out.

## 摘要
Andrej Karpathy 从零开始构建 GPT（Generatively Pretrained Transformer），全程代码实现。视频覆盖了 "Attention is All You Need" 论文的核心概念以及 OpenAI GPT-2/GPT-3 的实现思路，以 character-level language model 在 Tiny Shakespeare 数据集上训练 Transformer，最后链接到 nanoGPT 项目。这是 Zero to Hero 系列中专注于 Transformer 架构的核心课程。

## 关键要点
- GPT = Generative Pre-trained Transformer，核心是 Transformer 神经网络架构（2017年 "Attention is All You Need" 论文提出）
- ChatGPT 底层就是 GPT 架构 + 预训练+微调多阶段流程
- 视频以 character-level LM 为教学载体：vocab size=65（Tiny Shakespeare 数据集），block size（context length）从8开始
- Token embedding table 将每个整数 token ID 映射为可训练向量，是模型感知输入的入口
- Bigram 模型作为基线：仅根据当前 token 预测下一个，loss 从 ~4.87 开始训练至 ~2.5
- Self-attention 的核心数学技巧：用下三角矩阵（tril）做 masked weighted sum，实现高效并行
- 自回归生成：逐个 token 预测并拼接，使用 softmax + multinomial 采样
- AdamW 优化器（lr=3e-4）替代简单的 SGD
- nanoGPT 项目是该视频的最终产出：约 300 行代码即可定义 GPT 模型，能复现 GPT-2 (124M) 性能
- 视频链接的 GitHub/nanoGPT 等资源形成了完整的 Transformer 学习路径

## 系列关联
- **Zero to Hero 系列**: 该系列从 makemore（简单神经网络语言模型）开始，本视频是 Transformer 篇，后续有 Tokenizer 和 GPT-2 复现等视频
- **前置知识**: 推荐先看 makemore 系列了解 autogressive language modeling 框架和 PyTorch 基础
- **播放量**: 724万（系列最高，远超同类技术视频）

## 相关实体
- [[Andrej-Karpathy]] - 主讲人
- [[nanoGPT]] - 视频产出的开源项目
- [[OpenAI]] - GPT-2/GPT-3 论文来源
- [[PyTorch]] - 使用的深度学习框架
- [[Ilya-Sutskever]] - GPT 系列研究的核心推动者

## 相关概念
- [[GPT]] - Generative Pre-trained Transformer
- [[Transformer]] - 核心神经网络架构
- [[Self-Attention]] - 自注意力机制
- [[Byte-Pair-Encoding]] - GPT 实际使用的 tokenizer（视频中以 char-level 简化教学）

## 相关来源
- Attention is All You Need: https://arxiv.org/abs/1706.03762
- OpenAI GPT-3 paper: https://arxiv.org/abs/2005.14165
- nanoGPT repo: https://github.com/karpathy/nanoGPT
- 本视频 Colab: https://colab.research.google.com/drive/1JMLa53HDuA-i7ZBmqV7ZnA3c_fvtXnx-
- Zero to Hero 播放列表: https://www.youtube.com/watch?v=VMj-3S1tku0&list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ

## 个人思考
724万播放量说明了一切——这是目前最通俗的 Transformer 实现教程之一。Karpathy 的教学特点是"写代码给你看"而非 PPT 讲解，从 empty file 开始逐步构建完整的 GPT。与常见的"调库"教程不同，他深入到 self-attention 的矩阵乘法实现细节（tril trick），让学生真正理解"为什么 attention 能 work"。视频虽然只用了 character-level tokenizer 和 Shakespeare 玩具数据集，但框架完全可迁移到真实 GPT 训练。建议配合后续 tokenizer 和 GPT-2 复现视频一起看，形成完整的 GPT 知识闭环。
