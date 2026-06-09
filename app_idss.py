"""智慧決策支援系統（獨立入口）

介面風格參考期中報告：溫暖米白背景 + 深海軍藍標題 + 白色卡片
包含三個分頁：民眾出行輔助、決策分析、AI 智慧問答

運行方式：
    streamlit run app_idss.py --server.port 8502
"""
from __future__ import annotations

import math as _math
from pathlib import Path

import streamlit as st

# 從 app.py 取用共用渲染邏輯（不執行其 main()）
from app import (  # noqa: F401
    _render_analysis_page,
    _render_citizen_route_page,
    _render_question_page,
    DISTRICT_OPTIONS,
)

BASE_DIR = Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════════════
#  CSS — 期中報告配色：溫暖米白 + 深海軍藍 + 政府儀表板風格
# ══════════════════════════════════════════════════════════════════════
def _apply_idss_styles() -> None:
    st.html(
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;600;700'
        '&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
    )
    st.html("""
<style>
/* ══════ IDSS App — 期中報告配色：溫暖米白 × 深海軍藍 ══════ */
:root {
    /* ── 主色：參考期中報告深藍標題 ── */
    --navy:           #1e4d8c;
    --navy-dark:      #163a6b;
    --navy-light:     #2e6cbf;
    --blue-mid:       #4a90c4;
    --blue-soft:      #ddeaf8;

    /* ── 背景：參考報告溫暖米白底色 ── */
    --bg-base:        #f4f0e6;
    --bg-page:        #faf7f1;
    --bg-elevated:    #ffffff;
    --bg-glass:       #ffffff;
    --bg-glass-hover: #f0eee8;

    /* ── 邊框 ── */
    --border-subtle:  #ddd5c4;
    --border-medium:  #c8bfad;
    --border-accent:  #4a90c4;
    --border-navy:    #1e4d8c;

    /* ── 文字 ── */
    --text-primary:   #1e2d40;
    --text-secondary: #3d4f60;
    --text-muted:     #6b7a8a;
    --text-navy:      #1e4d8c;

    /* ── 風險色 ── */
    --risk-high:     #dc2626;
    --risk-high-bg:  #fff5f5;
    --risk-high-bdr: #fecaca;
    --risk-mid:      #d97706;
    --risk-mid-bg:   #fffbeb;
    --risk-mid-bdr:  #fde68a;
    --risk-low:      #15803d;
    --risk-low-bg:   #f0fdf4;
    --risk-low-bdr:  #bbf7d0;

    /* ── 工具 ── */
    --accent-blue:      #4a90c4;
    --accent-blue-glow: rgba(74,144,196,0.18);
    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-lg: 18px;
    --shadow-card: 0 2px 12px rgba(30,45,64,0.09);
    --shadow-hover: 0 4px 20px rgba(30,77,140,0.14);
    --transition: 0.2s cubic-bezier(0.4,0,0.2,1);
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans TC', -apple-system, sans-serif !important;
}
.stApp { background: var(--bg-page) !important; }
.block-container { padding-top: 2rem !important; padding-bottom: 7rem !important; max-width: 1440px !important; }
#MainMenu, footer { visibility: hidden !important; }
/* 隱藏 Streamlit 頂部工具列（避免遮住內容） */
header[data-testid="stHeader"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
.stAppHeader,
.stDecoration {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
}

/* ─── Sidebar（深海軍藍） ─── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a3a5c 0%, #163252 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.1) !important;
}
section[data-testid="stSidebar"] * { color: #d4e2f0 !important; }

.sidebar-logo {
    display: flex; align-items: center; gap: 12px;
    padding: 0.8rem 0.3rem 1.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 1.2rem;
}
.sidebar-icon { font-size: 30px; }
.sidebar-brand-name {
    font-size: 18px; font-weight: 700; color: #ffffff !important;
    letter-spacing: 0.01em; line-height: 1.3;
}
.sidebar-brand-sub { font-size: 13px; color: #7faac8 !important; margin-top: 2px; }

.sidebar-section-label {
    font-size: 12px; font-weight: 700; color: #7faac8 !important;
    letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.5rem;
}
.sidebar-hint {
    font-size: 14px; color: #9ec0d8 !important; line-height: 1.65; margin-top: 0.5rem;
    padding: 0.65rem 0.85rem;
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px;
}
.sidebar-divider { height: 1px; background: rgba(255,255,255,0.12); margin: 1rem 0; }
.sidebar-stats { display: flex; flex-direction: column; gap: 0.5rem; }
.sidebar-stat-item {
    display: flex; flex-direction: column; gap: 2px;
    padding: 0.5rem 0.75rem;
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px;
}
.sidebar-stat-label    { font-size: 13px; color: #7faac8 !important; }
.sidebar-stat-value    { font-size: 15px; color: #d4e2f0 !important; font-weight: 500; }
.sidebar-stat-highlight{ color: #fbbf24 !important; font-weight: 700; }

/* Radio（側欄） */
.stRadio > div { gap: 0.4rem !important; }
.stRadio label {
    padding: 0.45rem 0.75rem !important; border-radius: var(--radius-sm) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    background: rgba(255,255,255,0.07) !important;
    color: #d4e2f0 !important; transition: all var(--transition) !important;
}
.stRadio label:hover {
    border-color: #4a90c4 !important; background: rgba(74,144,196,0.15) !important; color: #e8f2fb !important;
}

/* ─── Hero（IDSS 頁首） ─── */
.nlp-hero {
    padding: 1rem 0 1rem 0;
    border-bottom: 2px solid var(--navy);
    margin-bottom: 1.4rem;
    position: relative;
}
.nlp-title {
    font-size: 42px; font-weight: 800; color: var(--navy);
    letter-spacing: -0.02em; margin: 0 0 0.4rem 0; line-height: 1.2;
}
.nlp-subtitle { font-size: 20px; color: var(--text-muted); margin: 0; line-height: 1.7; }
.nlp-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--blue-soft);
    border: 1px solid #b8d0ea;
    color: var(--navy); border-radius: 6px;
    padding: 0.28rem 0.9rem; font-size: 15px; font-weight: 700;
    margin-bottom: 0.8rem; letter-spacing: 0.03em;
    text-transform: uppercase;
}
.nlp-badge::before {
    content: ""; width: 8px; height: 8px; border-radius: 2px;
    background: var(--navy);
}

/* ─── IDSS 專屬：頁面分節標題 ─── */
.idss-section-header {
    display: flex; align-items: center; gap: 10px;
    padding: 0.75rem 1rem;
    background: var(--navy); color: #fff;
    border-radius: var(--radius-sm); margin-bottom: 1rem;
    font-size: 17px; font-weight: 700; letter-spacing: 0.01em;
}

/* ─── 白色卡片（報告風格） ─── */
.glass-card {
    background: #fff;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow-card);
    transition: all var(--transition);
}
.glass-card:hover {
    border-color: var(--blue-mid);
    box-shadow: var(--shadow-hover);
}

/* ─── Chat Messages ─── */
.stChatMessage {
    background: #fff !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-card) !important;
    animation: slideInUp 0.25s ease;
}
@keyframes slideInUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.stChatMessage p, .stChatMessage li {
    font-size: 18px !important; line-height: 1.75 !important; color: var(--text-primary) !important;
}
[data-testid="stChatMessageContent"] { background: transparent !important; }

/* ─── Buttons ─── */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-medium) !important;
    background: #fff !important; color: var(--text-secondary) !important;
    font-size: 16px !important; font-weight: 500 !important;
    transition: all var(--transition) !important;
}
.stButton > button:hover {
    border-color: var(--navy) !important; color: var(--navy) !important;
    background: var(--blue-soft) !important;
}
.stButton > button[kind="primary"] {
    background: var(--navy) !important; border: none !important; color: #fff !important;
    box-shadow: 0 2px 12px rgba(30,77,140,0.3) !important;
}
.stButton > button[kind="primary"]:hover { background: var(--navy-dark) !important; }

/* ─── Metrics ─── */
[data-testid="metric-container"] {
    background: #fff !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: 3px solid var(--navy) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
    box-shadow: var(--shadow-card) !important;
}
[data-testid="metric-container"] label {
    font-size: 14px !important; font-weight: 700 !important;
    color: var(--text-muted) !important; text-transform: uppercase !important; letter-spacing: 0.06em !important;
}
[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 800 !important; color: var(--navy) !important; }

/* ─── Expanders ─── */
div[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden; box-shadow: var(--shadow-card);
}
div[data-testid="stExpander"] summary {
    padding: 0.75rem 1rem !important; color: var(--text-secondary) !important;
    font-weight: 600 !important; font-size: 16px !important;
    border-bottom: 1px solid var(--border-subtle);
}

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    background: #fff !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    padding: 4px !important; gap: 2px !important;
    box-shadow: var(--shadow-card);
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important; font-size: 16px !important; font-weight: 600 !important;
    border-radius: var(--radius-sm) !important; padding: 0.45rem 1.1rem !important;
    transition: all var(--transition) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--navy) !important; color: #fff !important;
}
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding-top: 1.2rem !important; }

/* ─── Inputs ─── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: #fff !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important; font-size: 16px !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
    border-color: var(--navy) !important;
    box-shadow: 0 0 0 3px rgba(30,77,140,0.12) !important;
}

/* ─── Chat Input（無邊框，讓外層卡片作為容器）─── */
[data-testid="stChatInputTextArea"] {
    background: transparent !important; border: none !important;
    border-radius: 0 !important; box-shadow: none !important;
    color: var(--text-primary) !important;
}
[data-testid="stChatInputTextArea"] > div,
[data-testid="stChatInputTextArea"] div,
[data-testid="stChatInputTextArea"] [data-baseweb="textarea"] {
    background: transparent !important; border: 0 !important; box-shadow: none !important;
}
[data-testid="stChatInputTextArea"] textarea {
    background: transparent !important; color: var(--text-primary) !important;
    font-size: 17px !important; padding: 0.7rem 3rem 0.7rem 1rem !important;
    border: 0 !important; box-shadow: none !important; outline: none !important;
}
/* focus 效果套在卡片上 */
[data-testid="stBottomBlockContainer"]:focus-within {
    border-color: var(--navy) !important;
    box-shadow: 0 4px 32px rgba(30,45,64,0.14), 0 0 0 3px rgba(30,77,140,0.14) !important;
}
[data-testid="stChatInputTextArea"]:focus-within {
    border: none !important; box-shadow: none !important;
}
textarea::placeholder, input::placeholder { color: #9ca3af !important; }

/* ─── 底部浮動輸入卡片（置中，仿 Claude 風格）─── */

/* 外層：透明，頁面背景穿透 */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stChatFloatingInputContainer"],
[data-testid="stChatFloatingInputContainer"] > *,
.stChatInputContainer {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* 中間白色卡片：最大寬度 740px，自動置中，圓角陰影 */
[data-testid="stBottomBlockContainer"] {
    max-width: 740px !important;
    width: calc(100% - 3rem) !important;
    margin: 0 auto 1.4rem auto !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1.5px solid #c8d6e6 !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 32px rgba(30,45,64,0.13), 0 1px 4px rgba(30,45,64,0.07) !important;
    padding: 0.15rem 0.4rem !important;
}

[data-testid="stChatInput"],
[data-testid="stChatInput"] > div {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* 送出按鈕 */
[data-testid="stChatInput"] button,
[data-testid="stChatInput"] [role="button"],
[data-testid="stChatInputSubmitButton"] {
    color: #9ca3af !important; background: transparent !important; border: 0 !important; box-shadow: none !important;
    border-radius: 50% !important; width: 34px !important; height: 34px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
}
[data-testid="stChatInput"] button:hover,
[data-testid="stChatInput"] [role="button"]:hover,
[data-testid="stChatInputSubmitButton"]:hover {
    color: var(--navy) !important; background: var(--blue-soft) !important;
}
[data-testid="stChatInput"] button svg,
[data-testid="stChatInputSubmitButton"] svg { fill: currentColor !important; }

/* ─── NLP Components（在 IDSS 問答分頁中使用） ─── */
.nlp-panel-title { font-size: 19px; font-weight: 700; color: var(--navy); margin: 0 0 0.4rem 0; }
.nlp-panel-note  { font-size: 16px; color: var(--text-muted); line-height: 1.6; margin-bottom: 0.6rem; }
.nlp-flow-step   { border-left: 3px solid var(--navy); padding: 0.15rem 0 0.5rem 0.75rem; margin: 0.1rem 0; }
.nlp-flow-label  { color: var(--text-muted); font-size: 13px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
.nlp-flow-value  { color: var(--text-primary); font-size: 17px; font-weight: 600; line-height: 1.5; }
.nlp-empty {
    border: 1px dashed var(--border-medium); border-radius: var(--radius-md);
    padding: 1.4rem 1.6rem; color: var(--text-muted);
    background: #faf8f4; font-size: 17px; text-align: center; line-height: 1.7;
}

/* ─── Risk Badge ─── */
.risk-card {
    border-radius: var(--radius-md); padding: 1rem 1.4rem; margin-bottom: 0.8rem;
    display: flex; align-items: center; gap: 1rem; font-weight: 600;
}
.risk-card-high { background: var(--risk-high-bg); border: 1px solid var(--risk-high-bdr); color: var(--risk-high); }
.risk-card-mid  { background: var(--risk-mid-bg);  border: 1px solid var(--risk-mid-bdr);  color: var(--risk-mid); }
.risk-card-low  { background: var(--risk-low-bg);  border: 1px solid var(--risk-low-bdr);  color: var(--risk-low); }
.risk-card-icon  { font-size: 28px; }
.risk-card-label { font-size: 14px; opacity: 0.7; font-weight: 500; display: block; margin-bottom: 2px; }
.risk-card-level { font-size: 22px; font-weight: 800; }
.risk-card-score { margin-left: auto; font-size: 38px; font-weight: 800; opacity: 0.85; }

/* ─── Typography ─── */
h2 {
    font-size: 22px !important; font-weight: 800 !important; color: var(--navy) !important;
    border-bottom: 2px solid var(--blue-soft) !important; padding-bottom: 0.5rem !important;
    margin-bottom: 0.9rem !important;
}
h3 { font-size: 18px !important; font-weight: 700 !important; color: var(--navy-light) !important; }
.stCaption, [data-testid="caption"] { color: var(--text-muted) !important; font-size: 14px !important; }

/* ─── DataFrames / Maps ─── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: var(--shadow-card) !important;
}
[data-testid="stDeckGlJsonChart"], [data-testid="stMap"] {
    border-radius: var(--radius-lg) !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: var(--shadow-card) !important;
}

/* ─── Alert ─── */
[data-testid="stAlert"] { border-radius: var(--radius-md) !important; font-size: 16px !important; }

/* ─── Progress / Slider ─── */
.stProgress > div > div > div > div { background: var(--navy) !important; border-radius: 99px !important; }
.stProgress > div > div { background: var(--blue-soft) !important; border-radius: 99px !important; }
/* 滑桿軌道：只染非 tick bar 的 div */
[data-testid="stSlider"] > div > div > div:not([data-testid]) { background: var(--navy) !important; }
/* tick bar 數字框：背景透明、文字配頁面色 */
[data-testid="stTickBarMin"],
[data-testid="stTickBarMax"] {
    background: transparent !important;
    background-color: transparent !important;
    color: var(--text-primary) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
}

/* ─── Divider ─── */
hr { border: none !important; height: 1px !important; background: var(--border-subtle) !important; margin: 1.5rem 0 !important; }

/* ─── Download / Checkbox ─── */
[data-testid="stDownloadButton"] > button {
    background: var(--blue-soft) !important;
    border: 1px solid #b8d0ea !important;
    color: var(--navy) !important; font-weight: 700 !important;
}
[data-testid="stDownloadButton"] > button:hover { background: #c8ddf0 !important; }
.stCheckbox label { color: var(--text-secondary) !important; font-size: 16px !important; }

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #ede9e0; }
::-webkit-scrollbar-thumb { background: rgba(30,77,140,0.25); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(30,77,140,0.45); }
</style>
""")


