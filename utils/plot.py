import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

def plot_volleyball_court_with_background(player_names, bg_path="resource/court.png", liberos=None, serve_side=None, rotation_index=None, figsize=None):
    """绘制排球场地
    Args:
        player_names: 场上6个位置的球员名单，按[4号位,3号位,2号位,5号位,6号位,1号位]顺序
        bg_path: 背景图片路径
        liberos: 自由人列表
        serve_side: 发球方 ("us" 或 "them")
        rotation_index: 当前轮转次数（0-5）
        figsize: 图形大小元组 (width, height)，默认为 None
    """
    if liberos is None:
        liberos = []
    
    if figsize is None:
        # 使用相对尺寸，根据页面宽度自动调整
        figsize = (6, 4.8)  # 保持4:3.2的比例

    # 使用相对坐标（百分比）
    COURT_WIDTH = 1.0
    COURT_HEIGHT = 1.0
    
    # 位置使用相对坐标（0-1范围）
    positions = {
        0: (0.22, 0.72),  # 4号位（左前）- 左上角位置
        1: (0.50, 0.72),  # 3号位（中前）- 上中位置
        2: (0.78, 0.72),  # 2号位（右前）- 右上角位置
        3: (0.22, 0.28),  # 5号位（左后）- 左下角位置
        4: (0.50, 0.28),  # 6号位（中后）- 下中位置
        5: (0.78, 0.28)   # 1号位（右后）- 右下角位置
    }
    
    # 位置标签
    position_labels = {
        0: "4",  # 左前
        1: "3",  # 中前
        2: "2",  # 右前
        3: "5",  # 左后
        4: "6",  # 中后
        5: "1"   # 右后
    }

    # 轮转逻辑
    if rotation_index is not None and rotation_index > 0:
        # display_order_to_court_spot_map: 列表索引 -> 场上真实位置号 (e.g., display_order_to_court_spot_map[0] is 4 for 4号位)
        display_order_to_court_spot_map = [int(position_labels[i]) for i in range(6)]
        # court_spot_to_display_order_map: 场上真实位置号 -> 列表索引 (e.g., court_spot_to_display_order_map[4] is 0)
        court_spot_to_display_order_map = {spot: i for i, spot in enumerate(display_order_to_court_spot_map)}

        # 排球轮转规则：当前位置 -> 下一个位置
        rotation_path = {
            1: 6, 6: 5, 5: 4, 4: 3, 3: 2, 2: 1
        }

        original_player_names = list(player_names) # 传入的player_names是按显示顺序[4号位球员, 3号位球员,...]排列的
        rotated_player_list = [""] * 6

        for display_idx in range(6):
            current_player = original_player_names[display_idx]
            # 该球员当前所在的实际场上位置
            current_court_spot = display_order_to_court_spot_map[display_idx]
            
            # 计算经过 rotation_index 次轮转后，该球员会去到哪个实际场上位置
            player_target_court_spot = current_court_spot
            for _ in range(rotation_index % 6): # Apply rotation 'rotation_index' times
                player_target_court_spot = rotation_path[player_target_court_spot]
            
            # 找到这个新的实际场上位置对应的显示列表索引
            target_display_idx = court_spot_to_display_order_map[player_target_court_spot]
            rotated_player_list[target_display_idx] = current_player
        
        player_names = rotated_player_list

    # 创建图形
    fig, ax = plt.subplots(figsize=figsize)
    
    # 加载并显示背景图片
    img = Image.open(bg_path)
    ax.imshow(img, extent=[0, COURT_WIDTH, 0, COURT_HEIGHT])
    ax.set_xlim(0, COURT_WIDTH)
    ax.set_ylim(0, COURT_HEIGHT)
    ax.set_aspect('equal')
    ax.axis('off')

    # 计算圆圈大小（相对于场地大小）
    circle_radius = 0.08
    libero_circle_radius = 0.05
    
    # 绘制球员位置
    for i in range(6):
        name = player_names[i]
        x, y = positions[i]
        # 判断是否为发球位（1号位）
        is_server = (i == 5 and serve_side == "us")
        circle_color = 'lightgreen' if is_server else 'skyblue'
        # 绘制位置圆圈
        circle = plt.Circle((x, y), circle_radius, color=circle_color, alpha=0.3)
        ax.add_patch(circle)
        # 绘制球员名字或位置编号
        if not name:
            ax.text(x, y + 0.03, position_labels[i], fontsize=10, ha='center', va='center', color='gray')
        else:
            ax.text(x, y, name, fontsize=10, ha='center', va='center', color='black')
            if is_server:
                ax.text(x, y - 0.05, "🎾", fontsize=10, ha='center', va='center')

    # 绘制自由人位置（使用相对坐标）
    libero_positions = [(0.08, 0.05), (0.08, 0.15)]
    for i, name in enumerate(liberos[:2]):
        if name:
            x, y = libero_positions[i]
            circle = plt.Circle((x, y), libero_circle_radius, color='orange', alpha=0.3)
            ax.add_patch(circle)
            ax.text(x, y, name, fontsize=8, ha='center', va='center', color='black')

    # 移除轮转说明以避免乱码
    # ax.text(0.5, 0.95, f"当前轮转：第 {rotation_index + 1 if rotation_index is not None else 1} 轮", 
    #         fontsize=10, ha='center', va='center')

    plt.tight_layout()
    return fig
