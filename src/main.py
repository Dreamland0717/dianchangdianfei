"""
统调电厂用电量计算主程序
"""

import os
import traceback
import pandas as pd
from switch_processor import process_switch_data
from power_processor import process_power_data
from consumption_calculator import calculate_power_consumption
from config import INPUT_DIR, OUTPUT_DIR, START_DATE, END_DATE
from utils import get_asset_id_from_filename

def get_target_meters():
    """从电量数据中提取电能表资产编号"""
    power_file_path = os.path.join(INPUT_DIR, "电厂96点示值查询.xlsx")
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

def main():
    """主函数"""
    print("开始执行统调电厂用电量计算程序")
    print("=" * 60)
    
    try:
        # 初始化项目结构
        # 确保输入输出目录存在（已在config.py中处理）
        pass
        
        # 加载配置
        try:
            # 从电量数据中提取电能表资产编号
            meter_ids = get_target_meters()
            
            # 默认计算规则和变比值（如果没有配置文件则使用默认值）
            calculation_rules = {}
            transformation_ratios = {}
            
            # 尝试从配置文件加载计算规则和变比值
            config_file = os.path.join(INPUT_DIR, "meter_config.json")
            if os.path.exists(config_file):
                import json
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        calculation_rules = config_data.get("calculation_rules", {})
                        transformation_ratios = config_data.get("transformation_ratios", {})
                    print("成功从 input\\meter_config.json 加载电能表配置")
                except Exception as e:
                    print(f"读取配置文件失败: {e}")
            else:
                print("未找到配置文件，将使用默认配置")
                
            print(f"初始化电能表配置...")
        except Exception as e:
            print(f"配置加载失败: {e}")
            print("详细错误信息:")
            traceback.print_exc()
            return
            
        if not meter_ids:
            print("错误: 未找到任何电能表资产编号，请检查电量数据文件格式是否正确")
            return
            
        # 过滤掉标记为不计算的电能表
        active_meters = [meter for meter in meter_ids if calculation_rules.get(meter, 1) != 4]
        filtered_count = len(meter_ids) - len(active_meters)
        if filtered_count > 0:
            print(f"过滤掉 {filtered_count} 个不计算的电能表")
        print(f"已配置 {len(active_meters)} 个电能表")
        
        # 第一步：处理启停数据
        print("\n第一步：处理启停数据")
        downtime_intervals, change_points_with_status = process_switch_data()
        if downtime_intervals is None or change_points_with_status is None:
            print("启停数据处理失败，程序终止")
            return
            
        if len(downtime_intervals) == 0:
            print("警告: 未提取到任何停机时间段")
        else:
            print(f"成功提取到 {len(downtime_intervals)} 个停机时间段")
            
        if len(change_points_with_status) == 0:
            print("警告: 未提取到任何启停状态变化点")
        else:
            print(f"成功提取到 {len(change_points_with_status)} 个启停状态变化点")
        
        # 第二步：处理电量数据
        print("\n第二步：处理电量数据")
        try:
            process_power_data(meter_ids, calculation_rules)
        except Exception as e:
            print(f"电量数据处理失败: {e}")
            print("详细错误信息:")
            traceback.print_exc()
            return
        
        # 第三步：计算停机耗电量
        print("\n第三步：计算停机耗电量")
        try:
            calculate_power_consumption(downtime_intervals, change_points_with_status, START_DATE, END_DATE, 
                                      meter_ids, calculation_rules, transformation_ratios)
        except Exception as e:
            print(f"停机耗电量计算失败: {e}")
            print("详细错误信息:")
            traceback.print_exc()
            return
        
        print("\n" + "=" * 60)
        print("统调电厂用电量计算程序执行完成！")
        
    except Exception as e:
        print(f"程序执行过程中发生未预期的错误: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()