# app.py
# RAG-Shield Dashboard — Streamlit UI
# Run with: streamlit run dashboard/app.py

import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RAG-Shield | Red Teaming Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif;
    }

    .main { background-color: #0d0d0f; }
    .block-container { padding: 1.5rem 2rem; max-width: 1400px; }

    /* Header */
    .rs-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 1.2rem 1.5rem;
        background: #13131a;
        border: 1px solid #1e1e2e;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .rs-header-icon {
        width: 42px; height: 42px;
        background: #E24B4A;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
    }
    .rs-header-title {
        font-size: 22px; font-weight: 800;
        color: #f0f0f0; letter-spacing: -0.5px;
        margin: 0;
    }
    .rs-header-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px; color: #666;
        letter-spacing: 1px; text-transform: uppercase;
        margin: 0;
    }
    .rs-live-badge {
        margin-left: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        padding: 5px 12px;
        background: #1a0a0a;
        color: #E24B4A;
        border: 1px solid #3a1515;
        border-radius: 20px;
        letter-spacing: 1px;
    }

    /* Metric cards */
    .rs-metric {
        background: #13131a;
        border: 1px solid #1e1e2e;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        text-align: center;
    }
    .rs-metric-val {
        font-size: 36px; font-weight: 800;
        line-height: 1; margin-bottom: 6px;
    }
    .rs-metric-lbl {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px; color: #666;
        letter-spacing: 1px; text-transform: uppercase;
    }

    /* Section cards */
    .rs-section {
        background: #13131a;
        border: 1px solid #1e1e2e;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1rem;
    }
    .rs-section-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px; color: #666;
        letter-spacing: 1.5px; text-transform: uppercase;
        margin-bottom: 1rem;
    }

    /* Failure table rows */
    .fail-row {
        display: flex; align-items: flex-start;
        gap: 12px; padding: 10px 0;
        border-bottom: 1px solid #1e1e2e;
    }
    .fail-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px; font-weight: 700;
        padding: 3px 8px; border-radius: 4px;
        white-space: nowrap; flex-shrink: 0;
    }
    .fail-id-jailbreak  { background: #1a0f0a; color: #EF9F27; border: 1px solid #3a2010; }
    .fail-id-pii_probe  { background: #1a0a0a; color: #E24B4A; border: 1px solid #3a1515; }
    .fail-id-injection  { background: #0a0f1a; color: #378ADD; border: 1px solid #10203a; }

    .fail-sev {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px; padding: 2px 7px;
        border-radius: 3px; flex-shrink: 0;
    }
    .fail-sev-high   { background: #1a0a0a; color: #E24B4A; }
    .fail-sev-medium { background: #1a120a; color: #EF9F27; }
    .fail-sev-low    { background: #0a1a0a; color: #639922; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
REPORT_PATH = "results/final_report.json"

@st.cache_data
def load_report():
    if not os.path.exists(REPORT_PATH):
        return None
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

report = load_report()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="rs-header">
    <div class="rs-header-icon">🛡️</div>
    <div>
        <p class="rs-header-title">RAG-Shield</p>
        <p class="rs-header-sub">Automated Red Teaming Framework · Phi-3 Mini · FAISS</p>
    </div>
    <div class="rs-live-badge">● LIVE REPORT</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NO DATA STATE
# ─────────────────────────────────────────────
if report is None:
    st.error("⚠️  No report found. Run `python src/reporter/score.py` first.")
    st.stop()

summary = report["summary"]
results = report["detailed_results"]
ts      = report.get("report_timestamp", "")
if ts:
    ts = datetime.fromisoformat(ts).strftime("%d %b %Y · %H:%M")

# ─────────────────────────────────────────────
# TOP METRICS ROW
# ─────────────────────────────────────────────
score   = summary["overall_score"]
passed  = summary["total_passed"]
failed  = summary["total_failed"]
total   = summary["total_prompts"]

score_color = "#E24B4A" if score < 60 else "#EF9F27" if score < 80 else "#639922"

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="rs-metric">
        <div class="rs-metric-val" style="color:{score_color};">{score}%</div>
        <div class="rs-metric-lbl">RRI Score</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="rs-metric">
        <div class="rs-metric-val" style="color:#f0f0f0;">{total}</div>
        <div class="rs-metric-lbl">Total Attacks</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="rs-metric">
        <div class="rs-metric-val" style="color:#639922;">{passed}</div>
        <div class="rs-metric-lbl">Blocked ✓</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="rs-metric">
        <div class="rs-metric-val" style="color:#E24B4A;">{failed}</div>
        <div class="rs-metric-lbl">Breached ✗</div>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="rs-metric">
        <div class="rs-metric-val" style="color:#378ADD;">3</div>
        <div class="rs-metric-lbl">Categories</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CHARTS ROW
# ─────────────────────────────────────────────
chart_col1, chart_col2, chart_col3 = st.columns(3)

# ── Gauge chart
with chart_col1:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "%", "font": {"size": 36, "color": score_color, "family": "Syne"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#444", "tickfont": {"color": "#666", "size": 11}},
            "bar": {"color": score_color, "thickness": 0.25},
            "bgcolor": "#1e1e2e",
            "bordercolor": "#1e1e2e",
            "steps": [
                {"range": [0, 60],  "color": "#1a0a0a"},
                {"range": [60, 80], "color": "#1a120a"},
                {"range": [80, 100],"color": "#0a1a0a"},
            ],
            "threshold": {"line": {"color": "#ffffff", "width": 2}, "thickness": 0.8, "value": score}
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="#13131a", plot_bgcolor="#13131a",
        font={"color": "#f0f0f0"},
        height=240, margin=dict(t=20, b=10, l=30, r=30),
        title=dict(text="RAG Robustness Index", font=dict(size=12, color="#666", family="JetBrains Mono"), x=0.5)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# ── Category bar chart
with chart_col2:
    cat_data = summary["category_scores"]
    cats     = list(cat_data.keys())
    scores   = [cat_data[c]["score"] for c in cats]
    colors   = ["#378ADD", "#E24B4A", "#EF9F27"]

    fig_cat = go.Figure(go.Bar(
        x=cats, y=scores,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{s}%" for s in scores],
        textposition="outside",
        textfont=dict(color="#f0f0f0", size=12, family="JetBrains Mono")
    ))
    fig_cat.update_layout(
        paper_bgcolor="#13131a", plot_bgcolor="#13131a",
        font={"color": "#f0f0f0", "family": "Syne"},
        height=240, margin=dict(t=30, b=10, l=10, r=10),
        title=dict(text="Resistance by Category", font=dict(size=12, color="#666", family="JetBrains Mono"), x=0.5),
        yaxis=dict(range=[0, 110], showgrid=True, gridcolor="#1e1e2e", tickfont=dict(color="#666")),
        xaxis=dict(tickfont=dict(color="#aaa", family="JetBrains Mono", size=11)),
        showlegend=False
    )
    st.plotly_chart(fig_cat, use_container_width=True)

# ── Severity donut
with chart_col3:
    sev = summary["severity_summary"]
    sev_labels = ["High failed", "Medium failed", "Low failed", "High passed", "Medium passed", "Low passed"]
    sev_vals   = [
        sev["high"]["failed"], sev["medium"]["failed"], sev["low"]["failed"],
        sev["high"]["total"] - sev["high"]["failed"],
        sev["medium"]["total"] - sev["medium"]["failed"],
        sev["low"]["total"] - sev["low"]["failed"]
    ]
    sev_colors = ["#E24B4A","#EF9F27","#639922","#3a1515","#3a2010","#0a1a0a"]

    fig_sev = go.Figure(go.Pie(
        labels=sev_labels, values=sev_vals,
        hole=0.65,
        marker=dict(colors=sev_colors, line=dict(color="#13131a", width=2)),
        textinfo="none",
        hovertemplate="%{label}: %{value}<extra></extra>"
    ))
    fig_sev.update_layout(
        paper_bgcolor="#13131a",
        font={"color":"#f0f0f0","family":"Syne"},
        height=240, margin=dict(t=30, b=10, l=10, r=10),
        title=dict(text="Failures by Severity", font=dict(size=12, color="#666", family="JetBrains Mono"), x=0.5),
        showlegend=False,
        annotations=[dict(text=f"{failed}<br><span style='font-size:10px'>breached</span>",
                         x=0.5, y=0.5, font_size=18, showarrow=False,
                         font=dict(color="#E24B4A", family="Syne"))]
    )
    st.plotly_chart(fig_sev, use_container_width=True)

# ─────────────────────────────────────────────
# FAILURE LOG
# ─────────────────────────────────────────────
st.markdown("<div class='rs-section-title' style='font-family:JetBrains Mono,monospace;font-size:11px;color:#666;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:0.5rem;'>Critical Failure Log</div>", unsafe_allow_html=True)

# Filter controls
filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 4])
with filter_col1:
    cat_filter = st.selectbox("Category", ["All", "jailbreak", "pii_probe", "injection"], label_visibility="collapsed")
with filter_col2:
    sev_filter = st.selectbox("Severity", ["All", "high", "medium", "low"], label_visibility="collapsed")

# Build dataframe of failures
failures = [r for r in results if r["final_verdict"] == "FAIL"]
df = pd.DataFrame([{
    "ID":       r["id"],
    "Category": r["category"],
    "Severity": r["severity"],
    "Prompt":   r["prompt"][:90] + ("..." if len(r["prompt"]) > 90 else ""),
    "Reason":   r["failure_reason"][:100] + ("..." if len(r.get("failure_reason","")) > 100 else ""),
    "Verdict":  r["final_verdict"]
} for r in failures])

# Apply filters
if cat_filter != "All":
    df = df[df["Category"] == cat_filter]
if sev_filter != "All":
    df = df[df["Severity"] == sev_filter]

# Render failure rows
st.markdown("<div class='rs-section' style='padding:1rem 1.4rem;'>", unsafe_allow_html=True)
for _, row in df.iterrows():
    cat_class = f"fail-id-{row['Category']}"
    sev_class = f"fail-sev-{row['Severity']}"
    st.markdown(f"""
    <div class="fail-row">
        <span class="fail-id {cat_class}">{row['ID']}</span>
        <div style="flex:1;">
            <div style="font-size:13px;color:#d0d0d0;line-height:1.4;margin-bottom:3px;">{row['Prompt']}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#555;line-height:1.4;">{row['Reason']}</div>
        </div>
        <span class="fail-sev {sev_class}">{row['Severity']}</span>
    </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;margin-top:2rem;padding:1rem;
font-family:'JetBrains Mono',monospace;font-size:11px;color:#444;letter-spacing:1px;">
    RAG-SHIELD · Report generated {ts} · Model: Phi-3 Mini · Vector Store: FAISS
</div>
""", unsafe_allow_html=True)
