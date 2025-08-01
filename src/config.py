"""
配置文件 - 包含所有项目配置参数
"""

import os
from datetime import datetime

# ==================== 基础配置 ====================
# 工作目录
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(WORK_DIR))

# 修正 PROJECT_DIR 路径，确保指向 power_analysis_project 目录
if os.path.basename(PROJECT_DIR) != "power_analysis_project":
    PROJECT_DIR = os.path.join(os.path.dirname(PROJECT_DIR), "power_analysis_project")

# 输入输出目录
INPUT_DIR = os.path.join(PROJECT_DIR, "input")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

# 确保输入输出目录存在
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== 输入文件配置 ====================
INPUT_SWITCH_FILE = "机组启停数据查询（萧山）.xlsx"
INPUT_POWER_FILE = "电厂96点示值查询（萧山）.xlsx"

# ==================== 输出文件配置 ====================
OUTPUT_SWITCH_FILE = "处理后的机组启停数据（萧山）.xlsx"

# ==================== 处理参数配置 ====================
# 指定需要处理的电能表资产编号
TARGET_METERS = [
    '08450124465286',
    '08450124465285',
    '08450124465291',
    '08450124465288'
]

# 计算时间区间
START_DATE = datetime(2025, 7, 1, 0, 0)
END_DATE = datetime(2025, 8, 1, 0, 0)

# 电量计算相关列
ENERGY_COLS = [
    '正向有功总(kWh)',
    '反向有功总(kWh)',
]

# ==================== 计算规则配置 ====================
# 规则1: 原规则 (正向 - 反向)
RULE1_IDS = ['08000100084198']

# 规则2: 反向减正向
RULE2_IDS = ['00010008419844']

# 规则3: 只取正向
RULE3_IDS = ['08450124465285', '08450124465286', '08450124465288', '08450124465291']