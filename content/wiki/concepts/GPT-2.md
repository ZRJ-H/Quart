---
type: concept
name: GPT-2
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [GPT-2, OpenAI, 语言模型, Transformer]
---
# GPT-2

## 定义
GPT-2 是 OpenAI 于 2019 年发布的自回归语言模型系列，是 GPT-1 的扩展。GPT-2 首次展示了大规模语言模型在零样本（zero-shot）场景下跨任务泛化的能力。它包含 4 个规格的模型，从 124M 到 1.5B 参数。GPT-2 也是首个公开权重和代码的 GPT 系列模型，为后续 GPT-3/ChatGPT 和整个开源 LLM 生态奠定了基础。

## 核心要点
- 发布年份：2019，论文 "Language Models are Unsupervised Multitask Learners"
- 4 个规格：124M（12层/768维/12头）、355M（24层/1024维/16头）、774M（36层/1280维/20头）、1558M（48层/1600维/25头）
- 相对原始 Transformer 的三项改动：Pre-normalization、额外 final LayerNorm、GELU 激活
- 使用 BPE tokenizer，vocab size=50,257，context length=1024
- Decoder-only 架构：无编码器、无交叉注意力
- 采用因果掩码（causal mask）实现自回归生成
- 预训练数据：WebText（约 800 万网页，Reddit 3+ karma 的外链）
- 训练超参细节较模糊——GPT-3 论文提供了更详细的超参配置
- OpenAI 因安全顾虑推迟发布完整 1.5B 模型，先发布小规格版本
- 2024 年复现成本已降至 ~10 美元/小时（单 GPU），相对于 2019 年的数百万美元训练成本

## GPT-2 架构参数

| 模型 | 参数 | 层数 | 维度 | 注意力头 | 词汇表 |
|------|------|------|------|----------|--------|
| small | 124M | 12 | 768 | 12 | 50,257 |
| medium | 355M | 24 | 1024 | 16 | 50,257 |
| large | 774M | 36 | 1280 | 20 | 50,257 |
| xl | 1558M | 48 | 1600 | 25 | 50,257 |

## 相关概念
- [[GPT]] - GPT 系列总论
- [[Transformer]] - GPT-2 基于 Transformer 架构
- [[Self-Attention]] - GPT-2 的核心机制
- [[Byte-Pair-Encoding]] - GPT-2 的 tokenizer 算法
- [[缩放定律]] - GPT-2 miniseries 验证的规律

## 相关实体
- [[OpenAI]] - GPT-2 的开发者
- [[Andrej-Karpathy]] - 复现 GPT-2 并开源实现
- [[nanoGPT]] - Karpathy 的 GPT-2 复现实现

## 实际应用
暂无

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建，基于 Karpathy 复现 GPT-2 视频
