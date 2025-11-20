import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import base64
from prompt import get_prompt
from deepseek import get_airespon
import ast
# ========= 配置 =========
st.set_page_config(page_title="AI 计划生成器", layout="centered")
st.title("AI 智能计划生成器")
st.markdown("输入事件和目标，自动生成 **SMART 计划 + 时间表**")

API_URL = "http://localhost:8000/api/generate"  # 改成你的后端地址

# ========= 输入表单 =========
with st.form("plan_form"):
    event = st.text_input("事件名称", placeholder="例如：周末日程、工作周计划")
    goal = st.text_area("目标（SMART）", placeholder="例如：在 2025-11-15 至 11-16 周末，完成 ≥3 件让我开心的事，总放松+成长时间 ≥8 小时")
    col1, col2 = st.columns(2)
    with col1:
        deadline = st.date_input("截止日期（可选）", value=None)
    with col2:
        daily_hours = st.number_input("每日可用时间（小时）", min_value=0.5, max_value=12.0, value=3.0, step=0.5)

    submitted = st.form_submit_button("生成计划", type="primary")

# ========= 调用 API =========
if submitted:
    if not event or not goal:
        st.error("事件和目标不能为空")
    else:
        with st.spinner("AI 正在思考计划..."):
            try:
                payload = {
                    "event": event,
                    "goal": goal,
                    "deadline": deadline.strftime("%Y-%m-%d") if deadline else None,
                    "daily_hours": daily_hours
                }
                # prompt = get_prompt("愉快的周末", "在 2025-11-15 至 11-16 周末，完成 ≥3 件让我开心的事，总放松+成长时间 ≥8 小时", "2025-11-15", "3")
                prompt = get_prompt(payload.get("event"), payload.get("goal"), payload.get("deadline"), payload.get("daily_hours"))
                print(prompt)
                response = get_airespon(prompt)
                print(response)
                data = ast.literal_eval(response)

                if "error" in data:
                    st.error(f"生成失败：{data['error']}")
                else:
                    st.session_state.plan = data
                    st.success("计划生成成功！")
            except Exception as e:
                st.error(f"请求失败：{e}")

# ========= 展示结果 =========
if "plan" in st.session_state:
    plan = st.session_state.plan

    # --- 1. 总览卡片 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总步骤", len(plan["steps"]))
    with col2:
        st.metric("预计总耗时", f"{plan['total_hours']} 小时")
    with col3:
        st.metric("每日平均", f"{plan['total_hours'] / 5:.1f} 小时")

    if plan.get("notes"):
        st.info(f"备注：{plan['notes']}")

    # --- 2. 步骤列表（可展开）---
    st.subheader("执行步骤")
    steps_df = pd.DataFrame(plan["steps"])
    steps_df.index += 1
    st.dataframe(
        steps_df,
        column_config={
            "title": "步骤",
            "description": st.column_config.TextColumn("详细说明", width="medium"),
            "estimated_hours": st.column_config.NumberColumn("耗时（小时）", format="%.1f")
        },
        use_container_width=True
    )

    # --- 3. 时间表甘特图 ---
    st.subheader("时间表示例（按天分配）")
    if plan["schedule"]:
        schedule_df = pd.DataFrame(plan["schedule"])
        schedule_df["进度%"] = (schedule_df["hours"] / daily_hours * 100).round(1)

        # 按日期分组展示
        # 在展示时间表的地方替换原来的代码
        for date, group in schedule_df.groupby("date"):
            day_total = group['hours'].sum()
            weekday_names = ['一', '二', '三', '四', '五', '六', '日']
            weekday = datetime.strptime(date, '%Y-%m-%d').weekday()
            with st.expander(f"{date}（周{weekday_names[weekday]}） - 共 {day_total:.1f} 小时"
                             f"{' ⚠️超额' if day_total > daily_hours else ''}"):
                for _, row in group.iterrows():
                    st.write(f"**{row['step']}** - {row['hours']}h")
                    progress = min(row['hours'] / daily_hours, 1.0)
                    st.progress(progress)
                    if row['hours'] / daily_hours > 1:
                        st.caption(f"⚠️ {row['description']}（单项已超当日可用时间）")
                    else:
                        st.caption(row["description"])

    # --- 4. 导出按钮 ---
    col1, col2 = st.columns(2)
    with col1:
        json_str = json.dumps(plan, ensure_ascii=False, indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="plan.json">下载 JSON 文件</a>'
        st.markdown(href, unsafe_allow_html=True)

    with col2:
        csv = schedule_df.to_csv(index=False).encode()
        b64_csv = base64.b64encode(csv).decode()
        href_csv = f'<a href="data:text/csv;base64,{b64_csv}" download="schedule.csv">下载 CSV 时间表</a>'
        st.markdown(href_csv, unsafe_allow_html=True)

    # --- 5. 重新生成 ---
    if st.button("重新生成"):
        st.session_state.pop("plan")
        st.rerun()