# ══════════════════════════════════════════════════════════════════════
#  決策建議分頁 — AI 摘要 / 巡邏排班 / What-if 情境模擬
# ══════════════════════════════════════════════════════════════════════

def _idss_col(df, *candidates: str):
    for c in candidates:
        if c in df.columns:
            return c
    return None


@st.cache_data(show_spinner=False, ttl=1800)
def _idss_load_df():
    from data_loader import load_accident_data
    return load_accident_data()


def _render_decision_recommendations() -> None:
    with st.spinner("載入事故資料…"):
        try:
            df = _idss_load_df()
        except Exception as e:
            st.error(f"資料載入失敗：{e}")
            return

    dist_col    = _idss_col(df, "區", "行政區", "district")
    hour_col    = _idss_col(df, "hour", "時")
    weather_col = _idss_col(df, "天候_str", "天候", "weather")
    cause_col   = _idss_col(df, "肇事因素主要_str", "肇事因素主要")
    death_col   = _idss_col(df, "死亡數量", "死亡人數", "deaths")
    injury_col  = _idss_col(df, "受傷數量", "受傷人數", "injuries")

    st.html('<div class="idss-section-header">🎯 &nbsp;AI 決策摘要</div>')
    _idss_render_summary(df, dist_col, hour_col, weather_col, death_col, injury_col)

    st.divider()

    st.html('<div class="idss-section-header">🚔 &nbsp;巡邏最佳化排班</div>')
    _idss_render_patrol(df, dist_col, hour_col)

    st.divider()

    st.html('<div class="idss-section-header">🔬 &nbsp;What-if 情境模擬</div>')
    _idss_render_whatif(df, dist_col, death_col, injury_col)


