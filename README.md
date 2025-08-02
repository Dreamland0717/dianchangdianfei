# 统调电厂用电量计算程序

该项目用于分析统调电厂机组的电力消耗情况，特别是停机期间的耗电量统计。

## 项目结构

```
dianchangdianfei-1/
├── input/                           # 输入数据文件夹
│   ├── 机组启停数据查询.xlsx
│   └── 电厂96点示值查询.xlsx
├── output/                          # 输出结果文件夹（程序运行后会自动生成）
├── src/                             # 源代码文件夹
│   ├── main.py                     # 主程序入口
│   ├── config.py                   # 配置文件
│   ├── switch_processor.py         # 启停数据处理模块
│   ├── power_processor.py          # 电量数据处理模块
│   ├── consumption_calculator.py   # 耗电量计算模块
│   ├── meter_config.py             # 电能表配置模块
│   ├── init.py                     # 初始化模块
│   └── utils.py                    # 工具模块
├── run.py                          # 项目运行入口
├── init_run.py                     # 初始化程序运行入口
├── init_project.bat                # 初始化批处理脚本
├── init_git.bat                    # Git初始化批处理脚本
├── init_git.sh                     # Git初始化Shell脚本
├── requirements.txt                # 依赖包列表
├── .gitignore                      # Git忽略文件配置
└── README.md                       # 说明文档
```

## 使用方法

1. 确保系统已安装 Python 3.x 环境

2. 安装必要的依赖包：
   ```
   pip install pandas openpyxl
   ```

3. 将输入数据文件放入 `input` 文件夹：
   - 机组启停数据查询.xlsx
   - 电厂96点示值查询.xlsx

4. 首次运行需要配置电能表参数：
   程序会提示为每个电能表选择计算规则和输入变比值

5. 在项目根目录下运行程序：
   ```
   python run.py
   ```

6. 查看输出结果：
   程序运行后会在 `output` 文件夹中生成以下文件：
   - 处理后的机组启停数据.xlsx
   - 96点电量增量[电表编号].xlsx (每个电表一个文件)
   - 所有文件停机耗电汇总.xlsx
   - 按资产编号统计半小时电量数据.xlsx
   - 数据缺失时间点_[电表编号].xlsx (每个电表一个文件，如果存在缺失数据)
   - meter_config.json (电能表配置文件，保存配置参数)

## 初始化程序

项目提供了初始化程序，用于清空输入文件和重置配置：

- 运行 `init_project.bat` 或执行 `python init_run.py`
- 程序将清空 `input` 文件夹并删除配置文件
- 重新运行主程序时会提示重新配置电能表参数

## 模块说明

- `main.py`: 程序主入口，协调各模块执行
- `config.py`: 项目配置文件，包含输入输出文件名、时间范围等配置
- `switch_processor.py`: 处理机组启停数据，生成规范格式的启停时间点
- `power_processor.py`: 处理电量数据，计算每15分钟的电量增量
- `consumption_calculator.py`: 计算停机期间的耗电量
- `meter_config.py`: 管理电能表配置，包括计算规则和变比值
- `init.py`: 初始化模块，用于清空输入文件和重置配置
- `utils.py`: 工具函数模块

## 电能表计算规则

程序支持以下计算规则：
1. 正向 - 反向
2. 反向 - 正向
3. 只取正向
4. 不计算(跳过)

## 注意事项

1. 确保输入文件格式正确，特别是时间格式
2. 程序会自动创建缺失的文件夹
3. 输出文件会覆盖同名的旧文件
4. 为保护隐私，上传到Git时应忽略output目录和敏感数据文件
5. 配置文件 (meter_config.json) 保存在 input 目录中