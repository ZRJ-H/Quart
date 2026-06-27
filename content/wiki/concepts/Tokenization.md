---
type: concept
name: Tokenization
category: technical
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [LLM, Token, 分词, NLP, BPE]
---
# Tokenization

## 定义
将原始文本转换为Token（词元）序列的过程，是LLM理解人类语言的第一道工序。Token是模型的"基本计算单元"，每一次预测一个token，消耗一定计算资源。

## 核心要点
- Tokenization是理解LLM行为的关键：模型的世界由Token组成，而非字符或单词
- BPE（Byte Pair Encoding）是最主流的分词算法，用于GPT/LLaMA等现代LLM，通过合并高频字节对逐步构建词表
- GPT-2 tokenizer：vocab size=50,257（50,000 BPE merges + 256 byte tokens + 1 special token）
- GPT-4 tokenizer：vocab size≈100,000，通过翻倍词汇量提升文本密度，优化Python空格处理
- Tokenizer是LLM pipeline中完全独立的预处理阶段：有自己的训练集、训练算法（BPE）、编码/解码函数
- BPE训练：从256个byte tokens开始，迭代找最频繁相邻token对→合并→追加到词汇表
- BPE编码：字符串→UTF-8 bytes→按merges顺序贪心合并→token IDs
- BPE解码：token IDs→查表得bytes→拼接→UTF-8 decode→字符串（需errors="replace"处理非法UTF-8）
- 不同分词器对同一文本的分词结果不同——如"hello world"和"helloworld"在tokenizer眼中完全不同
- Token数量≈计算量≈"思考时间"：推理时每个新token的计算量与上下文长度成正比
- Tokenizer的词汇表本质是"硬编码"——白名单/黑名单机制决定了哪些词被保留或拆分
- 在线可视化工具：tiktokenizer.vercel.app可查看任意文本的分词结果

## Tokenization 导致的问题
- **拼写困难**：token不是字符级，模型看不到字母，很难做拼写任务
- **非英语劣势**：非英语token更碎片化，序列更长，在有限context中效能下降
- **算术不准**：数字可能被拆分为多个token（如677→两个token），破坏数值理解
- **Python编码低效**：GPT-2中空格缩进每个空格一个token，极其浪费；GPT-4改进
- **SolidGoldMagikarp现象**：罕见token导致模型行为异常
- **格式偏好**：YAML比JSON token效率高，因此推荐使用YAML

## Tokenizer 类型对比

| 类型 | 词汇量 | 序列长度 | 代表 |
|------|--------|----------|------|
| Character-level | 很小（~65） | 很长 | Karpathy教学示例 |
| Word-level | 很大（10万+） | 较短 | 传统NMT |
| BPE (subword) | 中等（5-10万） | 适中 | GPT, LLaMA, BERT |
| Byte-level | 256 | 极长 | MegaByte（研究阶段） |

## 相关概念
- [[Byte-Pair-Encoding]] - BPE算法的详细实现
- [[GPT]] - 使用BPE tokenizer的模型
- [[GPT-2]] - GPT-2的tokenizer规格（50,257 tokens）
- [[LLM训练流水线]] - Tokenization是流水线的数据预处理阶段

## 实际应用
暂无

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建（旧版）
- 日期: 2026-05-25
- 更新内容: 大幅扩展，追加BPE训练/编码/解码流程、GPT-2/GPT-4 tokenizer规格对比、tokenization导致的问题清单
