"""
统调电厂配置文件 - 包含所有项目配置参数
"""

import os
import pandas as pd
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
INPUT_SWITCH_FILE = "机组启停数据查询.xlsx"
INPUT_POWER_FILE = "电厂96点示值查询.xlsx"

# ==================== 输出文件配置 ====================
OUTPUT_SWITCH_FILE = "处理后的机组启停数据.xlsx"

# ==================== 处理参数配置 ====================
# 从电量数据中提取电能表资产编号
def get_target_meters():
    """从电量数据中提取电能表资产编号"""
    power_file_path = os.path.join(INPUT_DIR, INPUT_POWER_FILE)
    if os.path.exists(power_file_path):
        try:
            # 使用dtype参数确保资产编号正确读取为字符串
            df_power = pd.read_excel(power_file_path, dtype={'电能表资产编号': str})
            if '电能表资产编号' in df_power.columns:
                # 去除空值并去重
                meter_ids = df_power['电能表资产编号'].dropna().unique().tolist()
                # 转换为字符串并去除空格
                meter_ids = [str(meter_id).strip() for meter_id in meter_ids if str(meter_id).strip()]
                print(f"从电量数据中提取到 {len(meter_ids)} 个电能表资产编号: {meter_ids}")
                return meter_ids
            else:
                print("电量数据中未找到'电能表资产编号'列")
        except Exception as e:
            print(f"读取电量数据时出错: {e}")
    else:
        print(f"电量数据文件不存在: {power_file_path}")
    
    # 默认返回空列表
    return []

# TARGET_METERS 将在运行时动态获取
TARGET_METERS = get_target_meters()

# 计算时间区间
START_DATE = datetime(2025, 7, 1, 0, 0)
END_DATE = datetime(2025, 8, 1, 0, 0)

# 电量计算相关列
ENERGY_COLS = [
    '正向有功总(kWh)',
    '反向有功总(kWh)',
]