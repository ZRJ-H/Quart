---
type: concept
name: AI原生设备操作系统
category: technical
first_seen: 2026-06-03
last_updated: 2026-06-03
tags: [AI OS, 操作系统, Agent, 设备端AI]
---
# AI原生设备操作系统

## 定义
AI原生设备操作系统是指在操作系统内核层面直接集成AI Agent运行时，使芯片可以直接承载AI Agent与云端通信，而非在应用层运行。微软Project Solara（基于AOSP）是该概念的首个大型商业实现，它将AI Agent从"应用层加载项"变为"操作系统一级公民"。

## 核心要点
- Agent从应用层下沉到操作系统层，重新定义"个人计算"
- 基于AOSP（Android开源项目）构建
- 芯片直接承载AI Agent与云端通信
- 与RTX Spark（硬件）+ DGX Station（桌面站）形成完整闭环
- 对云端AI服务商的定价模式构成根本性挑战——本地优先

## 相关政策/事件
- [[Project Solara]] - 微软Build 2026发布
- [[NVIDIA RTX Spark]] - 硬件生态搭档

## 相关概念
- [[企业级AI Agent桌面部署]] - AI Agent桌面化趋势
- [[去蒸馏化技术竞赛]] - 同期技术自主趋势

## 实际应用
- 个人AI计算机无需网络即可运行Agent
- 企业数据隐私本地化处理
- 消费电子AI功能下沉（手机/平板/PC统一Agent体验）

## 最后更新
- 日期: 2026-06-03
- 更新内容: 首次收录，Project Solara发布
