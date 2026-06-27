---
type: source
title: "Let's reproduce GPT-2 (124M)"
source_type: youtube
url: https://www.youtube.com/watch?v=l8pRSuU81PU
date_accessed: 2026-05-25
date_published: 2024-06-09
tags: [youtube, Andrej Karpathy, GPT-2, nanoGPT, Transformer, Zero to Hero]
---
# Let's reproduce GPT-2 (124M)

## 摘要
Andrej Karpathy 完整复现 OpenAI GPT-2 124M 参数模型，覆盖从网络构建到优化加速再到完整训练的全流程。视频从加载 Hugging Face 的 GPT-2 权重出发验证实现正确性，然后从随机初始化开始训练，参照 GPT-2 和 GPT-3 论文的超参设置，最终在单 GPU 上约 1 小时/10 美元成本复现并超越原版 GPT-2 (124M) 性能。这是 Zero to Hero 系列中将前序知识（GPT 架构 + Tokenizer）整合为完整训练工程的终极课程。

## 关键要点
- GPT-2 有 4 个规格：124M（12层, 768维, 12头）、355M、774M、1558M
- GPT-2 相对原始 Transformer 的改动：(1) Pre-normalization (LayerNorm 前置) (2) 额外 final LayerNorm (3) GELU 激活函数
- 使用 Hugging Face Transformers 加载预训练权重验证模型实现
- 训练数据从 Tiny Shakespeare 升级到 OpenWebText（~9B tokens）
- 关键优化：torch.compile（~2x 加速）、tf32 精度、梯度累积、学习率预热 + cosine decay
- 参照 GPT-3 论文超参（GPT-2 论文省略了大量训练细节）
- 使用 tiktoken（GPT-2 tokenizer），vocab size=50,257，block size=1024
- Self-attention 使用 QKV 合并计算实现，更高效
- 注意力=通信操作（token 间交换信息），MLP=独立计算操作（每个 token 独立"思考"）
- 残差流：干净的梯度传播路径，Pre-normalization 使得训练更稳定
- 最终成果：复现模型比原版 GPT-2 (124M) validation loss 更低

## 系列关联
- **Zero to Hero 系列**: 本视频是该系列工程最强的一集，整合前两集知识完成完整训练
- **前置知识**: GPT from scratch（Transformer 架构）+ GPT Tokenizer（BPE 分词）
- **播放量**: 108万
- **本视频产出**: build-nanogpt GitHub repo

## 相关实体
- [[Andrej-Karpathy]] - 主讲人
- [[nanoGPT]] - 视频的目标代码仓库
- [[OpenAI]] - GPT-2/GPT-3 论文来源
- [[PyTorch]] - 使用的深度学习框架

## 相关概念
- [[GPT-2]] - 被复现的模型
- [[GPT]] - Generative Pre-trained Transformer
- [[Transformer]] - 基础架构
- [[Self-Attention]] - 注意力机制
- [[Byte-Pair-Encoding]] - GPT-2 tokenizer 使用的算法

## 相关来源
- Attention is All You Need: https://arxiv.org/abs/1706.03762
- OpenAI GPT-2 论文: https://d4mucfpksywv.cloudfront.net/better-language-models/language_models_are_unsupervised_multitask_learners.pdf
- OpenAI GPT-3 论文: https://arxiv.org/abs/2005.14165
- build-nanogpt repo: https://github.com/karpathy/build-nanogpt
- nanoGPT repo: https://github.com/karpathy/nanoGPT
- llm.c repo: https://github.com/karpathy/llm.c

## 个人思考
这是 Karpathy Zero to Hero 系列的集大成之作。四个小时的视频信息密度极高。"~10 美元复现 GPT-2" 的说法非常震撼——2019 年训练 GPT-2 的成本是数百万美元，五年后凭借 PyTorch、torch.compile、GPU 硬件进步和开源生态，个人开发者只需 10 美元就能复现甚至超越。注意视频参照的是 GPT-3 论文的超参而非 GPT-2 —— 这体现了学术论文中"隐藏知识"的现象，成功的工程实践往往需要结合多篇论文才能复现。Pre-normalization 的讲解非常清晰——残差流的干净梯度传播路径是 Transformer 训练稳定的关键设计决策。
