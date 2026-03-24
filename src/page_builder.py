import os
import json
import glob
import datetime

# 基础路径定义 (保持原样)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(CURRENT_DIR, "data")
TEMPLATE_DIR = os.path.join(CURRENT_DIR, "templates")

def load_template(name):
    # (保持原样)
    path = os.path.join(TEMPLATE_DIR, f"{name}.html")
    if not os.path.exists(path):
        print(f"❌ [错误] 找不到模板文件: {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def process_ai_insight(raw_insight):
    """清洗 AI 文本逻辑，适配新的浅色分析卡"""
    # 将 ** 替换为 <b>，用于简单清洗
    processed = raw_insight.replace("**", "<b>")
    # 进阶替换：将 <b> 替换为更深的蓝色强调用色 text-blue-700
    while "<b>" in processed:
        processed = processed.replace("<b>", "<strong class='text-blue-700'>", 1).replace("<b>", "</strong>", 1)
    return processed.replace("\n\n", "<br><br>").replace("\n", "<br>")

def generate_card_html(key, item):
    
    # (保持原样，会自动加载新的 card_template.html)
    card_tpl = load_template("card_template")
    
    val = float(item.get("mfg" if key == "pmi" else "value", 0.0))
    yoy = float(item.get("mfg_yoy" if key == "pmi" else "yoy", 0.0))
    
    mappings = {
        "{{KEY}}": key,
        "{{NAME}}": item.get("name", "未知指标"),
        "{{MONTH}}": item.get("month", "N/A"),
        "{{VALUE}}": f"{val:.1f}",
        "{{COLOR_CLASS}}": "text-emerald-500" if yoy >= 0 else "text-rose-500",
        "{{ICON_NAME}}": "trending-up" if yoy >= 0 else "trending-down",
        "{{YOY_DISPLAY}}": f"{yoy:+.1f}%" if yoy != 0 else "--",
        "{{AI_INSIGHT}}": process_ai_insight(item.get("ai_insight", "分析生成中..."))
    }
    
    for k, v in mappings.items():
        card_tpl = card_tpl.replace(k, v)
    return card_tpl

def build_page(json_data):
    #组装最终页面并注入动态图表脚本
    main_tpl = load_template("main_template")
    
    # 1. 加载历史数据用于绘图 (确保路径正确)
    history_path = os.path.join(DATA_DIR, "history.json")
    history_data = {}
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            try:
                history_data = json.load(f)
            except:
                history_data = {}

    # 2. 生成各指标卡片的 HTML
    metrics = json_data.get("metrics", {})
    all_cards = "".join([generate_card_html(k, v) for k, v in metrics.items() if v.get("status") == "success"])
    
    # 3. 【核心实现】生成 Chart.js 初始化脚本
    chart_scripts = ""
    for key in metrics.keys():
        # 如果该指标有历史记录，则生成对应的 JS
        records = history_data.get(key, [])
        if not records:
            continue
            
        # 提取月份作为 X 轴标签，数值作为 Y 轴数据
        labels = [r['month'] for r in records]
        values = [r['value'] for r in records]
        
        # 针对不同指标微调颜色（比如 PMI 50以上蓝色，CPI/PPI 动态色）
        # 这里统一用你喜欢的蓝色 #3b82f6
        chart_scripts += f"""
        // --- {key} Chart ---
        const ctx_{key} = document.getElementById('chart-{key}');
        if (ctx_{key}) {{
            new Chart(ctx_{key}, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)}, 
                    datasets: [{{
                        data: {json.dumps(values)},
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.05)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: '#3b82f6',
                        tension: 0.4,
                        fill: true,
                        spanGaps: false // 关键：数据缺失时不强行连线，表现更专业
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleFont: {{ size: 10 }},
                            bodyFont: {{ size: 12 }}
                        }}
                    }},
                    scales: {{
                        x: {{ display: false }}, // 隐藏坐标轴保持简约
                        y: {{ 
                            display: false,
                            beginAtZero: false,
                            grace: '5%' // 给顶部留一点空隙防止线被切断
                        }}
                    }},
                    interaction: {{
                        intersect: false,
                        mode: 'index',
                    }}
                }}
            }});
        }}
        """

    # 4. 填充并写出文件
    final_html = main_tpl.replace("{{UPDATE_TIME}}", json_data.get("update_time", "Unknown"))
    final_html = final_html.replace("{{ALL_CARDS_HTML}}", all_cards)
    final_html = final_html.replace("{{CHART_SCRIPTS}}", chart_scripts)

    output_path = os.path.join(ROOT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"✨ [渲染完成] 带有动态趋势图的页面已生成。")

# SEO 资产生成 (保持原样)
def generate_seo_assets(output_dir=ROOT_DIR):
    base_url = "https://data.ylh.top/"
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base_url}</loc><lastmod>{now}</lastmod><priority>1.0</priority></url></urlset>')
    
    robots_path = os.path.join(output_dir, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {base_url}sitemap.xml")

def main_run():
    # (保持原样)
    data_dir = os.path.join(CURRENT_DIR, "data")
    list_of_files = glob.glob(os.path.join(data_dir, "20*.json"))
    if not list_of_files: 
       print("❌ 未发现日期命名的 JSON 文件")
       return
    
    latest_file = max(list_of_files, key=os.path.getmtime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    build_page(data)
    generate_seo_assets()

if __name__ == "__main__":
    main_run()