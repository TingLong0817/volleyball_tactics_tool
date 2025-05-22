import streamlit as st
from utils.data_manager import DataManager
from utils.plot import plot_volleyball_court_with_background
import pandas as pd
import time
import copy  # Add this import for deep copying
import matplotlib.pyplot as plt
import numpy as np

# 设置页面和中文支持
st.set_page_config(layout="wide", page_title="比赛详情")

# 初始化数据管理器
data_manager = DataManager()

# 定义排球位置顺序常量
VOLLEYBALL_POSITIONS = [4, 3, 2, 5, 6, 1]  # 标准排球位置顺序

# 检查是否有当前比赛ID
if "current_match_id" not in st.session_state:
    st.error("⚠️ 请先选择一场比赛")
    st.stop()

def reload_match_data():
    """重新加载比赛数据的辅助函数"""
    fresh_match_data = data_manager.load_match(st.session_state.current_match_id)
    if not fresh_match_data:
        st.error("⚠️ 无法加载比赛数据")
        st.stop()
    return fresh_match_data

# 加载比赛数据
match_data = reload_match_data()
match_id = st.session_state.current_match_id

# 加载我方球队数据
team_data = data_manager.load_team(match_data['info']['team_us'])
if not team_data:
    st.error("⚠️ 无法加载球队数据")
    st.stop()

# 分开存储普通球员和自由人列表
regular_players = [p["name"] for p in team_data.get("player_list", []) if p["name"]]
libero_players = [p["name"] for p in team_data.get("libero_list", []) if p["name"]]
available_players = regular_players + libero_players

if not available_players:
    st.error("⚠️ 请先在球员名单中添加球员")
    st.stop()

# 显示比赛基本信息
info = match_data.get("info", {})
st.title(f"🏐 {info.get('name', '未命名比赛')}")

# 显示比赛总体信息
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**我方队伍**：{info.get('team_us', '未设置')}")
with col2:
    st.info(f"**对方队伍**：{info.get('team_them', '未设置')}")
with col3:
    st.info(f"**总比分**：{match_data.get('score', {}).get('us', 0)} - {match_data.get('score', {}).get('them', 0)}")

# 创建新的一局
create_col, delete_col = st.columns([1, 1])
with create_col:
    if st.button("➕ 创建新的一局"):
        current_set_count = len(match_data.get('sets', []))
        if data_manager.create_set(match_id, current_set_count):
            st.success(f"✅ 第 {current_set_count + 1} 局创建成功！")
            st.rerun()

with delete_col:
    if len(match_data.get('sets', [])) > 1:  # 至少保留一局
        if st.button("🗑️ 删除当前局"):
            # 添加确认机制
            confirm_delete = st.checkbox("确认删除？此操作不可撤销", key="confirm_delete_set")
            if confirm_delete:
                try:
                    # 1. 获取最新数据
                    fresh_match_data = data_manager.load_match(match_id)
                    
                    # 2. 从列表中删除当前局
                    if current_set < len(fresh_match_data['sets']):
                        del fresh_match_data['sets'][current_set]
                    
                    # 3. 如果删除的是最后一局，更新索引
                    if current_set >= len(fresh_match_data['sets']):
                        fresh_match_data['current_set'] = len(fresh_match_data['sets']) - 1
                    
                    # 4. 保存更新
                    data_manager.save_match(match_id, fresh_match_data)
                    
                    # 5. 显示成功消息
                    st.success("✅ 已删除当前局")
                except Exception as e:
                    st.error(f"删除失败: {str(e)}")
                
                # 6. 强制刷新页面
                st.rerun()
    else:
        st.caption("⚠️ 至少保留一局比赛")

# 显示所有局的标签页
if not match_data.get('sets'):
    st.warning("⚠️ 请先创建新的一局")
    st.stop()

# 选择当前局
current_set = st.radio(
    "选择比赛局次",
    range(len(match_data['sets'])),
    format_func=lambda x: f"第 {x + 1} 局",
    horizontal=True
)

# 获取当前局数据
set_data = match_data['sets'][current_set]

# 创建三个工具栏
tab1, tab2, tab3 = st.tabs(["⚙️ 局前设置", "🎮 比赛记录", "📊 数据统计"])

