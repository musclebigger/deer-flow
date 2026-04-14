---
name: gmeeting-application-agent
description: 自动化 Gmeeting UAT 季度计划添加会议并提交审批。触发词：添加会议、季度计划、gmeeting、提交审批。
disable-model-invocation: true
allowed-tools:
  - Bash
  - mcp__plugin_playwright_playwright__browser_navigate
  - mcp__plugin_playwright_playwright__browser_snapshot
  - mcp__plugin_playwright_playwright__browser_click
  - mcp__plugin_playwright_playwright__browser_type
  - mcp__plugin_playwright_playwright__browser_wait_for
  - mcp__plugin_playwright_playwright__browser_fill_form
  - mcp__plugin_playwright_playwright__browser_network_requests
---

# Gmeeting 季度计划 — 添加会议 Agent

完成 Gmeeting UAT 端到端流程：**季度计划 → 添加会议 → 提交审批 → 验证审批中**

## 环境

| 项目 | 值 |
|---|---|
| 前端 | `https://gmeeting-dev.igskapp.com` |
| 登录入口 | `https://gmeeting-dev.igskapp.com/#/login2`（UAT 账号密码登录，非 SSO）|
| API Base | `https://gmeeting-dev-api.igskapp.com/e2estservice` |
| 账号 | `ttz79417` / `222222` |

## 实现方式

**优先使用 API 脚本**（快速稳定）；API 路径不确定时用 Playwright MCP 抓包探索。

---

## 方式一：运行 Python 脚本（推荐）

### 执行流程（必须按此顺序）

**Step 1 — 向用户展示默认字段值并逐一确认**

skill 触发后，**不得直接运行脚本**。必须先向用户展示所有字段的默认值，询问是否需要修改：

```
以下是本次添加会议的字段值，请确认或告知需要修改的字段：

| 字段 | 当前值 |
|---|---|
| 会议名称 | 测试会议-CNS-利必通-自动化 |
| 业务部门 | MA CO |
| 治疗领域 | CNS |
| 产品名称 | 利必通 |
| 会议类别 | 全国会 |
| 会议形式 | 线下会议 |
| 单点会/多点会 | 单点会 |
| 举办地类别 | 酒店 |
| 开始年月 | 2026-07 |
| 省/直辖市 | 北京 |
| 城市 | 北京 |
| 计划讲者人数 | 2 |
| 计划讲者人数（线下）| 2 |
| 计划参会者人数 | 20 |
| 计划参会者人数（线下）| 20 |
| 总预算 | 10000 |
| 品牌预算（利必通）| 10000 |

如无修改请回复"确认"，如需修改请告知具体字段和新值。
```

用户回复修改意见后，更新对应字段，再次展示完整表格确认，直到用户明确回复"确认"。

**Step 2 — 生成 session ID 并写入 CSV**

用户确认后，生成 session ID 并将字段值写入 `<skill_dir>/temp/gmeeting_<session_id>.csv`：

```bash
cd "${CLAUDE_SKILL_DIR}/scripts"
python -c "
from form_session import new_session_id, write_csv
from config import DEFAULT_CONFIG
import json, sys

# 将用户确认的字段值合并到 cfg
cfg = dict(DEFAULT_CONFIG)
# （此处由 skill 将用户确认的值注入 cfg）
sid = new_session_id()
path = write_csv(sid, cfg)
print(sid)
print(path)
"
```

记录输出的 session_id，后续步骤使用。

**Step 3 — 运行主脚本**

```bash
cd "${CLAUDE_SKILL_DIR}/scripts"
python add_meeting.py --session-id <session_id>
```

### 脚本说明

| 文件 | 用途 |
|---|---|
| `scripts/config.py` | 默认配置，所有字段默认值 |
| `scripts/form_session.py` | session ID 生成、CSV 读写、确认表格生成 |
| `scripts/auth.py` | 登录，获取 session cookie |
| `scripts/api.py` | 枚举数据获取（部门/治疗领域/产品/省市）及名称→ID 解析 |
| `scripts/add_meeting.py` | 主流程：登录→解析枚举→创建会议→提交审批→验证审批中 |

### 流程步骤

1. 向用户展示字段默认值 → 用户确认或修改
2. 生成 session ID → 写入 `C:/tmp/gmeeting_<session_id>.csv`
3. `login()` — POST `/sys/login3`，session 自动保存 cookie
4. `resolve_ids()` — 获取枚举列表，将中文名称解析为 API 所需 ID/code
5. `create_meeting()` — POST `/planning/meeting/newCreate`，返回 `meeting_id`
6. `submit_meeting()` — POST `/planning/meeting/submit`，传入 `ids`
7. `verify_in_approval()` — POST `/planning/meeting/searchList`，确认会议出现

> 详细 API 端点见 [api-reference.md](api-reference.md)

