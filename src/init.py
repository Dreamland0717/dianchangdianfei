"""
统调电厂用电量计算程序初始化模块
用于清空input文件夹下文件并清除配置参数
"""

import os
import shutil
import logging

# 配置日志
# 定义input目录路径
INPUT_DIR = "input"

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_input_folder():
    """清空input文件夹下的所有文件"""
    logging.info(f"正在清空input文件夹，路径: {INPUT_DIR}")
    
    if os.path.exists(INPUT_DIR):
        try:
            # 获取input目录下的所有文件和文件夹
            items = os.listdir(INPUT_DIR)
            logging.info(f"找到 {len(items)} 个文件/文件夹需要删除: {items}")
            
            deleted_count = 0
            for item in items:
                file_path = os.path.join(INPUT_DIR, item)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        logging.info(f"已删除文件: {file_path}")
                        deleted_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        logging.info(f"已删除文件夹: {file_path}")
                        deleted_count += 1
                except Exception as e:
                    logging.error(f"删除 {file_path} 时出错: {e}")
            
            logging.info(f"已清空input文件夹，共删除 {deleted_count} 个项目")
            print(f"已清空input文件夹，共删除 {deleted_count} 个项目")
        except Exception as e:
            logging.error(f"清空input文件夹时出错: {e}")
            print(f"清空input文件夹时出错: {e}")
    else:
        logging.warning("input文件夹不存在")
        print("input文件夹不存在")

def clear_meter_config():
    """清除电能表配置参数"""
    config_file_path = os.path.join(INPUT_DIR, "meter_config.json")
    logging.info(f"正在尝试清除电能表配置文件: {config_file_path}")
    
    if os.path.exists(config_file_path):
        try:
            os.remove(config_file_path)
            logging.info("已清除电能表配置参数")
            print("已清除电能表配置参数")
        except Exception as e:
            logging.error(f"清除电能表配置参数时出错: {e}")
            print(f"清除电能表配置参数时出错: {e}")
    else:
        logging.warning("配置文件不存在，无需清除")
        print("配置文件不存在，无需清除")

def init_project():
    """初始化项目"""
    print("开始初始化统调电厂用电量计算程序...")
    print("=" * 50)
    
    # 清空input文件夹
    print("1. 清空input文件夹")
    clear_input_folder()
    
    # 清除配置参数
    print("\n2. 清除配置参数")
    clear_meter_config()
    
    print("\n" + "=" * 50)
    print("初始化完成！")
    print("请将新的输入文件放入input文件夹，然后重新运行主程序进行参数配置。")

if __name__ == "__main__":
    init_project()