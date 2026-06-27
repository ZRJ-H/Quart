---
type: source
title: "Let's build the GPT Tokenizer"
source_type: youtube
url: https://www.youtube.com/watch?v=zduSFxRajkE
date_accessed: 2026-05-25
date_published: 2024-02-20
tags: [youtube, Andrej Karpathy, Tokenizer, BPE, LLM, Zero to Hero]
---
# Let's build the GPT Tokenizer

## 摘要
Andrej Karpathy 系统讲解 LLM 中的 Tokenization 环节，从零实现 OpenAI GPT 系列使用的 Byte Pair Encoding (BPE) 分词算法。视频详细展示了 BPE 的训练、编码、解码全过程，并深入分析了 tokenization 导致的各类 LLM 行为异常。这是 Zero to Hero 系列中专门覆盖 LLM 预处理阶段的课程。

## 关键要点
- Tokenizer 是 LLM pipeline 中完全独立的预处理阶段，有独立的训练集和训练算法（BPE）
- GPT-2 tokenizer: vocab size=50,257（50,000 BPE merges + 256 byte tokens + 1 special end-of-text token）
- GPT-4 tokenizer: vocab size≈100,000，翻倍后文本密度提升
- BPE 算法：从 256 个 byte tokens 开始，迭代寻找最频繁的相邻 token 对，合并为新 token
- 编码（encode）：字符串 → UTF-8 bytes → 按 merges 顺序贪心匹配合并 → token IDs
- 解码（decode）：token IDs → 查 vocab（bytes 拼接）→ UTF-8 decode → 字符串
- 解码时需使用 errors="replace" 处理非法 UTF-8 序列
- 非英语语言因 tokenizer 训练集中占比低，token 更碎片化，序列更长
- Python 缩进空格在 GPT-2 tokenizer 中被拆为单个 token（token 220），GPT-4 改进为合并
- tokenization 是许多 LLM 怪异行为的根源：拼写困难、算术不准、非英语劣化等

## 系列关联
- **Zero to Hero 系列**: 本视频聚焦 LLM pipeline 中的 tokenization 环节
- **前置知识**: 建议先看 GPT from scratch 了解基本 LM 框架
- **播放量**: 110万

## 相关实体
- [[Andrej-Karpathy]] - 主讲人
- [[OpenAI]] - GPT-2/GPT-4 论文来源

## 相关概念
- [[Byte-Pair-Encoding]] - 核心分词算法
- [[Tokenization]] - Tokenization 总论
- [[GPT]] - GPT 系列模型
- [[GPT-2]] - GPT-2 使用的 tokenizer 规格

## 相关来源
- GPT-2 论文: https://d4mucfpksywv.cloudfront.net/better-language-models/language_models_are_unsupervised_multitask_learners.pdf
- tiktokenizer: https://tiktokenizer.vercel.app/
- tiktoken: https://github.com/openai/tiktoken

## 个人思考
Karpathy 反复强调 tokenization 是他"least favorite part"，但正因如此这恰恰是最容易被忽视却最关键的环节。视频中大量"怪现象"演示非常直观——比如同一个 "egg" 单词在句首（2 tokens）vs 前面有空格（1 token）的差异。tokenization 作为硬编码的前处理阶段，本质上是 LLM pipeline 中不可微分的"瓶颈"。这也解释了为什么社区有强烈的 "delete tokenization" 呼声（如 MegaByte 等免分词架构）。GPT-4 为改善 Python 能力而优化空格 tokenization 的做法，展示了 prompt 层面之外的"架构级"优化思路。
