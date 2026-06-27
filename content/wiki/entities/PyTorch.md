---
type: entity
name: PyTorch
category: tools
first_seen: 2022-09-07
last_updated: 2026-05-25
tags: [深度学习框架, AI, 开源]
---
# PyTorch

## 基本信息
- **类型**: 深度学习框架
- **开发者/主体**: Meta（原Facebook）AI Research
- **主要功能**: 张量计算、自动微分、神经网络构建与训练
- **首次发布**: 2016年

## 核心特性
- 动态计算图（Define-by-Run），调试方便
- `torch.Tensor`：多维数组，支持 GPU 加速
- `torch.autograd`：自动微分引擎，自动计算梯度
- `torch.nn`：模块化的神经网络层库
- 生态丰富（HuggingFace Transformers, TorchVision, TorchAudio 等）
- Karpathy 的 Zero to Hero 系列中从 micrograd 过渡到 PyTorch，清晰展示了自动微分引擎的原理到生产级实现的完整谱系

## 事件时间线
| 日期 | 事件 | 来源 |
|------|------|------|
| 2016 | PyTorch 首次发布 | - |
| 2017 | PyTorch 1.0 预览版发布 | - |
| 2022-09 | Karpathy Zero to Hero 系列开始使用 PyTorch 教学 | [[karpathy-makemore-part1]] |

## 相关实体
- [[Andrej-Karpathy]] - 在其教学系列中大量使用 PyTorch
- [[DeepMind]] - 主要使用 JAX/ TensorFlow，与 PyTorch 竞争

## 相关概念
- [[反向传播与自动微分(Backpropagation-Autograd)]] - PyTorch 的核心引擎
- [[多层感知机(MLP)]] - 可用 PyTorch 实现的架构

## 最后更新
- 日期: 2026-05-25
- 更新内容: 创建页面，关联 Karpathy Zero to Hero 系列
