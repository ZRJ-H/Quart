---
type: concept
name: 微回合交互
category: technical
first_seen: 2026-05-13
last_updated: 2026-05-13
tags: [ai, realtime, interaction, architecture]
---
# 微回合交互（Micro-Turn Interaction）

## 定义
将音频、视频、文本按 200ms 切分为连续"微回合"，实现边听边说的全双工人机交互。由 Thinking Machines Lab 首次作为模型原生能力实现。

## 核心要点
- **打破回合制**：传统 AI 交互是"人说完→AI答→人再说"的单轮对话；微回合模式实现持续流式双向交互
- **200ms 粒度**：每个微回合包含声音情绪、画面表情和文字犹豫等信息，在同一梯度流中捕捉
- **Encoder-Free Early Fusion**：所有模态从零开始联合训练，而非拼接式外部模块
- **竞争指标**：TimeSpeak 64.7 vs 竞品 4.3，CueSpeak 81.7 vs 2.9（数量级碾压）

## 相关政策/事件
- Thinking Machines Lab 2026-05-12 发布首款微回合交互模型

## 相关概念
- [[multi-agent-orchestration]] - Agent 协作中的实时交互需求
- 全双工交互 - 与微回合密切相关

## 实际应用
- AI 智能助手（全双工语音对话）
- AI 编程 Agent（实时协作编码）
- 具身 AI（机器人实时环境交互）
- 实时翻译系统

## 最后更新
- 日期: 2026-05-13
- 更新内容: 首次创建
