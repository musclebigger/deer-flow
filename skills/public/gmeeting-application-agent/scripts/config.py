"""
Gmeeting UAT 默认配置
"""

DEFAULT_CONFIG = {
    "env": "uat",
    "url": "https://gmeeting-dev.igskapp.com",
    "login_url": "https://gmeeting-dev.igskapp.com/#/login2",
    "api_base": "https://gmeeting-dev-api.igskapp.com/e2estservice",
    "username": "ttz79417",
    "password": "222222",
    # 会议字段默认值
    "meeting_name": "测试会议-CNS-利必通-自动化",
    "department": "MA CO",
    "therapy_area": "CNS",
    "products": ["利必通"],
    "meeting_type": "全国会",
    "meeting_format": "线下会议",
    "location_type": "单点会",
    "venue_type": "酒店",
    "start_month": "2026-07",
    "province": "北京",
    "city": "北京",
    "speakers_total": 2,
    "speakers_offline": 2,
    "attendees_total": 20,
    "attendees_offline": 20,
    "total_budget": 10000,
    "brand_budgets": {"利必通": 10000},
}