def _idss_render_summary(df, dist_col, hour_col, weather_col, death_col, injury_col):
    import pandas as pd
    # 使用正確欄位名稱
    real_dist   = _idss_col(df, "區", "行政區", "district")
    real_death  = _idss_col(df, "死亡數量", "死亡人數", "deaths")
    real_injury = _idss_col(df, "受傷數量", "受傷人數", "injuries")
    dist_col, death_col, injury_col = real_dist, real_death, real_injury

    total = len(df)

    top_dist = top_dist_pct = None
    if dist_col:
        ds = df[dist_col].value_counts()
        if len(ds):
            top_dist = str(ds.index[0])
            top_dist_pct = ds.iloc[0] / total * 100

    top_hour = top_hour_pct = None
    if hour_col:
        hs = df[hour_col].dropna().value_counts()
        if len(hs):
            top_hour = int(hs.index[0])
            top_hour_pct = hs.iloc[0] / total * 100

    top_weather = None
    if weather_col:
        ws = df[weather_col].dropna().value_counts()
        if len(ws):
            top_weather = str(ws.index[0])

    total_deaths   = int(df[death_col].fillna(0).sum())  if death_col   else 0
    total_injuries = int(df[injury_col].fillna(0).sum()) if injury_col  else 0
    severity_rate  = total_deaths / total * 100 if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("總事故筆數", f"{total:,}")
    c2.metric(
        "最高風險行政區",
        top_dist or "N/A",
        f"{top_dist_pct:.1f}% 事故" if top_dist_pct else "",
    )
    c3.metric(
        "最高風險時段",
        f"{top_hour}時" if top_hour is not None else "N/A",
        f"{top_hour_pct:.1f}% 事故" if top_hour_pct else "",
    )
    c4.metric("年度死亡人數", f"{total_deaths:,}", f"死亡率 {severity_rate:.2f}%")
    c5.metric("年度受傷人數", f"{total_injuries:,}")

    st.markdown("### 三大優先改善建議")

    hour_label = (
        "下班尖峰" if top_hour is not None and top_hour in range(17, 20)
        else "上班尖峰" if top_hour is not None and top_hour in range(7, 9)
        else "深夜離峰"
    )

    r1, r2, r3 = st.columns(3)
    with r1:
        st.html(f"""
<div class="glass-card" style="border-left:4px solid #1e4d8c;">
  <div style="font-size:20px;margin-bottom:8px;">🏙️ 路段勤務強化</div>
  <div style="font-weight:700;color:#1e4d8c;font-size:17px;margin-bottom:6px;">優先佈署地點</div>
  <div style="font-size:15px;color:#3d4f60;line-height:1.75;">
    <b>{top_dist or '高事故行政區'}</b> 佔全市事故
    <b>{f"{top_dist_pct:.1f}%" if top_dist_pct else "N/A"}</b>，
    應列為首要勤務目標，在 17–19 時前提早部署，
    並在主要路口設臨時警示標誌。
  </div>
</div>""")

    with r2:
        st.html(f"""
<div class="glass-card" style="border-left:4px solid #d97706;">
  <div style="font-size:20px;margin-bottom:8px;">⏰ 時段預警機制</div>
  <div style="font-weight:700;color:#d97706;font-size:17px;margin-bottom:6px;">高風險時段警戒</div>
  <div style="font-size:15px;color:#3d4f60;line-height:1.75;">
    <b>{top_hour}時（{hour_label}）</b> 為事故高峰，佔比
    <b>{f"{top_hour_pct:.1f}%" if top_hour_pct else "N/A"}</b>。
    建議提前 30 分鐘強化勤務，
    並透過 LINE 官方帳號發布即時預警通知。
  </div>
</div>""")

    with r3:
        st.html(f"""
<div class="glass-card" style="border-left:4px solid #dc2626;">
  <div style="font-size:20px;margin-bottom:8px;">🌧️ 天候管制建議</div>
  <div style="font-weight:700;color:#dc2626;font-size:17px;margin-bottom:6px;">惡劣天候因應策略</div>
  <div style="font-size:15px;color:#3d4f60;line-height:1.75;">
    <b>{top_weather or '雨天'}</b> 情境事故風險顯著上升。
    建議啟動天候聯防：降低測速執法門檻、
    加強路面積水通報，對 <b>{top_dist or '高風險區'}</b>
    實施臨時限速。
  </div>
</div>""")


