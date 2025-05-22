# 排球战术与比赛管理工具

本项目是一个基于 Streamlit 的排球战术与比赛管理分析工具，支持球队名单管理、比赛过程记录、事件采集、统计分析与可视化。

## 功能特色

- **球队管理**：支持球员、自由人名单的录入与导入导出。
- **比赛管理**：新建、编辑、删除比赛，设置局数、胜局规则等。
- **比赛详情**：每局可设置初始站位、发球方，实时记录得分、换人、暂停等事件。
- **事件采集**：每次得分后可补充事件详情（得分类型、关联球员、备注等）。
- **统计分析**：支持本局/全场统计，饼图横向排列，图例纵向在下方，统计明细可导出。
- **可视化**：所有统计图表美观紧凑，支持自定义字体和布局。

## 安装方法

1. 克隆本仓库：
   ```bash
   git clone <your-repo-url>
   cd volleyball_tactics_tool
   ```
2. 安装依赖（需 Python 3.8+，建议虚拟环境）：
   ```bash
   pip install -r requirements.txt
   ```
   > 如果没有 requirements.txt，可手动安装主要依赖：
   > ```
   > pip install streamlit matplotlib pandas pillow
   > ```

## 使用方法

1. 启动应用：
   ```bash
   streamlit run main.py
   ```
2. 按页面导航依次完成球队名单、比赛管理、比赛详情等操作。

## 目录结构

```
volleyball_tactics_tool/
├── main.py                # 入口，侧边栏导航
├── pages/
│   ├── 1_playerlist.py    # 球员名单管理
│   ├── 2_match_manager.py # 比赛管理
│   └── 3_match_detail.py  # 比赛详情与统计
├── utils/
│   ├── data_manager.py    # 数据管理与存储
│   └── plot.py            # 场地与统计图绘制
├── resource/
│   ├── court.png          # 场地图像
│   └── ...                # 其他资源
├── teams/                 # 球队数据
├── matches/               # 比赛数据
└── requirements.txt       # 依赖列表（如有）
```

## 贡献与反馈

欢迎提交 issue 或 PR 反馈建议与问题！ 