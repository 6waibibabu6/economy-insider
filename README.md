📈 Economy Insider (宏观内参系统)

[![Economy Update](https://github.com/6waibibabu6/economy-insider/actions/workflows/update.yml/badge.svg)](https://github.com/6waibibabu6/economy-insider/actions/workflows/update.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Economy Insider** 是一款基于 Python 与人工智能的宏观经济指标监控与分析系统。它能够自动抓取核心经济数据（PMI、CPI、PPI），并调用 Gemini 大模型进行深度研判，最终生成可视化网页并自动部署。



---

## 🌟 系统特性

- **自动化流水线**：基于 GitHub Actions 实现每月双次（1号、15号）定时触发，无需人工干预。
- **解耦架构设计**：采用中央路径管理器 (`paths.py`)，屏蔽了本地开发环境与云端 CI/CD 环境的物理差异。
- **AI 深度研判**：集成 Google Gemini 3 Flash 模型，针对波动数据提供结构性分析。
- **响应式展示**：采用 Tailwind CSS 构建高颜值、极简风格的 Web 报告页面。

## 🏗️ 项目结构

```text
economy-insider/
├── .github/workflows/   # CI/CD 自动化流水线配置
├── assets/              # 静态资源（favicon等）
├── data/                # 历史经济指标 JSON 数据库
├── src/                 # 核心代码库
│   ├── paths.py         # 路径指挥部（环境适配逻辑）
│   ├── data_fetcher.py  # 数据抓取（Akshare 驱动）
│   ├── ai_analyst.py    # AI 研判逻辑
│   ├── page_builder.py  # 网页渲染引擎
│   └── github_pusher.py # GitHub 同步模块
├── main.py              # 调度中心 (Orchestrator)
└── requirements.txt     # 依赖清单
```
##🚀 快速启动
1. 环境准备
```
Bash
git clone [https://github.com/6waibibabu6/economy-insider.git](https://github.com/6waibibabu6/economy-insider.git)
cd economy-insider
pip install -r requirements.txt
```
2. 本地运行
确保你已在环境变量或 config.py 中配置了 GEMINI_API_KEY：
```
Bash
python src/main.py
```
##🛠️ 自动化部署说明

本系统通过 GitHub Actions 实现全自动运维。若需复刻，请在仓库 Settings > Secrets 中配置以下变量：
```
GEMINI_API_KEY: Google Gemini 的 API 密钥。

MY_GITHUB_TOKEN: 具备 Repo 写入权限的 GitHub 个人访问令牌 (PAT)。
```