def _idss_render_patrol(df, dist_col, hour_col):
    import pandas as pd
    dist_col = _idss_col(df, "區", "行政區", "district")
    hour_col = _idss_col(df, "hour", "時")

    if not dist_col or not hour_col:
        st.warning("缺少行政區或時段欄位，無法產生排班建議。")
        return

    total = len(df)
    combos = (
        df.dropna(subset=[dist_col, hour_col])
        .groupby([dist_col, hour_col])
        .size()
        .reset_index(name="事故數")
        .sort_values("事故數", ascending=False)
        .reset_index(drop=True)
    )
    combos["佔全市%"] = (combos["事故數"] / total * 100).round(2)
    combos["累積涵蓋%"] = (combos["事故數"].cumsum() / total * 100).round(1)

    st.markdown(
        "每一個「班次」= 在**某行政區**的**某個小時**部署警力。\n"
        "系統依事故頻率自動排序——**班次數越多，覆蓋的事故場景越廣**，但所需資源也越多。"
    )

    col_s, col_m = st.columns([1, 2])
    with col_s:
        st.html("""
<div style="display:flex;justify-content:space-between;white-space:nowrap;
    font-size:13px;font-weight:700;color:#3d4f60;
    margin-bottom:-6px;padding:0 3px;">
  <span>1 班</span><span>30 班</span>
</div>""")
        n = st.slider("可投入班次數", 1, 30, 10, key="idss_patrol_n")
        covered = int(combos.head(n)["事故數"].sum())
        cov_pct = covered / total * 100
        st.metric("預估涵蓋事故", f"{covered:,} 件", f"佔全市 {cov_pct:.1f}%")
        st.caption("依行政區 × 時段頻率排序，優先部署可最大化勤務效益。")

    with col_m:
        top_n = combos.head(n).copy()
        top_n.index = range(1, len(top_n) + 1)
        top_n.index.name = "優先序"
        top_n["建議時段"] = top_n[hour_col].astype(int).apply(
            lambda h: f"{h:02d}:00–{(h+1)%24:02d}:59"
        )
        max_cnt = combos["事故數"].max()
        top_n["建議警力(人)"] = top_n["事故數"].apply(
            lambda c: max(1, min(5, round(1 + 4 * _math.log1p(c) / _math.log1p(max_cnt))))
        )
        disp = top_n[[dist_col, "建議時段", "事故數", "佔全市%", "累積涵蓋%", "建議警力(人)"]].copy()
        disp.columns = ["行政區", "建議時段", "歷史事故數", "佔全市%", "累積涵蓋%", "建議警力(人)"]
        st.dataframe(disp, use_container_width=True, hide_index=False)

    st.caption("班次數 vs. 累積涵蓋率曲線")
    curve_data = combos.head(30).reset_index(drop=True)
    curve_data.index = range(1, len(curve_data) + 1)
    st.line_chart(
        curve_data["累積涵蓋%"],
        height=200,
        use_container_width=True,
        color="#1e4d8c",
    )


