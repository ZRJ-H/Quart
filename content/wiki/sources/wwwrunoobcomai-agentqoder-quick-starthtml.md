---
type: source
title: "Qoder 教程"
source_type: tutorial
url: https://www.runoob.com/ai-agent/qoder-quick-start.html
date_accessed: 2026-06-05
tags: [tutorial, runoob, ai-agent]
---

# Qoder 教程

## 基本信息
- **来源**: 菜鸟教程
- **URL**: https://www.runoob.com/ai-agent/qoder-quick-start.html
- **采集日期**: 2026-06-05
- **章节数**: 2

## 目录
- 概述
- AI Agent(智能体) 教程

---

## 概述

# Qoder 教程

Qoder 是阿里巴巴于 2025 年 8 月正式发布的新一代 Agentic 编程平台，能够深度理解整个代码库、自主完成复杂开发任务的 AI 编程搭档。

Qoder 是一个基于 VSCode 开源代码（code-oss）构建的，所以操作起来跟 VS Code 没什么太大区别。

Qoder 在 VSCode 的基础上，深度定制并内置了 AI 能力（NES、行间对话、Agent、Quest Mode 等），而不是以插件形式附加。

Qoder 个人版目前向所有用户提供免费试用。

## 1、注册并安装 Qoder

注册完成后点击右上角的
下载
按钮，根据你的电脑系统，下载安装程序。

下载后，双击文件开始安装，比如 macOS 只需要拖动应用到应用目录：

然后，双击 Qoder IDE 图标启动 Qoder。

## 2、登录 Qoder

在 Qoder IDE 右上角，点击用户图标，或使用键盘快捷键（⌘ ⇧ ,（macOS）或 Ctrl Shift ,（Windows）），然后选择 登录。

如果还没账号，可以在打开的网页中点击底部的
立即注册
链接注册个账号，或使用 Google 或 GitHub 账号直接注册。

登录成功后，就会返回 Qoder IDE 后，然后我们可以自由使用所有功能。

整个界面上看，Qoder 操作上跟 VS Code 基本也没区别，本身 Qoder 是基于 VSCode 打造的，所以熟悉 VS Code 的用起来也轻车熟路。

## 打开项目

比如，我打开一个的 React 项目：

- 打开 Qoder。
打开 Qoder。

- 方法一：菜单
文件 → 打开文件夹
，选择你的项目文件夹（例如
my-first-react-app
）。
方法一：菜单
文件 → 打开文件夹
，选择你的项目文件夹（例如
my-first-react-app
）。

`my-first-react-app`
- 方法二（推荐）：在终端进入项目目录，然后一键打开：
cd my-first-react-app
qoder .
qoder .
命令会直接用 Qoder 打开当前文件夹。
方法二（推荐）：在终端进入项目目录，然后一键打开：

```
cd my-first-react-app
qoder .
```

qoder .
命令会直接用 Qoder 打开当前文件夹。

`qoder .`
现在你看到左侧文件 explorer，显示项目结构（如 src、public 等）。

终端使用唤起 Qoder 使用以下命令：

```
qoder
```

使用 Qoder 打开当前目录命令：

```
qoder .
```

指定目录路径使用以下命令：

```
qoder ~/runoob-test     # 打开指定目录的项目
```

## 相关链接

- Qoder 官网：
https://qoder.com/
- Qoder 文档：
https://docs.qoder.com/zh/quick-start
- Qoder 命令行工具：
https://docs.qoder.com/zh/cli/quick-start

---

## AI Agent(智能体) 教程

# AI Agent(智能体) 教程

AI Agent 称为智能体，本质是自动执行任务的程序，核心在于让模型不只回答问题，而是按步骤完成动作。

AI Agent（人工智能代理）
是一个能够感知环境、进行决策并执行行动，以达成特定目标的智能软件实体，它不仅仅是回答问题的聊天机器人，更是能够动手做事的智能执行者。

Agent = LLM (大脑) + Planning (规划) + Tool use (执行) + Memory (记忆)。

快速体验 0 代码，一句话生成应用：
https://www.miaoda.cn/
。

## 谁适合阅读本教程？

- 想使用 AI 自动化日常任务的人
- 对编程不熟但想用 AI 做实际工作的新人
- 已会基本电脑操作、但对 Agent/工作流 等概念零基础的人
- 想把 AI 从聊天提升到真正干活的人

## 课程内容

## 什么是 Agent？

Agent 就是一个能干活的智能助手。

Agent = LLM (大脑) + Planning (规划) + Tool use (执行) + Memory (记忆)。

学习 Agent 需要思维转变： 从
对话框问答
进化为
目标驱动的任务执行
。

传统的软件程序遵循固定的指令流程：
输入 → 处理 → 输出
，而 AI Agent 则更像一个有自主性的
员工
，它能够：

- 理解任务目标
：明白你想要什么结果
- 制定计划
：思考如何达成目标
- 使用工具
：调用各种资源和 API
- 自我调整
：根据反馈优化策略
- 持续执行
：直到完成任务或遇到无法解决的问题
类比理解：

- 传统程序 = 自动售货机：投币 → 按按钮→ 出商品
- AI Agent = 私人助理：告诉需求 → 助理规划 → 完成任务并汇报

## AI Agent 结构组成

结构由三块组成:

- 目标：
明确任务意图
- 逻辑：
按规则拆成可执行步骤
- 工具：
通过代码或 API 让步骤落地
运行方式:

- 接收输入
- 判断当前任务
- 调用对应工具执行
- 返回结果
- 保留必要上下文
- 支持多轮连续操作
- 遇阻时调整执行步骤
与普通大模型的差异点:

- 普通大模型：生成文本
- Agent：生成行动并执行行动，能完成实际工作
举例：

- 给出目标：如 "规划三天北京行程，预算 5000"。
- 自动检索机票、酒店与价格。
- 自动收集景点信息并做对比。
- 自动生成可执行行程表。
- 具备条件时可继续执行预订操作。

## AI Agent 的工作原理：一个简单的代码示例

让我们通过一个 Python 伪代码示例，直观感受一下 AI Agent 的工作流程。假设我们要创建一个能自动查询天气并给出穿衣建议的简单 Agent。

## 实例

代码解读
：

- WeatherAgent
类定义了一个简单的 Agent 框架。
`WeatherAgent`
- tools
字典定义了 Agent 可以使用的两种"工具"（函数）。
`tools`
- run
方法是核心流程：它
解析
用户指令，
规划
出需要调用
get_weather_api
和
generate_advice
两个工具，然后
按顺序执行
，并将中间结果存入
memory
，最后
输出
整合后的答案。
`run`
`get_weather_api`
`generate_advice`
`memory`

## 学习资源

Google 5 天智能体课程：
https://www.kaggle.com/learn-guide/5-day-agents

微软的课程：
https://github.com/microsoft/ai-agents-for-beginners

Hello-Agents：
https://github.com/datawhalechina/hello-agents

500 个智能体案例：
https://github.com/ashishpatel26/500-AI-Agents-Projects

智能体资源库：
https://github.com/NirDiamant/GenAI_Agents

HF 智能体课程：
https://github.com/huggingface/agents-course
