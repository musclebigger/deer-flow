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

## 职责边界

| 层 | 职责 |
|---|---|
| AI 对话层 | 与用户聊表单字段，收集确认值，**不执行任何 API 调用** |
| Tool 层 | `write_session.py` 写 CSV；`run_meeting.py` 跑全流程 |

---

## 执行流程（必须按此顺序）

### Step 1 — 与用户确认字段值

skill 触发后，**不得直接运行任何脚本**。展示默认值表格，等用户确认或修改：

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

用户修改后更新表格重新展示，直到用户明确回复"确认"。

### Step 2 — 调用 write_session.py 写入 CSV

用户确认后，将所有字段值序列化为 JSON，调用 tool 写入 CSV：

```bash
cd "c:/Users/fuwancheng/Desktop/llm-lab/gsk-gmeeting-agent"
python -m tools.write_session --json '<用户确认的完整字段 JSON>'
```

JSON 示例（只需传入与默认值不同的字段，其余自动使用默认值）：
```json
{
  "meeting_name": "测试会议-CNS-利必通-自动化",
  "province": "安徽",
  "city": "合肥",
  "total_budget": 3000,
  "brand_budgets": {"利必通": 3000},
  "speakers_total": 3,
  "speakers_offline": 3,
  "attendees_total": 18,
  "attendees_offline": 18
}
```

输出两行：
```
<session_id>
<csv_path>
```

记录 session_id，进入下一步。

### Step 3 — 调用 run_meeting.py 执行全流程

```bash
cd "c:/Users/fuwancheng/Desktop/llm-lab/gsk-gmeeting-agent"
python -m tools.run_meeting --session-id <session_id>
```

脚本自动完成：登录 → 枚举解析 → 创建会议 → 提交审批 → 验证审批中。

---

## Tool 说明

| 文件 | 用途 |
|---|---|
| `tools/write_session/` | 接收字段 JSON → 写 CSV → 输出 session_id 和路径 |
| `tools/run_meeting/` | 读取 session CSV → 跑完整流程 → 输出 meeting_id |

CSV 存放路径：`<project_root>/temp/gmeeting_<session_id>.csv`

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

**skill 触发后必须先与用户确认字段，不得直接执行 tool。**

---

## API 路径不确定时

若 run_meeting.py 报 404，用 Playwright 抓取真实端点：

```
browser_navigate: https://gmeeting-dev.igskapp.com/#/login2
# 登录后操作一次添加会议
browser_network_requests: filter="/e2estservice"
# 从网络请求中找到真实路径，更新 scripts/add_meeting.py
```

## 关键注意事项

| 问题 | 解决方案 |
|---|---|
| 产品名称点击无响应 | 点击外层 `el-select__input`，非内层 readonly `<input>` |
| 单点会/多点会不可见 | 先点"确认"触发渐进式展示 |
| 举办地类别不可见 | 选"单点会"后才出现 |
| 城市无法选择 | 等省份选择生效后再操作 |
| 审批中 Tab 点击无效 | 直接导航到 `?status=2` URL |
| API 路径 404 | 用 `browser_network_requests` 抓包确认真实路径 |
