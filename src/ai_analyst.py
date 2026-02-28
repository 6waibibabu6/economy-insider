import os
import json
import glob
from google import genai
import config  

# 初始化最新版 Client
client = genai.Client(api_key=config.GEMINI_API_KEY)

def get_ai_insight(metrics_data):
    
    # 构造更严谨的 Prompt，要求 AI 给出结构化回复
    prompt = f"""
    作为宏观经济专家，请分析以下数据：{json.dumps(metrics_data, ensure_ascii=False)}
    
    任务：
    1. 针对每一个指标（PMI, CPI, PPI），提供一段 120 字以内的锐利解读。
    2. 必须包含对“同比(yoy)”或“荣枯线(50)”的走势评价。
    3. 风格：去口水话，直击核心矛盾（如：内需疲软、工业复苏、剪刀差等）。
    4. 不要开场白，直接输出内容。
    """
    
    try:
        print(" [Gemini] 正在通过新版 SDK 研判数据...")
        # 新版调用方式
        response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"❌ [AI 异常] 调用失败: {e}")
        return "当前数据解析由于技术原因暂不可用。"

def process_latest_data():
   
    # 向上跳一级找到 data 目录
    data_pattern = os.path.join("..", "data", "*.json")
    list_of_files = glob.glob(data_pattern)
    
    if not list_of_files:
        print("❌ [错误] 没找到数据文件，请先运行 data_fetcher.py")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 检查是否已包含分析，避免重复消耗额度
    has_analysis = any("ai_insight" in item for item in data['metrics'].values())
    
    if not has_analysis:
        # 获取全量分析内容
        analysis_text = get_ai_insight(data['metrics'])
        
        # 将分析内容分发到各个成功抓取的指标中
        # 这里我们先采取简单策略：将整段分析同步给所有卡片，或者你可以让 AI 返回 JSON 后精准分配
        for key in data['metrics']:
            if data['metrics'][key]['status'] == 'success':
                data['metrics'][key]['ai_insight'] = analysis_text
        
        # 持久化回 JSON
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ [集成完毕] AI 分析已存入: {os.path.basename(latest_file)}")
    else:
        print("📦 [状态] 今日数据已有 AI 分析，跳过 API 调用。")

if __name__ == "__main__":
    process_latest_data()