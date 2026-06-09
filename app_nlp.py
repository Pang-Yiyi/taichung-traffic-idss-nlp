"""自然語言問答系統（獨立入口）

運行方式：
    streamlit run app_nlp.py --server.port 8501
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

# 從 app.py 取用共用渲染邏輯（不執行其 main()）
from app import _render_question_page  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════════════
#  CSS — 簡潔現代 AI 對話風格（深色側欄 + 純白主區）
# ══════════════════════════════════════════════════════════════════════
def _apply_nlp_styles() -> None:
    st.html(
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;600;700'
        '&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
    )
    st.html("""
<style>
/* ══════ NLP App — Clean Modern AI Chat ══════ */
:root {
    --bg-base:        #f0f4f8;
    --bg-elevated:    #ffffff;
    --bg-glass:       #ffffff;
    --bg-glass-hover: #f0f7f5;
    --border-subtle:  #e1e7ef;
    --border-medium:  #c9d4de;
    --border-accent:  #0d9488;

    --text-primary:   #111827;
    --text-secondary: #374151;
    --text-muted:     #6b7280;

    --accent-blue:      #0d9488;
    --accent-blue-glow: rgba(13,148,136,0.18);
    --accent-indigo:    #0891b2;
    --accent-cyan:      #06b6d4;

    --risk-high:     #ef4444;
    --risk-mid:      #f59e0b;
    --risk-low:      #10b981;

    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-xl: 28px;

    --shadow-glass: 0 2px 16px rgba(17,24,39,0.07);
    --shadow-card:  0 4px 20px rgba(17,24,39,0.09);
    --shadow-glow:  0 0 0 3px rgba(13,148,136,0.15);
    --transition:   0.2s cubic-bezier(0.4,0,0.2,1);
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans TC', -apple-system, sans-serif !important;
}
.stApp { background: var(--bg-base) !important; }
.block-container { padding-top: 2rem !important; padding-bottom: 7rem !important; max-width: 1380px !important; }
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

/* ─── Sidebar (dark navy) ─── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
section[data-testid="stSidebar"] * { color: #d1d5db !important; }

.sidebar-logo {
    display: flex; align-items: center; gap: 12px;
    padding: 0.7rem 0.2rem 1.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 1.2rem;
}
.sidebar-icon { font-size: 30px; }
.sidebar-brand-name { font-size: 19px; font-weight: 700; color: #f9fafb !important; }
.sidebar-brand-sub  { font-size: 13px; color: #6b7280 !important; margin-top: 1px; }

.sidebar-section-label {
    font-size: 13px; font-weight: 600; color: #6b7280 !important;
    letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.5rem;
}
.sidebar-hint {
    font-size: 14px; color: #9ca3af !important; line-height: 1.6; margin-top: 0.5rem;
    padding: 0.6rem 0.8rem;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px;
}
.sidebar-divider { height: 1px; background: rgba(255,255,255,0.1); margin: 1rem 0; }
.sidebar-stats { display: flex; flex-direction: column; gap: 0.5rem; }
.sidebar-stat-item {
    display: flex; flex-direction: column; gap: 2px;
    padding: 0.5rem 0.7rem;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px;
}
.sidebar-stat-label    { font-size: 13px; color: #6b7280 !important; }
.sidebar-stat-value    { font-size: 15px; color: #d1d5db !important; font-weight: 500; }
.sidebar-stat-highlight{ color: #34d399 !important; font-weight: 700; }

/* ─── Radio ─── */
.stRadio > div { gap: 0.4rem !important; }
.stRadio label {
    padding: 0.45rem 0.75rem !important; border-radius: var(--radius-sm) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    background: rgba(255,255,255,0.07) !important;
    color: #d1d5db !important; transition: all var(--transition) !important;
}
.stRadio label:hover {
    border-color: #0d9488 !important; background: rgba(13,148,136,0.12) !important; color: #5eead4 !important;
}

