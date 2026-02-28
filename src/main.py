import os
import sys

# 自动将 src 目录加入 Python 搜索路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import data_fetcher
import ai_analyst
import page_builder
import github_pusher

def start_pipeline():
    print("=== 🛠️  Economy Insider Pipeline 启动 ===")
    
    # 1. 抓取 (fetcher 内部也建议用同样的 abspath 逻辑)
    data_fetcher.get_today_data()
    
    # 2. AI 解析 (精准分发到 JSON)
    ai_analyst.process_latest_data()
    
    # 3. 渲染 (重新读取最新 JSON 并生成 index.html)
    # 这里直接调用 page_builder 的内部读取逻辑即可，因为它已经加固了
    # 或者手动传入数据以确保一致性
    page_builder.main_run() #  page_builder 里封装一个统一运行入口,充分解耦
    
    # 4. 推送
    github_pusher.push_to_github()

if __name__ == "__main__":
    start_pipeline()