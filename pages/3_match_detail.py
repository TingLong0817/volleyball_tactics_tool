import streamlit as st
from utils.data_manager import DataManager
from utils.plot import plot_volleyball_court_with_background
import pandas as pd
import time

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

# 加载比赛数据
match_id = st.session_state.current_match_id
match_data = data_manager.load_match(match_id)
if not match_data:
    st.error("⚠️ 无法加载比赛数据")
    st.stop()

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
        setTimeout(function() {
            document.querySelector('button[data-baseweb="tab"]:nth-child(2)').click();
        }, 500);
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
    # 重置标志
    st.session_state.should_switch_to_match_tab = False

with tab1:
    st.subheader("局前设置")
    
    # 添加重置按钮
    if st.button("🔄 重置所有选择", key=f"reset_settings_{current_set}"):
        # 清空所有球员选择
        st.session_state[f"selected_players_{current_set}"] = {
            str(pos): "" for pos in VOLLEYBALL_POSITIONS
        }
        st.session_state[f"selected_liberos_{current_set}"] = ["", ""]
        st.success("✅ 已重置所有选择")
        st.rerun()
    
    # 选择发球方
    serve_first = st.radio(
        "选择发球方",
        ["us", "them"],
        format_func=lambda x: "我方发球" if x == "us" else "对方发球",
        horizontal=True,
        key=f"serve_{current_set}"
    )
    
    # 设置初始站位
    st.subheader("我方初始站位")
    
    # 创建会话状态来跟踪已选择的球员和自由人
    if f"selected_players_{current_set}" not in st.session_state:
        st.session_state[f"selected_players_{current_set}"] = {
            str(pos): "" for pos in VOLLEYBALL_POSITIONS  # 使用实际排球位置号
        }
    
    if f"selected_liberos_{current_set}" not in st.session_state:
        st.session_state[f"selected_liberos_{current_set}"] = ["", ""]  # 最多两个自由人
    
    # 获取已选择的球员（排除当前正在选择的位置）
    def get_selected_players(current_pos):
        players = [p for pos, p in st.session_state[f"selected_players_{current_set}"].items() 
                if p and pos != str(current_pos)]
        players.extend([p for p in st.session_state[f"selected_liberos_{current_set}"] if p])
        return players
    
    def get_selected_liberos(current_index):
        return [p for i, p in enumerate(st.session_state[f"selected_liberos_{current_set}"]) 
                if p and i != current_index]
    
    def on_player_select(pos):
        key = f"pos_{pos}_{current_set}" if pos in [4, 3, 2] else f"pos_{pos}_{current_set}_back"
        if key in st.session_state:
            st.session_state[f"selected_players_{current_set}"][str(pos)] = st.session_state[key]
    
    def on_libero_select(index):
        key = f"libero_{index}_{current_set}"
        if key in st.session_state:
            st.session_state[f"selected_liberos_{current_set}"][index] = st.session_state[key]
    
    # 创建三行布局（前排、后排、自由人）
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # 前排（4-3-2号位）
    with col1:
        st.markdown("**前排**")
        front_positions = [4, 3, 2]  # 前排位置顺序
        front_row = st.columns(3)
        for i, pos in enumerate(front_positions):
            with front_row[i]:
                current_selected = st.session_state[f"selected_players_{current_set}"][str(pos)]
                other_selected = get_selected_players(pos)
                # 只显示普通球员，不含自由人
                available_for_pos = [""] + [p for p in regular_players if p not in other_selected or p == current_selected]
                
                st.selectbox(
                    f"{pos}号位",
                    available_for_pos,
                    key=f"pos_{pos}_{current_set}",
                    index=available_for_pos.index(current_selected) if current_selected in available_for_pos else 0,
                    on_change=on_player_select,
                    args=(pos,)
                )
    
    # 后排（5-6-1号位）
    with col2:
        st.markdown("**后排**")
        back_positions = [5, 6, 1]  # 后排位置顺序
        back_row = st.columns(3)
        for i, pos in enumerate(back_positions):
            with back_row[i]:
                current_selected = st.session_state[f"selected_players_{current_set}"][str(pos)]
                other_selected = get_selected_players(pos)
                # 只显示普通球员，不含自由人
                available_for_pos = [""] + [p for p in regular_players if p not in other_selected or p == current_selected]
                
                st.selectbox(
                    f"{pos}号位",
                    available_for_pos,
                    key=f"pos_{pos}_{current_set}_back",
                    index=available_for_pos.index(current_selected) if current_selected in available_for_pos else 0,
                    on_change=on_player_select,
                    args=(pos,)
                )
    
    # 自由人选择
    with col3:
        st.markdown("**自由人**")
        if libero_players:
            for i in range(min(2, len(libero_players) + 1)):  # 最多两个自由人
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
    
    
    # 显示场地预览
    st.subheader("场地预览")
    positions = []
    # 确保按照标准顺序排列：4-3-2-5-6-1
    for pos in VOLLEYBALL_POSITIONS:
        positions.append(st.session_state[f"selected_players_{current_set}"][str(pos)])
    
    # 获取选中的自由人
    liberos = [lib for lib in st.session_state[f"selected_liberos_{current_set}"] if lib]
    
    fig = plot_volleyball_court_with_background(
        positions,
        serve_side="us" if serve_first == "us" else None,
        rotation_index=0,  # 局前设置不应有轮转
        liberos=liberos  # 传递自由人列表
    )
    st.pyplot(fig)
    
    # 保存和确认区域
    save_col1, save_col2 = st.columns([1, 1])
    
    with save_col1:
        # 保存按钮
        if st.button("💾 保存设置", key=f"save_settings_{current_set}"):
            # 更新发球方
            set_data['serve_first'] = serve_first
            set_data['current_server'] = serve_first
            
            # 更新位置，确保按照标准顺序 4-3-2-5-6-1
            positions_list = []
            for pos in VOLLEYBALL_POSITIONS:
                positions_list.append(st.session_state[f"selected_players_{current_set}"][str(pos)])
            
            # 更新自由人列表
            if 'liberos' not in set_data:
                set_data['liberos'] = {'us': [], 'them': []}
            set_data['liberos']['us'] = [lib for lib in st.session_state[f"selected_liberos_{current_set}"] if lib]
            
            # 保存初始设置
            data_manager.update_set_position(match_id, current_set, 'us', positions_list, is_initial=True)
            
            # 同时更新当前场上位置
            data_manager.update_set_position(match_id, current_set, 'us', positions_list, is_initial=False)
            
            # 确保set_data中的current_position也被更新
            set_data['initial_position']['us'] = positions_list
            set_data['current_position']['us'] = positions_list.copy()
            
            # 设置初始状态标志和比赛状态
            set_data['initial_confirmed'] = True
            set_data['status'] = 'in_progress'
            
            # 保存所有更改
            data_manager.save_match(match_id, match_data)
            
            # 立即重新加载数据，确保使用最新数据
            match_data = data_manager.load_match(match_id)
            set_data = match_data['sets'][current_set]
            
            st.success("✅ 设置已保存")
            st.rerun()
    
    with save_col2:
        # 确认按钮 - 将设置应用到比赛记录
        if st.button("✓ 确认并开始比赛", key=f"confirm_settings_{current_set}"):
            # 检查是否已有球员被选择
            positions_list = []
            for pos in VOLLEYBALL_POSITIONS:
                player = st.session_state[f"selected_players_{current_set}"][str(pos)]
                positions_list.append(player)
            
            if not any(positions_list):
                st.error("⚠️ 请至少选择一名球员后确认")
            else:
                # 更新发球方
                set_data['serve_first'] = serve_first
                set_data['current_server'] = serve_first
                
                # 更新自由人列表
                if 'liberos' not in set_data:
                    set_data['liberos'] = {'us': [], 'them': []}
                set_data['liberos']['us'] = [lib for lib in st.session_state[f"selected_liberos_{current_set}"] if lib]
                
                # 保存初始设置
                data_manager.update_set_position(match_id, current_set, 'us', positions_list, is_initial=True)
                
                # 同时更新当前场上位置
                data_manager.update_set_position(match_id, current_set, 'us', positions_list, is_initial=False)
                
                # 设置初始状态标志和比赛状态
                set_data['initial_confirmed'] = True
                set_data['status'] = 'in_progress'
                
                # 保存所有更改
                data_manager.save_match(match_id, match_data)
                
                # 立即重新加载数据，确保使用最新数据
                match_data = data_manager.load_match(match_id)
                set_data = match_data['sets'][current_set]
                
                # 设置session state来触发页面跳转
                if "should_switch_to_match_tab" not in st.session_state:
                    st.session_state.should_switch_to_match_tab = True
                
                # 成功提示和重新加载
                st.success("✅ 设置已确认，请点击「比赛记录」标签继续")
                st.rerun()

