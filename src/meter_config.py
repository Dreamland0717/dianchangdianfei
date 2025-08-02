"""
统调电厂电能表配置模块 - 处理电能表资产编号和计算规则配置
"""

import json
import os
import pandas as pd
from config import INPUT_DIR, INPUT_POWER_FILE

# 配置文件路径 - 使用统一的input目录
METER_CONFIG_FILE = os.path.join("input", "meter_config.json")

# 计算规则定义
CALCULATION_RULES = {
    1: "正向 - 反向",
    2: "反向 - 正向", 
    3: "只取正向",
    4: "不计算(跳过)"
}

def get_meters_from_power_data():
    """从电量数据中提取电能表资产编号"""
    file_path = os.path.join(INPUT_DIR, INPUT_POWER_FILE)
    if os.path.exists(file_path):
        try:
            # 使用dtype参数确保资产编号正确读取为字符串
            df = pd.read_excel(file_path, dtype={'电能表资产编号': str})
            if '电能表资产编号' in df.columns:
                # 去除空值并去重
                meter_ids = df['电能表资产编号'].dropna().unique().tolist()
                # 转换为字符串并去除空格
                meter_ids = [str(meter_id).strip() for meter_id in meter_ids if str(meter_id).strip()]
                print(f"从电量数据中提取到 {len(meter_ids)} 个电能表资产编号: {meter_ids}")
                return meter_ids
            else:
                print("电量数据中未找到'电能表资产编号'列")
        except Exception as e:
            print(f"读取电量数据时出错: {e}")
    else:
        # 检查文件是否存在（使用完整路径）
        full_path = os.path.join(os.getcwd(), "input", INPUT_POWER_FILE)
        if os.path.exists(full_path):
            try:
                # 使用dtype参数确保资产编号正确读取为字符串
                df = pd.read_excel(full_path, dtype={'电能表资产编号': str})
                if '电能表资产编号' in df.columns:
                    # 去除空值并去重
                    meter_ids = df['电能表资产编号'].dropna().unique().tolist()
                    # 转换为字符串并去除空格
                    meter_ids = [str(meter_id).strip() for meter_id in meter_ids if str(meter_id).strip()]
                    print(f"从电量数据中提取到 {len(meter_ids)} 个电能表资产编号: {meter_ids}")
                    return meter_ids
                else:
                    print("电量数据中未找到'电能表资产编号'列")
            except Exception as e:
                print(f"读取电量数据时出错: {e}")
        else:
            print(f"电量数据文件不存在: {file_path}")
    
    # 默认返回空列表
    return []

def load_meter_config():
    """
    从JSON文件加载电能表配置
    返回: (资产编号列表, 计算规则字典, 变比值字典)
    """
    if os.path.exists(METER_CONFIG_FILE):
        try:
            with open(METER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"成功从 {METER_CONFIG_FILE} 加载电能表配置")
            return (
                config.get('meter_ids', []), 
                config.get('calculation_rules', {}), 
                config.get('transformation_ratios', {})
            )
        except Exception as e:
            print(f"读取JSON配置文件时出错: {e}")
    
    return [], {}, {}

