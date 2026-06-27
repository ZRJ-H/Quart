---
type: concept
name: Verifiability (AI)
category: technical
first_seen: 2026-04-30
last_updated: 2026-05-25
tags: [AI, LLM, 自动化框架, Karpathy]
---
# Verifiability (AI)

## 定义
Karpathy 提出的 AI 自动化核心框架："传统软件自动化你能指定的；LLM 和强化学习自动化你能验证的。"如果一个任务有自动化的奖励或成功信号（可验证性），模型就可以通过 RL 训练来掌握它。这是理解 LLM 能力分布（[[Jagged-Intelligence]]）的关键维度。

## 核心要点
- **传统软件**：自动化你能精确指定（specify）的任务
- **LLM + RL**：自动化你能验证（verify）的任务——不需要精确指定怎么做，只需要判断结果好坏
- 可验证的任务特点：可重置、可重复、有明确奖励信号
- 典型可验证领域：数学、编程、测试、基准测试、游戏、工程任务
- 编程 Agent 效果好于普通聊天机器人，因为编程有明确反馈（测试通过/失败、程序运行/崩溃）
- 对创始人的启示：寻找有经济价值但未被前沿实验室充分训练的"可验证领域"
- 即使基础模型在某个领域不强，如果可创建领域特定的 RL 环境，也可以通过微调显著提升

## 相关政策/事件
- 2026 年 Karpathy 在多处阐述此框架
- Sequoia Ascent 2026 上详细展开

## 相关概念
- [[Jagged-Intelligence]] - 可验证性是能力尖峰的核心驱动因素
- [[Agentic-Engineering]] - 需要为 Agent 构建评估循环（可验证性）
- [[Software-3.0]] - 新范式下的自动化边界

## 相关实体
- [[Andrej-Karpathy]] - 提出者

## 实际应用
- 评估 AI 产品/功能的可行性
- 设计 Agent 的自动化反馈回路
- 发现未被开发的 AI 自动化机会

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
