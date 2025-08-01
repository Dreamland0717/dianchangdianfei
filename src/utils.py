"""
工具模块 - 包含通用工具函数
"""

import re
from typing import Optional, List, Dict, Any
import pandas as pd

def get_asset_id_from_filename(filename: str) -> Optional[str]:
    """
    从文件名中提取电能表资产编号
    
    Args:
        filename: 文件名字符串
        
    Returns:
        匹配到的12-14位数字组成的字符串，如果没有匹配则返回None
    """
    # 尝试匹配文件名中的数字部分（优先匹配连续12-14位数字）
    match = re.search(r'(\d{12,14})', filename)
    
    # 如果没有找到长数字，尝试匹配所有数字部分
    if not match:
        numbers = re.findall(r'\d+', filename)
        # 优先返回最长的数字部分
        if numbers:
            return max(numbers, key=len)
    
    if match:
        return match.group(1)
    return None

def read_excel_with_date(file_path: str, date_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    读取Excel文件并正确解析日期列
    
    Args:
        file_path: Excel文件路径
        date_columns: 需要解析为日期的列名列表
        
    Returns:
        解析后的DataFrame
    """
    if date_columns is None:
        date_columns = ['启停时间', '日期']
    
    # 尝试直接解析日期时间列
    try:
        df = pd.read_excel(file_path, parse_dates=date_columns)
        return df
    except Exception as e:
        print(f"Warning: 日期列解析失败，将尝试在读取后转换: {str(e)}")
        # 如果直接解析失败，则先读取再转换
        df = pd.read_excel(file_path)
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception as e:
                    print(f"Warning: 列 '{col}' 转换为日期失败: {str(e)}")
        return df