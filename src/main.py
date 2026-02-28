import os
import sys
import json
import glob

# 定位项目根目录 (src 的上一级)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

# 导入同目录下的模块
import data_fetcher
import ai_analyst
import page_builder
import github_pusher

def start_pipeline():
    print("=== 🏁 Economy Insider 模块化流水线启动 ===")
    
    # 切换当前工作目录到根目录，确保后续所有模块的文件操作（data/, index.html）路径一致
    os.chdir(ROOT_DIR)
    print(f"📍 当前工作空间: {ROOT_DIR}")

    # 1. 抓取数据 (内部会写到 ../data，因为 chdir 了，现在直接写 data/ 即可)
    # 注意：如果之前的模块写死了 "../data"，建议统一改为相对 ROOT_DIR 的路径
    raw_data = data_fetcher.get_today_data()
    if not raw_data:
        print("❌ 数据抓取失败。")
        return

    # 2. AI 分析
    ai_analyst.process_latest_data()
    
    # 3. 渲染页面
    # 重新获取最新的 JSON
    data_files = glob.glob(os.path.join("data", "*.json"))
    if not data_files:
        print("❌ 未发现可渲染的数据文件。")
        return
        
    latest_file = max(data_files, key=os.path.getctime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)
    
    page_builder.build_page(final_data)

    # 4. GitHub 推送
    github_pusher.push_to_github()

    print("=== ✨ 任务圆满完成！ ===")

if __name__ == "__main__":
    start_pipeline()