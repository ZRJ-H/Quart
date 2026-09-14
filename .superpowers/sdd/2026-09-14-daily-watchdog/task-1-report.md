# Task 1 实施报告

## 变更摘要

- 新增 `worker/daily-watchdog.js`：使用 `Asia/Shanghai` 计算日期，并行检查四个日报页面；仅将 404 视为缺失，其它页面错误 fail closed。
- 缺失时查询 GitHub Actions workflow runs；存在 `queued` 或 `in_progress` 时返回 `collection-active`，否则仅向 `main` dispatch 一次并要求 HTTP 204。
- 使用依赖注入的 `fetch`/`now`，所有请求均 await；结构化日志只包含日期、缺失栏目、状态，不记录 token 或响应正文。
- 新增 `tests/daily-watchdog.test.mjs`，覆盖日期边界、健康、活动任务、dispatch、页面错误和 dispatch 错误。

## 测试证据

- RED 阶段：已写测试后尝试运行 `node --test tests/daily-watchdog.test.mjs`；本机执行器持续返回 `helper_unknown_error`，Node 进程未能启动，因此未取得运行输出。
- GREEN 阶段：同一执行器故障仍在，未能运行目标测试；`git diff --check` 已通过。

## Commit

`5aceb5b feat: add daily publication watchdog`

## 注意

工作区执行器在本次任务中无法稳定启动 Node/读取文件的辅助进程，故测试运行证据受环境限制；未修改 Task 2/3 文件，未 push。
