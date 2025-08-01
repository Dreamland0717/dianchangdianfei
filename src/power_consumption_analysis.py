import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import traceback
import re


# ==================== 配置参数 ====================
# 工作目录
WORK_DIR = r"E:\python\pythonchengxu\萧山"
os.chdir(WORK_DIR)

# 输入文件路径
INPUT_SWITCH_FILE = "机组启停数据查询（萧山）.xlsx"
INPUT_POWER_FILE = "电厂96点示值查询（萧山）.xlsx"

# 输出文件路径
OUTPUT_SWITCH_FILE = "处理后的机组启停数据（萧山）.xlsx"

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

# ==================== 工具函数 ====================
def get_asset_id_from_filename(filename):
    """从文件名中提取电能表资产编号"""
    # 尝试匹配文件名中的数字部分
    match = re.search(r'(\d{12,14})', filename)
    if match:
        return match.group(1)
    return None


# ==================== 第一部分：处理启停数据 ====================
def adjust_time(original_time, prev_status, current_status):
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
        return end_time
    
    elif prev_status == 1 and current_status == 0:
        # 从启动到停止：取当前15分钟时段的开始时间
        return base_time
    
    # 状态不变则返回原始时间
    return dt


def extract_downtime_intervals_and_changepoints(switch_file):
    """提取停机时间段和启停状态变化点"""
    try:
        # 读取Excel文件，直接解析日期时间列
        df_switch = pd.read_excel(switch_file, parse_dates=['启停时间'])
        print(f"成功读取启停数据文件: {switch_file}")
        print(f"数据行数: {len(df_switch)}")
        
        # 检查必要的列是否存在
        required_columns = ['电厂名称', '数据日期', '启停时间', '启停标识']
        for col in required_columns:
            if col not in df_switch.columns:
                print(f"错误: 文件 {switch_file} 缺少必要的列 '{col}'")
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
            print(f"添加未结束的停机时间段: {current_start} 至 {end_date}")
        
        print(f"共识别出 {len(downtime_intervals)} 个停机时间段")
        print(f"共识别出 {len(change_points)} 个启停状态变化点")
        return downtime_intervals, list(change_points)
    
    except Exception as e:
        print(f"处理启停数据文件时出错: {e}")
        traceback.print_exc()
        return [], []


def process_switch_data():
    """处理启停数据文件并保存结果"""
    input_path = os.path.join(WORK_DIR, INPUT_SWITCH_FILE)
    output_path = os.path.join(WORK_DIR, OUTPUT_SWITCH_FILE)
    
    print(f"输入文件路径: {input_path}")
    print(f"输出文件路径: {output_path}")
    
    # 确保输入文件存在
    if not os.path.exists(input_path):
        print(f"错误：输入文件不存在 - {input_path}")
        print("请确保文件路径正确")
        return None, None
    
    try:
        # 读取Excel文件
        print("正在读取Excel文件...")
        df = pd.read_excel(input_path, engine='openpyxl')
        print(f"成功读取 {len(df)} 条数据记录")
        
        # 确保有足够的列
        if len(df.columns) < 4:
            print("错误：文件列数不足，需要至少4列数据")
            return None, None
            
        # 保存原始列名
        original_columns = list(df.columns)
        
        # 确保时间列是datetime类型
        time_column = df.columns[2]  # 假设第3列是启停时间
        status_column = df.columns[3]  # 第4列是启停标识
        
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            print("正在转换时间列格式...")
            df[time_column] = pd.to_datetime(df[time_column])
        
        # 处理数据
        print("开始处理数据...")
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
                print(f"调整记录 {i+1}: {original_time} → {adjusted_time} (状态 {prev_status}→{current_status})")
        
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
            print(f"添加下个月月初记录: 时间={next_month_start}, 状态={last_row[status_column]}")
        
        # === 新增代码：删除重复状态记录（7月1日0时除外） ===
        print("开始删除重复状态记录...")
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
                print(f"标记删除记录 {i+1}：状态相同 ({current_status}→{prev_status})")
        
        # 执行删除操作
        df = df.drop(indices_to_drop).reset_index(drop=True)
        print(f"已删除 {len(indices_to_drop)} 条重复状态记录")
        
        # 保存处理后的数据
        print("正在保存结果...")
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        print(f"处理完成！结果已保存至: {output_path}")
        print(f"共处理 {len(df)} 条记录 (包含新增的下个月记录)")
        
        # 提取停机时间段和启停状态变化点
        downtime_intervals, change_points = extract_downtime_intervals_and_changepoints(output_path)
        return downtime_intervals, change_points
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
        traceback.print_exc()
        print("请确保文件格式正确且安装了必要的库")
        return None, None