/* ─── Hero ─── */
.nlp-hero {
    padding: 0.9rem 0 1rem 0;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1.2rem;
}
.nlp-title {
    font-size: 42px; font-weight: 800; color: #111827;
    letter-spacing: -0.02em; margin: 0 0 0.4rem 0; line-height: 1.2;
}
.nlp-subtitle { font-size: 20px; color: var(--text-muted); margin: 0; line-height: 1.7; }
.nlp-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(13,148,136,0.08);
    border: 1px solid rgba(13,148,136,0.22);
    color: #0d9488; border-radius: 999px;
    padding: 0.28rem 0.9rem; font-size: 15px; font-weight: 600;
    margin-bottom: 0.8rem; letter-spacing: 0.02em;
}
.nlp-badge::before {
    content: ""; width: 7px; height: 7px; border-radius: 999px;
    background: #0d9488; box-shadow: 0 0 0 3px rgba(13,148,136,0.2);
}

/* ─── Glass Card ─── */
.glass-card {
    background: #fff; border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg); padding: 1.2rem 1.4rem;
    box-shadow: var(--shadow-glass); transition: all var(--transition);
}
.glass-card:hover { border-color: var(--accent-blue); box-shadow: var(--shadow-glass), var(--shadow-glow); }

/* ─── Chat Messages ─── */
.stChatMessage {
    background: #fff !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: 0 2px 10px rgba(17,24,39,0.06) !important;
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
    border-color: var(--accent-blue) !important;
    color: var(--accent-blue) !important;
    background: rgba(13,148,136,0.06) !important;
}
.stButton > button[kind="primary"] {
    background: #0d9488 !important; border: none !important; color: #fff !important;
    box-shadow: 0 2px 12px rgba(13,148,136,0.3) !important;
}
.stButton > button[kind="primary"]:hover { background: #0f766e !important; }

/* ─── Metrics ─── */
[data-testid="metric-container"] {
    background: #fff !important; border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important; padding: 1rem !important;
    box-shadow: var(--shadow-glass) !important;
}
[data-testid="metric-container"] label {
    font-size: 14px !important; font-weight: 600 !important;
    color: var(--text-muted) !important; text-transform: uppercase !important; letter-spacing: 0.05em !important;
}
[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; }

/* ─── Expanders ─── */
div[data-testid="stExpander"] {
    background: #fff !important; border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important; overflow: hidden; box-shadow: var(--shadow-glass);
}
div[data-testid="stExpander"] summary {
    padding: 0.75rem 1rem !important; color: var(--text-secondary) !important;
    font-weight: 500 !important; font-size: 16px !important;
}
div[data-testid="stExpander"] summary:hover { color: var(--text-primary) !important; }

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    background: #fff !important; border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-subtle) !important; padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important; font-size: 16px !important; font-weight: 500 !important;
    border-radius: var(--radius-sm) !important; padding: 0.4rem 1rem !important;
    transition: all var(--transition) !important;
}
.stTabs [aria-selected="true"] { background: rgba(13,148,136,0.1) !important; color: #0d9488 !important; }
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding-top: 1rem !important; }

