#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统调电厂用电量计算程序运行入口
"""

import sys
import os

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 更改当前工作目录为项目根目录
os.chdir(project_root)

# 添加src目录到Python路径的前面，确保优先使用项目中的模块
sys.path.insert(0, os.path.join(project_root, 'src'))

# 确保不会从父目录导入config模块
parent_dir = os.path.dirname(project_root)
if parent_dir in sys.path:
    sys.path.remove(parent_dir)

from main import main
from config import INPUT_DIR, INPUT_POWER_FILE, INPUT_SWITCH_FILE

if __name__ == "__main__":
    # 检查输入文件是否存在
    switch_file = os.path.join(INPUT_DIR, INPUT_SWITCH_FILE)
    power_file = os.path.join(INPUT_DIR, INPUT_POWER_FILE)
    
    if not os.path.exists(switch_file) or not os.path.exists(power_file):
        print("警告：输入文件缺失！")
        print(f"请确保以下文件存在于 {INPUT_DIR} 目录中：")
        if not os.path.exists(switch_file):
            print(f"  - {INPUT_SWITCH_FILE}")
        if not os.path.exists(power_file):
            print(f"  - {INPUT_POWER_FILE}")
        print("\n如果要初始化项目，请运行 init_project.bat 或执行 python init_run.py")
        
    main()