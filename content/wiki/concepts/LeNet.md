---
type: concept
name: LeNet
category: technical
first_seen: 1989-01-01
last_updated: 2026-05-25
tags: [深度学习, 计算机视觉, CNN, 卷积神经网络, 历史]
---
# LeNet

## 定义
Yann LeCun 等人在 1989-1998 年间开发的早期卷积神经网络架构，是最早成功应用于实际问题的神经网络之一。1989 年的版本用于手写邮编识别，1998 年的 LeNet-5 成为 MNIST 手写数字识别的基准模型。

## 核心要点
- 1989 年版：4 层卷积网络，仅 9,760 个参数、64K MACs、1K 激活值
- 在 SUN-4/260 工作站上训练 3 天，处理 7,291 张 16x16 灰度图像
- 使用反向传播 + SGD 进行端到端训练——早期里程碑
- Karpathy 2022 年的复现：MacBook Air M1 仅需 90 秒（3,000x 速度提升）
- 原始网络使用 tanh 激活、MSE 损失函数
- 通过现代技术改进（交叉熵、AdamW、数据增广、Dropout、ReLU），错误率可降低 60%

## 相关政策/事件
- 1989 年论文 "Backpropagation Applied to Handwritten Zip Code Recognition" — 首次端到端反向传播实际应用
- 1998 年 LeNet-5 论文发布，同时发布 MNIST 数据集
- 2022 年 Karpathy 发表复现文章，对比 33 年间进步

## 相关概念
- [[Foundation-Models]] - LeNet 是"从零训练"时代的代表，与基础模型范式形成对比
- [[缩放定律]] - LeNet 与现代网络的规模对比
- [[神经网络训练配方]] - 现代技巧对 LeNet 的改进效果

## 相关实体
- [[Yann-LeCun]] - 创造者
- [[Andrej-Karpathy]] - 复现并分析

## 实际应用
- 手写数字/邮编识别
- CNN 架构的起点
- 深度学习历史研究的重要案例

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
