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
    card_tpl = load_template("card_template")
    
    # 提取数值
    val_raw = float(item.get("mfg" if key == "pmi" else "value", 0.0))
    yoy_raw = float(item.get("mfg_yoy" if key == "pmi" else "yoy", 0.0))
    
    # --- 核心逻辑区分 ---
    # 只要数值不为 0，就代表“已获取数据”
    is_data_fetched = (val_raw != 0.0)
    
    if is_data_fetched:
        display_value = f"{val_raw:.1f}"
        yoy_display = f"{yoy_raw:+.1f}%"
        
        # 处理增长率为 0 的“持平”情况
        if yoy_raw > 0:
            color_class = "text-emerald-500"
            icon_name = "trending-up"
        elif yoy_raw < 0:
            color_class = "text-rose-500"
            icon_name = "trending-down"
        else:
            # 增长率为 0，显示灰色持平图标
            color_class = "text-slate-400" 
            icon_name = "minus" 
            yoy_display = "0.0% (持平)"
    else:
        # 彻底没拿到数据的情况
        display_value = "暂未获取"
        yoy_display = "--"
        color_class = "text-slate-300"
        icon_name = "circle-dashed"

    mappings = {
        "{{KEY}}": key,
        "{{NAME}}": item.get("name", "未知指标"),
        "{{MONTH}}": item.get("month", "N/A"),
        "{{VALUE}}": display_value,
        "{{COLOR_CLASS}}": color_class,
        "{{ICON_NAME}}": icon_name,
        "{{YOY_DISPLAY}}": yoy_display,
        "{{AI_INSIGHT}}": process_ai_insight(item.get("ai_insight", "分析生成中..."))
    }
    
    for k, v in mappings.items():
        card_tpl = card_tpl.replace(k, v)
    return card_tpl

# 对历史数据进行转换时使用
def transform_growth_to_index(history_data):
    """
    将 CPI/PPI 的增长率转换为以 100 为基准的指数。
    如果数值已经在 100 附近（如 101.3），则保持不变。
    """
    processed_data = {}
    
    for key, records in history_data.items():
        processed_records = []
        for r in records:
            # 深度拷贝，避免修改原始引用
            new_r = r.copy()
            val = float(r.get("value", 0.0))
            
            # 只有 CPI 和 PPI 需要转换，且排除掉已经是指数形式的数据（> 10 判定）
            if key in ["cpi", "ppi"] and -10 < val < 10:
                # 核心转换逻辑：1.3 -> 101.3; -0.9 -> 99.1
                new_r["value"] = round(100.0 + val, 2)
            else:
                # PMI 本身就是指数（50基准），直接保留
                new_r["value"] = val
            
            processed_records.append(new_r)
        processed_data[key] = processed_records
        
    return processed_data

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
    
    # 对历史数据进行转换，增长率到数值的转换
    history_data = transform_growth_to_index(history_data)

    # 2. 生成各指标卡片的 HTML
    metrics = json_data.get("metrics", {})
    all_cards = "".join([generate_card_html(k, v) for k, v in metrics.items() if v.get("status") == "success"])
    

    # 3. 生成导航卡片 HTML
    nav_cards_html = """
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12 animate-card" style="animation-delay: 0.3s;">
        <a href="global-data.html" class="group relative bg-slate-900 p-8 rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-2xl hover:shadow-blue-900/20 hover:-translate-y-1">
            <div class="relative z-10 flex justify-between items-start">
                <div>
                    <div class="text-blue-400 mb-4">
                        <i data-lucide="globe" class="w-8 h-8"></i>
                    </div>
                    <h3 class="text-2xl font-black text-white tracking-tight mb-2">Global Markets</h3>
                    <p class="text-slate-400 text-xs leading-relaxed max-w-[240px]">
                        访问全球 GDP 排名、汇率看板及国际市场实时波动数据。
                    </p>
                </div>
                <div class="bg-white/10 p-2 rounded-full text-white group-hover:bg-blue-600 transition-colors">
                    <i data-lucide="arrow-up-right" class="w-5 h-5"></i>
                </div>
            </div>
            <div class="absolute -right-4 -bottom-4 opacity-10">
                <i data-lucide="trending-up" class="w-32 h-32 text-blue-400"></i>
            </div>
        </a>

        <a href="insights.html" class="group relative bg-white p-8 rounded-2xl border border-slate-100 shadow-sm transition-all duration-300 hover:border-blue-600 hover:-translate-y-1">
            <div class="relative z-10 flex justify-between items-start">
                <div>
                    <div class="text-blue-600 mb-4">
                        <i data-lucide="book-open" class="w-8 h-8"></i>
                    </div>
                    <h3 class="text-2xl font-black text-slate-900 tracking-tight mb-2">Deep Insights</h3>
                    <p class="text-slate-500 text-xs leading-relaxed max-w-[240px]">
                        查阅深度经济评论、政策解读及长篇研究报告。
                    </p>
                </div>
                <div class="bg-slate-50 p-2 rounded-full text-slate-400 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                    <i data-lucide="arrow-up-right" class="w-5 h-5"></i>
                </div>
            </div>
            <div class="absolute -right-4 -bottom-4 opacity-5">
                <i data-lucide="file-text" class="w-32 h-32 text-slate-900"></i>
            </div>
        </a>
    </div>
    """

    # 4. 生成 Chart.js 初始化脚本
    chart_scripts = ""
    for key in metrics.keys():
        records = history_data.get(key, [])
        if not records:
            continue
            
        # 【关键修复】清洗月份标签，防止出现 "\u5e74\u6708" 乱码
        clean_labels = []
        clean_values = []
        for r in records:
            m = str(r['month']).replace("年", "-").replace("月份", "").replace("月", "").strip()
            clean_labels.append(m)
            
            val = r.get('value', 0.0)
            # 只有数值不为 0 时才绘点，否则设为 null 跳过（保持折线连续性视 spanGaps 而定）
            clean_values.append(val if val != 0 else None)
        
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
                        tension: 0.4,
                        fill: true,
                        spanGaps: true // 建议开启，这样中间缺失月份会自动连线，不会断开
                    }}]
                }},
                options: {{
                    // ... 保持之前的 responsive 和 plugins 配置 ...
                    scales: {{
                        x: {{ display: false }},
                        y: {{ 
                            display: false,
                            beginAtZero: false, // 核心：不从0开始，这样数值微小波动在图上更明显
                            grace: '5%',      // 给顶部留出一点空间                            
                        }}
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
    #  注入导航卡片 HTML
    final_html = final_html.replace("{{NAV_CARDS_HTML}}", nav_cards_html)
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