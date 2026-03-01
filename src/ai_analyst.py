import os
import json
import glob
import re
from google import genai
import config  

# 初始化最新版 Client
client = genai.Client(api_key=config.GEMINI_API_KEY)

def get_ai_insight(metrics_data):
    prompt = f"""
    作为宏观经济专家，请分析以下数据：{json.dumps(metrics_data, ensure_ascii=False)}
    任务：为 PMI, CPI, PPI 分别生成一段 120 字以内的深度解读。
    必须返回如下格式的有效 JSON 字典：
    {{
      "pmi": "分析...",
      "cpi": "分析...",
      "ppi": "分析..."
    }}
    注意：只返回 JSON，不要任何 Markdown 标签或解释文字。
    """
    
    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        # 1. 拿到原始文本
        raw_text = response.text.strip()
        
        # 2. 【核心加固】使用正则提取第一个 { 到最后一个 } 之间的内容
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            print(f"❌ [解析失败] 没在回复中找到 JSON 结构。原始输出: {raw_text[:50]}...")
            return None
            
    except Exception as e:
        print(f"❌ [AI 调用异常] {e}")
        return None

def process_latest_data():
   # 1. 获取当前脚本 src/ai_analyst.py 的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 定位到父级目录（项目根目录），再进入 data 文件夹
    data_dir = os.path.abspath(os.path.join(current_dir, "..", "data"))
    
    # 3. 构造完整的 glob 模式
    data_pattern = os.path.join(data_dir, "*.json")
    
    print(f"🔍 [查找] 正在路径搜索数据: {data_pattern}")
    
    list_of_files = glob.glob(data_pattern)
    
    if not list_of_files:
        print(f"❌ [错误] 没找到数据文件，请检查目录: {data_dir}")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 只要有一个指标缺 AI 分析，就触发更新
    needs_update = any("ai_insight" not in item for item in data['metrics'].values() if item.get("status") == "success")
    
    if needs_update:
        # 获取 AI 返回的字典： {"pmi": "...", "cpi": "...", "ppi": "..."}
        analysis_dict = get_ai_insight(data['metrics'])
        
        if analysis_dict and isinstance(analysis_dict, dict):
            for key in data['metrics']:
                # 精准匹配：只有当 AI 返回的 key 在我们的数据中存在时才写入
                if key in analysis_dict:
                    data['metrics'][key]['ai_insight'] = analysis_dict[key]
                    print(f"✅ 已匹配指标: {key}")
            
            # 统一写回磁盘
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"🚀 [成功] AI 精准分析已集成至: {os.path.basename(latest_file)}")
        else:
            print("⚠️ [警告] AI 未返回有效字典，跳过本次更新。")
    else:
        print("📦 [状态] 所有指标均已有 AI 分析，无需重复调用。")

if __name__ == "__main__":
    process_latest_data()