import streamlit as st

st.set_page_config(page_title="排球战术工具", layout="wide")

st.sidebar.title("📋 页面导航")
st.sidebar.page_link("pages/1_playerlist.py", label="1️⃣ 球员名单输入")
st.sidebar.page_link("pages/2_match_manager.py", label="2️⃣ 比赛管理")
st.sidebar.page_link("pages/3_match_detail.py", label="3️⃣ 比赛详情")

st.title("🏐 欢迎使用排球战术分析工具")
st.markdown("""
### 使用说明

请按照以下步骤使用本工具：

1. **球员名单输入** 📝
   - 创建和管理球队名单
   - 添加、编辑或删除球员信息

2. **比赛管理** 🎮
   - 创建新比赛
   - 设置比赛基本信息（队名、局数等）
   - 编辑现有比赛

3. **比赛详情** 🎯
   - 设置每局比赛的初始站位和发球方
   - 记录比赛进程（得分、换人、暂停）
   - 查看技术统计和数据分析

每个页面都有详细的操作指引。请按照顺序使用各功能。
""")