---
type: concept
name: Software 3.0
category: technical
first_seen: 2026-04-30
last_updated: 2026-05-25
tags: [AI, 编程范式, Agent, Karpathy]
---
# Software 3.0

## 定义
Karpathy 提出的编程范式演进第三阶段，通过 prompt、上下文、工具、示例、记忆和指令来编程 LLM，将 LLM 视为可编程计算机——上下文窗口成为主要编程杠杆。这是对 Software 1.0（手动编写显式代码）和 Software 2.0（训练神经网络学得权重）的自然延伸。

## 核心要点
- **Software 1.0**：人类编写显式代码，程序由源代码定义
- **Software 2.0**：人类创建数据集和目标函数，神经网络在权重中学得程序
- **Software 3.0**：人类通过 prompt、上下文、工具来"编程"LLM，LLM 作为上下文解释器执行计算
- 安装范例：传统 shell 脚本（Software 1.0） vs 给 Agent 一段指令文本（Software 3.0）
- MenuGen 案例：传统 Web 应用堆栈（Software 1.0/2.0） vs 多模态模型直接输入输出变换（Software 3.0）
- 核心原则：不是问"AI 能加速什么现有工作？"，而是问"什么信息转换之前不可能，现在变得自然？"

## 相关政策/事件
- 2026 年 4 月 Karpathy 在 Sequoia Ascent 2026 上系统阐述
- [[Agentic-Engineering]] 和 [[Vibe-Coding]] 都是 Software 3.0 范式下的具体实践

## 相关概念
- [[Agentic-Engineering]] - Software 3.0 下的专业工程实践
- [[Vibe-Coding]] - Software 3.0 下的快速原型方式
- Agent-Native Infrastructure - Software 3.0 所需的基础设施
- [[Jagged-Intelligence]] - Software 3.0 中需要管理的 LLM 特性
- [[Agentic Coding]] - Software 3.0 在编程领域的体现

## 相关实体
- [[Andrej-Karpathy]] - 提出者

## 实际应用
- 用指令文本替代复杂 shell 脚本安装软件
- 多模态模型直接处理输入输出（如 MenuGen 模式）
- LLM Wiki 知识库构建

## 最后更新
- 日期: 2026-05-25
- 更新内容: 首次创建
