import os
import json
from datetime import datetime
import akshare as ak

# 1. 路径自动定位：指向 src/data/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

def clean_value(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def fetch_safe(func, name):
    try:
        print(f"🚀 [正在获取] {name}...")
        df = func()
        if df is not None and not df.empty:
            # 取最新的一条数据
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"⚠️ [警告] {name} 抓取失败: {e}")
        return None

def save_to_history(new_data):
    """
    将今日抓取的数据追加到历史库中，用于前端绘图
    """
    if not os.path.exists(HISTORY_FILE):
        history = {}
    else:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = {}

    for key, item in new_data['metrics'].items():
        if item.get("status") != "success":
            continue
        
        if key not in history:
            history[key] = []
        
        # 验证月份有效性，避免无效数据污染历史记录
        month = item.get("month")
        if not month or month == "N/A":
            print(f"⏩ [跳过] {key} 当前月份数据无效，不计入历史。")
            continue

        # 构造精简的历史记录点
        record = {
            "month": item.get("month"),
            "value": float(item.get("mfg" if key == "pmi" else "value", 0.0)),
            "yoy": float(item.get("mfg_yoy" if key == "pmi" else "yoy", 0.0))
        }

        # 去重逻辑：如果月份已存在则覆盖，不存在则追加
        existing_months = [r['month'] for r in history[key]]
        if record['month'] in existing_months:
            idx = existing_months.index(record['month'])
            history[key][idx] = record
        else:
            history[key].append(record)
        
        # 排序并只保留最近 12 个月的数据
        history[key] = sorted(history[key], key=lambda x: x['month'])[-12:]

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)
    print(f"💾 [同步] 历史数据已更新至: {HISTORY_FILE}")

def get_today_data():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 确保 src/data 目录存在
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    file_path = os.path.join(DATA_DIR, f"{today_str}.json")

    # 缓存逻辑
    if os.path.exists(file_path):
        print(f"📦 [本地缓存] 发现今日数据文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            save_to_history(data) # 确保即使读缓存也同步一下历史
            return data

    # 抓取逻辑
    pmi_raw = fetch_safe(ak.macro_china_pmi, "PMI")
    cpi_raw = fetch_safe(ak.macro_china_cpi, "CPI")
    ppi_raw = fetch_safe(ak.macro_china_ppi, "PPI")

    all_data = {
        "update_time": today_str,
        "metrics": {
            "pmi": {
                "name": "采购经理指数",
                "month": pmi_raw.get("月份", "N/A") if pmi_raw else "N/A",
                "mfg": clean_value(pmi_raw.get("制造业-指数")) if pmi_raw else 0.0,
                "mfg_yoy": 0.0, # PMI 通常看荣枯线，同比需计算，暂时设为0
                "status": "success" if pmi_raw else "fail"
            },
            "cpi": {
                "name": "居民消费价格指数",
                "month": cpi_raw.get("月份", "N/A") if cpi_raw else "N/A",
                "value": clean_value(cpi_raw.get("全国-当月")) if cpi_raw else 0.0,
                "yoy": clean_value(cpi_raw.get("全国-同比增长")) if cpi_raw else 0.0,
                "status": "success" if cpi_raw else "fail"
            },
            "ppi": {
                "name": "工业生产者出厂价格指数",
                "month": ppi_raw.get("月份", "N/A") if ppi_raw else "N/A",
                "value": clean_value(ppi_raw.get("当月")) if ppi_raw else 0.0,
                "yoy": clean_value(ppi_raw.get("同比增长")) if ppi_raw else 0.0,
                "status": "success" if ppi_raw else "fail"
            }
        }
    }

    # 保存今日快照
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    # 同步到长效历史库
    save_to_history(all_data)
    
    return all_data

if __name__ == "__main__":
    get_today_data()
    print("✅ 数据抓取、清洗与历史同步完成。")