# 检查是否需要切换到比赛记录标签
if "should_switch_to_match_tab" in st.session_state and st.session_state.should_switch_to_match_tab:
    # 使用JavaScript切换到第二个标签
    js = """
    <script>
        // 等待DOM加载完成
        function switchTab() {
            var tabs = document.querySelectorAll('button[data-baseweb="tab"]');
            if (tabs.length > 1) {
                tabs[1].click();
            } else {
                setTimeout(switchTab, 100);
            }
        }
        switchTab();
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
    # 重置标志
    del st.session_state.should_switch_to_match_tab

with tab1:
    st.subheader("局前设置")
    match_data = reload_match_data()
    set_data = match_data['sets'][current_set]
    # Ensure session state is initialized before use
    if f"selected_players_{current_set}" not in st.session_state:
        st.session_state[f"selected_players_{current_set}"] = {str(pos): "" for pos in VOLLEYBALL_POSITIONS}
    if f"selected_liberos_{current_set}" not in st.session_state:
        st.session_state[f"selected_liberos_{current_set}"] = ["", ""]

    fig_col, control_col = st.columns([3, 2])
    with fig_col:
        st.subheader("场地预览")
        positions = [st.session_state[f"selected_players_{current_set}"][str(pos)] for pos in VOLLEYBALL_POSITIONS]
        liberos = [lib for lib in st.session_state[f"selected_liberos_{current_set}"] if lib]
        fig = plot_volleyball_court_with_background(
            positions,
            serve_side="us" if st.session_state.get(f"serve_{current_set}", "us") == "us" else None,
            rotation_index=0,
            liberos=liberos,
            figsize=(3,2.4)
        )
        st.pyplot(fig)
    with control_col:
        if st.button("🔄 重置所有选择", key=f"reset_settings_{current_set}"):
            st.session_state[f"selected_players_{current_set}"] = {str(pos): "" for pos in VOLLEYBALL_POSITIONS}
            st.session_state[f"selected_liberos_{current_set}"] = ["", ""]
            st.success("✅ 已重置所有选择")
            st.rerun()
        serve_first = st.radio(
            "选择发球方",
            ["us", "them"],
            format_func=lambda x: "我方发球" if x == "us" else "对方发球",
            horizontal=True,
            key=f"serve_{current_set}"
        )
        st.subheader("我方初始站位")
        def get_selected_players(current_pos):
            players = [p for pos, p in st.session_state[f"selected_players_{current_set}"].items() if p and pos != str(current_pos)]
            players.extend([p for p in st.session_state[f"selected_liberos_{current_set}"] if p])
            return players
        def get_selected_liberos(current_index):
            return [p for i, p in enumerate(st.session_state[f"selected_liberos_{current_set}"]) if p and i != current_index]
        def on_player_select(pos):
            key = f"pos_{pos}_{current_set}" if pos in [4, 3, 2] else f"pos_{pos}_{current_set}_back"
            if key in st.session_state:
                st.session_state[f"selected_players_{current_set}"][str(pos)] = st.session_state[key]
        def on_libero_select(index):
            key = f"libero_{index}_{current_set}"
            if key in st.session_state:
                st.session_state[f"selected_liberos_{current_set}"][index] = st.session_state[key]
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.markdown("**前排**")
            front_positions = [4, 3, 2]
            for pos in front_positions:
                current_selected = st.session_state[f"selected_players_{current_set}"][str(pos)]
                other_selected = get_selected_players(pos)
                available_for_pos = [""] + [p for p in regular_players if p not in other_selected or p == current_selected]
                st.selectbox(
                    f"{pos}号位",
                    available_for_pos,
                    key=f"pos_{pos}_{current_set}",
                    index=available_for_pos.index(current_selected) if current_selected in available_for_pos else 0,
                    on_change=on_player_select,
                    args=(pos,)
                )
        with col2:
            st.markdown("**后排**")
            back_positions = [5, 6, 1]
            for pos in back_positions:
                current_selected = st.session_state[f"selected_players_{current_set}"][str(pos)]
                other_selected = get_selected_players(pos)
                available_for_pos = [""] + [p for p in regular_players if p not in other_selected or p == current_selected]
                st.selectbox(
                    f"{pos}号位",
                    available_for_pos,
                    key=f"pos_{pos}_{current_set}_back",
                    index=available_for_pos.index(current_selected) if current_selected in available_for_pos else 0,
                    on_change=on_player_select,
                    args=(pos,)
                )
        with col3:
            st.markdown("**自由人**")
            if libero_players:
                for i in range(min(2, len(libero_players) + 1)):
                    current_selected = st.session_state[f"selected_liberos_{current_set}"][i] if i < len(st.session_state[f"selected_liberos_{current_set}"]) else ""
                    other_selected = get_selected_liberos(i) + get_selected_players(None)
                    available_liberos = [""] + [p for p in libero_players if p not in other_selected or p == current_selected]
                    st.selectbox(
                        f"自由人 {i+1}",
                        available_liberos,
                        key=f"libero_{i}_{current_set}",
                        index=available_liberos.index(current_selected) if current_selected in available_liberos else 0,
                        on_change=on_libero_select,
                        args=(i,)
                    )
            else:
                st.info("没有可用的自由人，请在球员名单中添加")
        save_col1, save_col2 = st.columns(2)
        with save_col1:
            if st.button("💾 保存设置", key=f"save_settings_{current_set}"):
                try:
                    match_data = reload_match_data()
                    set_data = match_data['sets'][current_set]
                    set_data['serve_first'] = serve_first
                    set_data['current_server'] = serve_first
                    positions_list = [st.session_state[f"selected_players_{current_set}"][str(pos)] for pos in VOLLEYBALL_POSITIONS]
                    if 'liberos' not in set_data:
                        set_data['liberos'] = {'us': [], 'them': []}
                    set_data['liberos']['us'] = [lib for lib in st.session_state[f"selected_liberos_{current_set}"] if lib]
                    data_manager.update_set_position(match_id, current_set, 'us', positions_list, is_initial=True)
                    data_manager.update_set_position(match_id, current_set, 'us', positions_list, is_initial=False)
                    if 'initial_position' not in set_data:
                        set_data['initial_position'] = {'us': [], 'them': []}
                    if 'current_position' not in set_data:
                        set_data['current_position'] = {'us': [], 'them': []}
                    set_data['initial_position']['us'] = positions_list
                    set_data['current_position']['us'] = copy.deepcopy(positions_list)
                    data_manager.save_match(match_id, match_data)
                    st.success("✅ 设置已保存")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"保存失败: {str(e)}")
                    st.stop()
        with save_col2:
            if st.button("✓ 确认并开始比赛", key=f"confirm_settings_{current_set}"):
                try:
                    match_data = reload_match_data()
                    set_data = match_data['sets'][current_set]
                    positions_list = [st.session_state[f"selected_players_{current_set}"][str(pos)] for pos in VOLLEYBALL_POSITIONS]
                    if not any(positions_list):
                        st.error("⚠️ 请至少选择一名球员后确认")
                        st.stop()
                    set_data['serve_first'] = serve_first
                    set_data['current_server'] = serve_first
                    set_data['initial_position']['us'] = positions_list
                    set_data['current_position']['us'] = copy.deepcopy(positions_list)
                    set_data['initial_confirmed'] = True
                    set_data['status'] = 'in_progress'
                    set_data['rotation_index'] = 0
                    set_data['score'] = {'us': 0, 'them': 0}
                    if 'liberos' not in set_data:
                        set_data['liberos'] = {'us': [], 'them': []}
                    set_data['liberos']['us'] = [lib for lib in st.session_state[f"selected_liberos_{current_set}"] if lib]
                    data_manager.save_match(match_id, match_data)
                    st.session_state.should_switch_to_match_tab = True
                    st.success("✅ 设置已确认，正在切换到比赛记录标签...")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"确认失败: {str(e)}")
                    st.stop()

with tab2:
    match_data = reload_match_data()
    if not match_data:
        st.error("⚠️ 无法加载比赛数据")
        st.stop()
    set_data = match_data['sets'][current_set]
    st.subheader("比赛记录")
    # Ensure session state is initialized before use
    if f"selected_players_{current_set}" not in st.session_state:
        st.session_state[f"selected_players_{current_set}"] = {str(pos): "" for pos in VOLLEYBALL_POSITIONS}
    if f"selected_liberos_{current_set}" not in st.session_state:
        st.session_state[f"selected_liberos_{current_set}"] = ["", ""]

    # 事件采集session_state
    if "pending_event" not in st.session_state:
        st.session_state["pending_event"] = None

    # 事件触发函数
    def trigger_event_form(winner):
        score = set_data['score'].copy()
        rally_number = len(set_data['events']) + 1
        st.session_state["pending_event"] = {
            "set_number": current_set + 1,
            "rally_number": rally_number,
            "winner": winner,
            "score": score
        }

    fig_col, control_col = st.columns([3, 2])
    with fig_col:
        st.subheader("当前场上位置")
        liberos = set_data.get('liberos', {}).get('us', []) if 'liberos' in set_data else []
        current_positions = set_data['current_position']['us']
        fig = plot_volleyball_court_with_background(
            current_positions,
            serve_side="us" if set_data['current_server'] == "us" else None,
            rotation_index=set_data.get('rotation_index', 0),
            liberos=liberos,
            figsize=(3,2.4)
        )
        st.pyplot(fig)
    with control_col:
        # 强制刷新数据，保证分数和事件为最新
        match_data = reload_match_data()
        set_data = match_data['sets'][current_set]
        # 删除当前局功能（至少保留一局）
        if len(match_data['sets']) > 1:
            delete_col, confirm_col = st.columns([1, 2])
            with delete_col:
                if st.button("🗑️ 删除当前局", key=f"delete_set_{current_set}"):
                    st.session_state[f"delete_set_confirm_{current_set}"] = True
            with confirm_col:
                if st.session_state.get(f"delete_set_confirm_{current_set}"):
                    st.warning("确认删除当前局？此操作不可撤销！")
                    if st.button("确认删除", key=f"confirm_delete_set_{current_set}"):
                        match_data = reload_match_data()
                        del match_data['sets'][current_set]
                        # 修正current_set索引
                        if current_set >= len(match_data['sets']):
                            match_data['current_set'] = len(match_data['sets']) - 1
                        else:
                            match_data['current_set'] = current_set
                        data_manager.save_match(match_id, match_data)
                        st.success("当前局已删除")
                        # 清理确认状态
                        del st.session_state[f"delete_set_confirm_{current_set}"]
                        st.rerun()
                    if st.button("取消", key=f"cancel_delete_set_{current_set}"):
                        del st.session_state[f"delete_set_confirm_{current_set}"]
                        st.rerun()
        else:
            st.caption("⚠️ 至少保留一局比赛")
        # Reset set controls
        reset_state_key = f"reset_state_{current_set}"
        if reset_state_key not in st.session_state:
            st.session_state[reset_state_key] = "initial"
        if st.session_state[reset_state_key] == "initial":
            if st.button("🔄 重置本局", key=f"reset_match_{current_set}"):
                st.session_state[reset_state_key] = "confirming"
                st.rerun()
        elif st.session_state[reset_state_key] == "confirming":
            st.warning("确认要重置本局吗？这将清空所有记录！")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✓ 确认", key=f"confirm_reset_{current_set}"):
                    try:
                        match_data = reload_match_data()
                        set_data = match_data['sets'][current_set]
                        if 'initial_position' not in set_data or 'us' not in set_data['initial_position']:
                            st.error("⚠️ 无法重置：未找到初始站位数据")
                            st.session_state[reset_state_key] = "initial"
                            st.rerun()
                        set_data['current_position']['us'] = copy.deepcopy(set_data['initial_position']['us'])
                        set_data['current_position']['them'] = copy.deepcopy(set_data['initial_position'].get('them', [""] * 6))
                        set_data['score'] = {'us': 0, 'them': 0}
                        set_data['rotation_index'] = 0
                        set_data['current_server'] = set_data.get('serve_first', 'us')
                        set_data['events'] = []  # 重置事件统计
                        set_data['substitutions'] = []
                        set_data['timeouts'] = {'us': [], 'them': []}
                        set_data['stats'] = {
                            'us': {'attacks': [], 'blocks': [], 'serves': [], 'receives': []},
                            'them': {'attacks': [], 'blocks': [], 'serves': [], 'receives': []}
                        }
                        data_manager.save_match(match_id, match_data)
                        for key in list(st.session_state.keys()):
                            if str(current_set) in key:
                                del st.session_state[key]
                        st.session_state[reset_state_key] = "initial"
                        st.success("✅ 当前局已重置为初始站位和 0:0")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"重置失败: {str(e)}")
                        st.session_state[reset_state_key] = "initial"
                        st.rerun()
            with col2:
                if st.button("✗ 取消", key=f"cancel_reset_{current_set}"):
                    st.session_state[reset_state_key] = "initial"
                    st.rerun()
        # Score controls
        score_col1, score_col2, score_col3 = st.columns([2,1,2])
        is_completed = set_data.get('status') == 'completed'
        # 记分按钮：只负责加分，比分立即变化
        if st.button("我方得分 +1", key=f"score_us_{current_set}", disabled=is_completed):
            data_manager.record_point(match_id, current_set, "us")
            match_data = reload_match_data()
            set_data = match_data['sets'][current_set]
            st.session_state["pending_event"] = {
                "set_number": current_set + 1,
                "rally_number": len(set_data['events']) + 1,
                "winner": "us",
                "score": set_data['score'].copy()
            }
            st.rerun()
        if st.button("对方得分 +1", key=f"score_them_{current_set}", disabled=is_completed):
            data_manager.record_point(match_id, current_set, "them")
            match_data = reload_match_data()
            set_data = match_data['sets'][current_set]
            st.session_state["pending_event"] = {
                "set_number": current_set + 1,
                "rally_number": len(set_data['events']) + 1,
                "winner": "them",
                "score": set_data['score'].copy()
            }
            st.rerun()
        # 事件采集表单（可选填，提交后仅追加event，不影响比分）
        if st.session_state.get("pending_event"):
            with st.form("event_form", clear_on_submit=True):
                st.subheader("补充本球事件信息")
                score_reason = st.selectbox("得分类型", ["", "attack", "block", "serve", "opponent_error", "self_error"])
                player = st.selectbox("关联球员", ["None"] + available_players)
                note = st.text_input("备注")
                submitted = st.form_submit_button("提交")
                if submitted:
                    event = st.session_state["pending_event"]
                    event["score_reason"] = score_reason
                    event["player"] = player
                    event["note"] = note
                    match_data = reload_match_data()
                    set_data = match_data['sets'][current_set]
                    set_data['events'].append(event)
                    data_manager.save_match(match_id, match_data)
                    st.session_state["pending_event"] = None
                    st.success("事件已补充！")
                    st.rerun()
        with score_col2:
            latest_score = set_data['score']
            st.markdown(f"### {latest_score['us']} - {latest_score['them']}")
            is_completed = set_data.get('status') == 'completed'
            if is_completed:
                st.info("✅ 本局已结束")
                winner_name = "我方" if latest_score['winner'] == 'us' else "对方"
                st.success(f"🏆 本局结束！{winner_name}胜利！比分 {latest_score['us']}:{latest_score['them']}")
                match_data = reload_match_data()
                sets_to_win = match_data['info']['rules'].get('sets_to_win', 3)
                if latest_score['us'] >= sets_to_win:
                    if st.button("比赛已达胜局数，是否结束比赛？"):
                        match_data['info']['status'] = '已结束'
                        data_manager.save_match(match_id, match_data)
                        st.success("比赛已结束！")
                        st.rerun()
                else:
                    st.info("ℹ️ 可以创建新的一局继续比赛")
        # 其余换人、暂停等功能保持不变
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**换人记录**")
            with st.expander("换人"):
                current_players = [p for p in current_positions if p]
                available_subs = [p for p in available_players if p not in current_positions]
                out_player = st.selectbox(
                    "选择换下球员",
                    [""] + current_players,
                    format_func=lambda x: f"{x}" if x else "请选择球员"
                )
                if out_player:
                    position = current_positions.index(out_player)
                    in_player = st.selectbox(
                        "选择换上球员",
                        [""] + available_subs,
                        format_func=lambda x: f"{x}" if x else "请选择球员"
                    )
                    if st.button("确认换人", key=f"confirm_sub_{current_set}"):
                        if in_player:
                            if data_manager.record_substitution(match_id, current_set, 'us', in_player, out_player, position):
                                st.success("✅ 换人成功")
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.error("⚠️ 请选择要换上的球员")
                if set_data['substitutions']:
                    st.markdown("---")
                    st.markdown("**换人历史**")
                    for sub in set_data['substitutions']:
                        st.text(f"↔️ {sub['out_player']} → {sub['in_player']} ({sub['score']['us']}-{sub['score']['them']})")
        with col2:
            st.markdown("**暂停记录**")
            if st.button("记录暂停", key=f"timeout_{current_set}", disabled=is_completed):
                result = data_manager.record_timeout(match_id, current_set, 'us')
                if result:
                    st.success("✅ 暂停记录已保存")
                    st.rerun()
                else:
                    st.error("❌ 暂停记录失败，请检查比赛和局次是否有效")
            timeouts = set_data['timeouts']['us']
            if timeouts:
                for i, timeout in enumerate(timeouts, 1):
                    st.text(f"第{i}次暂停：{timeout['score']['us']}-{timeout['score']['them']}")
            else:
                st.info("暂无暂停记录")

with tab3:
    st.subheader("数据统计")
    # 选择统计范围
    stat_scope = st.radio("统计范围", ["本局", "全场"], horizontal=True)
    if stat_scope == "本局":
        events = set_data['events']
        # 添加重置本局统计按钮
        if st.button("🧹 重置本局统计", key=f"reset_stats_{current_set}"):
            match_data = reload_match_data()
            set_data = match_data['sets'][current_set]
            set_data['events'] = []
            data_manager.save_match(match_id, match_data)
            st.success("本局统计已重置！")
            st.rerun()
    else:
        events = []
        for s in match_data['sets']:
            events.extend(s.get('events', []))
    if not events:
        st.info("暂无事件数据")
    else:
        import pandas as pd
        df = pd.DataFrame(events)
        def pie_chart(data, legend_labels=None):
            fig, ax = plt.subplots(figsize=(2.2, 2.2))
            if data.empty:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=8)
                ax.axis('off')
            else:
                def autopct(pct):
                    total = sum(data.values)
                    count = int(round(pct/100*total))
                    return f'{count}\n' if count > 0 else ''
                wedges, texts, autotexts = ax.pie(
                    data.values,
                    labels=None,  # 不在扇区内显示标签
                    autopct=autopct,
                    textprops={'fontsize': 8},
                    radius=1,
                    pctdistance=0.7,
                    labeldistance=1.1
                )
                # 图例放在下方，纵向排列
                if legend_labels is None:
                    legend_labels = [str(label) for label in data.index]
                ax.legend(wedges, legend_labels, loc='lower center', bbox_to_anchor=(0.5, -0.25), fontsize=8, ncol=1, frameon=False)
                ax.set_position([0.05, 0.05, 0.9, 0.9])
            st.pyplot(fig)
        # 分开统计
        us_events = df[df['winner'] == 'us']
        them_events = df[df['winner'] == 'them']
        # 横向排列
        cols = st.columns(4)
        with cols[0]:
            st.markdown("**我方得分手段分布**")
            us_score_reason = us_events["score_reason"].value_counts()
            pie_chart(us_score_reason, legend_labels=us_score_reason.index.astype(str))
        with cols[1]:
            st.markdown("**我方球员得分排行榜**")
            us_player = us_events[us_events["player"].notna() & (us_events["player"] != "None")]["player"].value_counts()
            pie_chart(us_player, legend_labels=us_player.index.astype(str))
        with cols[2]:
            st.markdown("**我方球员丢分分布**")
            them_player = them_events[them_events["player"].notna() & (them_events["player"] != "None")]["player"].value_counts()
            pie_chart(them_player, legend_labels=them_player.index.astype(str))
        with cols[3]:
            st.markdown("**对方得分手段分布**")
            them_score_reason = them_events["score_reason"].value_counts()
            pie_chart(them_score_reason, legend_labels=them_score_reason.index.astype(str))
        # 事件明细表
        st.markdown("#### 事件明细")
        st.dataframe(df)
    if st.button("📊 导出统计数据", key=f"export_{current_set}"):
        # TODO: 实现数据导出功能
        pass 