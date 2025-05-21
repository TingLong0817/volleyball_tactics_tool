import streamlit as st
from utils.data_manager import DataManager
from datetime import datetime

st.set_page_config(layout="wide", page_title="比赛管理")

# 初始化数据管理器
data_manager = DataManager()

# 设置页面样式
st.markdown("""
<style>
    .match-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .match-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .match-info {
        font-size: 16px;
        color: #666;
        margin-bottom: 10px;
    }
    .match-score {
        font-size: 18px;
        font-weight: bold;
        color: #1f77b4;
        margin-top: 10px;
    }
    .match-status {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 14px;
        margin-right: 10px;
    }
    .status-not-started {
        background-color: #ffd700;
        color: #000;
    }
    .status-in-progress {
        background-color: #32cd32;
        color: #fff;
    }
    .status-completed {
        background-color: #4169e1;
        color: #fff;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏐 比赛管理")

# 获取要编辑的比赛ID
edit_match_id = st.session_state.get("edit_match_id")
edit_match_data = None
if edit_match_id:
    edit_match_data = data_manager.load_match(edit_match_id)

# 创建/编辑比赛的表单
with st.expander("创建/编辑比赛", expanded=not bool(edit_match_id)):
    with st.form("match_form"):
        if edit_match_data:
            st.subheader("✏️ 编辑比赛")
            match_info = edit_match_data.get("info", {})
        else:
            st.subheader("➕ 创建新比赛")
            match_info = {}
        
        # 比赛基本信息
        col1, col2 = st.columns(2)
        with col1:
            match_name = st.text_input("比赛名称", 
                                     value=match_info.get("name", ""),
                                     placeholder="例如：2024市联赛第一轮")
            
            # 加载已有球队列表
            team_list = [""] + data_manager.list_teams()
            team_us = st.selectbox("我方球队", 
                                 team_list,
                                 index=team_list.index(match_info.get("team_us", "")) if match_info.get("team_us") in team_list else 0)
            
            team_them = st.text_input("对方球队名称", 
                                    value=match_info.get("team_them", ""))
        
        with col2:
            match_date = st.date_input("比赛日期", 
                                     value=datetime.now().date())
            match_time = st.time_input("比赛时间", 
                                     value=datetime.now().time())
            match_location = st.text_input("比赛地点",
                                         value=match_info.get("location", ""),
                                         placeholder="例如：市体育馆")
        
        # 比赛规则设置
        st.subheader("⚙️ 比赛规则")
        col3, col4, col5 = st.columns(3)
        with col3:
            sets_to_win = st.number_input("获胜局数", 
                                        min_value=2, max_value=3, 
                                        value=match_info.get("rules", {}).get("sets_to_win", 2))
        with col4:
            points_to_win = st.number_input("每局获胜分数", 
                                          min_value=15, max_value=25, 
                                          value=match_info.get("rules", {}).get("points_to_win", 25))
        with col5:
            point_diff = st.number_input("获胜分差", 
                                       min_value=1, max_value=2, 
                                       value=match_info.get("rules", {}).get("point_diff", 2))
        
        # 备注信息
        notes = st.text_area("备注信息", 
                           value=match_info.get("notes", ""),
                           placeholder="其他需要记录的信息...")
        
        submitted = st.form_submit_button("保存比赛信息")
        
        if submitted:
            if not match_name:
                st.error("❗ 请输入比赛名称")
            elif not team_us:
                st.error("❗ 请选择我方球队")
            elif not team_them:
                st.error("❗ 请输入对方球队名称")
            else:
                # 创建比赛数据结构
                new_match_info = {
                    "name": match_name,
                    "team_us": team_us,
                    "team_them": team_them,
                    "date": match_date.isoformat(),
                    "time": match_time.isoformat(),
                    "location": match_location,
                    "rules": {
                        "sets_to_win": sets_to_win,
                        "points_to_win": points_to_win,
                        "point_diff": point_diff
                    },
                    "notes": notes,
                    "status": match_info.get("status", "未开始")
                }
                
                # 保存比赛
                if edit_match_id:
                    edit_match_data["info"] = new_match_info
                    data_manager.save_match(edit_match_id, edit_match_data)
                    st.success("✅ 比赛信息已更新！")
                    # 清除编辑状态
                    st.session_state.edit_match_id = None
                else:
                    match_id = data_manager.create_match(new_match_info)
                    if match_id:
                        st.success("✅ 比赛创建成功！")
                        st.session_state.current_match_id = match_id
                        # 创建第一局
                        data_manager.create_set(match_id, 0)
                    else:
                        st.error("❌ 比赛创建失败")
                st.rerun()

# 显示已有比赛列表
st.markdown("---")
st.subheader("📋 比赛列表")
matches = data_manager.list_matches()

if not matches:
    st.info("🤷‍♂️ 暂无比赛记录")
else:
    # 添加筛选选项
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "按状态筛选",
            ["全部", "未开始", "进行中", "已结束"],
            index=0
        )
    with col2:
        sort_by = st.selectbox(
            "排序方式",
            ["创建时间（新→旧）", "创建时间（旧→新）", "比赛日期（近→远）", "比赛日期（远→近）"],
            index=0
        )

    for match_id in matches:
        match_data = data_manager.load_match(match_id)
        if match_data:
            info = match_data.get("info", {})
            score = match_data.get("score", {"us": 0, "them": 0})
            
            # 应用状态筛选
            if status_filter != "全部" and info.get("status") != status_filter:
                continue
            
            with st.container():
                st.markdown(f"""
                <div class="match-box">
                    <div class="match-title">{info.get('name', '未命名比赛')}</div>
                    <div class="match-info">
                        <span class="match-status status-{info.get('status', '未开始').lower().replace(' ', '-')}">
                            {info.get('status', '未开始')}
                        </span>
                        {info.get('team_us', '我方')} vs {info.get('team_them', '对方')}
                    </div>
                    <div class="match-info">
                        📅 {info.get('date', '未设置')} {info.get('time', '')} | 
                        📍 {info.get('location', '未设置')}
                    </div>
                    <div class="match-score">
                        比分：{score['us']} - {score['them']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
                with col1:
                    if st.button("✏️ 编辑", key=f"edit_{match_id}"):
                        st.session_state.edit_match_id = match_id
                        st.rerun()
                with col2:
                    if st.button("🎮 进入比赛", key=f"enter_{match_id}"):
                        st.session_state.current_match_id = match_id
                        st.session_state.match_status = "ready"
                        st.switch_page("pages/3_match_detail.py")
                with col3:
                    if st.button("📊 查看统计", key=f"stats_{match_id}"):
                        st.session_state.current_match_id = match_id
                        # TODO: 添加统计页面跳转

# 添加下一页按钮
st.markdown("---")
next_col1, next_col2, next_col3 = st.columns([2, 1, 2])
with next_col2:
    if st.session_state.get("current_match_id"):
        if st.button("下一页 ⏭️", use_container_width=True):
            st.switch_page("pages/3_match_detail.py") 