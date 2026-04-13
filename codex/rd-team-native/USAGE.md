# rd-team-native 使用说明

本文覆盖两个典型场景：旧项目 / 新项目。

## 一、旧项目中使用（推荐）

### 方式 A：进入旧项目目录执行

```bash
cd /path/to/existing-project
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode feature "给订单模块增加导出 CSV 功能"
```

修复 bug：

```bash
cd /path/to/existing-project
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode bugfix "修复登录接口返回 500，复现步骤：..."
```

重构：

```bash
cd /path/to/existing-project
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode refactor "重构 data 层，保持外部 API 不变"
```

### 方式 B：不切目录，指定 --workdir

```bash
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --workdir /path/to/existing-project \
  --mode feature "新增用户检索功能"
```

---

## 二、新项目中使用

先创建并进入新目录：

```bash
mkdir -p /path/to/new-project
cd /path/to/new-project
```

然后执行：

```bash
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode new_project "从零创建用户中心，支持注册、登录、RBAC"
```

> 建议：新项目场景建议显式使用“从零创建/新建项目”等表述，以降低模式误判概率。

---

## 三、trpc-go + vue 示例

在已有项目中执行（推荐）：

```bash
cd /path/to/trpc-go-vue-project
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode feature \
  "在现有项目上新增用户画像能力。后端使用 trpc-go，前端使用 vue，沿用当前技术栈，不切换框架或语言。"
```

不切目录执行：

```bash
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --workdir /path/to/trpc-go-vue-project \
  --mode feature \
  "新增用户画像能力，保持 trpc-go + vue 技术栈"
```

---

## 四、可选参数

- `--mode auto|new_project|feature|bugfix|refactor`
- `--workdir <项目目录>`
- `--model <模型名>`
- `--objective-file <文件路径>`
- `--dry-run`
- `--verbose`
- `--log-file <日志文件路径>`

示例：

```bash
CODEX_BIN=codex \
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --model gpt-5.4 \
  --mode feature \
  --workdir /path/to/existing-project \
  "新增审计日志导出"
```

从文件读取需求：

```bash
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode bugfix \
  --objective-file ./objective.txt
```

调试预览（不实际执行）：

```bash
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode feature \
  --dry-run --verbose \
  "新增导出功能"
```

保存执行日志：

```bash
/Users/fangken/codex-ai-rd-team/codex/rd-team-native/bin/ai-rd-native \
  --mode bugfix \
  --log-file ./runtime/ai-rd-native.log \
  "修复登录接口500"
```

环境变量兼容：

- `TARGET_WORKDIR`（等价 `--workdir`）
- `CODEX_MODEL`（等价 `--model`）
- `CODEX_BIN`

---

## 五、与 Python 版本的区别

- `python/bin/ai-rd`：走 Python 编排器
- `codex/rd-team-native/bin/ai-rd-native`：纯 Codex 原生工具编排（不走 Python）
