---
type: source
title: "How I use LLMs"
source_type: youtube
url: https://www.youtube.com/watch?v=EWvNQjAaOHw
date_accessed: 2026-05-25
date_published: 2025-02-27
tags: [youtube, Andrej Karpathy, LLM实践, AI工具, 提示工程]
---

# How I use LLMs

## 基本信息
- **视频ID**: EWvNQjAaOHw | **频道**: Andrej Karpathy
- **时长**: 2:11:12 | **播放**: 2,447,018
- **点赞**: 63,229
- **发布时间**: 2025-02-27
- **系列**: 通用向LLM系列的第二部（实践篇），前作：[[karpathy-deep-dive-llms]]

## 摘要
Karpathy通过大量真实使用案例，展示如何高效利用LLM（ChatGPT、Claude、Gemini、Grok等）进行日常工作。从最基本的文本交互到高级功能（思维模型、工具使用、深度研究、多模态），提供了一套完整的LLM使用方法论。

## 关键要点
- **LLM的本质**：一个"1TB的zip文件"——预训练压缩了整个互联网的知识，后训练赋予助手人格；知识有截止日期，近期信息需靠工具补充
- **模型选择意识**：不同定价层（免费/Plus $20/Pro $200）对应不同模型能力；GPT-4o（旗舰）、GPT-4o mini（轻量）、o1/o3（推理模型）各有适用场景
- **上下文窗口管理**：每次新对话重置token窗口；避免用无关token"污染"上下文（影响性能+增加成本）
- **思维模型(Thinking Models)**：o1/o3/DeepSeek R1等经过RL训练，能"思考"（内部对话）数分钟；适用于数学、代码等复杂问题；简单问题无需使用
- **"LLM委员会"策略**：同时向多个不同模型提问同一问题，比较答案；Karpathy本人同时订阅多个服务
- **工具使用**：
  - 联网搜索：Perplexity（默认首选）、ChatGPT Search、Grok Search
  - 深度研究(Deep Research)：$200/月的Pro功能，模型花10+分钟进行多轮搜索+思考，输出研究报告
  - 文件上传：将文档加入上下文窗口供模型参考
  - Python解释器：ChatGPT Advanced Data Analysis进行数据分析和绘图
  - Claude Artifacts：生成可预览的网页/应用/图表
  - Cursor Composer：AI辅助编程
- **多模态应用**：
  - 语音输入/输出：Advanced Voice Mode实现端到端语音对话
  - 图像输入：OCR识别、截图分析
  - 图像输出：DALL-E、Ideogram等
  - 视频输入/输出：视频理解、Sora/Veo 2视频生成
- **ChatGPT记忆与自定义指令**：模型可记住用户偏好，跨会话保持一致行为
- **自定义GPTs**：创建专用版本的聊天助手

## 相关实体
- [[Andrej-Karpathy]] - 主讲人
- [[OpenAI]] - ChatGPT/GPT-4o/o1/o3开发者
- [[Anthropic]] - Claude开发者
- [[Google]] - Gemini开发者
- [[xAI]] - Grok开发者
- [[Meta]] - Llama系列
- [[deepseek]] - DeepSeek R1
- Microsoft - Copilot
- [[Mistral]] - Le Chat
- [[Perplexity-AI]] - 深度研究服务
- [[Eureka-Labs]] - Karpathy 创立的 AI 原生教育公司
- [[Perplexity-AI]] - AI 搜索引擎，Karpathy 日常首选工具

## 相关概念
- [[推理模型]] - o1/o3/DeepSeek R1等思维模型
- [[LLM工具使用]] - 联网搜索/代码解释器/深度研究
- [[深度研究(Deep Research)]] - 自主多步研究能力
- [[上下文窗口]] - LLM的工作内存
- [[LLM即操作系统]] - Karpathy的核心类比
- [[多模态AI]] - 图像/语音/视频输入输出
- [[Tokenization]] - Token可视化和理解
- [[LLM训练流水线]] - 预训练+后训练

## 个人思考
这是Karpathy"通用向LLM系列"中最实用的视频。核心价值：(1)"LLM委员会"策略比依赖单一模型更可靠；(2)思维模型的正确使用——只在复杂问题上调用，避免浪费；(3)深度研究能力常被低估，实际上是$200/月Pro tier最有价值的功能之一；(4)上下文窗口管理是最高频使用的技巧——保持token窗口干净比任何高级提示词都重要。

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
