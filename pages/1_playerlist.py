import streamlit as st
import json
import os
from utils.data_manager import DataManager

# 设置页面
st.set_page_config(layout="wide", page_title="球队管理")

# 设置页面样式
st.markdown("""
<style>
    .stTextInput>div>div>input {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
    }
    .stTextInput>div>div {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 球队管理")

# 初始化数据管理
data_manager = DataManager()

# 初始化 session state
if 'player_confirmed' not in st.session_state:
    st.session_state.player_confirmed = False
    st.session_state.player_list = [{"number": "", "name": ""} for _ in range(14)]
    st.session_state.libero_list = [{"number": "", "name": ""} for _ in range(2)]

# 顶部：新建/加载球队
col_top = st.columns([1, 1, 1])
with col_top[0]:
    team_name = st.text_input("球队名称", key="team_name")
with col_top[1]:
    existing_teams = data_manager.list_teams()
    selected_team = st.selectbox("选择已有球队", [""] + existing_teams, key="selected_team")
with col_top[2]:
    uploaded_file = st.file_uploader("导入球队 JSON", type="json")

# 加载球队数据
if selected_team:
    team_data = data_manager.load_team(selected_team)
    if team_data:
        st.session_state.player_list = team_data.get("player_list", []) + [{"number": "", "name": ""}] * (14 - len(team_data.get("player_list", [])))
        st.session_state.libero_list = team_data.get("libero_list", []) + [{"number": "", "name": ""}] * (2 - len(team_data.get("libero_list", [])))
        st.success(f"✅ 已加载球队：{selected_team}")

# 导入 JSON 文件
if uploaded_file:
    try:
        data = json.load(uploaded_file)
        if isinstance(data, dict) and "player_list" in data and "libero_list" in data:
            st.session_state.player_list = data["player_list"] + [{"number": "", "name": ""}] * (14 - len(data["player_list"]))
            st.session_state.libero_list = data["libero_list"] + [{"number": "", "name": ""}] * (2 - len(data["libero_list"]))
            st.success("✅ 球队名单导入成功")
        else:
            st.error("❌ 文件格式错误，请上传系统导出的 JSON")
    except Exception as e:
        st.error(f"❌ 文件读取失败：{str(e)}")

# 添加号码验证函数
def validate_number(number):
    """验证球衣号码"""
    if not number:
        return True
    try:
        num = int(number)
        return 1 <= num <= 99
    except ValueError:
        return False

def check_duplicate_numbers():
    """检查重复号码"""
    numbers = []
    # 检查主力和替补
    for player in st.session_state.player_list:
        if player["number"]:
            if player["number"] in numbers:
                return True, player["number"]
            numbers.append(player["number"])
    # 检查自由人
    for libero in st.session_state.libero_list:
        if libero["number"]:
            if libero["number"] in numbers:
                return True, libero["number"]
            numbers.append(libero["number"])
    return False, None

# 主力与替补球员输入区
st.markdown("### 🟩 主力与替补球员（最多14人）")

# 表头
col_headers = st.columns([0.5, 1, 2, 0.5, 1, 2])
with col_headers[0]: st.markdown("**序号**")
with col_headers[1]: st.markdown("**号码**")
with col_headers[2]: st.markdown("**姓名**")
with col_headers[3]: st.markdown("**序号**")
with col_headers[4]: st.markdown("**号码**")
with col_headers[5]: st.markdown("**姓名**")

# 球员输入区
for i in range(7):
    cols = st.columns([0.5, 1, 2, 0.5, 1, 2])
    # 左侧球员
    with cols[0]:
        st.markdown(f"**{i+1}**")
    with cols[1]:
        number = st.text_input("", value=st.session_state.player_list[i]["number"], key=f"player_number_{i}", label_visibility="collapsed", max_chars=2)
        if number and not validate_number(number):
            st.error("号码必须是1-99的数字")
        st.session_state.player_list[i]["number"] = number
    with cols[2]:
        name = st.text_input("", value=st.session_state.player_list[i]["name"], key=f"player_name_{i}", label_visibility="collapsed")
        st.session_state.player_list[i]["name"] = name
    
    # 右侧球员
    with cols[3]:
        st.markdown(f"**{i+8}**")
    with cols[4]:
        number = st.text_input("", value=st.session_state.player_list[i+7]["number"], key=f"player_number_{i+7}", label_visibility="collapsed", max_chars=2)
        if number and not validate_number(number):
            st.error("号码必须是1-99的数字")
        st.session_state.player_list[i+7]["number"] = number
    with cols[5]:
        name = st.text_input("", value=st.session_state.player_list[i+7]["name"], key=f"player_name_{i+7}", label_visibility="collapsed")
        st.session_state.player_list[i+7]["name"] = name

# 自由人输入区
st.markdown("### 🟨 自由人（最多2人）")
libero_headers = st.columns([0.5, 1, 2, 0.5, 1, 2])
with libero_headers[0]: st.markdown("**序号**")
with libero_headers[1]: st.markdown("**号码**")
with libero_headers[2]: st.markdown("**姓名**")

libero_cols = st.columns([0.5, 1, 2, 0.5, 1, 2])
# 第一个自由人
with libero_cols[0]:
    st.markdown("**1**")
with libero_cols[1]:
    number = st.text_input("", value=st.session_state.libero_list[0]["number"], key="libero_number_0", label_visibility="collapsed", max_chars=2)
    if number and not validate_number(number):
        st.error("号码必须是1-99的数字")
    st.session_state.libero_list[0]["number"] = number
with libero_cols[2]:
    name = st.text_input("", value=st.session_state.libero_list[0]["name"], key="libero_name_0", label_visibility="collapsed")
    st.session_state.libero_list[0]["name"] = name

# 第二个自由人
with libero_cols[3]:
    st.markdown("**2**")
with libero_cols[4]:
    number = st.text_input("", value=st.session_state.libero_list[1]["number"], key="libero_number_1", label_visibility="collapsed", max_chars=2)
    if number and not validate_number(number):
        st.error("号码必须是1-99的数字")
    st.session_state.libero_list[1]["number"] = number
with libero_cols[5]:
    name = st.text_input("", value=st.session_state.libero_list[1]["name"], key="libero_name_1", label_visibility="collapsed")
    st.session_state.libero_list[1]["name"] = name

# 底部：操作按钮
col_buttons = st.columns(2)

with col_buttons[0]:
    if st.button("💾 保存球队名单", use_container_width=True):
        has_duplicate, dup_number = check_duplicate_numbers()
        if has_duplicate:
            st.error(f"❌ 号码 {dup_number} 重复使用")
            st.stop()
            
        invalid_numbers = [p["number"] for p in st.session_state.player_list if p["number"] and not validate_number(p["number"])]
        invalid_numbers.extend([l["number"] for l in st.session_state.libero_list if l["number"] and not validate_number(l["number"])])
        if invalid_numbers:
            st.error(f"❌ 以下号码无效：{', '.join(invalid_numbers)}")
            st.stop()

        try:
            players = [p for p in st.session_state.player_list if p["number"] and p["name"]]
            liberos = [l for l in st.session_state.libero_list if l["number"] and l["name"]]
            
            team_data = {
                "player_list": players,
                "libero_list": liberos
            }
            
            if team_name:
                data_manager.save_team(team_name, team_data)
                st.success(f"✅ 已保存球队：{team_name}，{len(players)} 名球员 + {len(liberos)} 名自由人")
            else:
                st.error("❌ 请输入球队名称")
        except Exception as e:
            st.error(f"❌ 保存失败：{str(e)}")

with col_buttons[1]:
    if st.button("✅ 确认球队名单", type="primary", use_container_width=True):
        has_duplicate, dup_number = check_duplicate_numbers()
        if has_duplicate:
            st.error(f"❌ 号码 {dup_number} 重复使用")
            st.stop()
            
        invalid_numbers = [p["number"] for p in st.session_state.player_list if p["number"] and not validate_number(p["number"])]
        invalid_numbers.extend([l["number"] for l in st.session_state.libero_list if l["number"] and not validate_number(l["number"])])
        if invalid_numbers:
            st.error(f"❌ 以下号码无效：{', '.join(invalid_numbers)}")
            st.stop()

        players = [p for p in st.session_state.player_list if p["number"] and p["name"]]
        if len(players) >= 6:
            st.session_state.player_list = players
            st.session_state.libero_list = [l for l in st.session_state.libero_list if l["number"] and l["name"]]
            st.session_state.player_confirmed = True
            st.success(f"✅ 已确认主力与替补 {len(players)} 人，自由人 {len(st.session_state.libero_list)} 人")
            st.session_state.rotation_confirmed = False  # 重置轮转确认状态
        else:
            st.error("❌ 至少需要输入 6 名主力球员")
