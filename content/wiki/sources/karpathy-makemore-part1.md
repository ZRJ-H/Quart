---
type: source
title: "The spelled-out intro to language modeling: building makemore"
source_type: youtube
url: https://www.youtube.com/watch?v=PaCmpygFfXo
date_accessed: 2026-05-25
date_published: 2022-09-07
tags: [youtube, Andrej Karpathy, Neural Networks Zero to Hero, 语言模型, 深度学习]
---
# The spelled-out intro to language modeling: building makemore

> 本系列第 2 部分，属于 **Neural Networks: Zero to Hero** 系列。建议先观看 [[karpathy-micrograd]]。

## 摘要
进入语言建模领域。Karpathy 构建了 **makemore**——一个字符级 bigram 语言模型，输入名字数据集（32,000 个名字），学习生成"听起来像名字"的新字符串。

本视频的核心教学目标：(1) 引入 **PyTorch Tensor**（对比上一节纯 Python 的 micrograd），展示如何使用张量高效地计算神经网络；(2) 建立语言模型的完整框架：模型训练、采样、损失评估。

从最简单的计数法 bigram 模型开始，然后过渡到基于 PyTorch Tensor 的实现，引入多项式采样（multinomial）、广播（broadcasting）等关键概念。

## 关键要点
- **字符级语言模型**：将每个单词视为字符序列，模型学习预测序列中的下一个字符
- **Bigram 模型**：仅依赖前一个字符预测下一个字符，最简单的语言模型
- **计数法实现**：创建 27x27（26 字母 + 特殊标记 "."）的计数矩阵，通过频率归一化得到概率分布
- **PyTorch Tensor 入门**：torch.tensor、索引、数据类型、torch.multinomial 采样
- **广播（Broadcasting）** 是 PyTorch 中极易出错但极为重要的概念——错误方向广播会导致静默 bug
- **负对数似然（NLL）**：语言模型的标准损失函数

## 相关实体
- [[Andrej-Karpathy]] - 讲师/作者
- [[PyTorch]] - 本视频的核心工具

## 相关概念
- [[字符级语言模型(Character-Level-Language-Model)]] - 本视频构建的模型类型
- [[Softmax与交叉熵(Softmax-CrossEntropy)]] - 负对数似然与交叉熵的关系

## 个人思考
从 micrograd 过渡到 PyTorch Tensor 是精心设计的教学节奏——先理解数学本质，再引入效率工具。广播部分特别好，展示了一个简单错误（忘记 keepdim）如何导致静默 bug。

## 参考资料
- makemore GitHub: https://github.com/karpathy/makemore
- 系列笔记本: https://github.com/karpathy/nn-zero-to-hero/blob/master/lectures/makemore/makemore_part1_bigrams.ipynb
