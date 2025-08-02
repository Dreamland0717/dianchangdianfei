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

if __name__ == "__main__":
    main()