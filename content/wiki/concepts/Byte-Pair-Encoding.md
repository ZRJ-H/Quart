---
type: concept
name: Byte-Pair-Encoding
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [BPE, tokenizer, 分词算法, LLM]
---
# Byte-Pair-Encoding (BPE)

## 定义
Byte Pair Encoding（字节对编码）是一种数据压缩算法，被广泛用于 LLM 的 tokenization 阶段。BPE 从 256 个基础 byte tokens 开始，迭代地找到并合并最频繁出现的相邻 token 对，逐步构建词汇表。该算法被 OpenAI GPT 系列和众多主流 LLM 采用。

## 核心要点
- 算法起点：UTF-8 编码的原始字节序列（256 个基础 tokens）
- 迭代过程：统计相邻 token 对出现频率 → 找到最高频对 → 合并为新 token（追加到词汇表）→ 重复
- 每次合并将词汇表大小 +1，序列长度缩短
- 词汇表大小是超参：GPT-2=50,257，GPT-4≈100,000
- 训练：在独立训练集上执行 BPE 算法，记录所有 merges
- 编码（encode）：输入字符串 → UTF-8 bytes → 按 merges 顺序贪心匹配合并 → token IDs
- 解码（decode）：token IDs → 查表得到 bytes → 拼接 → UTF-8 decode → 字符串
- 解码需用 errors="replace" 处理非法 UTF-8（对于解码器生成的 token 序列很常见）
- 训练集配比影响各语言的 token 效率：英语占比高 → 更紧凑；非英语占比低 → 更碎片化
- BPE 词汇表形成一个"森林"而非树——每个 merge 像二叉树节点，但不同分支不共享根

## BPE vs 其他方案

| 方案 | 词汇量 | 序列长度 | 代表模型 |
|------|--------|----------|----------|
| Char-level | 很小（~65-200） | 很长 | 教学示例 |
| Word-level | 很大（~10万+） | 较短 | 早期 NMT |
| BPE (subword) | 中等（5-10万） | 适中 | GPT, LLaMA, BERT |
| Byte-level (无 tokenizer) | 256 | 很长 | MegaByte（研究阶段） |

## 相关概念
- [[Tokenization]] - BPE 是 Tokenization 的一种具体算法
- [[GPT]] - 使用 BPE tokenizer 的模型系列
- [[GPT-2]] - GPT-2 使用的 BPE tokenizer 规格

## 相关实体
- [[Andrej-Karpathy]] - 从零实现 BPE 的教学者
- [[OpenAI]] - GPT 系列 BPE tokenizer 的开发者

## 实际应用
- GPT-2/GPT-3/GPT-4 的 tokenizer（tiktoken 库）
- LLaMA 系列 tokenizer（SentencePiece + BPE）
- BERT 的 WordPiece 类似 BPE 但略有不同

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建，基于 Karpathy 视频中从零实现的 BPE
