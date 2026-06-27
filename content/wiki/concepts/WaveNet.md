---
type: concept
name: WaveNet
category: technical
first_seen: 2022-11-21
last_updated: 2026-05-25
tags: [深度学习, 生成模型, 音频, 架构]
---
# WaveNet

## 定义
WaveNet 是 DeepMind 于 2016 年提出的深度生成模型，用于原始音频波形生成。其核心创新是 **因果空洞卷积（Dilated Causal Convolution）** 架构，通过层次化逐步融合信息来实现大感受野。后被证明可泛化至任何序列建模任务。

## 核心要点
- **层次化融合（Hierarchical Fusion）**：与将上下文一次性压平的 MLP 不同，WaveNet 逐层两两融合（字符->双字组->四字组->...），形成树状结构
- **空洞卷积（Dilated Convolution）**：通过在卷积核中插入空洞来指数级扩大感受野，无需增加参数量
- **因果卷积（Causal Convolution）**：保证预测只依赖过去信息，不泄露未来
- WaveNet 的树状结构本质上是对 MLP "平铺"式处理的改进——信息融合应该是渐进的
- PyTorch 中实现等价效果：用 `FlattenConsecutive(2)` + Linear 替代空洞卷积操作
- 模型本质是 MLP + 树状层次化结构；真正的卷积实现只是让滑动窗口计算更高效

## 相关政策/事件
- **WaveNet 论文** (van den Oord et al., 2016, DeepMind): 原始音频生成
- **PixelCNN**：将类似架构用于图像生成
- 受 WaveNet 启发的序列建模架构：TCN (Temporal Convolutional Networks)

## 相关实体
- [[DeepMind]] - 发表 WaveNet 论文

## 相关概念
- [[多层感知机(MLP)]] - WaveNet 的起点架构
- [[批归一化(BatchNormalization)]] - WaveNet 中的重要组件
- [[字符级语言模型(Character-Level-Language-Model)]] - WaveNet 可用于文本建模

## 实际应用
- Google Assistant 中的语音合成（使用 WaveNet 引擎）
- 音乐生成（Magenta Studio）
- 文本转语音（TTS）系统
- 任何序列到序列的建模任务

## 最后更新
- 日期: 2026-05-25
- 更新内容: 创建页面，关联 Karpathy Zero to Hero 系列
