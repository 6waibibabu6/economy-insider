import os
import json
import glob
import data_fetcher
import ai_analyst
import page_builder
import github_pusher

def start_pipeline():
    # 获取根目录
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(ROOT_DIR)
    
    print("--- 🔬 开始执行验证流程 ---")
    
    # 步骤 1: 抓取原始数据
    raw_data = data_fetcher.get_today_data()
    print(f"DEBUG [阶段1]: 原始数据抓取完成。是否有分析字段: {'ai_insight' in raw_data['metrics']['pmi']}")

    # 步骤 2: 执行 AI 分析 (此时它会把结果写进硬盘里的 JSON)
    ai_analyst.process_latest_data()
    print("DEBUG [阶段2]: AI 分析任务已结束。")

    # 步骤 3: 【关键重写】强制从硬盘重新加载！
    # 这一步是为了解决内存里 raw_data 还是旧数据的问题
    latest_json = max(glob.glob(os.path.join("data", "*.json")), key=os.path.getctime)
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        verified_data = json.load(f)
    
    has_ai = "ai_insight" in verified_data['metrics']['pmi']
    print(f"DEBUG [阶段3]: 重新加载磁盘文件: {latest_json}")
    print(f"DEBUG [阶段3]: 验证数据中是否有 AI 分析内容: {has_ai}")

    if has_ai:
        print("✅ [验证通过] 数据已同步，开始渲染 HTML...")
        # 必须传入这个从磁盘重新读取的 verified_data
        page_builder.build_page(verified_data)
        
        # 步骤 4: 推送
        github_pusher.push_to_github()
    else:
        print("❌ [验证失败] 磁盘文件仍未包含 AI 分析，请检查 ai_analyst.py 的保存逻辑。")

if __name__ == "__main__":
    start_pipeline()