# ==================== 第二部分：处理电量数据 ====================
def process_power_data():
    """读取并预处理电量数据"""
    file_path = os.path.join(WORK_DIR, INPUT_POWER_FILE)
    output_dir = WORK_DIR

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


# ==================== 第三部分：计算停机耗电量 ====================
def calculate_net_value(forward, reverse, asset_id, is_change_point_interval):
    """根据资产编号计算净电量增量"""
    # 规则1: 原规则
    rule1_ids = ['08000100084198']
    # 规则2: 反向减正向
    rule2_ids = ['00010008419844']
    # 规则3: 只取正向
    rule3_ids = ['08450124465285', '08450124465286', '08450124465288', '08450124465291']
    
    if asset_id in rule1_ids:
        net_value = forward - reverse
        rule = "正向 - 反向"
    elif asset_id in rule2_ids:
        net_value = reverse - forward
        rule = "反向 - 正向"
    elif asset_id in rule3_ids:
        net_value = forward
        rule = "只取正向"
    else:
        # 默认使用原规则
        net_value = forward 
        rule = "默认: 正向 - 反向"
    
    original_net_value = net_value
    
    # 应用变化点区间负值置零规则
    if is_change_point_interval and net_value < 0:
        net_value = 0.0
        adjusted = True
    else:
        adjusted = False
        net_value = round(net_value, 4)
    
    return net_value, original_net_value, rule, adjusted


