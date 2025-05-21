import json
import os
import uuid
from datetime import datetime

TEAM_DIR = 'teams'
MATCH_DIR = 'matches'

os.makedirs(TEAM_DIR, exist_ok=True)
os.makedirs(MATCH_DIR, exist_ok=True)

class DataManager:
    """统一数据管理，支持球队、比赛管理，并为统计功能预留接口"""
    def __init__(self):
        pass

    # 球队相关
    def save_team(self, team_name, team_data):
        path = os.path.join(TEAM_DIR, f'{team_name}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(team_data, f, ensure_ascii=False, indent=4)

    def load_team(self, team_name):
        path = os.path.join(TEAM_DIR, f'{team_name}.json')
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_teams(self):
        return [f[:-5] for f in os.listdir(TEAM_DIR) if f.endswith('.json')]

    # 比赛相关
    def create_match(self, match_info):
        """创建新比赛
        Args:
            match_info (dict): 包含比赛基本信息的字典
        Returns:
            str: 新创建的比赛ID
        """
        match_id = str(uuid.uuid4())
        match_data = {
            'id': match_id,
            'created_at': datetime.now().isoformat(),
            'info': match_info,  # 比赛名称、双方队名、规则等
            'sets': [],         # 每局比赛数据
            'current_set': 0,   # 当前局数
            'score': {          # 总比分
                'us': 0,
                'them': 0
            }
        }
        self.save_match(match_id, match_data)
        return match_id

    def save_match(self, match_id, match_data):
        """保存比赛数据
        Args:
            match_id (str): 比赛ID
            match_data (dict): 比赛数据
        """
        path = os.path.join(MATCH_DIR, f'{match_id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(match_data, f, ensure_ascii=False, indent=4)

    def load_match(self, match_id):
        """加载比赛数据
        Args:
            match_id (str): 比赛ID
        Returns:
            dict: 比赛数据，如果不存在返回None
        """
        path = os.path.join(MATCH_DIR, f'{match_id}.json')
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_matches(self):
        """列出所有比赛
        Returns:
            list: 比赛ID列表
        """
        return [f[:-5] for f in os.listdir(MATCH_DIR) if f.endswith('.json')]

    def create_set(self, match_id, set_number):
        """创建新的一局
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
        Returns:
            dict: 新创建的一局数据
        """
        match_data = self.load_match(match_id)
        if not match_data:
            return None

        new_set = {
            'number': set_number,
            'initial_position': {
                'us': ["" for _ in range(6)],
                'them': ["" for _ in range(6)]
            },
            'current_position': {  # 当前场上位置
                'us': ["" for _ in range(6)],
                'them': ["" for _ in range(6)]
            },
            'serve_first': 'us',  # 发球方，'us' 或 'them'
            'current_server': 'us',  # 当前发球方
            'rotation_index': 0,  # 当前轮转次数
            'score': {
                'us': 0,
                'them': 0
            },
            'events': [],  # 比赛事件记录
            'substitutions': [],  # 换人记录
            'timeouts': {  # 暂停记录
                'us': [],
                'them': []
            },
            'stats': {  # 技术统计
                'us': {
                    'attacks': [],  # 进攻
                    'blocks': [],   # 拦网
                    'serves': [],   # 发球
                    'receives': []  # 接发球
                },
                'them': {
                    'attacks': [],
                    'blocks': [],
                    'serves': [],
                    'receives': []
                }
            },
            'status': 'not_started'  # not_started, in_progress, completed
        }

        match_data['sets'].append(new_set)
        match_data['current_set'] = set_number
        self.save_match(match_id, match_data)
        return new_set

    def update_set(self, match_id, set_number, set_data):
        """更新某一局的数据
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
            set_data (dict): 该局的新数据
        """
        match_data = self.load_match(match_id)
        if not match_data or set_number >= len(match_data['sets']):
            return False

        match_data['sets'][set_number] = set_data
        self.save_match(match_id, match_data)
        return True

    def get_set(self, match_id, set_number):
        """获取某一局的数据
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
        Returns:
            dict: 该局的数据，如果不存在返回None
        """
        match_data = self.load_match(match_id)
        if not match_data or set_number >= len(match_data['sets']):
            return None
        return match_data['sets'][set_number]

    def update_set_position(self, match_id, set_number, team, positions, is_initial=False):
        """更新某一局的场上位置
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
            team (str): 队伍 ('us' 或 'them')
            positions (list): 位置列表
            is_initial (bool): 是否为初始站位
        """
        match_data = self.load_match(match_id)
        if not match_data or set_number >= len(match_data['sets']):
            return False

        if is_initial:
            match_data['sets'][set_number]['initial_position'][team] = positions
        match_data['sets'][set_number]['current_position'][team] = positions
        self.save_match(match_id, match_data)
        return True

    def record_point(self, match_id, set_number, team):
        """记录得分
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
            team (str): 得分方 ('us' 或 'them')
        """
        match_data = self.load_match(match_id)
        if not match_data or set_number >= len(match_data['sets']):
            return False

        # 更新该局比分
        match_data['sets'][set_number]['score'][team] += 1
        
        # 如果得分方是发球方，不需要轮转
        # 如果得分方不是发球方，获得发球权并轮转
        current_server = match_data['sets'][set_number]['current_server']
        if team != current_server:
            match_data['sets'][set_number]['current_server'] = team
            if team == 'us':
                # 我方获得发球权时轮转
                rotation_index = match_data['sets'][set_number]['rotation_index']
                match_data['sets'][set_number]['rotation_index'] = (rotation_index + 1) % 6

        # 检查是否达到获胜条件
        score = match_data['sets'][set_number]['score']
        rules = match_data['info']['rules']
        points_to_win = rules['points_to_win']
        point_diff = rules['point_diff']
        
        if (score['us'] >= points_to_win or score['them'] >= points_to_win) and \
           abs(score['us'] - score['them']) >= point_diff:
            match_data['sets'][set_number]['status'] = 'completed'
            # 更新总比分
            winner = 'us' if score['us'] > score['them'] else 'them'
            match_data['score'][winner] += 1

        self.save_match(match_id, match_data)
        return True

    def record_substitution(self, match_id, set_number, team, in_player, out_player, position):
        """记录换人
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
            team (str): 队伍 ('us' 或 'them')
            in_player (str): 上场球员
            out_player (str): 下场球员
            position (int): 换人位置
        """
        match_data = self.load_match(match_id)
        if not match_data or set_number >= len(match_data['sets']):
            return False

        sub_record = {
            'time': datetime.now().isoformat(),
            'team': team,
            'in_player': in_player,
            'out_player': out_player,
            'position': position,
            'score': match_data['sets'][set_number]['score'].copy()
        }
        
        match_data['sets'][set_number]['substitutions'].append(sub_record)
        
        # 更新场上位置
        current_positions = match_data['sets'][set_number]['current_position'][team]
        current_positions[position] = in_player
        
        self.save_match(match_id, match_data)
        return True

    def record_timeout(self, match_id, set_number, team):
        """记录暂停
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
            team (str): 请求暂停的队伍 ('us' 或 'them')
        """
        match_data = self.load_match(match_id)
        if not match_data or set_number >= len(match_data['sets']):
            return False

        timeout_record = {
            'time': datetime.now().isoformat(),
            'score': match_data['sets'][set_number]['score'].copy()
        }
        
        match_data['sets'][set_number]['timeouts'][team].append(timeout_record)
        self.save_match(match_id, match_data)
        return True

    def record_stat(self, match_id, set_number, team, stat_type, player, result):
        """记录技术统计
        Args:
            match_id (str): 比赛ID
            set_number (int): 局数
            team (str): 队伍 ('us' 或 'them')
            stat_type (str): 统计类型 ('attacks', 'blocks', 'serves', 'receives')
            player (str): 球员名称
            result (str): 结果
        """
        match_data = self.load_match(match_id)
        if not match_data or set_number >= len(match_data['sets']):
            return False

        stat_record = {
            'time': datetime.now().isoformat(),
            'player': player,
            'result': result,
            'score': match_data['sets'][set_number]['score'].copy()
        }
        
        match_data['sets'][set_number]['stats'][team][stat_type].append(stat_record)
        self.save_match(match_id, match_data)
        return True

    # 统计接口预留
    def save_stats(self, match_id, stats):
        match = self.load_match(match_id)
        if match:
            match['stats'] = stats
            self.save_match(match_id, match)

    def save_tactics(self, match_id, tactics):
        match = self.load_match(match_id)
        if match:
            match['tactics'] = tactics
            self.save_match(match_id, match)

    def get_stats(self, match_id):
        match = self.load_match(match_id)
        return match.get('stats', {}) if match else {}

    def get_tactics(self, match_id):
        match = self.load_match(match_id)
        return match.get('tactics', {}) if match else {}

    def load_data(self):
        """
        加载JSON数据文件
        Returns:
            dict: 加载的数据，如果文件不存在则返回默认数据结构
        """
        if not os.path.exists(self.json_path):
            return self.create_default_data()
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return self.create_default_data()
    
    def create_default_data(self):
        """
        创建默认的数据结构
        Returns:
            dict: 默认的数据结构
        """
        return {
            "rotation_setup": ["" for _ in range(6)],
            "libero_positions": ["", ""],
            "final_rotation": 0,
            "player_list": [],
            "libero_list": []
        }
    
    def save_data(self):
        """
        保存数据到JSON文件
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存数据失败：{str(e)}")
            return False
    
    def update_rotation_setup(self, rotation_setup):
        """
        更新轮转设置
        Args:
            rotation_setup: 新的轮转设置列表
        """
        self.data["rotation_setup"] = rotation_setup
        self.save_data()
    
    def update_libero_positions(self, libero_positions):
        """
        更新自由人位置
        Args:
            libero_positions: 新的自由人位置列表
        """
        self.data["libero_positions"] = libero_positions
        self.save_data()
    
    def update_final_rotation(self, rotation_index):
        """
        更新最终轮转位置
        Args:
            rotation_index: 轮转索引（0-5）
        """
        self.data["final_rotation"] = rotation_index
        self.save_data()
    
    def get_current_rotation(self):
        """
        获取当前轮转设置
        Returns:
            tuple: (rotation_setup, libero_positions, final_rotation)
        """
        return (
            self.data["rotation_setup"],
            self.data["libero_positions"],
            self.data["final_rotation"]
        ) 