"""
统调电厂用电量计算主程序
"""

import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from switch_processor import process_switch_data
from power_processor import process_power_data
from consumption_calculator import calculate_power_consumption
from config import START_DATE, END_DATE
from meter_config import initialize_meter_config

def main():
    """主程序入口"""
    print("开始执行统调电厂用电量计算程序")
    print("=" * 60)
    
    # 初始化电能表配置
    print("\n初始化电能表配置...")
    meter_ids, calculation_rules, transformation_ratios = initialize_meter_config()
    
    # 过滤掉标记为不计算的电能表
    active_meters = [meter for meter in meter_ids if calculation_rules.get(meter, 1) != 4]
    filtered_count = len(meter_ids) - len(active_meters)
    if filtered_count > 0:
        print(f"过滤掉 {filtered_count} 个不计算的电能表")
    print(f"已配置 {len(active_meters)} 个电能表")
    
    # 第一步：处理启停数据
    print("\n第一步：处理启停数据")
    downtime_intervals, change_points = process_switch_data()
    if downtime_intervals is None or change_points is None:
        print("启停数据处理失败，程序终止")
        return
    
    # 第二步：处理电量数据
    print("\n第二步：处理电量数据")
    process_power_data(meter_ids, calculation_rules)
    
    # 第三步：计算停机耗电量
    print("\n第三步：计算停机耗电量")
    calculate_power_consumption(downtime_intervals, change_points, START_DATE, END_DATE, 
                              meter_ids, calculation_rules, transformation_ratios)
    
    print("\n" + "=" * 60)
    print("统调电厂用电量计算程序执行完成！")

if __name__ == "__main__":
    main()