def _idss_render_whatif(df, dist_col, death_col, injury_col):
    import pandas as pd

    # 修正欄位名稱（以實際資料為主）
    real_dist_col   = _idss_col(df, "區", "行政區", "district")
    real_death_col  = _idss_col(df, "死亡數量", "死亡人數", "deaths")
    real_injury_col = _idss_col(df, "受傷數量", "受傷人數", "injuries")

    INTERVENTIONS = {
        "增設測速照相": {
            "desc": "安裝固定式或行動式測速照相，針對超速行為。文獻顯示可降低超速相關事故 15–25%。",
            "effect": 0.20, "color": "#dc2626",
        },
        "增加巡邏警力": {
            "desc": "全面加強路面勤務，嚇阻各類違規行為，估計可降低整體事故 8–12%。",
            "effect": 0.10, "color": "#1e4d8c",
        },
        "調整號誌時序": {
            "desc": "優化路口號誌配時與感應設計，針對路口衝突，可降低路口型事故 10–15%。",
            "effect": 0.12, "color": "#d97706",
        },
        "加強酒駕執法": {
            "desc": "加強路邊酒測站頻率與夜間攔查，對飲酒相關事故效果顯著，可降低 20–30%。",
            "effect": 0.25, "color": "#7c3aed",
        },
        "改善路面標線": {
            "desc": "補畫車道線、停止線與行人穿越線，降低因標線模糊造成的偏向衝突事故 5–8%。",
            "effect": 0.065, "color": "#059669",
        },
    }

    col_l, col_r = st.columns([1, 1], gap="large")

    with col_l:
        intervention = st.selectbox("選擇介入措施", list(INTERVENTIONS.keys()), key="idss_wi_intv")
        target_dist  = st.selectbox("目標行政區", DISTRICT_OPTIONS, key="idss_wi_dist")
        st.html("""
<div style="display:flex;justify-content:space-between;white-space:nowrap;
    font-size:13px;font-weight:700;color:#3d4f60;
    margin-bottom:-6px;padding:0 3px;">
  <span>10%</span><span>100%</span>
</div>""")
        intensity = st.slider(
            "介入強度（%）", 10, 100, 60, 10,
            key="idss_wi_intensity",
            help="代表措施落實程度，100% = 全面完整執行",
        )
        info = INTERVENTIONS[intervention]
        st.html(f"""
<div class="glass-card" style="border-top:4px solid {info['color']};margin-top:12px;">
  <div style="font-size:17px;font-weight:700;color:{info['color']};margin-bottom:6px;">{intervention}</div>
  <div style="font-size:15px;color:#3d4f60;line-height:1.65;">{info['desc']}</div>
</div>""")

    with col_r:
        if real_dist_col and target_dist and target_dist != "不指定":
            df_t = df[df[real_dist_col] == target_dist]
        else:
            df_t = df

        current  = len(df_t)
        deaths   = int(pd.to_numeric(df_t[real_death_col],  errors="coerce").fillna(0).sum()) if real_death_col  else 0
        injuries = int(pd.to_numeric(df_t[real_injury_col], errors="coerce").fillna(0).sum()) if real_injury_col else 0

        eff   = info["effect"] * (intensity / 100)
        red   = int(current * eff)
        new   = max(0, current - red)
        d_red = int(deaths * eff * 0.8)
        i_red = int(injuries * eff)

        scope = target_dist if target_dist != "不指定" else "全台中市"
        st.markdown(f"**{scope} · {intervention} · 強度 {intensity}%**")

        # 事故件數（三欄，不顯示紅色負值 delta）
        m1, m2, m3 = st.columns(3)
        m1.metric("目前事故數", f"{current:,} 件")
        m2.metric("預估可減少", f"{red:,} 件", delta=f"↓ {eff*100:.1f}%", delta_color="off")
        m3.metric("介入後預估", f"{new:,} 件")

        # 死亡 / 受傷（有資料才顯示；避免 0 的誤導）
        if deaths > 0 or injuries > 0:
            m4, m5 = st.columns(2)
            if deaths > 0:
                m4.metric("預估減少死亡", f"{d_red} 人", delta=f"↓ {eff*80:.0f}%", delta_color="off")
            else:
                m4.metric("死亡人數", "無死亡記錄", delta_color="off")
            if injuries > 0:
                m5.metric("預估減少受傷", f"{i_red:,} 人", delta=f"↓ {eff*100:.1f}%", delta_color="off")
            else:
                m5.metric("受傷人數", "無受傷記錄", delta_color="off")

        # 前後對比長條圖
        bar_data = pd.DataFrame(
            {"事故數": [current, new]},
            index=["介入前", "介入後"],
        )
        st.bar_chart(bar_data, color="#1e4d8c", height=160, use_container_width=True)

        st.caption(
            f"統計估算：基礎效益 {info['effect']*100:.0f}%，"
            f"介入強度 {intensity}% → 實際效益約 {eff*100:.1f}%。"
            "實際成效依執行品質與地區特性而異。"
        )


