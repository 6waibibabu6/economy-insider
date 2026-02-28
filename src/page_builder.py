import os
import json
import glob

# 1. 获取当前脚本的绝对路径 (src/page_builder.py)
current_script_path = os.path.abspath(__file__)

# 2. 获取 src 目录
current_dir = os.path.dirname(current_script_path)

# 3. 锁定真正的项目根目录 (economy-insider)
# 注意：只向上跳一级，确保它停在 economy-insider 文件夹
ROOT_DIR = os.path.dirname(current_dir)

print(f"📍 [路径定位] 项目根目录已锁定为: {ROOT_DIR}")

def generate_card_html(key, item):
    """
    为每个经济指标生成一对卡片：数据卡 (左) + 分析卡 (右)
    """
    name = item.get("name", "未知指标")
    month = item.get("month", "N/A")
    
    # 1. 提取主数值 (PMI 取 mfg, 其他取 value)
    value_raw = item.get("mfg") if key == "pmi" else item.get("value", 0.0)
    value = float(value_raw) if value_raw is not None else 0.0

    # 2. 提取并清洗同比数据 (yoy)，防止 NoneType 比较报错
    yoy_raw = item.get("mfg_yoy") if key == "pmi" else item.get("yoy", 0.0)
    yoy = float(yoy_raw) if yoy_raw is not None else 0.0
    
    # 3. 动态判断 UI 颜色和图标
    color_class = "text-emerald-500" if yoy >= 0 else "text-rose-500"
    icon_name = "trending-up" if yoy >= 0 else "trending-down"
    
    # yoy 展示逻辑 (0.0 显示为横线)
    yoy_display = f"{yoy:+.1f}%" if yoy != 0 else "--"

    # 4. 获取并处理 AI 分析内容 (Markdown 转换为 HTML 简单格式)
    raw_insight = item.get("ai_insight", "AI 正在深度解析该项指标的结构性变化...")
    
    # 极简 Markdown 处理：把 ** 替换为 <b>，把 \n 替换为 <br>
    # 这样可以在不引入复杂 md 库的情况下保证格式正确
    processed_insight = raw_insight.replace("**", "<b>").replace("</b>", "") # 简单替换开头的加粗
    # 进阶替换：利用字符串替换实现成对加粗处理
    while "<b>" in processed_insight:
        processed_insight = processed_insight.replace("<b>", "<strong class='text-slate-900'>", 1).replace("<b>", "</strong>", 1)
    
    # 处理换行：双换行转为段落间距，单换行转为折行
    processed_insight = processed_insight.replace("\n\n", "</p><p class='mt-3'>").replace("\n", "<br>")

    return f"""
    <section class="space-y-6 animate-card">
        <div class="flex items-center gap-2 text-xl font-bold text-slate-700">
            <i data-lucide="layers" class="w-6 h-6"></i>
            <h2>{name} <span class="text-sm font-normal text-slate-400 ml-2">{month}</span></h2>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-1 glass-card p-8 rounded-3xl shadow-sm border border-white/40">
                <div class="flex justify-between items-start mb-6">
                    <span class="px-3 py-1 bg-slate-100 text-slate-500 text-xs font-bold rounded-full uppercase tracking-tighter">Live</span>
                    <i data-lucide="database" class="text-blue-500 w-5 h-5"></i>
                </div>
                <div class="space-y-1">
                    <p class="text-sm font-medium text-slate-400 uppercase tracking-widest">指标数值</p>
                    <div class="flex items-baseline gap-2">
                        <h3 class="text-6xl font-black text-slate-800 tracking-tighter">{value:.1f}</h3>
                        <span class="{color_class} font-bold flex items-center text-sm">
                            <i data-lucide="{icon_name}" class="w-4 h-4 mr-1"></i> {yoy_display}
                        </span>
                    </div>
                </div>
            </div>

            <div class="lg:col-span-2 glass-card p-8 rounded-3xl shadow-sm border border-white/40">
                <div class="flex items-center gap-2 mb-4 text-blue-600">
                    <i data-lucide="sparkles" class="w-5 h-5"></i>
                    <span class="text-sm font-bold uppercase tracking-widest text-xs">AI Analyst Perspective</span>
                </div>
                <article class="prose prose-slate max-w-none text-slate-600 leading-relaxed text-sm">
                    <p>{processed_insight}</p>
                </article>
            </div>
        </div>
    </section>
    """

def build_page(json_data):
    update_time = json_data.get("update_time", "Unknown")
    metrics = json_data.get("metrics", {})
    all_cards_html = "".join([generate_card_html(k, v) for k, v in metrics.items() if v.get("status") == "success"])

    template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Economy Insider</title>
    <link rel="icon" href="assets/favicon.ico" type="image/x-icon">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .animate-card {{ animation: slideUp 0.6s ease-out forwards; }}
        .glass-card {{ background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(16px); }}
    </style>
</head>
<body class="bg-slate-50 text-slate-900 font-sans tracking-tight">
    <header class="py-16 px-6 max-w-7xl mx-auto flex justify-between items-end">
        <div>
            <h1 class="text-5xl font-black tracking-tighter text-slate-900">ECONOMY <span class="text-blue-600 italic">INSIDER</span></h1>
            <p class="mt-2 text-slate-400 font-medium tracking-wide">数据驱动的宏观内参系统</p>
        </div>
        <div class="text-right">
            <p class="text-xs font-bold text-slate-300 uppercase tracking-widest">Updated At</p>
            <p class="text-sm font-mono text-slate-500">{update_time}</p>
        </div>
    </header>
    <main class="max-w-7xl mx-auto px-6 pb-24 space-y-16">
        {all_cards_html}
    </main>
    <footer class="text-center py-20 border-t border-slate-200 text-slate-300 text-[10px] uppercase tracking-[0.2em]">
        &copy; 2026 Bjarne Yang | Generated by Gemini 2.0
    </footer>
    <script>lucide.createIcons();</script>
</body>
</html>
    """
    
    # 网页生成在根目录 (src 的上一级)
    output_path = os.path.join(ROOT_DIR, "index.html")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"✨ [修正成功] index.html 已生成至正确位置: {output_path}")

def main_run():
    print("🎨 [渲染] 正在准备更新网页内容...")
    
    # 1. 确保锁定 data 目录
    data_dir = os.path.join(ROOT_DIR, "data")
    data_pattern = os.path.join(data_dir, "*.json")
    list_of_files = glob.glob(data_pattern)
    
    if not list_of_files:
        print("❌ [错误] 未发现数据文件")
        return

    # 2. 【核心点】强制使用修改时间 (mtime) 排序，确保拿到 AI 写入后的文件
    latest_file = max(list_of_files, key=os.path.getmtime) 
    print(f"📖 [读取] 目标文件: {os.path.basename(latest_file)}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 3. 【强力验证】如果发现加载的数据里还是没有 ai_insight，报错提醒
    sample_key = 'pmi'
    if 'ai_insight' not in data['metrics'][sample_key]:
        print(f"⚠️ [警告] 加载的文件 {os.path.basename(latest_file)} 不包含 AI 分析字段！")
        print("请确认 ai_analyst.py 是否成功执行了写回操作。")
    else:
        print(f"✅ [成功] 验证到 AI 内容，长度: {len(data['metrics'][sample_key]['ai_insight'])}")

    # 执行渲染
    build_page(data)

# 保留原有的直接运行支持
if __name__ == "__main__":
    main_run()