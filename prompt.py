from typing import Optional


def get_prompt(event: str, goal: str, deadline: Optional[str], daily_hours: str) -> str:
    deadline_str = deadline or "无固定截止日期"
    return f"""你是一个专业且严谨的项目管理助手，擅长把模糊目标拆解成可执行的 SMART 计划。

请根据用户输入，严格按以下 JSON 格式输出，**不要有任何多余文字、解释、markdown 代码块、前缀后缀**，直接输出纯 JSON：

{{
  "steps": [
    {{
      "title": "简洁的步骤标题（必须以动词开头）",
      "description": "具体怎么做，包含工具/地点/资源建议，越详细越好",
      "estimated_hours": 数字（精确到 0.25，例如 0.5、1.0、2.5、8.0）
    }}
  ],
  "total_hours": 所有步骤 estimated_hours 的准确总和（数字，不加单位）,
  "notes": "对整个计划的风险、建议、SMART 验证说明（字符串，可为空但必须有该字段）",
  "schedule": [
    {{
      "date": "YYYY-MM-DD",
      "step": "步骤标题或合并后的简洁描述（可以把多个小步骤合并写）",
      "hours": 这一天该事项实际分配的小时数（数字，精确到 0.25）,
      "description": "简要说明这天做了什么（50字以内）"
    }}
  ]
}}

### 必须严格遵守的规则（违反任意一条都算失败）：
1. 步骤总数 5~10 个，越细越好
2. 每步 estimated_hours 必须 ≥0.25，总和 ≤30 小时
3. total_hours 必须等于 steps 中所有 estimated_hours 之和，精确到小数点后两位
5. schedule 中所有 hours 之和必须等于 total_hours
8. 输出必须是合法 JSON，禁止出现 trailing comma、单引号、注释
9. notes 字段必须存在，哪怕写“计划已满足所有要求”

### 用户输入：
事件：{event}
目标：{goal}
每日可用时间：{daily_hours} 小时（仅供参考，不硬性限制）
**截止日期**：{deadline_str}

现在直接输出 JSON：""".strip()