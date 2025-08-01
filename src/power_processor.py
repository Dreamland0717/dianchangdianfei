"""
电量数据处理模块
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import traceback
from config import (
    INPUT_DIR, OUTPUT_DIR, INPUT_POWER_FILE, TARGET_METERS, 
    START_DATE, END_DATE, ENERGY_COLS
)

def process_power_data():
    """读取并预处理电量数据"""
    # 使用相对路径而不是绝对路径
    file_path = os.path.join("input", INPUT_POWER_FILE)
    output_dir = "output"

    print(f"正在读取文件: {file_path}")
    try:
        # 使用dtype参数确保资产编号正确读取为字符串
        df = pd.read_excel(file_path, dtype={'电能表资产编号': str})
        print(f"原始数据包含 {len(df)} 条记录")
        
        # 清理资产编号（去除空格等）
        df['电能表资产编号'] = df['电能表资产编号'].str.strip()
        
        # 日期转换（使用errors='coerce'处理可能的格式问题）
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        
        # 筛选指定日期范围
        date_mask = (df['日期'] >= START_DATE) & (df['日期'] <= END_DATE)
        
        # 筛选指定电能表
        meter_mask = df['电能表资产编号'].isin(TARGET_METERS)
        df = df[date_mask & meter_mask]
        
        print(f"筛选后数据包含 {len(df)} 条记录")
        print(f"涉及电能表: {df['电能表资产编号'].unique().tolist()}")
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        raise

    # 2. 生成完整时间序列
    full_times = pd.date_range(
        start=START_DATE,
        end=END_DATE,
        freq='15min'
    )
    print(f"完整时间序列包含 {len(full_times)} 个时间点")

    # 3. 处理每个电能表
    for meter in TARGET_METERS:
        print(f"\n{'='*50}")
        print(f"处理电能表: {meter}")
        
        # 筛选当前电能表数据
        meter_df = df[df['电能表资产编号'] == meter].copy()
        
        if meter_df.empty:
            print(f"警告: 没有找到电能表 {meter} 的数据")
            # 创建空结果文件
            empty_df = pd.DataFrame(columns=['时间区间'] + [f'{col}_增量' for col in ENERGY_COLS])
            output_file = os.path.join(output_dir, f"96点电量增量_{meter}.xlsx")
            empty_df.to_excel(output_file, index=False)
            print(f"已创建空结果文件: {output_file}")
            continue
            
        print(f"找到 {len(meter_df)} 条原始记录")
        
        # 创建完整时间序列的DataFrame
        full_df = pd.DataFrame({'日期': full_times})
        merged_df = pd.merge(full_df, meter_df, on='日期', how='left')
        
        # 检查缺失数据
        missing = merged_df[merged_df['电能表资产编号'].isna()]
        missing_count = len(missing)
        
        if missing_count > 0:
            print(f"发现 {missing_count} 个缺失时间点")
            missing_file = os.path.join(output_dir, f"数据缺失时间点_{meter}.xlsx")
            missing[['日期']].to_excel(missing_file, index=False)
            print(f"已保存缺失时间点到: {missing_file}")
        
        # 关键改进：使用合格版本的填充方法
        # 获取所有列名（除了日期）
        all_columns = merged_df.columns.tolist()
        data_columns = [col for col in all_columns if col != '日期']
        
        # 向前填充所有列
        for col in data_columns:
            # 向前填充
            merged_df[col] = merged_df[col].fillna(method='ffill')
            
            # 对于第一个时间点可能没有前一时刻数据的情况
            if merged_df[col].isna().any():
                # 获取该列的第一个非空值（如果有）
                if not merged_df[col].dropna().empty:
                    first_valid = merged_df[col].dropna().iloc[0]
                    merged_df[col] = merged_df[col].fillna(first_valid)
        
        # 5. 计算电量增量
        merged_df = merged_df.sort_values('日期')
        for col in ENERGY_COLS:
            # 确保列存在
            if col in merged_df.columns:
                # 计算差值 = 后一时间点 - 当前时间点
                merged_df[f'{col}_增量'] = merged_df[col].shift(-1) - merged_df[col]
            else:
                print(f"警告: 列 {col} 不存在，跳过计算")
        
        # 6. 生成时间区间格式（使用合格版本的格式）
        time_intervals = []
        times = merged_df['日期'].dt.strftime('%Y-%m-%d %H:%M:%S')
        for i in range(len(merged_df)-1):
            start_time = times.iloc[i]
            end_time = times.iloc[i+1].split()[1]  # 只取时间部分
            time_intervals.append(f"{start_time}-{end_time}")
        
        # 构建结果DataFrame
        result_df = pd.DataFrame({
            '时间区间': time_intervals
        })
        for col in ENERGY_COLS:
            col_name = f'{col}_增量'
            if col_name in merged_df.columns:
                # 对增量列进行四舍五入，保留4位小数
                result_df[col + '_增量'] = merged_df[col_name].values[:len(time_intervals)].round(4)
        
        # 7. 保存结果
        output_file = os.path.join(output_dir, f"96点电量增量{meter}.xlsx")
        result_df.to_excel(output_file, index=False)
        
        # 检查首条记录
        if not result_df.empty:
            first_record = result_df.iloc[0]
            print(f"已生成电量增量文件: {output_file}")
          
            
            # 尝试获取正向和反向增量值
            forward_col = '正向有功总(kWh)_增量'
            reverse_col = '反向有功总(kWh)_增量'
            
            forward_val = first_record.get(forward_col, float('nan'))
            reverse_val = first_record.get(reverse_col, float('nan'))
            
            print(f"正向增量: {forward_val:.4f} | 反向增量: {reverse_val:.4f}")
        else:
            print(f"警告: 结果为空，无法生成首条记录")

    print("\n所有电能表处理完成！")