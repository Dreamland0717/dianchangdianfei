"""
电力消耗分析主程序
"""

import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from switch_processor import process_switch_data
from power_processor import process_power_data
from consumption_calculator import calculate_power_consumption
from config import START_DATE, END_DATE

def main():
    """主程序入口"""
    print("开始执行电力消耗分析程序")
    print("=" * 60)
    
    # 第一步：处理启停数据
    print("\n第一步：处理启停数据")
    downtime_intervals, change_points = process_switch_data()
    if downtime_intervals is None or change_points is None:
        print("启停数据处理失败，程序终止")
        return
    
    # 第二步：处理电量数据
    print("\n第二步：处理电量数据")
    process_power_data()
    
    # 第三步：计算停机耗电量
    print("\n第三步：计算停机耗电量")
    calculate_power_consumption(downtime_intervals, change_points, START_DATE, END_DATE)
    
    print("\n" + "=" * 60)
    print("电力消耗分析程序执行完成！")

if __name__ == "__main__":
    main()