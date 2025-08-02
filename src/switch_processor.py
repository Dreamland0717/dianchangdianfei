"""
统调电厂启停数据处理模块
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import traceback
import logging
from typing import List, Tuple, Optional
from config import INPUT_DIR, OUTPUT_DIR, INPUT_SWITCH_FILE, OUTPUT_SWITCH_FILE, START_DATE, END_DATE

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def adjust_time(original_time: str | datetime, prev_status: int, current_status: int) -> datetime:
    """根据规则调整时间"""
    # 如果原始时间是字符串，转换为datetime
    if isinstance(original_time, str):
        dt = datetime.strptime(original_time.strip(), '%Y-%m-%d %H:%M:%S')
    else:
        dt = original_time
    
    # 计算当前时间所在的15分钟时段
    base_minute = (dt.minute // 15) * 15
    base_time = dt.replace(minute=base_minute, second=0, microsecond=0)
    
    # 新规则：
    # 0→1：调整为当前15分钟时段的结束时间（开始时间+15分钟）
    # 1→0：调整为当前15分钟时段的开始时间
    if prev_status == 0 and current_status == 1:
        # 从停止到启动：取当前15分钟时段的结束时间
        end_time = base_time + timedelta(minutes=15)
        logger.info(f"将时间从 {dt} 调整为 {end_time} (状态变化: {prev_status}→{current_status})")
        return end_time
    
    elif prev_status == 1 and current_status == 0:
        # 从启动到停止：取当前15分钟时段的开始时间
        logger.info(f"将时间从 {dt} 调整为 {base_time} (状态变化: {prev_status}→{current_status})")
        return base_time
    
    # 状态不变则返回原始时间
    logger.debug(f"状态未变化，保持原始时间 {dt}")
    return dt

def extract_downtime_intervals_and_changepoints(switch_file: str) -> Tuple[List[Tuple[datetime, datetime]], List[datetime]]:
    """提取停机时间段和启停状态变化点"""
    try:
        logger.info(f"开始处理启停数据文件: {switch_file}")
        
        # 读取Excel文件，直接解析日期时间列
        df_switch = pd.read_excel(switch_file, parse_dates=['启停时间'])
        logger.info(f"成功读取启停数据文件: {switch_file}")
        logger.info(f"数据行数: {len(df_switch)}")
        
        # 检查必要的列是否存在
        required_columns = ['电厂名称', '数据日期', '启停时间', '启停标识']
        missing_columns = [col for col in required_columns if col not in df_switch.columns]
        if missing_columns:
            error_msg = f"文件 {switch_file} 缺少必要列: {', '.join(missing_columns)}"
            logger.error(error_msg)
            return [], []
        
        # 按时间排序
        df_switch = df_switch.sort_values('启停时间')
        
        downtime_intervals = []
        current_start = None
        change_points = set()  # 存储所有启停状态变化点
        
        # 记录第一个状态变化点
        if len(df_switch) > 0:
            change_points.add(df_switch.iloc[0]['启停时间'])
        
        for i in range(1, len(df_switch)):
            prev_row = df_switch.iloc[i-1]
            current_row = df_switch.iloc[i]
            
            prev_status = prev_row['启停标识']
            current_status = current_row['启停标识']
            current_time = current_row['启停时间']
            
            # 如果状态发生变化，记录变化点
            if prev_status != current_status:
                change_points.add(current_time)
            
            # 构建停机时间段
            if current_status == 0 and current_start is None:
                current_start = current_time
            elif current_status == 1 and current_start is not None:
                downtime_intervals.append((current_start, current_time))
                current_start = None
        
        # 处理最后一个未结束的停机时间段
        if current_start is not None:
            end_date = END_DATE
            downtime_intervals.append((current_start, end_date))
            logger.debug(f"添加未结束的停机时间段: {current_start} 至 {end_date}")
        
        return downtime_intervals, list(change_points)
    
    except Exception as e:
        print(f"处理启停数据文件时出错: {e}")
        traceback.print_exc()
        return [], []

def process_switch_data():
    """处理启停数据文件并保存结果"""
    # 使用相对路径而不是绝对路径
    input_path = os.path.join("input", INPUT_SWITCH_FILE)
    output_path = os.path.join("output", OUTPUT_SWITCH_FILE)
    
    print(f"输入文件路径: {input_path}")
    print(f"输出文件路径: {output_path}")
    
    # 调试信息
    print(f"当前工作目录: {os.getcwd()}")
    print(f"INPUT_DIR: {repr(INPUT_DIR)}")
    print(f"INPUT_SWITCH_FILE: {repr(INPUT_SWITCH_FILE)}")
    print(f"input_path: {repr(input_path)}")
    
    # 检查INPUT_DIR是否存在以及其中的内容
    if os.path.exists(INPUT_DIR):
        print(f"INPUT_DIR内容: {os.listdir(INPUT_DIR)}")
    else:
        print(f"INPUT_DIR不存在: {INPUT_DIR}")
        
        # 尝试使用相对路径
        relative_input_dir = "input"
        if os.path.exists(relative_input_dir):
            print(f"相对路径input目录存在，内容: {os.listdir(relative_input_dir)}")
            # 使用相对路径
            input_path = os.path.join(relative_input_dir, INPUT_SWITCH_FILE)
            print(f"使用相对路径: {input_path}")
    
    print(f"文件是否存在: {os.path.exists(input_path)}")
    
    # 确保输入文件存在
    if not os.path.exists(input_path):
        print(f"错误：输入文件不存在 - {input_path}")
        print("请确保文件路径正确")
        return None, None
    
    try:
        # 读取Excel文件
        logger.info("正在读取Excel文件...")
        df = pd.read_excel(input_path, engine='openpyxl')
        logger.info(f"成功读取 {len(df)} 条数据记录")
        
        # 确保有足够的列
        if len(df.columns) < 4:
            return None, None
            
        # 保存原始列名
        original_columns = list(df.columns)
        
        # 确保时间列是datetime类型
        time_column = df.columns[2]  # 假设第3列是启停时间
        status_column = df.columns[3]  # 第4列是启停标识
        
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            df[time_column] = pd.to_datetime(df[time_column])
        
        # 处理数据
        for i in range(1, len(df)):
            # 获取前一行和当前行的状态
            prev_status = df.iloc[i-1, 3]  # 第4列是启停标识
            current_status = df.iloc[i, 3]
            
            # 仅当状态变化时才调整时间
            if prev_status != current_status:
                original_time = df.iloc[i, 2]  # 第3列是启停时间
                adjusted_time = adjust_time(
                    original_time, 
                    prev_status,
                    current_status
                )
                # 更新启停时间
                df.iat[i, 2] = adjusted_time
                
        # 恢复原始列名
        df.columns = original_columns
        
        # === 新增代码：添加下个月月初0点的记录 ===
        if len(df) > 0:
            # 获取最后一条记录
            last_row = df.iloc[-1].copy()
            
            # 计算下个月月初0点时间
            last_date = last_row[time_column]
            year = last_date.year
            month = last_date.month + 1
            if month > 12:
                month = 1
                year += 1
            next_month_start = datetime(year, month, 1, 0, 0, 0)
            
            # 更新时间为下个月月初0点
            last_row[time_column] = next_month_start
            
            # 将新记录添加到DataFrame末尾
            df = pd.concat([df, pd.DataFrame([last_row])], ignore_index=True)
        
        # === 新增代码：删除重复状态记录（7月1日0时除外） ===
        # 获取最后一条记录的索引（7月1日0时）
        last_record_index = len(df) - 1
        # 存储要删除的索引列表
        indices_to_drop = []
        
        # 从第一条记录遍历到倒数第二条记录
        for i in range(1, len(df)):
            # 跳过最后一条记录（7月1日0时）
            if i == last_record_index:
                continue
                
            # 比较当前行与前一行的状态
            prev_status = df.iloc[i-1, 3]  # 第4列是启停标识
            current_status = df.iloc[i, 3]
            
            if current_status == prev_status:
                indices_to_drop.append(i)
        
        # 执行删除操作
        df = df.drop(indices_to_drop).reset_index(drop=True)
        
        # 保存处理后的数据
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        
        # 提取停机时间段和启停状态变化点
        downtime_intervals, change_points = extract_downtime_intervals_and_changepoints(output_path)
        return downtime_intervals, change_points
        
    except Exception as e:
        
        return None, None