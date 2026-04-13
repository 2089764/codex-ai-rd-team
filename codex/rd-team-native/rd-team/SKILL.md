---
name: rd-team-native
description: Codex 原生多 Agent 软件研发团队（不依赖 Python 编排器）。适用于新建项目、新增功能、修复 bug、代码重构。
---

# 软件研发 Agent Team（Codex 原生）

## 使用方式

输入 `/rd-team <需求>` 启动。

执行规范文件：`./commands/rd-team.md`

## 前置条件

- 需加载角色模板：`../agents/*.md`
- 需读取画像配置：`./shared-rd-resources/tech-profiles/tech-profiles.json`

## 4 种入口场景

- 新建项目
- 新增功能
- 修复 bug
- 代码重构

## 角色成员

- rd-analyst
- rd-architect
- rd-backend-dev
- rd-frontend-dev（按需）
- rd-code-reviewer
- rd-tester

## 工具链调用流程（Codex 原生）

`spawn_agent -> send_input -> wait_agent -> close_agent`

## 关键运行约束

- 每 30 秒轮询一次 `wait_agent`
- 150 秒无有效进展触发重启机制
- 每角色最多重启 2 次
- reviewer/tester 回退最多 2 轮
- analyst 产出 PRD 后必须用户确认
- main 需维护“状态面板 + 通信日志 + 越权审计”
