import pandas as pd
from datetime import datetime, timedelta
import os

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

def process_excel():
    """处理Excel文件并保存结果"""
    # 使用原始字符串表示法解决路径问题
    input_path = r"E:\python\pythonchengxu\萧山\机组启停数据查询（萧山）.xlsx"
    output_path = r"E:\python\pythonchengxu\萧山\处理后的机组启停数据（萧山）.xlsx"
    
    print(f"输入文件路径: {input_path}")
    print(f"输出文件路径: {output_path}")
    
    # 确保输入文件存在
    if not os.path.exists(input_path):
        print(f"错误：输入文件不存在 - {input_path}")
        print("请确保文件路径正确")
        return
    
    try:
        # 读取Excel文件
        print("正在读取Excel文件...")
        df = pd.read_excel(input_path, engine='openpyxl')
        print(f"成功读取 {len(df)} 条数据记录")
        
        # 确保有足够的列
        if len(df.columns) < 4:
            print("错误：文件列数不足，需要至少4列数据")
            return
            
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
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
        print("请确保文件格式正确且安装了必要的库")
        print("需要安装的库: pip install pandas openpyxl")

if __name__ == "__main__":
    # 检查是否安装了必要的库
    try:
        import pandas as pd
        import openpyxl
        process_excel()
    except ImportError as e:
        print(f"缺少必要的库: {e}")
        print("请先安装所需库: pip install pandas openpyxl")