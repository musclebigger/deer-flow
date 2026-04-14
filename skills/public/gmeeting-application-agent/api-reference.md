# Gmeeting UAT API Reference

Base URL: `https://gmeeting-dev-api.igskapp.com/e2estservice`

所有请求需携带登录后的 Cookie（通过 session 自动管理）。

---

## 认证

### POST /auth/login

登录获取 Cookie。

```json
Request:
{ "username": "ttz79417", "password": "222222" }

Response:
{ "code": 0, "data": { "token": "..." } }
```

---

## 枚举数据

### GET /common/department/list
获取业务部门列表。返回 `[{ "id": "...", "name": "MA CO" }, ...]`

### GET /common/therapy-area/list
获取治疗领域列表。返回 `[{ "id": "...", "name": "CNS" }, ...]`

### GET /common/product/list
获取产品列表（可传 `therapyAreaId` 过滤）。

### GET /common/province/list
获取省份列表。返回 `[{ "code": "...", "name": "北京" }, ...]`

### GET /common/city/list?provinceCode=xxx
获取城市列表，依赖省份 code。

---

## 会议操作

### POST /meeting/create
创建会议。

```json
{
  "meetingName": "测试会议-CNS-利必通-自动化",
  "department": "<dept_id>",
  "therapyArea": "<ta_id>",
  "products": ["<product_id>"],
  "meetingType": "全国会",
  "meetingFormat": "线下会议",
  "locationType": "单点会",
  "venueType": "酒店",
  "startMonth": "2026-07",
  "province": "<province_code>",
  "city": "<city_code>",
  "speakersTotal": 2,
  "speakersOffline": 2,
  "attendeesTotal": 20,
  "attendeesOffline": 20,
  "totalBudget": 10000,
  "brandBudgets": [{ "productId": "<product_id>", "budget": 10000 }]
}
```

Response: `{ "code": 0, "data": { "id": "<meeting_id>" } }`

### POST /meeting/submit
提交审批。

```json
{ "meetingIds": ["<meeting_id>"] }
```

### GET /meeting/list?status=2
查询会议列表。`status=1` 待提交，`status=2` 审批中。

---

## 注意事项

- 若以上路径返回 404，使用 Playwright MCP 的 `browser_network_requests` 工具抓取真实 API 端点。
- 枚举字段（meetingType、meetingFormat 等）的实际 code 值需通过接口或抓包确认。
