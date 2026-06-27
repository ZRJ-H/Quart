---
type: entity
name: Claude API旧模型停用
category: events
first_seen: 2026-06-14
last_updated: 2026-06-15
tags: [Anthropic, API, 模型生命周期]
---

# Claude API旧模型停用

## 基本信息
- **类型**: 技术事件
- **开发者/主体**: Anthropic
- **主要功能**: Claude Sonnet 4和Opus 4旧版本（20250514版）将于2026年6月15日9:00 AM PT停止响应，叠加Fable 5/Mythos 5被禁，造成API产品线「中空」断层

## 核心特性

- claude-sonnet-4-20250514和claude-opus-4-20250514将于6/15停用
- Agent SDK调用从订阅限制中分离，改为独立月度信用额度
- 旧模型停用+Fable5/Mythos5被禁=API产品线中空断层
- 开发者面临「旧模型停用、新模型被禁」双重困境

## 事件时间线
| 日期 | 事件 | 来源 |
|------|------|------|
| 2026-06-15 | Claude Sonnet 4/Opus 4旧版模型停止响应（9:00 AM PT） | Anthropic官网-2026-06-14-模型停用 |


| 2026-06-15 | 太平洋时间9:00AM，claude-sonnet-4-20250514和claude-opus-4-20250514正式下线，调用旧ID直接返回错误 | [[aitoolsrecap-2026-06-15-Claude-API下线]] |

## 相关实体
- [[Anthropic]] - API运营商

## 相关概念
- [[Anthropic API产品线断层危机]] - 旧模型停用+新模型被禁的组合效应



## 最后更新
- 日期: 2026-06-15
- 更新内容: Sonnet 4/Opus 4旧模型ID正式下线