def calculate_downtime_consumption(power_file, downtime_intervals, change_points):
    """计算停机时间段内的净电量增量"""
    try:
        print(f"\n处理电量文件: {power_file}")
        df_power = pd.read_excel(power_file)
        print(f"成功读取电量文件，行数: {len(df_power)}")
        
        # 检查必要的列是否存在
        required_columns = ['时间区间', '正向有功总(kWh)_增量', '反向有功总(kWh)_增量']
        for col in required_columns:
            if col not in df_power.columns:
                print(f"错误: 文件 {power_file} 缺少必要的列 '{col}'")
                return 0.0, None, None, None
        
        # 从文件名中提取资产编号
        asset_id = get_asset_id_from_filename(power_file)
        print(f"识别到电能表资产编号: {asset_id}")
        
        total_consumption = 0.0
        matched_count = 0
        unmatched_count = 0
        boundary_adjustments = 0  # 记录边界调整次数
        
        # 创建详细结果列表
        detailed_results = []
        boundary_adjustments_list = []  # 记录置零时间段的信息
        interval_results = {}
        
        # 为每个停机时间段初始化结果
        for i, (start, end) in enumerate(downtime_intervals):
            interval_key = f"{start.strftime('%Y-%m-%d %H:%M:%S')} 至 {end.strftime('%Y-%m-%d %H:%M:%S')}"
            interval_results[interval_key] = {
                'interval_id': i+1,
                'start_time': start,
                'end_time': end,
                'total_consumption': 0.0,
                'interval_count': 0
            }
        
        # 处理每个15分钟区间
        for index, row in df_power.iterrows():
            interval_str = str(row['时间区间']).strip()
            
            # 拆分时间区间 - 处理不同的格式
            if ' ' not in interval_str or '-' not in interval_str:
                unmatched_count += 1
                continue
                
            # 提取日期和时间部分
            date_part = interval_str.split(' ')[0]
            time_range = interval_str.split(' ')[1]
            
            # 拆分开始和结束时间
            start_time_str, end_time_str = time_range.split('-', 1)
            
            try:
                # 构建完整的开始时间
                full_start_str = f"{date_part} {start_time_str}"
                interval_start = datetime.strptime(full_start_str, '%Y-%m-%d %H:%M:%S')
                
                # 计算区间结束时间 (15分钟后)
                interval_end = interval_start + timedelta(minutes=15)
            except Exception as e:
                unmatched_count += 1
                continue
            
            # 获取电量增量值
            forward = row['正向有功总(kWh)_增量']
            reverse = row['反向有功总(kWh)_增量']
            
            # 处理空值
            if pd.isna(forward): forward = 0.0
            if pd.isna(reverse): reverse = 0.0
            
            # 检查是否在启停状态变化点所在的区间
            is_change_point_interval = any(
                interval_start <= change_point < interval_end 
                for change_point in change_points
            )
            
            # 根据资产编号计算净电量增量
            net_value, original_net_value, rule_used, adjusted = calculate_net_value(
                forward, reverse, asset_id, is_change_point_interval
            )
            
            # 记录边界调整
            if adjusted:
                boundary_adjustments += 1
                # 记录置零时间段信息
                boundary_adjustments_list.append({
                    '时间区间': interval_str,
                    '区间开始时间': interval_start,
                    '区间结束时间': interval_end,
                    '正向增量(kWh)': forward,
                    '反向增量(kWh)': reverse,
                    '置零前净增量(kWh)': original_net_value,
                    '置零后净增量(kWh)': net_value,
                    '所属文件': os.path.basename(power_file),
                    '资产编号': asset_id,
                    '计算规则': rule_used,
                    '变化点时间': ', '.join([cp.strftime('%Y-%m-%d %H:%M:%S') 
                                  for cp in change_points 
                                  if interval_start <= cp < interval_end])
                })
            
            # 检查是否在停机时间段内
            matched = False
            for start_dt, end_dt in downtime_intervals:
                # 检查整个15分钟区间是否完全在停机时间段内
                if interval_start >= start_dt and interval_end <= end_dt:
                    total_consumption += net_value
                    matched_count += 1
                    matched = True
                    
                    # 记录详细结果
                    interval_key = f"{start_dt.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
                    interval_results[interval_key]['total_consumption'] += net_value
                    interval_results[interval_key]['interval_count'] += 1
                    
                    # 添加到详细结果列表
                    detailed_results.append({
                        '机组文件': os.path.basename(power_file),
                        '资产编号': asset_id,
                        '计算规则': rule_used,
                        '停机时间段': interval_key,
                        '时间区间': interval_str,
                        '区间开始时间': interval_start,
                        '区间结束时间': interval_end,
                        '正向增量(kWh)': forward,
                        '反向增量(kWh)': reverse,
                        '净电量增量(kWh)': net_value,
                        '原始净电量增量(kWh)': original_net_value,
                        '是否变化点区间': '是' if is_change_point_interval else '否',
                        '是否被置零': '是' if adjusted else '否'
                    })
                    
                    break
            
            if not matched:
                unmatched_count += 1
        
        # 创建汇总结果DataFrame
        summary_data = []
        for interval_key, data in interval_results.items():
            if data['interval_count'] > 0:  # 只包含有数据的区间
                summary_data.append({
                    '机组文件': os.path.basename(power_file),
                    '资产编号': asset_id,
                    '停机时间段序号': data['interval_id'],
                    '开始时间': data['start_time'],
                    '结束时间': data['end_time'],
                    '区间数量': data['interval_count'],
                    '总耗电量(kWh)': round(data['total_consumption'], 4)
                })
        
        # 创建DataFrame
        summary_df = pd.DataFrame(summary_data)
        detailed_df = pd.DataFrame(detailed_results)
        boundary_df = pd.DataFrame(boundary_adjustments_list) if boundary_adjustments_list else None
        
        print(f"匹配统计: {matched_count} 个区间匹配, {unmatched_count} 个区间未匹配")
        print(f"边界调整: {boundary_adjustments} 个变化点区间电量被置零")
        print(f"总耗电量: {total_consumption:.4f} kWh")
        return total_consumption, summary_df, detailed_df, boundary_df
    
    except Exception as e:
        print(f"处理电量文件 {power_file} 时出错: {e}")
        traceback.print_exc()
        return 0.0, None, None, None


