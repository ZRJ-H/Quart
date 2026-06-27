---
type: entity
name: nanoGPT
category: projects
first_seen: 2026-05-25
last_updated: 2026-05-25
tags: [GPT, PyTorch, Transformer, Karpathy, 开源项目]
---
# nanoGPT

## 基本信息
- **类型**: 开源项目
- **开发者/主体**: Andrej Karpathy
- **仓库**: https://github.com/karpathy/nanoGPT
- **主要功能**: 极简的 GPT 训练/微调代码库，约 300 行代码即可定义和训练 GPT 模型

## 核心特性
- 仅两个核心文件：model.py（约 300 行，定义 GPT 模型）+ train.py（约 300 行，训练流程）
- 设计原则：简单、可读、可修改——不是生产级框架而是教学级实现
- 支持加载 OpenAI 官方 GPT-2 权重进行微调
- 在 OpenWebText 上训练可复现 GPT-2 (124M) 性能
- 相关仓库：build-nanogpt（Karpathy 逐 commit 教学版）、llm.c（纯 C 实现的 GPT 训练）

## 事件时间线
| 日期 | 事件 | 来源 |
|------|------|------|
| 2023-01-17 | Karpathy 发布 "Let's build GPT" 视频，展示 nanoGPT 雏形 | [[karpathy-gpt-from-scratch]] |
| 2024-06-09 | Karpathy 发布 "Let's reproduce GPT-2" 视频，build-nanogpt 与 nanoGPT 约 90% 相似 | [[karpathy-reproduce-gpt2]] |

## 相关实体
- [[Andrej-Karpathy]] - 开发者
- [[PyTorch]] - 使用的深度学习框架

## 相关概念
- [[GPT]] - 实现的目标模型类型
- [[GPT-2]] - 可复现的模型规格
- [[Transformer]] - 底层架构
- [[Self-Attention]] - 核心机制

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