def save_meter_config(meter_ids, calculation_rules, transformation_ratios):
    """
    保存电能表配置到JSON文件
    不保存计算规则为4（不计算）的电能表变比值
    """
    # 过滤掉计算规则为4的电能表变比值
    filtered_transformation_ratios = {}
    for meter_id, ratio in transformation_ratios.items():
        # 如果计算规则为4（不计算），则不保存变比值
        if calculation_rules.get(meter_id, 1) != 4:
            filtered_transformation_ratios[meter_id] = ratio
        else:
            # 对于不计算的电能表，保存默认变比值1.0
            filtered_transformation_ratios[meter_id] = 1.0
    
    config = {
        'meter_ids': meter_ids,
        'calculation_rules': calculation_rules,
        'transformation_ratios': filtered_transformation_ratios
    }
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(METER_CONFIG_FILE), exist_ok=True)
        
        with open(METER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        print(f"电能表配置已保存到 {METER_CONFIG_FILE}")
    except Exception as e:
        print(f"保存JSON配置文件时出错: {e}")

def get_user_input_for_meter(meter_id):
    """
    获取用户对特定电能表的配置输入
    返回: (计算规则, 变比值)
    """
    print(f"\n电能表资产编号: {meter_id}")
    
    # 获取计算规则
    while True:
        print("请选择计算规则:")
        for rule_num, rule_desc in CALCULATION_RULES.items():
            print(f"  {rule_num}. {rule_desc}")
        
        try:
            rule_choice = int(input("请输入规则编号 (1-4): "))
            if rule_choice in CALCULATION_RULES:
                if rule_choice == 4:  # 不计算规则
                    print(f"电能表 {meter_id} 将被跳过计算")
                    return rule_choice, 1.0
                break
            else:
                print("无效的选择，请输入 1-4 之间的数字")
        except ValueError:
            print("请输入有效的数字")
    
    # 如果选择了不计算，则不需要输入变比值
    if rule_choice == 4:
        return rule_choice, 1.0
    
    # 获取变比值
    while True:
        try:
            ratio = float(input("请输入变比值 (例如 1.0): "))
            if ratio > 0:
                break
            else:
                print("变比值必须大于0")
        except ValueError:
            print("请输入有效的数字")
    
    return rule_choice, ratio

def filter_skipped_meters(meter_ids, calculation_rules):
    """
    过滤掉计算规则为4（不计算）的电能表
    """
    return [meter_id for meter_id in meter_ids 
            if calculation_rules.get(meter_id, 1) != 4]

def reset_meter_config():
    """
    重置电能表配置（删除配置文件）
    """
    config_file_path = os.path.join(INPUT_DIR, "meter_config.json")
    if os.path.exists(config_file_path):
        try:
            os.remove(config_file_path)
            print("电能表配置已重置")
            return True
        except Exception as e:
            print(f"重置电能表配置时出错: {e}")
            return False
    elif os.path.exists(METER_CONFIG_FILE):  # 检查相对路径
        try:
            os.remove(METER_CONFIG_FILE)
            print("电能表配置已重置")
            return True
        except Exception as e:
            print(f"重置电能表配置时出错: {e}")
            return False
    else:
        print("配置文件不存在，无需重置")
        return True

def initialize_meter_config(force_reset=False):
    """
    初始化电能表配置，如果配置文件不存在，则询问用户输入配置
    """
    # 如果强制重置，则删除现有配置文件
    if force_reset and os.path.exists(METER_CONFIG_FILE):
        reset_meter_config()
    
    # 获取电能表资产编号
    meter_ids = get_meters_from_power_data()
    
    # 尝试加载现有配置
    loaded_meter_ids, calculation_rules, transformation_ratios = load_meter_config()
    
    # 如果配置文件存在且包含所有电能表，则直接使用
    if not force_reset and loaded_meter_ids and set(meter_ids).issubset(set(loaded_meter_ids)):
        print("使用现有的电能表配置")
        # 只返回当前需要的电能表配置
        filtered_calculation_rules = {meter_id: calculation_rules.get(meter_id, 1) for meter_id in meter_ids}
        filtered_transformation_ratios = {meter_id: transformation_ratios.get(meter_id, 1.0) for meter_id in meter_ids}
        return meter_ids, filtered_calculation_rules, filtered_transformation_ratios
    
    # 否则需要用户输入配置
    print("未找到有效的配置文件，需要为每个电能表输入配置信息")
    calculation_rules = {}
    transformation_ratios = {}
    
    for meter_id in meter_ids:
        rule_choice, ratio = get_user_input_for_meter(meter_id)
        calculation_rules[meter_id] = rule_choice
        transformation_ratios[meter_id] = ratio
    
    # 保存配置
    save_meter_config(meter_ids, calculation_rules, transformation_ratios)
    
    return meter_ids, calculation_rules, transformation_ratios