### API 路径不确定时

若脚本报 404，用 Playwright 抓取真实端点：

```
browser_navigate: https://gmeeting-dev.igskapp.com/#/login2
# 登录后操作一次添加会议
browser_network_requests: filter="/e2estservice"
# 从网络请求中找到真实路径，更新 api.py / add_meeting.py
```

---

## 方式二：Playwright MCP 浏览器自动化

当需要截图验证或 API 方式不可用时使用。

### Step 1 — 登录

```
browser_navigate: https://gmeeting-dev.igskapp.com/#/login2
browser_snapshot → 找用户名/密码框 ref
browser_type: 用户名 → "ttz79417"
browser_type: 密码 → "222222"
browser_click: 登录按钮
browser_wait_for: text="季度计划"
```

### Step 2 — 导航到季度计划

```
browser_navigate: https://gmeeting-dev.igskapp.com/#/stalone/quarterly-plan/q-list
browser_snapshot → 确认"添加会议"按钮可见
```

### Step 3 — 打开表单

```
browser_click: "添加会议"
browser_wait_for: text="会议名称"
```

### Step 4 — 填写表单（每填一字段后截快照确认）

| 字段 | 操作 |
|---|---|
| 会议名称 | `browser_type` 直接输入 |
| 业务部门 | `browser_click` 下拉 → 等待选项 → 点击"MA CO" |
| 治疗领域 | 同上，选"CNS" |
| 产品名称 | ⚠️ 点击**外层** `el-select__input`（非内层 readonly input）→ 选"利必通" |
| 会议类别/形式 | 默认已选，截快照确认即可 |
| 单点会/多点会 | ⚠️ 初始隐藏，先点"确认"触发展示，再选"单点会" |
| 举办地类别 | ⚠️ 选"单点会"后才出现，选"酒店" |
| 开始年月 | 点日期选择器，导航到"2026-07" |
| 省/直辖市 | 下拉选"北京" |
| 城市 | 等省份生效后，下拉选"北京" |
| 人数字段 | 依次输入 2 / 2 / 20 / 20 |
| 总预算 | 输入"10000" |
| 品牌预算 | 输入"10000" |

### Step 5 — 渐进式确认（最多 3 次）

```
browser_click: "确认"
browser_snapshot → 检查是否有新必填字段（红色高亮）
# 有新字段 → 填写 → 再次点"确认"
# 重复直到出现"添加会议成功"
browser_wait_for: text="添加会议成功"
browser_click: 成功对话框"确认"
```

典型节奏：第1次确认触发"单点会/多点会"，第2次触发"举办地类别"，第3次成功。

### Step 6 — 待提交 Tab 确认

```
browser_wait_for: text="待提交"
browser_snapshot → 确认新会议卡片可见
```

### Step 7 — 提交审批

```
browser_click: 会议卡片复选框
browser_click: "提交"
browser_wait_for: text="提交后不可修改"
browser_click: "确认"
browser_wait_for: text="提交成功"
browser_click: "确认"
```

### Step 8 — 验证审批中

```
browser_navigate: https://gmeeting-dev.igskapp.com/#/stalone/quarterly-plan/q-list?status=2
browser_snapshot → 确认会议卡片出现
```

---

## 默认字段值

| 字段 | 默认值 |
|---|---|
| 会议名称 | 测试会议-CNS-利必通-自动化 |
| 业务部门 | MA CO |
| 治疗领域 | CNS |
| 产品名称 | 利必通 |
| 会议类别 | 全国会 |
| 会议形式 | 线下会议 |
| 单点会/多点会 | 单点会 |
| 举办地类别 | 酒店 |
| 开始年月 | 2026-07 |
| 省/直辖市 | 北京 |
| 城市 | 北京 |
| 计划讲者人数 | 2 |
| 计划讲者人数（线下）| 2 |
| 计划参会者人数 | 20 |
| 计划参会者人数（线下）| 20 |
| 总预算 | 10000 |
| 品牌预算（利必通）| 10000 |

用户未提供字段值时使用上表默认值。**skill 触发后必须先向用户展示字段表格并等待确认，不得直接执行脚本。**

## 关键注意事项

| 问题 | 解决方案 |
|---|---|
| 产品名称点击无响应 | 点击外层 `el-select__input`，非内层 readonly `<input>` |
| 单点会/多点会不可见 | 先点"确认"触发渐进式展示 |
| 举办地类别不可见 | 选"单点会"后才出现 |
| 表单第一次点"确认"未提交 | 正常，填新字段后再次点"确认" |
| 城市无法选择 | 等省份选择生效后再操作 |
| 审批中 Tab 点击无效 | 直接导航到 `?status=2` URL |
| API 路径 404 | 用 `browser_network_requests` 抓包确认真实路径 |