def calculate_half_hourly_consumption_by_asset(power_files, downtime_intervals):
    """按资产编号统计每个小时的30分钟时间段的正向有功电量（仅计算停电期间）"""
    try:
        print("\n开始按资产编号统计每个小时的30分钟时间段的正向有功电量...")
        
        # 创建48个时间段的标签
        half_hour_labels = []
        for hour in range(24):
            for minute in [0, 30]:
                next_hour = hour
                next_minute = minute + 30
                if next_minute == 60:
                    next_hour = hour + 1
                    next_minute = 0
                half_hour_labels.append(f"{hour:02d}:{minute:02d}-{next_hour:02d}:{next_minute:02d}")
        
        # 为每个资产编号初始化结果字典
        asset_results = {}
        
        # 处理每个电量文件
        for power_file in power_files:
            if not os.path.exists(power_file):
                print(f"警告: 文件 {power_file} 不存在，已跳过")
                continue
                
            print(f"处理文件: {power_file}")
            df_power = pd.read_excel(power_file)
            
            # 从文件名中提取资产编号
            asset_id = get_asset_id_from_filename(power_file)
            if not asset_id:
                print(f"无法从文件名 {power_file} 中提取资产编号，已跳过")
                continue
                
            # 如果资产编号不在结果字典中，则初始化
            if asset_id not in asset_results:
                asset_results[asset_id] = {label: 0.0 for label in half_hour_labels}
            
            # 处理每个15分钟区间
            for index, row in df_power.iterrows():
                interval_str = str(row['时间区间']).strip()
                
                # 解析时间区间
                if ' ' not in interval_str or '-' not in interval_str:
                    continue
                    
                # 提取日期和时间部分
                date_part = interval_str.split(' ')[0]
                time_range = interval_str.split(' ')[1]
                
                # 拆分开始和结束时间
                start_time_str, end_time_str = time_range.split('-', 1)
                
                try:
                    # 构建完整的开始时间
                    full_start_str = f"{date_part} {start_time_str}"
                    interval_start = datetime.strptime(full_start_str, '%Y-%m-%d %H:%M:%S')
                    
                    # 定义统计周期
                    start_date = START_DATE
                    end_date = END_DATE
                    
                    # 检查是否在统计周期内
                    if interval_start < start_date or interval_start >= end_date:
                        continue
                        
                    # 计算区间结束时间 (15分钟后)
                    interval_end = interval_start + timedelta(minutes=15)
                except Exception as e:
                    continue
                
                # 检查是否在停机时间段内
                in_downtime = False
                for downtime_start, downtime_end in downtime_intervals:
                    # 检查整个15分钟区间是否完全在停机时间段内
                    if interval_start >= downtime_start and interval_end <= downtime_end:
                        in_downtime = True
                        break
                
                # 如果不在停机时间段内，则跳过
                if not in_downtime:
                    continue
                
                # 获取正向有功电量
                forward = row['正向有功总(kWh)_增量']
                if pd.isna(forward):
                    forward = 0.0
                
                # 确定该15分钟区间属于哪个30分钟时间段
                hour = interval_start.hour
                minute = interval_start.minute
                if minute < 30:
                    half_hour_label = f"{hour:02d}:00-{hour:02d}:30"
                else:
                    if hour < 23:
                        half_hour_label = f"{hour:02d}:30-{hour+1:02d}:00"
                    else:
                        half_hour_label = f"{hour:02d}:30-24:00"
                
                # 累加到对应的时间段
                asset_results[asset_id][half_hour_label] += forward
        
        # 创建结果DataFrame
        results_data = []
        for asset_id, half_hours_data in asset_results.items():
            for half_hour, consumption in half_hours_data.items():
                results_data.append({
                    '资产编号': asset_id,
                    '时间段': half_hour,
                    '正向有功电量(kWh)': round(consumption, 4)
                })
        
        results_df = pd.DataFrame(results_data)
        return results_df
        
    except Exception as e:
        print(f"按资产编号统计每个小时的30分钟时间段的正向有功电量时出错: {e}")
        traceback.print_exc()
        return None


