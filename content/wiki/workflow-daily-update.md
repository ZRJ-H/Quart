# 每日Wiki更新工作流

## 使用方法

### 手动触发
在OpenClaw/WorkBuddy中执行：
```
请处理今日的时政要闻/AI科技动态/GitHub Trending，并同步GitHub项目档案，更新Wiki系统
```

### 自动执行流程

当收到"更新Wiki"指令时，执行以下步骤：

## 步骤0：同步GitHub项目档案（新增）

```bash
# 检查GitHub项目档案目录是否有新文件
rtk diff <(ls /Users/fjj/Documents/Obsidian/GitHub\ 项目档案/ | sort) <(ls /Users/fjj/Documents/Obsidian/wiki/entities/ | sort)

# 同步新文件
rtk cp "/Users/fjj/Documents/Obsidian/GitHub 项目档案/"*.md "/Users/fjj/Documents/Obsidian/wiki/entities/"

# 为新文件添加type字段
python3 << 'EOF'
import os
import re

entities_dir = "/Users/fjj/Documents/Obsidian/wiki/entities"
source_dir = "/Users/fjj/Documents/Obsidian/GitHub 项目档案"

for filename in os.listdir(source_dir):
    if filename.endswith('.md'):
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(entities_dir, filename)
        
        # 检查是否已存在
        if not os.path.exists(target_path):
            # 复制文件
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加type字段
            if not re.search(r'^type:', content, re.MULTILINE):
                content = re.sub(r'^(---)\n', r'---\ntype: entity\n', content, count=1)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Synced: {filename}")
        else:
            # 更新已有文件（检查last_seen字段）
            with open(source_path, 'r', encoding='utf-8') as f:
                source_content = f.read()
            with open(target_path, 'r', encoding='utf-8') as f:
                target_content = f.read()
            
            # 提取last_seen
            source_last_seen = re.search(r'last_seen:\s*(\d{4}-\d{2}-\d{2})', source_content)
            target_last_seen = re.search(r'last_seen:\s*(\d{4}-\d{2}-\d{2})', target_content)
            
            if source_last_seen and target_last_seen:
                if source_last_seen.group(1) > target_last_seen.group(1):
                    # 源文件更新，覆盖目标文件
                    if not re.search(r'^type:', source_content, re.MULTILINE):
                        source_content = re.sub(r'^(---)\n', r'---\ntype: entity\n', source_content, count=1)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(source_content)
                    print(f"Updated: {filename}")
                else:
                    print(f"Up to date: {filename}")
EOF
```

## 步骤1：读取今日数据

```bash
# 读取时政要闻
cat /Users/fjj/Documents/Obsidian/时政要闻/$(date +%Y-%m-%d).md

# 读取AI科技动态
cat /Users/fjj/Documents/Obsidian/AI科技动态/$(date +%Y-%m-%d).md

# 读取GitHub Trending
cat /Users/fjj/Documents/Obsidian/GitHub\ Trending/$(date +%Y-%m-%d).md
```

## 步骤2：创建来源摘要页

为每个来源创建 `wiki/sources/{日期}-{来源名}.md`

格式参考：
```yaml
---
type: source
title: {来源标题}
source_type: {类型}
url: local
date_accessed: {日期}
date_published: {日期}
tags: [标签1, 标签2]
---
# {来源标题}

## 摘要
{来源摘要}

## 关键要点
- 要点1
- 要点2

## 相关实体
- [[实体1]] - {关联说明}

## 相关概念
- [[概念1]] - {关联说明}

## 个人思考
{个人思考和启发}
```

## 步骤3：识别新实体/概念

检查今日内容中出现的：
- **新项目/产品** → 创建实体页
- **新政策/趋势** → 创建概念页
- **已有实体的新事件** → 更新实体页的事件时间线

## 步骤4：创建/更新实体页

### 新实体
创建 `wiki/entities/{实体名}.md`

格式参考：
```yaml
---
type: entity
name: {实体名称}
category: {分类}
first_seen: {日期}
last_updated: {日期}
tags: [标签1, 标签2]
---
# {实体名称}

## 基本信息
- **类型**: {类型}
- **开发者/主体**: {开发者}
- **主要功能**: {功能描述}

## 核心特性
- 特性1
- 特性2

## 事件时间线
| 日期 | 事件 | 来源 |
|------|------|------|
| {日期} | {事件描述} | [[来源页]] |

## 相关实体
- [[相关实体1]] - {关系说明}

## 最后更新
- 日期: {日期}
- 更新内容: {更新内容}
```

### 已有实体
更新事件时间线和相关信息

## 步骤5：创建/更新概念页

### 新概念
创建 `wiki/concepts/{概念名}.md`

格式参考：
```yaml
---
type: concept
name: {概念名称}
category: {分类}
first_seen: {日期}
last_updated: {日期}
tags: [标签1, 标签2]
---
# {概念名称}

## 定义
{概念定义}

## 核心要点
- 要点1
- 要点2

## 相关实体
- [[相关实体1]] - {关系说明}

## 最后更新
- 日期: {日期}
- 更新内容: {更新内容}
```

### 已有概念
更新关联信息和实际应用

## 步骤6：更新索引

更新 `wiki/index.md`：
- 添加新实体到实体表格
- 添加新概念到概念表格
- 添加新来源到来源表格
- 更新快速导航

## 步骤7：记录日志

在 `wiki/log.md` 追加：
```markdown
## [{日期}] ingest | {来源标题}
- 读取来源: {来源路径}
- 创建来源摘要: [[来源页]]
- 创建实体: [[实体1]], [[实体2]]
- 创建概念: [[概念1]]
- 更新已有实体: [[实体3]]
- 更新 index.md 索引
```

## 步骤8：健康检查（可选）

每周执行一次：
- 检查孤儿页面
- 检查页面间矛盾
- 检查过时信息
- 生成健康检查报告

---

## 快速命令参考

### 每日更新
```
更新今日Wiki
```

### 健康检查
```
检查Wiki健康状况
```

### 查询测试
```
基于Wiki分析{主题}
```

---

*工作流版本: v1.0*
*创建日期: 2026-05-09*
