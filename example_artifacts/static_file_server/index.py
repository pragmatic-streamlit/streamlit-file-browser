import os
import random
from pathlib import Path

# 设置根目录路径
root_dir = "./root"

suffix = ['csv', 'txt']

Path(root_dir).mkdir(parents=True, exist_ok=True)

# 定义递归生成目录的函数
def generate_directories(parent_dir, level, num_dirs, num_files):
    if level == 0:
        return
    else:
        for i in range(num_files):
            (Path(parent_dir) / f"file_{i}.{random.choice(suffix)}").write_text("Hello World!")
        
        for i in range(num_dirs): 
            Path(parent_dir + f"/dir_{i}_{level}").mkdir(parents=True, exist_ok=True)
            generate_directories(parent_dir + f"/dir_{i}_{level}", level - 1, num_dirs, num_files)
# 调用生成目录函数
generate_directories(root_dir, 5, 5, 5)
print("目录生成完成。")