/* ─── Inputs ─── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: #fff !important; border: 1px solid var(--border-medium) !important;
    border-radius: var(--radius-sm) !important; color: var(--text-primary) !important; font-size: 16px !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
    border-color: var(--accent-blue) !important; box-shadow: 0 0 0 3px var(--accent-blue-glow) !important;
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
    border-color: #0d9488 !important;
    box-shadow: 0 4px 32px rgba(17,24,39,0.12), 0 0 0 3px rgba(13,148,136,0.15) !important;
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
    border: 1.5px solid #dde4ed !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 32px rgba(17,24,39,0.12), 0 1px 4px rgba(17,24,39,0.06) !important;
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
    color: #0d9488 !important; background: rgba(13,148,136,0.1) !important;
}
[data-testid="stChatInput"] button svg,
[data-testid="stChatInputSubmitButton"] svg { fill: currentColor !important; }

/* ─── NLP Components ─── */
.nlp-panel-title { font-size: 19px; font-weight: 700; color: var(--text-primary); margin: 0 0 0.4rem 0; }
.nlp-panel-note  { font-size: 16px; color: var(--text-muted); line-height: 1.6; margin-bottom: 0.6rem; }
.nlp-flow-step   { border-left: 3px solid #0d9488; padding: 0.15rem 0 0.5rem 0.75rem; margin: 0.1rem 0; }
.nlp-flow-label  { color: var(--text-muted); font-size: 13px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
.nlp-flow-value  { color: var(--text-primary); font-size: 17px; font-weight: 600; line-height: 1.5; }
.nlp-empty {
    border: 1px dashed var(--border-medium); border-radius: var(--radius-md);
    padding: 1.2rem 1.4rem; color: var(--text-muted);
    background: #fff; font-size: 17px; text-align: center; line-height: 1.7;
}

/* ─── Risk Badge ─── */
.risk-card {
    border-radius: var(--radius-md); padding: 1rem 1.4rem; margin-bottom: 0.8rem;
    display: flex; align-items: center; gap: 1rem; font-weight: 600;
}
.risk-card-high { background: #fff5f5; border: 1px solid #fecaca; color: #dc2626; }
.risk-card-mid  { background: #fffbeb; border: 1px solid #fde68a; color: #d97706; }
.risk-card-low  { background: #f0fdf4; border: 1px solid #bbf7d0; color: #059669; }
.risk-card-icon  { font-size: 28px; }
.risk-card-label { font-size: 14px; opacity: 0.75; font-weight: 500; display: block; margin-bottom: 2px; }
.risk-card-level { font-size: 22px; font-weight: 800; }
.risk-card-score { margin-left: auto; font-size: 38px; font-weight: 800; opacity: 0.9; }

/* ─── Typography ─── */
h2 {
    font-size: 22px !important; font-weight: 700 !important; color: var(--text-primary) !important;
    border-bottom: 1px solid var(--border-subtle) !important; padding-bottom: 0.5rem !important;
    margin-bottom: 0.8rem !important;
}
h3 { font-size: 18px !important; font-weight: 600 !important; color: var(--text-secondary) !important; }
.stCaption, [data-testid="caption"] { color: var(--text-muted) !important; font-size: 14px !important; }

/* ─── DataFrames / Maps ─── */
[data-testid="stDataFrame"] { border-radius: var(--radius-md) !important; border: 1px solid var(--border-subtle) !important; }
[data-testid="stDeckGlJsonChart"], [data-testid="stMap"] { border-radius: var(--radius-lg) !important; border: 1px solid var(--border-subtle) !important; }

/* ─── Misc ─── */
[data-testid="stAlert"] { border-radius: var(--radius-md) !important; font-size: 16px !important; }
hr { border: none !important; height: 1px !important; background: var(--border-subtle) !important; margin: 1.5rem 0 !important; }
.stProgress > div > div > div > div { background: #0d9488 !important; border-radius: 99px !important; }
[data-testid="stSlider"] > div > div > div:not([data-testid]) { background: #0d9488 !important; }
[data-testid="stTickBarMin"],
[data-testid="stTickBarMax"] {
    background: transparent !important;
    background-color: transparent !important;
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
}
[data-testid="stDownloadButton"] > button {
    background: rgba(13,148,136,0.1) !important; border: 1px solid rgba(13,148,136,0.3) !important;
    color: #0d9488 !important; font-weight: 600 !important;
}
.stCheckbox label { color: var(--text-secondary) !important; font-size: 16px !important; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f3f4f6; }
::-webkit-scrollbar-thumb { background: rgba(13,148,136,0.3); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(13,148,136,0.55); }
</style>
""")


# ══════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════
def main() -> None:
    st.set_page_config(
        page_title="交通風險 NLP 問答系統",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_nlp_styles()

    with st.sidebar:
        st.html("""
        <div class="sidebar-logo">
            <div class="sidebar-icon">💬</div>
            <div class="sidebar-brand">
                <div class="sidebar-brand-name">NLP 問答系統</div>
                <div class="sidebar-brand-sub">台中市交通風險自然語言介面</div>
            </div>
        </div>
        """)
        st.html('<div class="sidebar-section-label">系統能力</div>')
        st.html("""
        <div class="sidebar-hint">
            以口語中文提問，系統自動完成：<br>
            • 意圖辨識（規則 + LLM）<br>
            • 實體擷取（地區／時段／天候）<br>
            • 工具路由 &amp; 資料查詢<br>
            • BM25 RAG 知識庫檢索<br>
            • LLM 生成自然語言回答
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
            智慧決策支援系統請執行<br>
            <code style="background:rgba(255,255,255,0.1);padding:1px 4px;border-radius:4px;">
            streamlit run app_idss.py</code>
        </div>
        """)

    _render_question_page(show_debug)


if __name__ == "__main__":
    main()
