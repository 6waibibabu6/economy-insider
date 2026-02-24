import base64
import datetime
import requests
import akshare as ak
from google import genai
import config  # 必须确保 config.py 在同级目录

def get_macro_data():
    """抓取核心指标：CPI, PPI, PMI"""
    try:
        # 制造业PMI
        df_pmi = ak.macro_china_pmi_pmi()
        pmi_val = df_pmi['采购经理指数'].iloc[-1]
        
        # CPI同比
        df_cpi = ak.macro_china_cpi()
        cpi_val = df_cpi['同比'].iloc[-1]
        
        # PPI同比
        df_ppi = ak.macro_china_ppi()
        ppi_val = df_ppi['同比'].iloc[-1]

        return f"PMI: {pmi_val}, CPI同比: {cpi_val}%, PPI同比: {ppi_val}%"
    except Exception as e:
        return f"数据抓取失败: {e}"

def analyze_as_economist(data):
    """使用最新 SDK 调用 Gemini"""
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    prompt = f"""
    你是一位资深宏观经济学家。请分析以下数据：
    {data}
    
    要求：
    1. 分析景气度、库存周期及成本传导。
    2. 使用专业术语（如边际、预期、剪刀差）。
    3. 输出 HTML 格式（包含 <h3> 和 <strong>）。
    """
    
    # 使用你要求的 Client 调用方式
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt
    )
    return response.text

def push_to_github(analysis_html):
    """GitHub REST API 提交逻辑"""
    # 构造完整网页内容
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <title>YLH17 经济内参</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; background: #f4f7f9; }}
            .card {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-top: 5px solid #0366d6; }}
            h3 {{ color: #0366d6; }}
            strong {{ color: #d73a49; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>ylh17.top 经济内参</h1>
            <p style="color: #666;">更新于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <hr>
            {analysis_html}
        </div>
    </body>
    </html>
    """
    
    url = f"https://api.github.com/repos/{config.REPO_OWNER}/{config.REPO_NAME}/contents/{config.FILE_PATH}"
    headers = {"Authorization": f"token {config.GITHUB_TOKEN}"}
    
    # 尝试获取旧文件 SHA 用于更新
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None

    content_b64 = base64.b64encode(full_html.encode('utf-8')).decode('utf-8')
    payload = {
        "message": f"📊 Monthly Update {datetime.date.today()}",
        "content": content_b64,
        "branch": "main"
    }
    if sha: payload["sha"] = sha

    put_res = requests.put(url, json=payload, headers=headers)
    return put_res.json()

if __name__ == "__main__":
    print("Step 1: 抓取数据...")
    data = get_macro_data()
    print("Step 2: AI 分析中...")
    analysis = analyze_as_economist(data)
    print("Step 3: 推送至 ylh17.top...")
    result = push_to_github(analysis)
    
    if "commit" in result:
        print("✅ 成功！请刷新 data.ylh17.top 查看。")
    else:
        print(f"❌ 失败: {result}")