"""
InsightReport - 自动化数据分析报告生成器
一键上传数据，AI 驱动分析，输出专业报告。
可部署为 SaaS / 接 freelance 单子。
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
import json
import datetime
import hashlib
import re
import os
from pathlib import Path

# ── Page Config ──
st.set_page_config(
    page_title="InsightReport · 智能数据分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ──
if "df" not in st.session_state:
    st.session_state.df = None
if "report_history" not in st.session_state:
    st.session_state.report_history = []
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

# ── Freemium Limits ──
FREE_MAX_ROWS = 5000
FREE_MAX_COLS = 20
PRO_MAX_ROWS = 100000
PRO_MAX_COLS = 200

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 📊 InsightReport")
    st.caption("智能数据分析报告引擎")
    st.divider()

    plan = st.radio("选择方案", ["免费版", "Pro 版"], index=0,
                    help="免费版限制 5000 行/20 列，Pro 版无限制")
    is_pro = plan == "Pro 版"
    max_rows = PRO_MAX_ROWS if is_pro else FREE_MAX_ROWS
    max_cols = PRO_MAX_COLS if is_pro else FREE_MAX_COLS

    st.divider()
    uploaded_file = st.file_uploader(
        "上传数据文件",
        type=["csv", "xlsx", "xls", "tsv", "json"],
        help="支持 CSV、Excel、JSON、TSV 格式",
    )

    if uploaded_file:
        st.caption(f"文件: {uploaded_file.name} ({uploaded_file.size/1024:.1f} KB)")

    st.divider()
    st.markdown("#### ⚡ 快速开始")
    st.markdown("""
    1. 上传 CSV/Excel 文件
    2. 自动生成分析报告
    3. 导出 HTML/PDF
    4. 分享给客户或团队
    """)

    st.divider()
    st.caption("💡 Pro 版即将上线: 无限制、API 接入、团队协作")

# ── Main Area ──
st.title("📊 InsightReport")
st.markdown("**上传数据 → 智能分析 → 导出专业报告**")

tabs = st.tabs(["📤 数据上传", "📋 数据概览", "📈 分析报告", "📄 导出"])

# ═══════════════════════════════════════════
# TAB 1: Data Upload
# ═══════════════════════════════════════════
with tabs[0]:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("上传数据")
        if not uploaded_file:
            st.info("请从左侧边栏上传文件")
            # Show sample data option
            if st.button("试用样例数据 (鸢尾花数据集)"):
                df = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")
                st.session_state.df = df
                st.session_state.usage_count += 1
                st.success(f"已加载样例数据: {df.shape[0]} 行 × {df.shape[1]} 列")
                st.rerun()
        else:
            try:
                ext = Path(uploaded_file.name).suffix.lower()
                if ext == ".csv":
                    df = pd.read_csv(uploaded_file)
                elif ext == ".tsv":
                    df = pd.read_csv(uploaded_file, sep="\t")
                elif ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(uploaded_file)
                elif ext == ".json":
                    df = pd.read_json(uploaded_file)
                else:
                    st.error(f"不支持的文件格式: {ext}")
                    st.stop()

                # Check limits
                if df.shape[0] > max_rows:
                    st.warning(f"数据行数 ({df.shape[0]}) 超过免费版限制 ({max_rows})，已截取前 {max_rows} 行")
                    df = df.head(max_rows)
                if df.shape[1] > max_cols:
                    st.warning(f"数据列数 ({df.shape[1]}) 超过免费版限制 ({max_cols})，已截取前 {max_cols} 列")
                    df = df.iloc[:, :max_cols]

                st.session_state.df = df
                st.session_state.usage_count += 1
                st.success(f"✅ 加载成功: {df.shape[0]} 行 × {df.shape[1]} 列")
                st.dataframe(df.head(100), use_container_width=True)

                with st.expander("列信息"):
                    info_df = pd.DataFrame({
                        "列名": df.columns,
                        "类型": df.dtypes.astype(str),
                        "非空值": df.count().values,
                        "空值": df.isna().sum().values,
                        "唯一值": [df[c].nunique() for c in df.columns],
                    })
                    st.dataframe(info_df, use_container_width=True)

            except Exception as e:
                st.error(f"读取文件失败: {e}")

    with col2:
        st.subheader("使用统计")
        c1, c2, c3 = st.columns(3)
        c1.metric("分析次数", st.session_state.usage_count)
        c2.metric("当前方案", "免费版" if not is_pro else "Pro 版")
        if st.session_state.df is not None:
            c3.metric("数据规模", f"{st.session_state.df.shape[0]}×{st.session_state.df.shape[1]}")
        else:
            c3.metric("数据规模", "-")

        st.divider()
        st.markdown("#### 价格方案")
        plans = pd.DataFrame({
            "功能": ["最大行数", "最大列数", "导出报告", "API 接入", "价格"],
            "免费版": ["5,000", "20", "✓", "✗", "¥0"],
            "Pro 版": ["100,000", "200", "✓ (PDF)", "✓", "¥99/月"],
            "企业版": ["无限", "无限", "✓ (定制)", "✓ (专属)", "¥499/月"],
        })
        st.dataframe(plans, hide_index=True, use_container_width=True)

# ═══════════════════════════════════════════
# TAB 2: Data Overview
# ═══════════════════════════════════════════
with tabs[1]:
    if st.session_state.df is None:
        st.info("请先在「数据上传」页面上传数据")
        st.stop()

    df = st.session_state.df

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("行数", df.shape[0])
    col2.metric("列数", df.shape[1])
    col3.metric("缺失值", df.isna().sum().sum())
    col4.metric("内存占用", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

    st.divider()

    st.subheader("描述统计")
    desc = df.describe(include="all").T
    desc["数据类型"] = df.dtypes.astype(str).values
    st.dataframe(desc, use_container_width=True)

    st.subheader("缺失值矩阵")
    if df.isna().any().any():
        fig = px.imshow(df.isna(), color_continuous_scale=["#1a2c3a", "#ff5d5d"],
                        title="缺失值热力图 (黄色=缺失)", aspect="auto")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("🎉 数据中没有缺失值")

    st.subheader("相关性矩阵 (数值列)")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                        aspect="auto", title="相关性热力图")
        fig.update_layout(height=500, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("需要至少 2 个数值列才能计算相关性")

# ═══════════════════════════════════════════
# TAB 3: Analysis Report
# ═══════════════════════════════════════════
with tabs[2]:
    if st.session_state.df is None:
        st.info("请先在「数据上传」页面上传数据")
        st.stop()

    df = st.session_state.df

    st.subheader("📈 自动分析报告")
    report_sections = []

    # Section 1: Data Quality
    with st.expander("📊 数据质量", expanded=True):
        st.markdown("#### 数据质量评分")
        completeness = 1 - df.isna().sum().sum() / (df.shape[0] * df.shape[1])
        uniqueness = np.mean([df[c].nunique() / max(df[c].nunique(), 1) for c in df.columns])
        quality_score = int((completeness * 0.6 + min(uniqueness, 1) * 0.4) * 100)

        c1, c2, c3 = st.columns(3)
        c1.metric("完整度", f"{completeness*100:.1f}%")
        c2.metric("唯一度", f"{uniqueness*100:.1f}%")
        c3.metric("质量评分", f"{quality_score}/100")

        st.progress(quality_score / 100)

        if quality_score < 50:
            st.warning("⚠️ 数据质量较低，建议清洗后再分析")
        elif quality_score < 80:
            st.info("📋 数据质量一般，部分列可能需要处理")
        else:
            st.success("✅ 数据质量良好")

        report_sections.append({
            "title": "数据质量",
            "completeness": f"{completeness*100:.1f}%",
            "quality_score": quality_score,
        })

    # Section 2: Distribution Analysis
    with st.expander("📈 分布分析", expanded=True):
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        if num_cols:
            st.markdown("#### 数值列分布")
            # Show top 8 numerical distributions
            cols_to_show = num_cols[:8]
            n_cols = min(3, len(cols_to_show))
            n_rows = (len(cols_to_show) + n_cols - 1) // n_cols

            fig = make_subplots(rows=n_rows, cols=n_cols,
                                subplot_titles=cols_to_show)
            for i, col in enumerate(cols_to_show):
                row = i // n_cols + 1
                col_pos = i % n_cols + 1
                fig.add_trace(
                    go.Histogram(x=df[col].dropna(), name=col,
                                 marker_color=px.colors.qualitative.Plotly[i % 10]),
                    row=row, col=col_pos,
                )
            fig.update_layout(height=250 * n_rows, showlegend=False,
                              margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

            # Box plots
            st.markdown("#### 箱线图 (异常值检测)")
            if len(cols_to_show) >= 1:
                fig2 = go.Figure()
                for i, col in enumerate(cols_to_show[:6]):
                    fig2.add_trace(go.Box(y=df[col].dropna(), name=col,
                                          marker_color=px.colors.qualitative.Plotly[i % 10]))
                fig2.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig2, use_container_width=True)

        if cat_cols:
            st.markdown("#### 分类列分布")
            for col in cat_cols[:4]:
                value_counts = df[col].value_counts().head(10)
                fig3 = px.bar(
                    x=value_counts.values, y=value_counts.index,
                    orientation="h", title=f"Top 10 - {col}",
                    color=value_counts.values, color_continuous_scale="Viridis",
                )
                fig3.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig3, use_container_width=True)

    # Section 3: Insights
    with st.expander("💡 关键洞察", expanded=True):
        st.markdown("#### 自动发现的洞察")

        insights = []

        # Correlation insights
        if len(num_cols) >= 2:
            corr = df[num_cols].corr()
            high_corr = []
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    v = corr.iloc[i, j]
                    if abs(v) > 0.7:
                        high_corr.append((num_cols[i], num_cols[j], v))
            if high_corr:
                insights.append(f"🔗 **强相关**: 发现 {len(high_corr)} 对高相关性变量")
                for a, b, v in high_corr[:5]:
                    direction = "正相关" if v > 0 else "负相关"
                    insights.append(f"  - `{a}` 与 `{b}`: {direction} ({v:.3f})")

        # Skewness insights
        if num_cols:
            for col in num_cols[:5]:
                skew = df[col].skew()
                if abs(skew) > 1:
                    direction = "右偏" if skew > 0 else "左偏"
                    insights.append(f"📊 **偏态分布**: `{col}` 呈 {direction} (偏度={skew:.2f})")

        # Missing value insights
        missing_cols = df.columns[df.isna().sum() > 0].tolist()
        if missing_cols:
            insights.append(f"⚠️ **缺失数据**: {len(missing_cols)} 列存在缺失值")
            for col in missing_cols[:3]:
                pct = df[col].isna().mean() * 100
                insights.append(f"  - `{col}`: {pct:.1f}% 缺失")

        # Outlier insights
        if num_cols:
            outlier_count = 0
            outlier_cols = []
            for col in num_cols:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
                if len(outliers) > 0:
                    outlier_count += len(outliers)
                    outlier_cols.append(col)
            if outlier_cols:
                insights.append(f"🎯 **异常值**: {outlier_count} 个异常值分布在 {len(outlier_cols)} 列中")

        if not insights:
            insights.append("✅ 数据较为规整，无明显异常模式")

        for ins in insights:
            st.markdown(ins)

        report_sections.append({
            "title": "关键洞察",
            "insights": insights,
        })

    # Section 4: Recommendations
    with st.expander("🎯 建议", expanded=True):
        st.markdown("#### 基于数据的建议")

        recs = []

        if missing_cols:
            recs.append(f"🧹 **数据清洗**: 处理 {len(missing_cols)} 列中的缺失值（填充或删除）")

        if len(num_cols) >= 2:
            high_corr_pairs = []
            corr = df[num_cols].corr()
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    if abs(corr.iloc[i, j]) > 0.85:
                        high_corr_pairs.append((num_cols[i], num_cols[j]))
            if high_corr_pairs:
                recs.append(f"🔄 **特征降维**: {len(high_corr_pairs)} 对变量高度相关，建议考虑 PCA 或特征选择")

        if num_cols:
            for col in num_cols[:3]:
                if df[col].nunique() < 5:
                    recs.append(f"📋 **分类编码**: `{col}` 可视为分类变量，建议 One-Hot 编码")

        if df.shape[1] > 10:
            recs.append("📐 **维度约简**: 数据集维度较高，建议探索 t-SNE 或 UMAP 可视化")

        if df.shape[0] > 10000:
            recs.append("⚡ **采样分析**: 数据量较大，可先采样进行探索性分析")

        if not recs:
            recs.append("✅ 数据质量较高，可直接进入建模阶段")

        for rec in recs:
            st.markdown(rec)

        report_sections.append({
            "title": "建议",
            "recommendations": recs,
        })

    # Store report in session
    st.session_state.report_data = report_sections

# ═══════════════════════════════════════════
# TAB 4: Export
# ═══════════════════════════════════════════
with tabs[3]:
    if st.session_state.df is None:
        st.info("请先在「数据上传」页面上传数据")
        st.stop()

    st.subheader("📄 导出报告")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### HTML 报告")
        st.markdown("导出为独立的 HTML 文件，可在浏览器中打开")
        if st.button("📥 生成 HTML 报告", use_container_width=True):
            html_content = generate_html_report(st.session_state.df, st.session_state.get("report_data", []))
            b64 = base64.b64encode(html_content.encode("utf-8")).decode()
            filename = f"InsightReport_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            href = f'<a href="data:text/html;base64,{b64}" download="{filename}">点击下载 {filename}</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.success("✅ HTML 报告生成完毕！")

    with col2:
        st.markdown("#### CSV 导出")
        st.markdown("导出清洗后的数据")
        csv_buffer = io.BytesIO()
        st.session_state.df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        b64_csv = base64.b64encode(csv_buffer.getvalue()).decode()
        href_csv = f'<a href="data:text/csv;base64,{b64_csv}" download="cleaned_data.csv">下载 CSV 文件</a>'
        st.markdown(href_csv, unsafe_allow_html=True)

        if st.button("📋 复制报告摘要", use_container_width=True):
            summary = generate_text_summary(st.session_state.df)
            st.code(summary, language="text")
            st.info("请手动复制以上内容")

    st.divider()
    st.markdown("#### 共享报告")
    st.markdown("""
    💡 **变现思路:**
    - 为客户生成分析报告，每次收费 ¥50-200
    - 部署为 SaaS，按月订阅 ¥99/月
    - 接入 API，按调用量计费
    """)


# ═══════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════

def generate_html_report(df, report_sections):
    """Generate a standalone HTML report."""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Create charts as base64
    charts_html = ""
    if num_cols:
        fig, axes = plt.subplots(min(3, len(num_cols)), 1, figsize=(10, 3 * min(3, len(num_cols))))
        if len(num_cols) == 1:
            axes = [axes]
        for i, col in enumerate(num_cols[:3]):
            axes[i].hist(df[col].dropna(), bins=30, color="#3dc9a0", alpha=0.7)
            axes[i].set_title(col, color="#d6e6f0")
            axes[i].set_facecolor("#111d27")
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, facecolor="#0b1219")
        buf.seek(0)
        charts_html = f'<img src="data:image/png;base64,{base64.b64encode(buf.read()).decode()}" style="width:100%;max-width:700px;border-radius:8px"/>'
        plt.close()

    sections_html = ""
    for s in report_sections:
        if s["title"] == "数据质量":
            sections_html += f"""
            <div class="section">
                <h2>📊 数据质量</h2>
                <p>完整度: {s.get("completeness", "N/A")}</p>
                <p>质量评分: {s.get("quality_score", "N/A")}/100</p>
            </div>"""
        elif s["title"] == "关键洞察":
            ins = "<br>".join(s.get("insights", []))
            sections_html += f"""
            <div class="section">
                <h2>💡 关键洞察</h2>
                <p>{ins}</p>
            </div>"""
        elif s["title"] == "建议":
            recs = "<br>".join(s.get("recommendations", []))
            sections_html += f"""
            <div class="section">
                <h2>🎯 建议</h2>
                <p>{recs}</p>
            </div>"""

    html = f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"/>
<title>InsightReport 分析报告</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:"Microsoft YaHei","Segoe UI",sans-serif;background:#0b1219;color:#d6e6f0;padding:40px}}
  .container{{max-width:900px;margin:0 auto}}
  h1{{color:#3dc9a0;font-size:28px;margin-bottom:6px}}
  .meta{{color:#7e9aaa;font-size:14px;margin-bottom:30px}}
  .section{{background:#111d27;border:1px solid rgba(100,160,200,.08);border-radius:10px;padding:20px;margin-bottom:16px}}
  .section h2{{font-size:18px;margin-bottom:10px;color:#f5b85a}}
  .section p{{font-size:14px;line-height:1.8;color:#d6e6f0}}
  .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:20px 0}}
  .stat-card{{background:#1a2c3a;border-radius:8px;padding:14px;text-align:center}}
  .stat-card .val{{font-size:24px;font-weight:700;color:#3dc9a0}}
  .stat-card .label{{font-size:12px;color:#7e9aaa;margin-top:4px}}
  .footer{{text-align:center;color:#4d6a7a;font-size:12px;margin-top:40px}}
</style>
</head>
<body>
<div class="container">
  <h1>📊 InsightReport</h1>
  <p class="meta">生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")} · 数据: {df.shape[0]}行 × {df.shape[1]}列</p>

  <div class="stats">
    <div class="stat-card"><div class="val">{df.shape[0]}</div><div class="label">行数</div></div>
    <div class="stat-card"><div class="val">{df.shape[1]}</div><div class="label">列数</div></div>
    <div class="stat-card"><div class="val">{df.isna().sum().sum()}</div><div class="label">缺失值</div></div>
    <div class="stat-card"><div class="val">{len(num_cols)}</div><div class="label">数值列</div></div>
  </div>

  {charts_html}
  {sections_html}

  <div class="footer">由 InsightReport 生成 · 基于 Streamlit</div>
</div>
</body>
</html>"""
    return html


def generate_text_summary(df):
    """Generate a plain text summary."""
    lines = [
        "=" * 50,
        "📊 InsightReport 数据报告摘要",
        "=" * 50,
        f"数据规模: {df.shape[0]} 行 × {df.shape[1]} 列",
        f"缺失值: {df.isna().sum().sum()}",
        f"数值列: {len(df.select_dtypes(include=[np.number]).columns)}",
        f"分类列: {len(df.select_dtypes(include=['object','category']).columns)}",
        "-" * 50,
        "列信息:",
    ]
    for c in df.columns:
        lines.append(f"  {c}: {df[c].dtype} | {df[c].nunique()} 唯一值 | {df[c].isna().sum()} 缺失")
    lines.append("-" * 50)
    lines.append("生成时间: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append("=" * 50)
    return "\n".join(lines)


# ── Footer ──
st.divider()
st.caption("InsightReport v1.0 · 数据仅保存在本地浏览器 · 基于 Python + Streamlit")