with tab2:
    st.subheader("比赛记录")
    
    # 重新加载最新数据，确保显示最新设置
    match_data = data_manager.load_match(match_id)
    if not match_data:
        st.error("⚠️ 无法加载比赛数据")
        st.stop()
    
    # 获取最新的当前局数据
    set_data = match_data['sets'][current_set]
    
    # 获取当前场上位置（无论是否已确认，都需要这个变量）
    current_positions = set_data['current_position']['us']
    
    # 检查是否已确认初始设置
    if not set_data.get('initial_confirmed', False):
        st.warning("⚠️ 请先在「局前设置」标签页完成并确认初始设置")
        st.info("点击上方「局前设置」标签，完成初始设置并点击「确认并开始比赛」按钮")
    else:
        # 添加重置按钮
        reset_col1, reset_col2 = st.columns([1, 3])
        with reset_col1:
            if st.button("🔄 重置本局", key=f"reset_match_{current_set}"):
                # 确认框
                confirm = st.checkbox("确认重置?", key=f"confirm_reset_{current_set}")
                if confirm:
                    # 直接重写整个逻辑，简单明了地处理
                    try:
                        # 1. 获取最新数据
                        fresh_match_data = data_manager.load_match(match_id)
                        
                        # 2. 获取原始初始位置和设置
                        initial_position = fresh_match_data['sets'][current_set]['initial_position'].copy()
                        initial_serve = fresh_match_data['sets'][current_set].get('serve_first', 'us')
                        initial_liberos = fresh_match_data['sets'][current_set].get('liberos', {}).get('us', [])
                        
                        # 3. 直接修改当前局数据
                        fresh_match_data['sets'][current_set] = {
                            'number': current_set,
                            'initial_position': initial_position,
                            'current_position': {
                                'us': initial_position['us'].copy() if 'us' in initial_position else ["" for _ in range(6)],
                                'them': initial_position['them'].copy() if 'them' in initial_position else ["" for _ in range(6)]
                            },
                            'serve_first': initial_serve,
                            'current_server': initial_serve,
                            'rotation_index': 0,
                            'score': {'us': 0, 'them': 0},
                            'events': [],
                            'substitutions': [],
                            'timeouts': {'us': [], 'them': []},
                            'stats': {
                                'us': {'attacks': [], 'blocks': [], 'serves': [], 'receives': []},
                                'them': {'attacks': [], 'blocks': [], 'serves': [], 'receives': []}
                            },
                            'status': 'in_progress',
                            'initial_confirmed': True,
                            'liberos': {'us': initial_liberos if initial_liberos else [], 'them': []}
                        }
                        
                        # 4. 保存修改后的数据
                        data_manager.save_match(match_id, fresh_match_data)
                        
                        # 5. 显示成功消息
                        st.success("✅ 已重置本局")
                    except Exception as e:
                        st.error(f"重置失败: {str(e)}")
                    
                    # 6. 强制刷新页面
                    st.rerun()
        
        # 显示当前场上位置
        st.subheader("当前场上位置")
        # 获取自由人信息
        liberos = set_data.get('liberos', {}).get('us', []) if 'liberos' in set_data else []
        
        # 确保当前位置和自由人信息是最新的
        current_positions = set_data['current_position']['us']
        
        fig = plot_volleyball_court_with_background(
            current_positions,
            serve_side="us" if set_data['current_server'] == "us" else None,
            rotation_index=set_data.get('rotation_index', 0),
            liberos=liberos  # 传递自由人列表
        )
        st.pyplot(fig)
        
        # 比分显示和控制
        score_col1, score_col2, score_col3 = st.columns([2,1,2])
        with score_col1:
            if st.button("我方得分 +1", key=f"score_us_{current_set}"):
                try:
                    # 1. 获取最新数据
                    fresh_match_data = data_manager.load_match(match_id)
                    
                    # 2. 直接更新比分
                    fresh_match_data['sets'][current_set]['score']['us'] += 1
                    
                    # 3. 检查发球权变更
                    current_server = fresh_match_data['sets'][current_set]['current_server']
                    if 'us' != current_server:
                        # 获得发球权并轮转
                        fresh_match_data['sets'][current_set]['current_server'] = 'us'
                        current_rotation = fresh_match_data['sets'][current_set].get('rotation_index', 0)
                        fresh_match_data['sets'][current_set]['rotation_index'] = (current_rotation + 1) % 6
                    
                    # 4. 保存更新
                    data_manager.save_match(match_id, fresh_match_data)
                except Exception as e:
                    st.error(f"记录得分失败: {str(e)}")
                
                # 5. 强制刷新页面    
                st.rerun()
                
        with score_col2:
            # 实时获取最新比分显示
            latest_match = data_manager.load_match(match_id)
            latest_score = latest_match['sets'][current_set]['score']
            st.markdown(f"### {latest_score['us']} - {latest_score['them']}")
            
        with score_col3:
            if st.button("对方得分 +1", key=f"score_them_{current_set}"):
                try:
                    # 1. 获取最新数据
                    fresh_match_data = data_manager.load_match(match_id)
                    
                    # 2. 直接更新比分
                    fresh_match_data['sets'][current_set]['score']['them'] += 1
                    
                    # 3. 检查发球权变更
                    current_server = fresh_match_data['sets'][current_set]['current_server']
                    if 'them' != current_server:
                        # 获得发球权
                        fresh_match_data['sets'][current_set]['current_server'] = 'them'
                    
                    # 4. 保存更新
                    data_manager.save_match(match_id, fresh_match_data)
                except Exception as e:
                    st.error(f"记录得分失败: {str(e)}")
                
                # 5. 强制刷新页面
                st.rerun()
        
        # 比赛事件记录
        col1, col2 = st.columns(2)
        with col1:
            # 换人记录
            st.markdown("**换人记录**")
            with st.expander("换人"):
                # 选择换人位置
                position = st.selectbox("选择换人位置", range(1, 7), format_func=lambda x: f"{x}号位")
                # 获取当前该位置的球员
                current_player = current_positions[position-1]
                st.text(f"当前球员：{current_player}")
                # 选择替换球员（排除已上场球员）
                available_subs = [p for p in available_players if p not in current_positions]
                sub_player = st.selectbox("选择替换球员", [""] + available_subs)
                
                if st.button("确认换人", key=f"confirm_sub_{current_set}"):
                    if sub_player:
                        if data_manager.record_substitution(match_id, current_set, 'us', sub_player, current_player, position-1):
                            # 立即重新加载数据
                            match_data = data_manager.load_match(match_id)
                            set_data = match_data['sets'][current_set]
                            current_positions = set_data['current_position']['us']
                            st.success("✅ 换人成功")
                            st.rerun()
        
        with col2:
            # 暂停记录
            st.markdown("**暂停记录**")
            if st.button("记录暂停", key=f"timeout_{current_set}"):
                if data_manager.record_timeout(match_id, current_set, 'us'):
                    # 立即重新加载数据
                    match_data = data_manager.load_match(match_id)
                    set_data = match_data['sets'][current_set]
                    current_positions = set_data['current_position']['us']
                    st.success("✅ 暂停记录已保存")
                    st.rerun()
            
            # 显示暂停记录
            timeouts = set_data['timeouts']['us']
            if timeouts:
                for i, timeout in enumerate(timeouts, 1):
                    st.text(f"第{i}次暂停：{timeout['score']['us']}-{timeout['score']['them']}")

with tab3:
    st.subheader("数据统计")
    
    # 显示本局统计数据
    stats = set_data['stats']['us']
    
    # 创建统计表格
    stats_df = pd.DataFrame({
        '球员': list(set([stat['player'] for stat_type in stats.values() for stat in stat_type])),
    })
    
    # 计算各项统计数据
    for stat_type in ['attacks', 'blocks', 'serves', 'receives']:
        stats_df[stat_type] = stats_df['球员'].apply(
            lambda player: len([s for s in stats[stat_type] if s['player'] == player])
        )
    
    # 重命名列
    stats_df.columns = ['球员', '进攻', '拦网', '发球', '接发球']
    
    # 显示统计表格
    st.dataframe(stats_df)
    
    # 导出数据按钮
    if st.button("📊 导出统计数据", key=f"export_{current_set}"):
        # TODO: 实现数据导出功能
        pass 