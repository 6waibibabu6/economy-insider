import os
import json
import glob
import datetime

# 基础路径定义
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(CURRENT_DIR, "data")
TEMPLATE_DIR = os.path.join(CURRENT_DIR, "templates")

def load_template(name):
    """加载 HTML 模板"""
    path = os.path.join(TEMPLATE_DIR, f"{name}.html")
    if not os.path.exists(path):
        print(f"❌ [错误] 找不到模板文件: {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def process_ai_insight(raw_insight):
    """清洗 AI 文本逻辑，适配浅色分析卡"""
    # 将 ** 替换为 <b>
    processed = raw_insight.replace("**", "<b>")
    # 进阶替换：将 <b> 替换为更深的蓝色强调用色
    while "<b>" in processed:
        processed = processed.replace("<b>", "<strong class='text-blue-700'>", 1).replace("<b>", "</strong>", 1)
    return processed.replace("\n\n", "<br><br>").replace("\n", "<br>")

def generate_card_html(key, item):
    """生成单个指标卡片的 HTML"""
    card_tpl = load_template("card_template")
    
    # 兼容不同指标的字段名
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
    """组装最终页面并注入动态图表脚本"""
    main_tpl = load_template("main_template")
    
    # 1. 加载历史数据用于绘图
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
    
    # 3. 生成 Chart.js 初始化脚本
    chart_scripts = ""
    for key in metrics.keys():
        records = history_data.get(key, [])
        if not records:
            continue
            
        # 【关键修复】清洗月份标签，防止出现 "\u5e74\u6708" 乱码
        clean_labels = []
        clean_values = []
        for r in records:
            # 将 "2026年02月份" 统一清洗为 "2026-02"
            m = str(r['month']).replace("年", "-").replace("月份", "").replace("月", "").strip()
            clean_labels.append(m)
            clean_values.append(r['value'])
        
        chart_scripts += f"""
        // --- {key} Chart ---
        const ctx_{key} = document.getElementById('chart-{key}');
        if (ctx_{key}) {{
            new Chart(ctx_{key}, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(clean_labels)}, 
                    datasets: [{{
                        data: {json.dumps(clean_values)},
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.05)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: '#3b82f6',
                        tension: 0.4,
                        fill: true,
                        spanGaps: false
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
                        x: {{ display: false }},
                        y: {{ 
                            display: false,
                            beginAtZero: false,
                            grace: '5%'
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
    # 优先使用 JSON 中的 update_time，确保与数据同步
    update_time = json_data.get("update_time", datetime.datetime.now().strftime("%Y-%m-%d"))
    final_html = main_tpl.replace("{{UPDATE_TIME}}", update_time)
    final_html = final_html.replace("{{ALL_CARDS_HTML}}", all_cards)
    final_html = final_html.replace("{{CHART_SCRIPTS}}", chart_scripts)

    output_path = os.path.join(ROOT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"✨ [渲染完成] 目标文件日期: {update_time}")

def generate_seo_assets(output_dir=ROOT_DIR):
    """生成站点地图和爬虫协议"""
    base_url = "https://data.ylh.top/"
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base_url}</loc><lastmod>{now}</lastmod><priority>1.0</priority></url></urlset>')
    
    robots_path = os.path.join(output_dir, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {base_url}sitemap.xml")

def main_run():
    # 获取 data 目录下所有 202x 开头的 JSON
    list_of_files = glob.glob(os.path.join(DATA_DIR, "20*.json"))
    if not list_of_files: 
       print(f"❌ 未在 {DATA_DIR} 发现日期命名的 JSON 文件")
       return
    
    # 【优化】按文件名排序（如 2026-03-24.json），确保取到日期最新的文件
    latest_file = sorted(list_of_files)[-1] 
    
    print(f"📖 [读取数据] {os.path.basename(latest_file)}")
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    build_page(data)
    generate_seo_assets()

if __name__ == "__main__":
    main_run()