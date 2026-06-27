---
type: concept
name: MicroVMs
category: technical
first_seen: 2026-06-27
last_updated: 2026-06-27
tags: [Serverless, 虚拟化, AWS, 容器, 云原生]
---
# MicroVMs (微虚拟机)

## 定义
一种轻量级虚拟化技术，在AWS Lambda中首次以"MicroVMs"功能形态发布。MicroVMs在传统Serverless函数执行环境之上提供完全隔离的沙箱，用户拥有完整的生命周期控制权（启动、暂停、销毁），同时保持了Lambda的轻量特性。相比传统VM开销更低，比容器隔离性更强。

## 核心要点
- AWS Lambda首次引入MicroVM隔离机制
- 完全隔离沙箱 + 完整生命周期控制
- 保持Serverless轻量特性的同时提升安全隔离性
- Firecracker等MicroVM技术已在容器领域验证
- Serverless基础设施从共享内核隔离向硬件级隔离演进

## 相关政策/事件
- AWS Lambda MicroVMs功能发布
- 云原生安全隔离技术演进

## 相关概念
- Serverless - 基础计算范式
- 容器隔离 - 传统方案对比
- 云原生 - 技术背景

## 实际应用
- 多租户安全隔离场景
- 不可信代码执行环境
- Serverless函数的更高安全等级计算

## 最后更新
- 日期: 2026-06-27
- 更新内容: 首次创建，记录AWS Lambda MicroVMs发布