def calculate_power_consumption(downtime_intervals, change_points):
    """计算停机耗电量主流程"""
    print("="*50)
    print("机组停机耗电量计算程序")
    print(f"工作目录: {WORK_DIR}")
    print("="*50)
    
    # 步骤1: 计算电量文件的停机耗量
    power_files = [
        f"96点电量增量{meter}.xlsx" for meter in TARGET_METERS
    ]
    
    results = {}
    all_summaries = []
    all_detailed = []
    all_boundaries = []  # 收集所有置零记录
    all_consumption = []  # 收集所有机组的耗电量
    
    for file in power_files:
        if not os.path.exists(file):
            print(f"\n警告: 文件 {file} 不存在，已跳过")
            continue
            
        total, summary_df, detailed_df, boundary_df = calculate_downtime_consumption(file, downtime_intervals, change_points)
        results[file] = total
        
        if summary_df is not None and not summary_df.empty:
            all_summaries.append(summary_df)
            all_consumption.append(total)  # 收集每个文件的总耗电量
        
        if detailed_df is not None and not detailed_df.empty:
            all_detailed.append(detailed_df)
        
        # 确保boundary_df不为None且非空才添加
        if boundary_df is not None and not boundary_df.empty:
            all_boundaries.append(boundary_df)
        
        print(f"\n文件 {file} 中所有停机时间段内的净电量增量之和: {total:.4f} kWh")
        print("-"*50)
    
    # 创建汇总文件
    if all_summaries:
        # 合并所有汇总结果
        combined_summary = pd.concat(all_summaries, ignore_index=True)
        
        # 添加机组小计行
        unit_summaries = []
        for file in power_files:
            if file in results:
                # 获取该机组的所有汇总行
                unit_rows = combined_summary[combined_summary['机组文件'] == os.path.basename(file)]
                if not unit_rows.empty:
                    # 计算该机组的总耗电量
                    unit_total = unit_rows['总耗电量(kWh)'].sum()
                    asset_id = get_asset_id_from_filename(file)
                    unit_summaries.append({
                        '机组文件': os.path.basename(file),
                        '资产编号': asset_id,
                        '开始时间': '小计',
                        '结束时间': '',
                        '区间数量': unit_rows['区间数量'].sum(),
                        '总耗电量(kWh)': round(unit_total, 4)
                    })
        
        # 添加总电量行
        grand_total = sum(all_consumption)
        unit_summaries.append({
            '机组文件': '总计',
            '资产编号': '',
            '开始时间': '',
            '结束时间': '',
            '区间数量': combined_summary['区间数量'].sum(),
            '总耗电量(kWh)': round(grand_total, 4)
        })
        
        # 创建小计和总计的DataFrame
        summary_total_df = pd.DataFrame(unit_summaries)
        
        # 合并原始汇总数据和小计/总计数据
        final_summary = pd.concat([combined_summary, summary_total_df], ignore_index=True)
        
        # 保存到Excel文件
        combined_filename = "所有文件停机耗电汇总.xlsx"
        with pd.ExcelWriter(combined_filename) as writer:
            final_summary.to_excel(writer, sheet_name='汇总', index=False)
            
            # 如果有详细数据，也保存到同一个文件的不同sheet
            if all_detailed:
                combined_detailed = pd.concat(all_detailed, ignore_index=True)
                combined_detailed.to_excel(writer, sheet_name='明细', index=False)
                print(f"详细结果已保存到汇总文件的'明细'工作表")
        
        print(f"\n所有文件的汇总结果已保存到: {combined_filename}")
        
    
    # 保存所有置零记录到一个文件
    if all_boundaries:
        combined_boundaries = pd.concat(all_boundaries, ignore_index=True)
        boundaries_filename = "所有文件置零时间段记录.xlsx"
        combined_boundaries.to_excel(boundaries_filename, index=False)
        print(f"\n所有文件的置零时间段记录已保存到: {boundaries_filename}")
        print(f"总计 {len(combined_boundaries)} 条置零记录")
    else:
        print("\n没有置零记录，因此未生成置零记录汇总文件")
    
    # 输出最终结果
    print("\n" + "="*50)
    print("最终计算结果:")
    for file, total in results.items():
        asset_id = get_asset_id_from_filename(file)
        print(f"{file} (资产编号: {asset_id}): {total:.4f} kWh")
    print(f"总耗电量: {grand_total:.4f} kWh")
    print("="*50)
    
    # 添加按资产编号统计每天48个30分钟时间段的正向有功电量功能
    print("\n开始生成按资产编号统计的半小时电量数据...")
    half_hourly_df = calculate_half_hourly_consumption_by_asset(power_files, downtime_intervals)
    
    if half_hourly_df is not None and not half_hourly_df.empty:
        half_hourly_filename = "按资产编号统计半小时电量数据.xlsx"
        half_hourly_df.to_excel(half_hourly_filename, index=False)
        print(f"按资产编号统计的半小时电量数据已保存到: {half_hourly_filename}")
    else:
        print("未能生成按资产编号统计的半小时电量数据")


# ==================== 主程序入口 ====================
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
    calculate_power_consumption(downtime_intervals, change_points)
    
    print("\n" + "=" * 60)
    print("电力消耗分析程序执行完成！")


if __name__ == "__main__":
    main()