# ══════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════
def main() -> None:
    st.set_page_config(
        page_title="台中市交通事故智慧決策支援系統",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_idss_styles()

    # ── 側欄 ─────────────────────────────────────────────────────────
    with st.sidebar:
        st.html("""
        <div class="sidebar-logo">
            <div class="sidebar-icon">🚦</div>
            <div class="sidebar-brand">
                <div class="sidebar-brand-name">智慧決策支援系統</div>
                <div class="sidebar-brand-sub">台中市交通事故分析平台</div>
            </div>
        </div>
        """)

        st.html('<div class="sidebar-section-label">系統功能</div>')
        st.html("""
        <div class="sidebar-hint">
            <b style="color:#e8f2fb;">民眾出行輔助</b><br>
            根據起終點、時段與天候提供出行風險提醒<br><br>
            <b style="color:#e8f2fb;">決策分析</b><br>
            事故熱點地圖・天候時段熱力圖・巡邏優化<br><br>
            <b style="color:#e8f2fb;">AI 智慧問答</b><br>
            以自然語言問答快速查詢風險與建議
        </div>
        """)

        try:
            from data_loader import get_data_summary
            summary = get_data_summary()
            st.html('<div class="sidebar-divider"></div>')
            st.html(f"""
            <div class="sidebar-stats">
                <div class="sidebar-stat-item">
                    <span class="sidebar-stat-label">📂 資料來源</span>
                    <span class="sidebar-stat-value">台中市開放資料</span>
                </div>
                <div class="sidebar-stat-item">
                    <span class="sidebar-stat-label">📅 時間範圍</span>
                    <span class="sidebar-stat-value">{summary['date_range_str']}</span>
                </div>
                <div class="sidebar-stat-item">
                    <span class="sidebar-stat-label">📅 資料年份</span>
                    <span class="sidebar-stat-value">{summary['year_range_str']}</span>
                </div>
                <div class="sidebar-stat-item">
                    <span class="sidebar-stat-label">🗂️ 總事故筆數</span>
                    <span class="sidebar-stat-value sidebar-stat-highlight">{summary['total_count']:,} 件</span>
                </div>
            </div>
            """)
        except Exception:
            pass

        st.html('<div class="sidebar-divider"></div>')
        show_debug = st.checkbox("顯示進階除錯資訊", value=False)
        st.html('<div class="sidebar-divider"></div>')
        st.html("""
        <div class="sidebar-hint" style="font-size:11px;opacity:0.6;">
            NLP 問答系統請執行<br>
            <code style="background:rgba(255,255,255,0.1);padding:1px 4px;border-radius:4px;">
            streamlit run app_nlp.py</code>
        </div>
        """)

    # ── 頁首 ─────────────────────────────────────────────────────────
    st.html("""
    <div class="nlp-hero">
        <div class="nlp-badge">IDSS · 智慧決策支援系統</div>
        <div class="nlp-title">台中市交通事故智慧決策支援系統</div>
        <p class="nlp-subtitle">
            以歷史事故資料、RF 預測模型、熱點分析與處方性建議，支援交通安全決策與民眾出行參考。
        </p>
    </div>
    """)

    # ── 四個分頁 ─────────────────────────────────────────────────────
    tab_citizen, tab_analysis, tab_recommend, tab_chat = st.tabs([
        "🚶 民眾出行輔助",
        "📊 決策分析",
        "🎯 決策建議",
        "💬 AI 智慧問答",
    ])

    with tab_citizen:
        _render_citizen_route_page()

    with tab_analysis:
        _render_analysis_page(st.session_state.get("pipeline_result"))

    with tab_recommend:
        _render_decision_recommendations()

    with tab_chat:
        st.html("""
        <div style="
            background: #ddeaf8;
            border: 1px solid #b8d0ea;
            border-left: 4px solid #1e4d8c;
            border-radius: 8px;
            padding: 0.65rem 1rem;
            margin-bottom: 1rem;
            font-size: 15px;
            color: #1e4d8c;
            font-weight: 500;
        ">
            💡 以自然語言提問，系統自動辨識意圖並結合資料、模型與 RAG 知識庫生成回答。
        </div>
        """)
        _render_question_page(show_debug)


if __name__ == "__main__":
    main()
