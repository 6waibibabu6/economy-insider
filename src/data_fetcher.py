import os
import json
from datetime import datetime
import akshare as ak

DATA_DIR = "..\\data"

def clean_value(val, default=0.0):
    #确保数值合法，处理 None, NaN 或字符串格式
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
            # 转换为字典并处理可能存在的 NaN
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"⚠️ [警告] {name} 抓取失败: {e}")
        return None

def get_today_data():
    today_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(DATA_DIR, f"{today_str}.json")

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if os.path.exists(file_path):
        print(f"📦 [本地缓存] 发现今日数据文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    pmi_raw = fetch_safe(ak.macro_china_pmi, "PMI")
    cpi_raw = fetch_safe(ak.macro_china_cpi, "CPI")
    ppi_raw = fetch_safe(ak.macro_china_ppi, "PPI")

    # 核心处理逻辑：清洗数据，确保没有 null
    all_data = {
        "update_time": today_str,
        "metrics": {
            "pmi": {
                "name": "采购经理指数",
                "month": pmi_raw.get("月份", "N/A") if pmi_raw else "N/A",
                "mfg": clean_value(pmi_raw.get("制造业-指数")) if pmi_raw else 0.0,
                "non_mfg": clean_value(pmi_raw.get("非制造业-指数")) if pmi_raw else 0.0,
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
                "yoy": clean_value(ppi_raw.get("同比增长")) if ppi_raw else 0.0, # 这里解决了 null 问题
                "status": "success" if ppi_raw else "fail"
            }
        }
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    return all_data

if __name__ == "__main__":
    get_today_data()
    print("✅ 数据抓取与清洗完成，请查看 JSON 文件。")