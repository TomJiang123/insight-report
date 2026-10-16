# InsightReport · 智能数据分析报告引擎

一键上传数据 → 自动分析 → 导出专业报告。可部署为 SaaS 盈利。

## 快速启动

```bash
# 确保已安装依赖
pip install streamlit pandas numpy matplotlib seaborn plotly

# 启动 Web 应用
streamlit run insight_report.py
```

浏览器访问 http://localhost:8501

## 部署方式

### 方案一：本地部署（免费）
直接运行 `streamlit run insight_report.py`，本地可用。

### 方案二：云服务器部署（推荐变现）
1. 购买 VPS（腾讯云轻量 ¥34/月，或阿里云 ECS）
2. 用 Docker 或直接部署
3. 绑定域名，接入微信/支付宝支付

### 方案三：Streamlit Cloud（免费）
1. 推送到 GitHub
2. 在 share.streamlit.io 部署
3. 免费额度足够个人使用

## 变现思路

| 方式 | 定价 | 说明 |
|------|------|------|
| Freelance 接单 | ¥50-200/次 | 帮客户做数据分析报告 |
| SaaS 订阅 | ¥99/月 | 部署到服务器按月收费 |
| API 服务 | ¥0.1/次 | 开放 API 按调用量计费 |
| 企业定制 | ¥2000+ | 定制报告模板和功能 |

## 文件说明

- `insight_report.py` - Streamlit 应用主程序
- `index.html` - 产品落地页
- `server.py` - Flask REST API 版本（可选）

## 技术栈

- Python 3 + Streamlit
- Pandas + NumPy（数据处理）
- Plotly + Matplotlib + Seaborn（可视化）
- Flask（API 版本）
