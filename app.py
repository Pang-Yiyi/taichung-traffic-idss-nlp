"""Streamlit demo for the traffic accident LLM/Agent system."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

try:
    from streamlit_autorefresh import st_autorefresh
    _AUTOREFRESH_OK = True
except ImportError:
    _AUTOREFRESH_OK = False

import pandas as pd
import streamlit as st

from agents import run_agent_pipeline
from advanced_analysis_tools import build_segment_hotspots, export_markdown_report
from analysis_tools import citizen_route_advice_tool
from data_loader import get_data_summary, load_accident_data
from external_api_tools import fetch_cwa_weather_tool, fetch_osrm_route_tool, fetch_tdx_traffic_tool


BASE_DIR = Path(__file__).resolve().parent
CHART_FILES = [
    BASE_DIR / "charts" / "hourly_accidents.png",
    BASE_DIR / "charts" / "weekly_accidents.png",
    BASE_DIR / "charts" / "monthly_accidents.png",
    BASE_DIR / "charts" / "district_accidents.png",
    BASE_DIR / "charts" / "main_causes.png",
    BASE_DIR / "charts" / "weather_accidents.png",
    BASE_DIR / "charts" / "alcohol_accidents.png",
    BASE_DIR / "charts" / "hourly_regression.png",
    BASE_DIR / "charts" / "weather_hour_heatmap.png",
    BASE_DIR / "Figure_1.png",
    BASE_DIR / "Figure_2.png",
    BASE_DIR / "Figure_3.png",
    BASE_DIR / "Figure_4.png",
    BASE_DIR / "Figure_5.png",
    BASE_DIR / "Figure_6.png",
    BASE_DIR / "Figure_7.png",
    BASE_DIR / "Figure_8.png",
    BASE_DIR / "Figure_9.png",
]

DEMO_QUESTIONS = {
    "🔴 風險預測 ─ 西屯區晚上六點雨天":      "西屯區星期五晚上六點雨天危險嗎？",
    "📍 熱點查詢 ─ 哪個行政區事故最多":      "台中市哪個行政區事故最多？",
    "⏰ 時段查詢 ─ 什麼時間最容易發生事故":   "什麼時間最容易發生交通事故？",
    "🔍 肇因分析 ─ 最常見肇事原因":          "最常見肇事原因是什麼？",
    "🌧️ 熱點查詢 ─ 雨天事故統計":           "雨天是否比較容易發生事故？",
    "📋 政策建議 ─ 交通局視角":             "如果我是交通局，應該優先改善哪些問題？",
    "🔍 肇因分析 ─ 西屯區外在因素":          "西屯區事故多，是否可能和車流量、通勤人口或商圈有關？",
    "📖 代碼說明 ─ 肇事因素代碼 07":         "肇事因素代碼 07 是什麼？",
    "🚫 超出範圍 ─ 台北市（系統邊界展示）":   "台北市事故熱點如何？",
    "🚫 超出範圍 ─ 未來事故（系統邊界展示）": "明天早上會不會出車禍？",
}

# 時段標籤（供 selectbox format_func 使用）
_HOUR_LABELS = {
    0: "深夜", 1: "深夜", 2: "深夜", 3: "深夜", 4: "深夜",
    5: "清晨", 6: "清晨",
    7: "上班尖峰", 8: "上班尖峰",
    9: "早上", 10: "早上", 11: "早上",
    12: "中午",
    13: "下午", 14: "下午", 15: "下午", 16: "下午",
    17: "下班尖峰", 18: "下班尖峰",
    19: "晚上", 20: "晚上", 21: "晚上",
    22: "深夜", 23: "深夜",
}

def _fmt_hour(x):
    if x == "不指定":
        return "不指定"
    return f"{x}時（{_HOUR_LABELS.get(x, '')}）"

# EDA 圖表中文說明
_CHART_CAPTIONS = {
    "hourly_accidents.png":      "每小時事故分布",
    "weekly_accidents.png":      "每週（星期）事故分布",
    "monthly_accidents.png":     "每月事故分布",
    "district_accidents.png":    "行政區事故排名 Top 10",
    "main_causes.png":           "主要肇事因素 Top 10",
    "weather_accidents.png":     "天候與事故數量關係",
    "alcohol_accidents.png":     "飲酒情形分析",
    "hourly_regression.png":     "時段事故迴歸分析",
    "weather_hour_heatmap.png":  "天候 × 時段熱力圖",
}

_CHART_DECISION_USE = {
    "hourly_accidents.png":      "判斷哪些時段應避開或加強勤務。",
    "weekly_accidents.png":      "比較平日、週末事故差異，支援排班與宣導規劃。",
    "monthly_accidents.png":     "觀察月份與季節性變化，支援中長期政策規劃。",
    "district_accidents.png":    "找出事故集中行政區，支援優先改善排序。",
    "main_causes.png":           "確認主要肇因，支援宣導、執法與工程改善方向。",
    "weather_accidents.png":     "比較不同天候事故量，支援天候警示與出行提醒。",
    "alcohol_accidents.png":     "檢視酒駕相關風險，支援取締與宣導策略。",
    "hourly_regression.png":     "觀察時段趨勢，支援尖峰風險解釋。",
    "weather_hour_heatmap.png":  "同時比較天候與時段交互風險，支援複合情境判斷。",
}

DISTRICT_OPTIONS = [
    "不指定",
    # 市區
    "中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區",
    # 山線
    "豐原區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "潭子區",
    "大雅區", "神岡區",
    # 屯區/海線
    "大肚區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區",
    # 大台中
    "大里區", "太平區", "烏日區", "霧峰區",
]
WEEKDAY_OPTIONS = ["不指定", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
WEATHER_OPTIONS = ["不指定", "晴", "雨", "陰", "霧", "風", "風沙", "雪"]
ROLE_OPTIONS = ["一般民眾", "公家單位（交通局/警察/工程）"]


def _apply_app_styles() -> None:
    # ── Google Fonts ────────────────────────────────────────────────
    st.html(
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;600;700'
        '&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
    )
    # ── 全域 CSS 設計系統 ────────────────────────────────────────────
    st.html("""
<style>
/* ══════════════════════════════════════════════════
   設計系統 token
══════════════════════════════════════════════════ */
:root {
    --bg-base:        #1e293b;
    --bg-elevated:    #273549;
    --bg-glass:       rgba(255,255,255,0.07);
    --bg-glass-hover: rgba(255,255,255,0.12);
    --border-subtle:  rgba(255,255,255,0.12);
    --border-medium:  rgba(255,255,255,0.2);
    --border-accent:  rgba(96,165,250,0.5);

    --text-primary:   #f1f5f9;
    --text-secondary: #cbd5e1;
    --text-muted:     #94a3b8;

    --accent-blue:      #60a5fa;
    --accent-blue-glow: rgba(96,165,250,0.3);
    --accent-indigo:    #818cf8;
    --accent-cyan:      #22d3ee;

    --risk-high:     #f87171;
    --risk-high-glow:rgba(248,113,113,0.3);
    --risk-mid:      #fb923c;
    --risk-mid-glow: rgba(251,146,60,0.3);
    --risk-low:      #4ade80;
    --risk-low-glow: rgba(74,222,128,0.3);

    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-lg: 18px;
    --radius-xl: 24px;

    --shadow-glass: 0 8px 32px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.08);
    --shadow-card:  0 4px 24px rgba(0,0,0,0.2);
    --shadow-glow:  0 0 20px var(--accent-blue-glow);
    --transition:   0.22s cubic-bezier(0.4,0,0.2,1);
}

/* ─── Global & Fonts ─── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: var(--bg-base) !important;
    color: var(--text-primary) !important;
}
.block-container {
    padding-top: 1.5rem !important;
    max-width: 1420px !important;
}

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #253550 0%, #1e2d45 100%) !important;
    border-right: 1px solid var(--border-subtle) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}
.sidebar-logo {
    display: flex; align-items: center; gap: 12px;
    padding: 0.6rem 0.2rem 1.2rem;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1.2rem;
}
.sidebar-icon { font-size: 32px; line-height: 1; filter: drop-shadow(0 0 8px rgba(59,130,246,0.5)); }
.sidebar-brand-name {
    font-size: 18px; font-weight: 700; letter-spacing: 0.02em;
    background: linear-gradient(90deg, #60a5fa, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.sidebar-brand-sub { font-size: 11px; color: var(--text-muted); margin-top: 1px; letter-spacing: 0.04em; }
.sidebar-section-label {
    font-size: 11px; font-weight: 600; color: var(--text-muted);
    letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.5rem;
}
.sidebar-hint {
    font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-top: 0.5rem;
    padding: 0.6rem 0.8rem; background: var(--bg-glass);
    border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);
}
.sidebar-divider { height: 1px; background: var(--border-subtle); margin: 1rem 0; }
.sidebar-stats { display: flex; flex-direction: column; gap: 0.5rem; }
.sidebar-stat-item {
    display: flex; flex-direction: column; gap: 2px;
    padding: 0.5rem 0.7rem; background: var(--bg-glass);
    border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);
}
.sidebar-stat-label { font-size: 11px; color: var(--text-muted); }
.sidebar-stat-value { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.sidebar-stat-highlight { color: var(--accent-blue) !important; font-weight: 700; }

/* ─── Radio ─── */
.stRadio > div { gap: 0.4rem !important; }
.stRadio label {
    padding: 0.5rem 0.75rem !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-subtle) !important;
    background: var(--bg-glass) !important;
    color: var(--text-secondary) !important;
    transition: all var(--transition) !important;
    cursor: pointer !important;
}
.stRadio label:hover {
    border-color: var(--accent-blue) !important;
    background: var(--bg-glass-hover) !important;
    color: var(--text-primary) !important;
}

/* ─── Hero Section ─── */
.nlp-hero {
    padding: 1.4rem 0 1.2rem 0;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1.2rem;
    position: relative;
}
.nlp-hero::before {
    content: '';
    position: absolute; top: 0; left: -2rem; right: -2rem;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent-blue), var(--accent-indigo), transparent);
    border-radius: 99px;
}
.nlp-title {
    font-size: 36px; line-height: 1.2; font-weight: 800;
    margin: 0 0 0.4rem 0; letter-spacing: -0.02em;
    background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.nlp-subtitle { font-size: 15px; line-height: 1.7; color: var(--text-muted); margin: 0; }
.nlp-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(99,102,241,0.1));
    border: 1px solid rgba(59,130,246,0.3);
    color: #93c5fd; border-radius: 999px;
    padding: 0.2rem 0.7rem; font-size: 12px; font-weight: 500;
    margin-bottom: 0.8rem; letter-spacing: 0.03em;
}

/* ─── Glass Card ─── */
.glass-card {
    background: var(--bg-glass); border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg); padding: 1.2rem 1.4rem;
    backdrop-filter: blur(12px); box-shadow: var(--shadow-glass);
    transition: all var(--transition);
}
.glass-card:hover {
    border-color: var(--border-accent);
    box-shadow: var(--shadow-glass), var(--shadow-glow);
    transform: translateY(-2px);
}

/* ─── Chat Messages ─── */
.stChatMessage {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    padding: 0.85rem 1rem !important;
    backdrop-filter: blur(8px);
    animation: slideInUp 0.3s cubic-bezier(0.4,0,0.2,1);
}
@keyframes slideInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.stChatMessage p, .stChatMessage li {
    font-size: 16px; line-height: 1.75; color: var(--text-primary) !important;
}
[data-testid="stChatMessageContent"] { background: transparent !important; }

/* ─── Buttons ─── */
.stButton > button {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-medium) !important;
    background: var(--bg-glass) !important;
    color: var(--text-secondary) !important;
    font-size: 14px !important;
    font-family: 'Inter', 'Noto Sans TC', sans-serif !important;
    font-weight: 500 !important;
    transition: all var(--transition) !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    border-color: var(--accent-blue) !important;
    background: rgba(59,130,246,0.12) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 0 16px var(--accent-blue-glow) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
    border: none !important; color: #fff !important;
    box-shadow: 0 4px 15px rgba(59,130,246,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
    box-shadow: 0 4px 25px rgba(59,130,246,0.5) !important;
    transform: translateY(-2px) !important;
}

/* ─── Metrics ─── */
[data-testid="metric-container"] {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem 1rem 0.8rem !important;
    transition: all var(--transition);
}
[data-testid="metric-container"]:hover {
    border-color: var(--border-accent) !important;
    box-shadow: var(--shadow-glow) !important;
    transform: translateY(-2px);
}
[data-testid="metric-container"] label {
    font-size: 12px !important; font-weight: 600 !important;
    color: var(--text-muted) !important; letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 700 !important; color: var(--text-primary) !important; }
[data-testid="stMetricDelta"] { font-size: 13px !important; }

/* ─── Expanders ─── */
div[data-testid="stExpander"] {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden;
}
div[data-testid="stExpander"]:hover { border-color: var(--border-medium) !important; }
div[data-testid="stExpander"] summary {
    padding: 0.75rem 1rem !important; color: var(--text-secondary) !important;
    font-weight: 500 !important; font-size: 14px !important;
}
div[data-testid="stExpander"] summary:hover { color: var(--text-primary) !important; }

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-glass) !important; border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-subtle) !important; padding: 4px !important; gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--text-muted) !important;
    border-radius: var(--radius-sm) !important; font-size: 14px !important;
    font-weight: 500 !important; transition: all var(--transition) !important; padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(59,130,246,0.25), rgba(99,102,241,0.2)) !important;
    color: #93c5fd !important; box-shadow: none !important;
}
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding-top: 1rem !important; }

/* ─── Selectbox / Input ─── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important; font-size: 14px !important;
}
.stSelectbox > div > div:hover,
.stTextInput > div > div > input:hover { border-color: var(--accent-blue) !important; }
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px var(--accent-blue-glow) !important;
}

/* ─── Chat Input ─── */
[data-testid="stChatInputTextArea"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--radius-lg) !important;
    color: var(--text-primary) !important; font-size: 15px !important;
}
[data-testid="stChatInputTextArea"]:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px var(--accent-blue-glow) !important;
}
.stChatInputContainer {
    background: var(--bg-elevated) !important;
    border-top: 1px solid var(--border-subtle) !important; padding: 0.75rem !important;
}

/* ─── DataFrames ─── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-md) !important; overflow: hidden;
    border: 1px solid var(--border-subtle) !important;
}

/* ─── Alerts ─── */
[data-testid="stAlert"] { border-radius: var(--radius-md) !important; border-width: 1px !important; font-size: 14px !important; }

/* ─── Progress bar ─── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-indigo)) !important;
    border-radius: 99px !important;
}
.stProgress > div > div { background: var(--bg-elevated) !important; border-radius: 99px !important; }

/* ─── Slider ─── */
[data-testid="stSlider"] > div > div > div:not([data-testid]) {
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-indigo)) !important;
}
[data-testid="stTickBarMin"],
[data-testid="stTickBarMax"] {
    background: transparent !important;
    background-color: transparent !important;
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
}

/* ─── Divider ─── */
hr {
    border: none !important; height: 1px !important;
    background: var(--border-subtle) !important; margin: 1.5rem 0 !important;
}

/* ─── NLP Components ─── */
.nlp-panel-title { font-size: 18px; font-weight: 700; color: var(--text-primary); margin: 0.1rem 0 0.5rem 0; letter-spacing: -0.01em; }
.nlp-panel-note { font-size: 14px; color: var(--text-muted); line-height: 1.6; margin-bottom: 0.6rem; }
.nlp-flow-step { border-left: 3px solid var(--accent-blue); padding: 0.2rem 0 0.6rem 0.8rem; margin: 0.15rem 0 0.3rem 0; }
.nlp-flow-label { color: var(--text-muted); font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.05rem; }
.nlp-flow-value { color: var(--text-primary); font-size: 15px; font-weight: 600; line-height: 1.5; }
.nlp-empty {
    border: 1px dashed var(--border-medium); border-radius: var(--radius-md);
    padding: 1.2rem 1.4rem; color: var(--text-muted);
    background: var(--bg-glass); font-size: 15px; line-height: 1.7; text-align: center;
}

/* ─── Risk Badge ─── */
.risk-card {
    border-radius: var(--radius-md); padding: 1rem 1.4rem; margin-bottom: 0.8rem;
    display: flex; align-items: center; gap: 1rem; font-weight: 600;
}
.risk-card-high { background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05)); border: 1px solid rgba(239,68,68,0.4); color: #fca5a5; }
.risk-card-mid  { background: linear-gradient(135deg, rgba(249,115,22,0.15), rgba(249,115,22,0.05)); border: 1px solid rgba(249,115,22,0.4); color: #fdba74; }
.risk-card-low  { background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05)); border: 1px solid rgba(34,197,94,0.4); color: #86efac; }
.risk-card-icon { font-size: 28px; }
.risk-card-label { font-size: 13px; opacity: 0.75; font-weight: 500; display: block; margin-bottom: 2px; }
.risk-card-level { font-size: 20px; font-weight: 800; letter-spacing: -0.02em; }
.risk-card-score { margin-left: auto; font-size: 36px; font-weight: 800; opacity: 0.9; letter-spacing: -0.04em; }

/* ─── Headings ─── */
h2 {
    font-size: 20px !important; font-weight: 700 !important; color: var(--text-primary) !important;
    letter-spacing: -0.01em !important; padding-bottom: 0.5rem !important;
    border-bottom: 1px solid var(--border-subtle) !important; margin-bottom: 0.8rem !important;
}
h3 { font-size: 17px !important; font-weight: 600 !important; color: var(--text-secondary) !important; }

/* ─── Caption ─── */
.stCaption, [data-testid="caption"] { color: var(--text-muted) !important; font-size: 12.5px !important; }

/* ─── Map ─── */
[data-testid="stDeckGlJsonChart"], [data-testid="stMap"] {
    border-radius: var(--radius-lg) !important; overflow: hidden;
    border: 1px solid var(--border-subtle) !important;
}

/* ─── Download Button ─── */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.15)) !important;
    border: 1px solid rgba(59,130,246,0.4) !important;
    color: #93c5fd !important; font-weight: 600 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, rgba(59,130,246,0.35), rgba(99,102,241,0.25)) !important;
    box-shadow: 0 0 20px rgba(59,130,246,0.3) !important;
}

/* ─── Checkbox ─── */
.stCheckbox label { color: var(--text-secondary) !important; font-size: 14px !important; }

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-elevated); }
::-webkit-scrollbar-thumb { background: rgba(59,130,246,0.3); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(59,130,246,0.55); }

/* ══════════════════════════════════════════════════
   Light refinement override
   讓介面回到明亮、柔和、乾淨的聊天工具感
══════════════════════════════════════════════════ */
:root {
    --bg-base:        #fbfcfb;
    --bg-elevated:    #ffffff;
    --bg-glass:       #ffffff;
    --bg-glass-hover: #f4f8f7;
    --border-subtle:  #e3e8e5;
    --border-medium:  #cfd9d5;
    --border-accent:  #9ab7c8;

    --text-primary:   #24313a;
    --text-secondary: #43535d;
    --text-muted:     #718079;

    --accent-blue:      #6f99b3;
    --accent-blue-glow: rgba(111,153,179,0.16);
    --accent-indigo:    #7c92b6;
    --accent-cyan:      #83b8b2;

    --shadow-glass: 0 8px 26px rgba(43,61,74,0.06);
    --shadow-card:  0 4px 18px rgba(43,61,74,0.08);
    --shadow-glow:  0 0 0 3px rgba(111,153,179,0.13);
}

.stApp {
    background:
        linear-gradient(180deg, #ffffff 0%, #fafcfb 45%, #f6f9f7 100%) !important;
}
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 5rem !important;
}

header[data-testid="stHeader"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
.stAppHeader,
.stDecoration {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    color: var(--text-primary) !important;
}
header[data-testid="stHeader"]::before,
[data-testid="stHeader"]::before {
    background: transparent !important;
}
#MainMenu,
footer {
    visibility: hidden !important;
}

section[data-testid="stSidebar"] {
    background: #f7faf8 !important;
    border-right: 1px solid var(--border-subtle) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--text-secondary) !important;
}
.sidebar-logo {
    border-bottom: 1px solid var(--border-subtle) !important;
}
.sidebar-icon {
    filter: none !important;
}
.sidebar-brand-name {
    background: none !important;
    -webkit-text-fill-color: var(--text-primary) !important;
    color: var(--text-primary) !important;
}
.sidebar-brand-sub,
.sidebar-section-label,
.sidebar-hint,
.sidebar-stat-label {
    color: var(--text-muted) !important;
}
.sidebar-hint,
.sidebar-stat-item {
    background: rgba(255,255,255,0.72) !important;
    border-color: var(--border-subtle) !important;
}
.sidebar-stat-value {
    color: var(--text-secondary) !important;
}

.stRadio label {
    background: #ffffff !important;
    color: var(--text-secondary) !important;
    border-color: var(--border-subtle) !important;
}
.stRadio label span {
    color: var(--text-secondary) !important;
}
.stRadio label:hover {
    background: #f7fbfa !important;
    border-color: var(--border-accent) !important;
    color: var(--text-primary) !important;
}
.stRadio label:hover span {
    color: var(--text-primary) !important;
}

.nlp-hero {
    padding: 1rem 0 0.9rem 0 !important;
    border-bottom-color: var(--border-subtle) !important;
}
.nlp-hero::before {
    height: 2px !important;
    background: linear-gradient(90deg, transparent, #9ab7c8, #a7c3b8, transparent) !important;
    opacity: 0.75 !important;
}
.nlp-title {
    background: none !important;
    -webkit-text-fill-color: #1f2f3a !important;
    color: #1f2f3a !important;
    font-size: 42px !important;
    letter-spacing: -0.01em !important;
}
.nlp-subtitle {
    color: #596b72 !important;
    font-size: 18px !important;
}
.nlp-badge {
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.45rem !important;
    background: transparent !important;
    border: 0 !important;
    border-radius: 0 !important;
    color: #6a7f7a !important;
    padding: 0 !important;
    margin-bottom: 0.65rem !important;
    font-size: 13px !important;
    font-weight: 650 !important;
    letter-spacing: 0.02em !important;
}
.nlp-badge::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #9fbfb7;
    box-shadow: 0 0 0 4px #eaf4f1;
}

.stChatMessage {
    background: #ffffff !important;
    border-color: var(--border-subtle) !important;
    border-radius: 10px !important;
    box-shadow: 0 5px 18px rgba(43,61,74,0.055) !important;
    backdrop-filter: none !important;
}
.stChatMessage p,
.stChatMessage li {
    color: var(--text-primary) !important;
    font-size: 17px !important;
}

.stButton > button {
    background: #ffffff !important;
    color: var(--text-secondary) !important;
    border-color: var(--border-medium) !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    background: #f5faf8 !important;
    color: var(--text-primary) !important;
    border-color: var(--border-accent) !important;
    box-shadow: 0 3px 12px rgba(43,61,74,0.08) !important;
}

div[data-testid="stExpander"],
[data-testid="metric-container"],
.glass-card {
    background: #ffffff !important;
    border-color: var(--border-subtle) !important;
    box-shadow: var(--shadow-glass) !important;
    backdrop-filter: none !important;
}
div[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important;
    border-color: var(--border-subtle) !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
}
.stTabs [aria-selected="true"] {
    background: #edf5f3 !important;
    color: var(--text-primary) !important;
}

.stSelectbox > div > div,
.stTextInput > div > div > input,
[data-testid="stChatInputTextArea"] {
    background: #fbfdfc !important;
    border: 1px solid #d6e1dc !important;
    border-radius: 18px !important;
    color: var(--text-primary) !important;
    box-shadow: 0 3px 14px rgba(43,61,74,0.055) !important;
    min-height: 44px !important;
    overflow: hidden !important;
}
[data-testid="stChatInputTextArea"] > div,
[data-testid="stChatInputTextArea"] div,
[data-testid="stChatInputTextArea"] [data-baseweb="textarea"] {
    background: transparent !important;
    border: 0 !important;
    border-radius: 18px !important;
    box-shadow: none !important;
    overflow: hidden !important;
}
[data-testid="stChatInputTextArea"] textarea,
[data-testid="stChatInputTextArea"] textarea::placeholder,
textarea::placeholder,
input::placeholder {
    color: #8b9aa0 !important;
    opacity: 1 !important;
}
[data-testid="stChatInputTextArea"] textarea {
    background: transparent !important;
    border: 0 !important;
    color: #263640 !important;
    caret-color: #52736f !important;
    font-size: 15px !important;
    line-height: 1.45 !important;
    padding: 0.68rem 3.1rem 0.68rem 1rem !important;
    min-height: 42px !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInputTextArea"]:focus,
[data-testid="stChatInputTextArea"]:focus-within,
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
    border-color: #9fbfb7 !important;
    box-shadow: 0 0 0 3px rgba(159,191,183,0.18), 0 3px 14px rgba(43,61,74,0.055) !important;
}
/* 底部輸入框：固定釘在底部，乾淨簡潔 */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stChatInput"],
[data-testid="stChatFloatingInputContainer"],
.stChatInputContainer {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border-top: 1px solid #e8eeeb !important;
    box-shadow: none !important;
    color: var(--text-primary) !important;
}
[data-testid="stBottom"],
.stChatInputContainer {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 999999 !important;
}
[data-testid="stToolbarActions"],
[data-testid="stStatusWidget"],
[data-testid="stMainMenu"],
[data-testid="stDeployButton"],
[data-testid="stBaseButton-header"] {
    background: #ffffff !important;
    color: var(--text-secondary) !important;
}
[data-testid="stChatInput"] button,
[data-testid="stChatInput"] [role="button"],
[data-testid="stChatInputSubmitButton"] {
    color: #7d9399 !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] button:hover,
[data-testid="stChatInput"] [role="button"]:hover,
[data-testid="stChatInputSubmitButton"]:hover {
    color: #4f7470 !important;
    background: #edf6f3 !important;
}
[data-testid="stChatInput"] button svg,
[data-testid="stChatInput"] [role="button"] svg,
[data-testid="stChatInputSubmitButton"] svg {
    fill: #7d9399 !important;
    color: #7d9399 !important;
}
[data-testid="stChatInput"] button:hover svg,
[data-testid="stChatInput"] [role="button"]:hover svg,
[data-testid="stChatInputSubmitButton"]:hover svg {
    fill: #4f7470 !important;
    color: #4f7470 !important;
}
[data-testid="stAlert"],
[data-testid="stAlert"] *,
.stAlert,
.stAlert * {
    color: #3f2d2d !important;
}
[data-testid="stAlert"] {
    background: #fff4f2 !important;
    border-color: #efc9c2 !important;
}

.nlp-empty {
    background: #ffffff !important;
    color: var(--text-muted) !important;
    border-color: var(--border-medium) !important;
}
.nlp-panel-title {
    color: var(--text-primary) !important;
}
.nlp-panel-note,
.stCaption,
[data-testid="caption"] {
    color: var(--text-muted) !important;
}

h2, h3 {
    color: var(--text-primary) !important;
    border-bottom-color: var(--border-subtle) !important;
}

::-webkit-scrollbar-track { background: #f4f7f5; }
::-webkit-scrollbar-thumb { background: #c9d8d2; }
::-webkit-scrollbar-thumb:hover { background: #a9c1b8; }
</style>
""")


def main() -> None:
    st.set_page_config(
        page_title="台中市交通事故風險決策支援系統",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_app_styles()

    with st.sidebar:
        st.html(
            """
            <div class="sidebar-logo">
                <div class="sidebar-icon">🚦</div>
                <div class="sidebar-brand">
                    <div class="sidebar-brand-name">TrafficAI</div>
                    <div class="sidebar-brand-sub">台中市交通風險系統</div>
                </div>
            </div>
            """
        )
        st.html('<div class="sidebar-section-label">系統模式</div>')
        system_mode = st.radio(
            "選擇展示介面",
            ["自然語言處理系統", "智慧決策支援系統"],
            label_visibility="collapsed",
        )
        st.html('<div class="sidebar-hint">NLP：語言理解 · RAG · LLM 回答<br>IDSS：風險預測 · 熱點 · 決策建議</div>')

        # 資料時間範圍提示
        try:
            summary = get_data_summary()
            st.html('<div class="sidebar-divider"></div>')
            st.html(
                f"""
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
                        <span class="sidebar-stat-label">📆 資料年份</span>
                        <span class="sidebar-stat-value">{summary['year_range_str']}</span>
                    </div>
                    <div class="sidebar-stat-item">
                        <span class="sidebar-stat-label">🗂️ 總事故筆數</span>
                        <span class="sidebar-stat-value sidebar-stat-highlight">{summary['total_count']:,} 件</span>
                    </div>
                </div>
                """
            )
        except Exception:
            pass

        st.html('<div class="sidebar-divider"></div>')
        show_debug = st.checkbox("顯示進階除錯資訊", value=False)

    if system_mode == "自然語言處理系統":
        _render_question_page(show_debug)
    else:
        st.session_state["_nlp_layout"] = False
        st.html(
            """
            <div class="nlp-hero">
              <div class="nlp-badge">智慧決策支援系統</div>
              <div class="nlp-title">台中市交通事故智慧決策支援系統</div>
              <p class="nlp-subtitle">以歷史事故資料、預測模型、熱點分析與處方性建議支援交通安全決策。</p>
            </div>
            """
        )
        page_citizen, page_analysis = st.tabs(["民眾出行輔助", "決策分析"])
        with page_citizen:
            _render_citizen_route_page()
        with page_analysis:
            _render_analysis_page(st.session_state.get("pipeline_result"))


def _get_realtime_context() -> dict:
    """取得現在時間（每次即時）+ CWA 即時天氣（快取 10 分鐘）。

    時間永遠即時計算，不快取；天氣資料才快取以減少 API 呼叫。
    """
    # 時間：永遠取即時值
    now = datetime.now()
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    # 天氣 + 車流：快取 10 分鐘（車流自身另有 3 分鐘內部快取）
    cache = st.session_state.get("_rt_cache")
    if cache and time.time() - cache["ts"] < 600:
        weather_result = cache["weather_result"]
        traffic_result = cache.get("traffic_result", {})
    else:
        weather_result = fetch_cwa_weather_tool(None)
        traffic_result = fetch_tdx_traffic_tool(None)
        st.session_state["_rt_cache"] = {
            "ts": time.time(),
            "weather_result": weather_result,
            "traffic_result": traffic_result,
        }

    weather_data = weather_result.get("weather") or {}

    # 即時車流不可用（資料源未更新）→ 用歷史時段密度推估
    traffic_is_estimate = False
    if not traffic_result.get("available"):
        from external_api_tools import estimate_hourly_traffic
        est = estimate_hourly_traffic(now.hour)
        if est.get("available"):
            traffic_result = est
            traffic_is_estimate = True

    return {
        "datetime_str": now.strftime("%Y-%m-%d %H:%M"),
        "hour": now.hour,
        "hour_label": _HOUR_LABELS.get(now.hour, ""),
        "weekday": weekday_names[now.weekday()],
        "weather_available": weather_result.get("available", False),
        "weather_summary": weather_result.get("summary", ""),
        "weather_condition": weather_data.get("weather", ""),
        "temperature": weather_data.get("temperature", ""),
        "humidity": weather_data.get("humidity", ""),
        "traffic_available": traffic_result.get("available", False),
        "traffic_summary": traffic_result.get("summary", ""),
        "traffic_avg_speed": traffic_result.get("avg_speed"),
        "traffic_level": traffic_result.get("level", ""),
        "traffic_congested_ratio": traffic_result.get("congested_ratio"),
        "traffic_is_estimate": traffic_is_estimate,
    }


def _generate_followups(result: dict) -> list[str]:
    """根據當前意圖與實體，產生 2-3 個情境相關的引導提問。"""
    intent = result.get("intent", {}).get("intent", "")
    district = result.get("query", {}).get("district")

    if intent == "風險預測":
        if district:
            return [
                f"{district}最常見的肇事原因是什麼？",
                f"政府應如何改善{district}的交通安全？",
                f"{district}哪個時段事故最多？",
            ]
        return [
            "台中市哪個行政區事故最多？",
            "最常見的肇事原因是什麼？",
            "雨天事故比較多嗎？",
        ]
    if intent == "時段查詢":
        return [
            "哪個行政區在下班時段最危險？",
            "最常見的肇事原因是什麼？",
            "如果我是交通局，應優先改善哪些問題？",
        ]
    if intent == "事故熱點查詢":
        return [
            "事故最多的行政區主要肇因是什麼？",
            "如果我是交通局，應優先改善哪些問題？",
            "什麼時段事故最多？",
        ]
    if intent == "肇因分析":
        if district:
            return [
                f"{district}在什麼時段風險最高？",
                f"政府應如何針對{district}的肇因改善？",
                "如果我是交通局，應優先改善哪些問題？",
            ]
        return [
            "哪個行政區這個問題最嚴重？",
            "如果我是交通局，應優先處理哪些問題？",
            "事故代碼 07 是什麼意思？",
        ]
    if intent == "政策建議":
        return [
            "台中市哪個行政區最需要優先改善？",
            "下班時段的主要肇因是什麼？",
            "肇事因素代碼 07 是什麼？",
        ]
    if intent == "民眾出行建議":
        return [
            "雨天騎機車危險嗎？",
            "哪個時段出門最安全？",
            "台中市哪個行政區事故最多？",
        ]
    # 預設
    return [
        "台中市哪個行政區事故最多？",
        "什麼時間最容易發生交通事故？",
        "最常見的肇事原因是什麼？",
    ]


def _render_question_page(show_debug: bool) -> None:
    st.session_state["_nlp_layout"] = True
    # 即時 context 放最前面，後續所有地方都能使用
    rt = _get_realtime_context()

    st.html("""
        <div class="nlp-hero">
          <div class="nlp-badge">自然語言問答系統</div>
          <div class="nlp-title">自然語言交通風險問答系統</div>
          <p class="nlp-subtitle">用口語問題查詢台中交通事故風險、原因與出行建議。</p>
        </div>
        """)

    user_role = "一般民眾"

    # ── 即時背景資訊列（pill 樣式）────────────────────────────────
    _ps = (
        "display:inline-flex;align-items:center;gap:5px;"
        "background:#eef6f4;border:1px solid #d4e6e1;"
        "color:#52736f;border-radius:999px;padding:0.25rem 0.7rem;"
        "font-size:13px;font-weight:500;white-space:nowrap;"
    )
    time_pill = f"<span style='{_ps}'>🕐 {rt['datetime_str']}（{rt['weekday']} {rt['hour_label']}）</span>"
    if rt["weather_available"]:
        w = rt["weather_condition"] or ""
        t = f" {rt['temperature']}°C" if rt["temperature"] else ""
        h = f" 濕度{rt['humidity']}%" if rt["humidity"] else ""
        weather_pill = f"<span style='{_ps}'>🌤️ {w}{t}{h}</span>"
    else:
        weather_pill = f"<span style='{_ps}'>⛅ 天氣暫不可用</span>"
    if rt.get("traffic_available"):
        if rt.get("traffic_is_estimate"):
            traffic_pill = f"<span style='{_ps}'>🚗 {rt['traffic_level']}（推估）</span>"
        else:
            traffic_pill = f"<span style='{_ps}'>🚗 {rt['traffic_avg_speed']} km/h · {rt['traffic_level']}</span>"
    else:
        traffic_pill = ""
    st.html(f'<div style="display:flex;gap:0.45rem;flex-wrap:wrap;margin-bottom:0.6rem;">{time_pill}{weather_pill}{traffic_pill}</div>')

    with st.expander("範例問題", expanded=False):
        demo_items = list(DEMO_QUESTIONS.items())[:6]
        demo_cols = st.columns(2)
        for i, (label, question) in enumerate(demo_items):
            clean_label = label.split("─")[-1].strip()
            if demo_cols[i % 2].button(clean_label, key=f"nlp_demo_{i}", use_container_width=True):
                _process_chat_input(question, user_role, rt, show_debug)

    # ── 對話歷史 ───────────────────────────────────────────
    history = st.session_state.get("chat_history", [])
    latest_result = _get_latest_chat_result(history)

    chat_left, chat_center, chat_right = st.columns([0.08, 0.84, 0.08])
    with chat_center:
        top_cols = st.columns([0.78, 0.22])
        with top_cols[0]:
            st.html('<div class="nlp-panel-title">對話</div>')
            st.html('<div class="nlp-panel-note">輸入口語問題，系統會用簡短回答說明交通風險與建議。</div>')
        with top_cols[1]:
            if st.button("清除對話", use_container_width=True, key="clear_chat"):
                st.session_state["chat_history"] = []
                st.rerun()

        if not history:
            st.html('<div class="nlp-empty">請輸入問題，例如：西屯區星期五晚上六點雨天危險嗎？</div>')

        for msg in history:
            with st.chat_message(msg["role"]):
                if msg["role"] == "user":
                    st.markdown(f"**{msg['content']}**")
                else:
                    _render_chat_result(msg.get("result", {}), show_debug)

    # ── pending followup（引導按鈕點擊觸發）──────────────
    pending = st.session_state.pop("_pending_followup", None)
    if pending:
        _process_chat_input(pending, user_role, rt, show_debug)

    # ── 底部輸入框 ─────────────────────────────────────────
    user_input = st.chat_input("請輸入問題，例如：西屯區晚上六點雨天危險嗎？")
    if user_input:
        _process_chat_input(user_input, user_role, rt, show_debug)

    if show_debug:
        with st.expander("進階 NLP 技術細節與評估", expanded=False):
            _render_nlp_technical_tabs(latest_result)


def _get_latest_chat_result(history: list[dict]) -> dict | None:
    for msg in reversed(history):
        if msg.get("role") == "assistant" and msg.get("result"):
            return msg["result"]
    return None


def _render_nlp_process_panel(result: dict | None) -> None:
    st.html('<div class="nlp-panel-title">NLP 理解流程</div>')
    st.html('<div class="nlp-panel-note">顯示最近一次問題的理解重點。</div>')
    if not result:
        st.html('<div class="nlp-empty">尚無解析結果。送出問題後，這裡會顯示自然語言理解流程。</div>')
        return

    intent_info = result.get("intent", {})
    query = result.get("query", {})
    nlu_debug = result.get("nlu", {})
    llm_parse = nlu_debug.get("llm_parse") or {}
    tool_plan = result.get("tool_plan", [])
    source = intent_info.get("source", "rules")
    source_label = "本機 LLM" if source == "local_llm" else "規則式 NLU"

    confidence = llm_parse.get("confidence")
    source_text = source_label if confidence is None else f"{source_label} / {confidence:.2f}"
    _render_flow_step("Intent", intent_info.get("intent", "未知"))
    _render_flow_step("來源", source_text)

    entity_labels = {
        "district": "行政區",
        "origin_district": "起點",
        "destination_district": "終點",
        "weekday": "星期",
        "hour": "時段",
        "month": "月份",
        "weather": "天候",
        "transport_mode": "交通工具",
        "keyword": "關鍵詞",
    }
    entities = []
    for key, label in entity_labels.items():
        val = query.get(key)
        if val is not None and val != "" and val != "不指定":
            suffix = "時" if key == "hour" and isinstance(val, int) else ""
            entities.append(f"{label}: {val}{suffix}")
    _render_flow_step("Entities", "、".join(entities) if entities else "未擷取到明確條件")

    tool_labels = {
        "risk_score_tool": "風險預測",
        "accident_query_tool": "事故查詢",
        "weather_time_heatmap_tool": "天候時段分析",
        "cause_analysis_tool": "肇因分析",
        "recommendation_tool": "決策建議",
        "citizen_route_advice_tool": "出行建議",
        "rag_lookup_tool": "BM25 RAG",
    }
    plan_text = " → ".join(tool_labels.get(tool, tool) for tool in tool_plan) if tool_plan else "未呼叫工具"
    _render_flow_step("工具路由", plan_text)


def _render_flow_step(label: str, value: str) -> None:
    st.html(f"""
        <div class="nlp-flow-step">
          <div class="nlp-flow-label">{label}</div>
          <div class="nlp-flow-value">{value}</div>
        </div>
        """)


def _summarize_response_evidence(result: dict) -> str:
    tool_results = result.get("tool_results", {})
    evidence: list[str] = []
    risk = tool_results.get("risk_score_tool", {}).get("risk")
    if risk:
        evidence.append(f"{risk.get('level', '')} {risk.get('score', '')}分".strip())
    route = tool_results.get("citizen_route_advice_tool", {})
    if route.get("summary"):
        evidence.append("路線風險摘要")
    cause = tool_results.get("cause_analysis_tool", {})
    if cause.get("top_causes") or cause.get("combined_causes"):
        evidence.append("肇因統計")
    rag = tool_results.get("rag_lookup_tool", {})
    if rag.get("answer") or rag.get("results"):
        evidence.append("RAG 知識庫")
    if not evidence:
        intent = result.get("intent", {}).get("intent", "")
        return intent or "依查詢條件產生回答"
    return "、".join(evidence)


def _render_nlp_technical_tabs(result: dict | None) -> None:
    tabs = st.tabs(["NLU 解析", "RAG 檢索", "回答生成", "評估結果", "案例分析"])

    with tabs[0]:
        if result:
            _render_nlu_pipeline_inner(result)
        else:
            st.info("送出問題後會顯示 intent、entities、Rule/LLM 來源與工具路由。")

    with tabs[1]:
        _render_rag_technical_view(result)

    with tabs[2]:
        _render_generation_technical_view(result)

    with tabs[3]:
        _render_nlp_eval_overview()

    with tabs[4]:
        _render_nlp_case_overview()


def _render_rag_technical_view(result: dict | None) -> None:
    if not result:
        st.info("代碼或欄位說明類問題會觸發 BM25 RAG，例如：肇事因素代碼 07 是什麼？")
        return
    rag = result.get("tool_results", {}).get("rag_lookup_tool", {})
    if not rag:
        st.info("這次問題沒有觸發 RAG 檢索。可嘗試詢問「肇事因素代碼 07 是什麼？」")
        return
    if rag.get("expanded_terms"):
        st.write("查詢擴展詞")
        st.write("、".join(map(str, rag.get("expanded_terms", []))))
    if rag.get("answer"):
        st.write("檢索回答")
        st.markdown(rag["answer"])
    rows = rag.get("results") or rag.get("matches") or []
    if rows:
        st.write("Top-k 檢索結果")
        st.dataframe(pd.DataFrame(rows).head(5), hide_index=True, use_container_width=True)


def _render_generation_technical_view(result: dict | None) -> None:
    if not result:
        st.info("送出問題後會顯示回答生成結果與事實依據摘要。")
        return
    st.write("最終回答")
    st.markdown(result.get("response", "（無回答）"))
    st.write("事實依據摘要")
    st.info(_summarize_response_evidence(result), icon=None)
    thinking = result.get("llm_thinking", "")
    if thinking:
        with st.expander("模型思考內容（已收合）", expanded=False):
            st.markdown(thinking)


def _render_nlp_eval_overview() -> None:
    st.write("理解層評估採 30 題任務導向測試集，結果用於檢查 intent 與 entity 是否能覆蓋本專題定義的主要問句。")
    metrics = pd.DataFrame(
        [
            {"方法": "規則式 NLU", "Accuracy": "100.0%", "Macro-F1": "1.000", "說明": "任務導向測試集中的理解層結果"},
            {"方法": "本機 LLM（Qwen3 4B）", "Accuracy": "83.3%", "Macro-F1": "0.817", "說明": "單獨語義解析比較"},
        ]
    )
    st.dataframe(metrics, hide_index=True, use_container_width=True)
    st.caption("此數字不代表所有未知中文問句都能維持相同表現；生成層另以案例分析檢查自然度與可信度。")

    entity = pd.DataFrame(
        [
            {"實體欄位": "行政區", "測試題數": 8, "準確率": "100.0%"},
            {"實體欄位": "起點行政區", "測試題數": 2, "準確率": "100.0%"},
            {"實體欄位": "終點行政區", "測試題數": 2, "準確率": "100.0%"},
            {"實體欄位": "交通工具", "測試題數": 5, "準確率": "100.0%"},
            {"實體欄位": "天候", "測試題數": 7, "準確率": "100.0%"},
            {"實體欄位": "星期", "測試題數": 2, "準確率": "100.0%"},
            {"實體欄位": "時段（±1 小時）", "測試題數": 6, "準確率": "66.7%"},
        ]
    )
    st.write("實體擷取摘要")
    st.dataframe(entity, hide_index=True, use_container_width=True)


def _render_nlp_case_overview() -> None:
    success = pd.DataFrame(
        [
            {"類型": "條件式風險預測", "問句": "西屯區星期五晚上六點雨天危險嗎？", "成功原因": "行政區、星期、時段、天候皆可結構化"},
            {"類型": "地標路線建議", "問句": "現在從逢甲騎機車去火車站危險嗎？", "成功原因": "地標對應行政區並觸發路線模式"},
            {"類型": "代碼知識查詢", "問句": "肇事因素代碼07是什麼？", "成功原因": "BM25 RAG 可檢索代碼知識"},
        ]
    )
    st.write("成功案例")
    st.dataframe(success, hide_index=True, use_container_width=True)

    failures = pd.DataFrame(
        [
            {"問題": "路線問句被誤判為一般風險", "修正": "將「從X到Y」路線規則提前"},
            {"問題": "使用者指定條件卻混入現在天氣", "修正": "有明確條件就依條件，缺少條件才補現在"},
            {"問題": "起霧無法對應資料欄位", "修正": "將起霧、有霧、煙霧正規化為「霧或煙」"},
        ]
    )
    st.write("失敗案例與修正")
    st.dataframe(failures, hide_index=True, use_container_width=True)


def _render_analysis_page(result: dict | None) -> None:
    st.subheader("決策分析")
    st.caption("此頁獨立呈現地圖、熱點排序與 EDA 圖表，可作為公家單位的空間決策儀表板。")

    st.write("地圖篩選條件")
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        district = st.selectbox("分析行政區", DISTRICT_OPTIONS, key="analysis_district")
    with col_b:
        hour = st.selectbox("分析時段", ["不指定"] + list(range(24)),
                            format_func=_fmt_hour, key="analysis_hour")
    with col_c:
        weekday = st.selectbox("分析星期", WEEKDAY_OPTIONS, key="analysis_weekday")
    with col_d:
        month = st.selectbox("分析月份", ["不指定"] + list(range(1, 13)), key="analysis_month")
    with col_e:
        weather = st.selectbox("分析天候", WEATHER_OPTIONS, key="analysis_weather")

    query = {
        "district": district,
        "hour": hour,
        "weekday": weekday,
        "month": month,
        "weather": weather,
    }
    query = {key: value for key, value in query.items() if value not in (None, "", "不指定")}

    _render_weather_panel(query.get("district"))
    st.divider()
    segment_result = _render_decision_map({"query": query})
    st.divider()
    _render_weather_hour_heatmap(query)
    st.divider()
    _render_rf_model_insights()
    st.divider()
    _render_top_risk_combos()
    st.divider()
    _render_patrol_coverage()
    st.divider()
    _render_chart_gallery()
    st.divider()
    _render_report_export(
        title="台中市交通事故決策分析報告",
        query=query,
        pipeline_result=result,
        weather_result=st.session_state.get("weather_result"),
        segment_result=segment_result,
    )


def _render_citizen_route_page() -> None:
    st.subheader("民眾出行輔助")
    st.caption("此功能根據歷史事故資料提供出行風險提醒；目前不是完整導航或即時路線規劃。")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        origin = st.selectbox("起點行政區", DISTRICT_OPTIONS, index=1)
    with col_b:
        destination = st.selectbox("終點行政區", DISTRICT_OPTIONS, index=6)
    with col_c:
        route_hour = st.selectbox("出發時段", list(range(24)), index=18)
    with col_d:
        transport_mode = st.selectbox("交通工具", ["機車", "汽車", "行人", "自行車", "大眾運輸"])

    route_weather = st.selectbox("天候情境", ["晴", "雨", "陰", "霧", "風", "風沙", "雪"], index=1)

    if st.button("評估出行風險", type="primary", use_container_width=True):
        with st.spinner("評估中..."):
            route_advice = citizen_route_advice_tool(
                origin_district=None if origin == "不指定" else origin,
                destination_district=None if destination == "不指定" else destination,
                hour=route_hour,
                weather=route_weather,
                transport_mode=transport_mode,
            )
            route_result = fetch_osrm_route_tool(
                None if origin == "不指定" else origin,
                None if destination == "不指定" else destination,
            )
            weather_result = fetch_cwa_weather_tool(None if origin == "不指定" else origin)
        st.session_state["citizen_route_result"] = route_advice
        st.session_state["route_result"] = route_result
        st.session_state["weather_result"] = weather_result

    result = st.session_state.get("citizen_route_result")
    if not result:
        st.info("請選擇起點、終點、時段與天候後，按下「評估出行風險」開始分析。")
        return

    _render_citizen_route_result(result)
    _render_report_export(
        title="民眾出行風險提醒報告",
        query=result.get("query", {}),
        route_result=st.session_state.get("route_result"),
        weather_result=st.session_state.get("weather_result"),
    )


def _render_citizen_route_result(result: dict) -> None:
    risk = result.get("risk", {})
    _render_citizen_summary_cards(result)
    left, right = st.columns([0.8, 1.2])

    with left:
        st.metric("出行風險", risk.get("level", "未判定"), f"{risk.get('score', 0)} / 100")
        breakdown = risk.get("breakdown", {})
        if breakdown:
            st.write("風險組成")
            st.dataframe(
                pd.DataFrame(
                    [{"項目": key, "分數": value} for key, value in breakdown.items()]
                ),
                hide_index=True,
                use_container_width=True,
            )

    with right:
        st.write("主要風險因素")
        factors = result.get("factors") or ["目前沒有明顯高風險因素。"]
        for factor in factors:
            st.write(f"- {factor}")

    st.write("出行建議")
    for advice in result.get("advice", []):
        st.write(f"- {advice}")

    _render_action_levels("一般民眾", result.get("risk", {}).get("level"))
    _render_limitation_notice(result.get("limitation", ""))

    route_query = result.get("query", {})
    origin = route_query.get("origin_district")
    destination = route_query.get("destination_district")
    route_districts = [item for item in [origin, destination] if item]
    if route_districts:
        _render_route_map(route_districts, route_query)
        _render_route_api_result(st.session_state.get("route_result"))
    _render_weather_result(st.session_state.get("weather_result"))


def _render_route_map(route_districts: list[str], route_query: dict) -> None:
    st.subheader("起訖區域事故點位參考")
    try:
        map_df = _load_map_data()
    except Exception as exc:
        st.warning(f"目前無法載入地圖資料：{exc}")
        return

    filtered = map_df[map_df["區"].isin(route_districts)]
    if route_query.get("hour") is not None:
        filtered = filtered[filtered["hour"] == route_query["hour"]]
    if route_query.get("weather"):
        filtered = filtered[filtered["天候_str"] == route_query["weather"]]

    if filtered.empty:
        st.info("起訖行政區在此時段與天候條件下沒有可顯示的事故點位。")
        return

    sample_size = min(len(filtered), 3000)
    display_df = filtered.sample(sample_size, random_state=7) if len(filtered) > sample_size else filtered
    st.map(display_df[["lat", "lon"]], use_container_width=True)
    st.caption(f"顯示起訖行政區相關事故點位 {len(display_df):,} / {len(filtered):,} 筆。")


def _render_result(result: dict, show_debug: bool = False) -> None:
    st.subheader("分析結果")
    risk = result.get("tool_results", {}).get("risk_score_tool", {}).get("risk")
    _render_answer_summary_cards(result)
    if risk:
        _render_risk_badge(risk["level"], risk["score"])
    _render_severity_cards(result)
    st.markdown(result.get("response", ""))
    _render_nlu_pipeline(result)
    _render_role_action_guidance(result)

    if show_debug:
        with st.expander("進階除錯資訊", expanded=False):
            _render_tool_summaries(result.get("tool_results", {}))
            st.subheader("完整 Pipeline JSON")
            st.json(_json_safe(result))


def _process_chat_input(
    user_input: str,
    user_role: str,
    realtime_context: dict,
    show_debug: bool,
) -> None:
    """Pipeline 執行 + 對話歷史更新。"""
    history = st.session_state.setdefault("chat_history", [])
    history.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(f"**{user_input}**")

    with st.chat_message("assistant"):
        with st.spinner("AI 分析中..."):
            result = run_agent_pipeline(
                user_input,
                user_role=user_role,
                realtime_context=realtime_context,
            )
        _render_chat_result(result, show_debug)

    history.append({
        "role": "assistant",
        "content": result.get("response", ""),
        "result": result,
    })
    st.session_state["pipeline_result"] = result  # 供決策分析頁使用
    st.rerun()


def _render_chat_result(result: dict, show_debug: bool = False) -> None:
    """在對話氣泡內顯示分析結果，依意圖決定顯示哪些元件。"""
    if not result:
        st.write("（無結果）")
        return

    nlp_layout = st.session_state.get("_nlp_layout", False)
    intent = result.get("intent", {}).get("intent", "")
    risk = result.get("tool_results", {}).get("risk_score_tool", {}).get("risk")

    # 風險評分只在「風險預測」時顯示（不含民眾出行，避免卡片資訊錯誤）
    if intent == "風險預測":
        if risk:
            _render_risk_badge(risk["level"], risk["score"])
        _render_severity_cards(result)

    # 核心回答（永遠顯示）
    st.markdown(result.get("response", ""))

    # Qwen3 思考過程（有思考內容時顯示）
    thinking = result.get("llm_thinking", "")
    if thinking and not nlp_layout:
        with st.expander("🧠 模型思考過程（Qwen3 Extended Thinking）", expanded=False):
            st.markdown(thinking)

    # 細節收進 expander
    if not nlp_layout:
        with st.expander("🔍 NLU Pipeline 解析過程", expanded=False):
            _render_nlu_pipeline_inner(result)

        with st.expander("👤 角色化建議與行動分級", expanded=False):
            _render_role_action_guidance(result)

    _render_inline_multimodal_evidence(result)

    if show_debug:
        with st.expander("🛠 除錯資訊", expanded=False):
            st.json(_json_safe(result))

    # ── 引導提問按鈕 ──────────────────────────────────────
    followups = _generate_followups(result)
    if followups:
        st.html(
            '<div style="font-size:13px;color:#64748b;font-weight:600;letter-spacing:0.04em;'
            'text-transform:uppercase;margin:0.8rem 0 0.4rem;">💡 繼續探索</div>'
        )
        cols = st.columns(len(followups))
        for i, (col, q) in enumerate(zip(cols, followups)):
            uid = abs(hash(result.get("user_input", "") + q)) % 100000
            if col.button(q, key=f"fu_{uid}_{i}", use_container_width=True):
                st.session_state["_pending_followup"] = q
                st.rerun()


def _render_risk_badge(level: str, score: int) -> None:
    """風險等級色彩標示 + 自訂卡片樣式。"""
    if level == "高風險":
        css_class = "risk-card risk-card-high"
        icon = "🔴"
    elif level == "中風險":
        css_class = "risk-card risk-card-mid"
        icon = "🟡"
    else:
        css_class = "risk-card risk-card-low"
        icon = "🟢"
    st.html(f"""
        <div class="{css_class}">
            <div class="risk-card-icon">{icon}</div>
            <div>
                <span class="risk-card-label">風險評估結果</span>
                <div class="risk-card-level">{level}</div>
            </div>
            <div class="risk-card-score">{int(score)}<span style="font-size:16px;opacity:0.55;font-weight:400;">/100</span></div>
        </div>
        """)
    st.progress(int(score) / 100)



def _render_nlu_pipeline(result: dict) -> None:
    """NLU Pipeline 透明化（含 expander）— 用於智慧問答頁舊版 _render_result。"""
    with st.expander("🔍 NLU Pipeline 解析過程", expanded=False):
        _render_nlu_pipeline_inner(result)


def _render_nlu_pipeline_inner(result: dict) -> None:
    """NLU Pipeline 透明化（無 expander wrapper）— 用於 chat 泡泡內。"""
    intent_info = result.get("intent", {})
    query = result.get("query", {})
    nlu_debug = result.get("nlu", {})
    tool_plan = result.get("tool_plan", [])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**意圖識別**")
        source = intent_info.get("source", "rules")
        source_label = "本機 LLM（Qwen3 4B）" if source == "local_llm" else "規則式 NLU"
        st.write(f"- 意圖：**{intent_info.get('intent', '未知')}**")
        st.write(f"- 來源：{source_label}")
        llm_parse = nlu_debug.get("llm_parse") or {}
        if llm_parse.get("confidence") is not None:
            st.write(f"- LLM 信心值：{llm_parse['confidence']:.2f}")
        reason = intent_info.get("reason", "")
        if reason:
            st.write(f"- 說明：{reason}")

    with col2:
        st.markdown("**實體提取（jieba + 規則）**")
        entity_labels = {
            "district": "行政區",
            "hour": "時段",
            "weekday": "星期",
            "month": "月份",
            "weather": "天候",
            "transport_mode": "交通工具",
            "origin_district": "起點行政區",
            "destination_district": "終點行政區",
        }
        has_entity = False
        for key, label in entity_labels.items():
            val = query.get(key)
            if val is not None and val != "" and val != "不指定":
                st.write(f"- {label}：`{val}`")
                has_entity = True
        if not has_entity:
            st.caption("（未提取到特定實體）")

    if tool_plan:
        st.markdown("**工具執行計畫（Multi-Agent Pipeline）**")
        _tool_labels = {
            "risk_score_tool":           "Risk Agent — 風險評分",
            "accident_query_tool":       "Query Agent — 事故查詢",
            "weather_time_heatmap_tool": "Heatmap Agent — 天候時段",
            "cause_analysis_tool":       "Cause Agent — 肇因分析",
            "recommendation_tool":       "Recommend Agent — 改善建議",
            "citizen_route_advice_tool": "Route Agent — 出行輔助",
            "rag_lookup_tool":           "RAG Agent — BM25 知識庫",
        }
        for i, tool in enumerate(tool_plan, 1):
            st.write(f"{i}. `{_tool_labels.get(tool, tool)}`")


def _render_tool_summaries(tool_results: dict) -> None:
    for tool_name, output in tool_results.items():
        with st.expander(tool_name, expanded=False):
            summary = output.get("summary") or output.get("answer")
            if summary:
                st.write(summary)
            st.json(_json_safe(output))


@st.cache_data(show_spinner=False)
def _load_map_data():
    df = load_accident_data()
    map_df = df.copy()
    map_df["lon"] = map_df["GPS座標X"].astype(str).str.strip()
    map_df["lat"] = map_df["GPS座標Y"].astype(str).str.strip()
    map_df["lon"] = map_df["lon"].str.replace(",", ".", regex=False)
    map_df["lat"] = map_df["lat"].str.replace(",", ".", regex=False)
    map_df["lon"] = pd.to_numeric(map_df["lon"], errors="coerce")
    map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
    map_df = map_df.dropna(subset=["lat", "lon"])
    map_df = map_df[
        map_df["lat"].between(24.0, 24.5)
        & map_df["lon"].between(120.4, 121.0)
    ]
    return map_df


def _render_decision_map(result: dict) -> dict:
    st.subheader("事故熱點決策地圖")
    st.caption("地圖根據歷史事故 GPS 點位顯示，可輔助判斷熱點區域、勤務配置與後續路口盤點。")

    try:
        map_df = _load_map_data()
    except Exception as exc:
        st.warning(f"目前無法載入地圖資料：{exc}")
        return {"segments": [], "summary": f"目前無法載入地圖資料：{exc}"}

    query = result.get("query", {})
    filtered = map_df
    if query.get("district"):
        filtered = filtered[filtered["區"] == query["district"]]
    if query.get("hour") is not None:
        filtered = filtered[filtered["hour"] == query["hour"]]
    if query.get("weekday"):
        filtered = filtered[filtered["weekday"] == query["weekday"]]
    if query.get("month") is not None:
        filtered = filtered[filtered["month"] == query["month"]]
    if query.get("weather"):
        filtered = filtered[filtered["天候_str"] == query["weather"]]

    total_count = len(filtered)
    if filtered.empty:
        st.info("目前查詢條件下沒有可顯示的 GPS 點位。")
        return {"segments": [], "summary": "目前查詢條件下沒有可顯示的 GPS 點位。"}

    left, right = st.columns([1.2, 1])
    with left:
        sample_size = min(total_count, 5000)
        display_df = filtered.sample(sample_size, random_state=42) if total_count > sample_size else filtered
        st.map(display_df[["lat", "lon"]], use_container_width=True)
        st.caption(f"顯示 {len(display_df):,} / {total_count:,} 筆事故點位。資料量較大時會抽樣顯示以維持介面流暢。")

    with right:
        st.metric("符合條件事故點位", f"{total_count:,}")

        district_counts = (
            filtered["區"]
            .value_counts()
            .head(8)
            .rename_axis("行政區")
            .reset_index(name="事故筆數")
        )
        st.write("行政區熱點排序")
        st.dataframe(district_counts, hide_index=True, use_container_width=True)

        st.write("決策用途")
        st.markdown(
            "\n".join(
                [
                    "- 優先盤點事故密集行政區與路口。",
                    "- 搭配時段條件安排尖峰勤務或巡邏。",
                    "- 搭配天候條件設定雨天、霧天提醒策略。",
                    "- 後續可接道路路網與車流資料，延伸為路線風險輔助。",
                ]
            )
        )
        _render_map_interpretation(query, filtered, district_counts)
        segment_result = _render_segment_hotspots(filtered)
    return segment_result


def _render_chat_map_preview(query: dict) -> None:
    """聊天泡泡內的輕量地圖預覽，完整分析仍放在決策分析頁。"""
    try:
        map_df = _load_map_data()
    except Exception as exc:
        st.warning(f"目前無法載入地圖資料：{exc}")
        return

    filtered = map_df
    if query.get("district"):
        filtered = filtered[filtered["區"] == query["district"]]
    if query.get("hour") is not None:
        filtered = filtered[filtered["hour"] == query["hour"]]
    if query.get("weekday"):
        filtered = filtered[filtered["weekday"] == query["weekday"]]
    if query.get("month") is not None:
        filtered = filtered[filtered["month"] == query["month"]]
    if query.get("weather"):
        filtered = filtered[filtered["天候_str"] == query["weather"]]

    if filtered.empty:
        st.info("目前條件下沒有可顯示的事故點位。")
        return

    sample_size = min(len(filtered), 1000)
    display_df = filtered.sample(sample_size, random_state=42) if len(filtered) > sample_size else filtered
    st.map(display_df[["lat", "lon"]], use_container_width=True)
    st.caption(f"顯示 {len(display_df):,} / {len(filtered):,} 筆事故點位。")

    top_districts = (
        filtered["區"]
        .value_counts()
        .head(5)
        .rename_axis("行政區")
        .reset_index(name="事故數")
    )
    if not top_districts.empty:
        st.markdown("**地圖範圍內行政區事故排序**")
        st.dataframe(top_districts, hide_index=True, use_container_width=True)


def _render_weather_hour_heatmap(query: dict) -> None:
    """天候 × 時段事故熱力圖（互動式 DataFrame 色階版）。"""
    st.subheader("天候 × 時段事故熱力圖")
    st.caption("顏色越深表示事故件數越多，可快速識別哪種天候與時段組合最危險。")
    try:
        map_df = _load_map_data()
    except Exception as exc:
        st.warning(f"無法載入熱力圖資料：{exc}")
        return

    filtered = map_df
    if query.get("district"):
        filtered = filtered[filtered["區"] == query["district"]]

    if "天候_str" not in filtered.columns or "hour" not in filtered.columns:
        st.info("資料欄位不完整，無法產生熱力圖。")
        return

    cross = (
        filtered.groupby(["天候_str", "hour"])
        .size()
        .reset_index(name="事故數")
        .pivot(index="天候_str", columns="hour", values="事故數")
        .fillna(0)
        .astype(int)
    )

    if cross.empty:
        st.info("目前篩選條件下沒有足夠資料產生熱力圖。")
        return

    cross.columns = [f"{h}時" for h in cross.columns]

    styled = cross.style.background_gradient(cmap="YlOrRd", axis=None).format("{:,}")
    st.dataframe(styled, use_container_width=True)

    # 找出最危險組合
    flat = filtered.groupby(["天候_str", "hour"]).size()
    if not flat.empty:
        top_weather, top_hour = flat.idxmax()
        st.caption(
            f"最高事故組合：天候「{top_weather}」× {top_hour} 時（{flat.max():,} 件）"
        )


@st.cache_data(show_spinner=False)
def _load_risk_combos(top_n: int = 15) -> tuple:
    """高風險條件組合與勤務覆蓋資料（快取）。"""
    df = load_accident_data()
    df["hour_int"] = pd.to_numeric(df["hour"], errors="coerce")
    total = len(df)

    # 前 top_n 高頻條件組合
    combos = (
        df.groupby(["區", "hour_int", "天候_str"])
        .size()
        .reset_index(name="事故數")
        .sort_values("事故數", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    combos.index += 1
    combos["佔全市%"] = (combos["事故數"] / total * 100).round(2)
    combos = combos.rename(columns={"區": "行政區", "hour_int": "時段", "天候_str": "天候"})
    combos["時段"] = combos["時段"].astype(int).astype(str) + "時"

    # 勤務覆蓋：以 (行政區, 時段) 排序
    patrol = (
        df.groupby(["區", "hour_int"])
        .size()
        .reset_index(name="事故數")
        .sort_values("事故數", ascending=False)
        .reset_index(drop=True)
    )
    patrol["累積事故數"] = patrol["事故數"].cumsum()
    patrol["覆蓋率%"] = (patrol["累積事故數"] / total * 100).round(1)
    patrol["排名"] = patrol.index + 1
    patrol = patrol.rename(columns={"區": "行政區", "hour_int": "時段"})
    patrol["時段"] = patrol["時段"].astype(int).astype(str) + "時"

    return combos, patrol, total


def _render_rf_model_insights() -> None:
    """RF 模型洞察：特徵重要性 + 準確率比較。"""
    st.subheader("🤖 預測模型洞察（Random Forest）")

    model_path = BASE_DIR / "rf_risk_model.pkl"
    if not model_path.exists():
        st.info("尚未訓練預測模型，請先執行 train_risk_model.py")
        return

    try:
        import joblib
        md = joblib.load(model_path)
    except Exception as exc:
        st.warning(f"模型載入失敗：{exc}")
        return

    fi      = md.get("feature_importance", {})
    metrics = md.get("metrics", {})

    _fi_labels = {
        "district":  "行政區",
        "hour_int":  "時段",
        "weather":   "天候",
        "month_int": "月份",
        "weekday":   "星期",
    }

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("**特徵重要性**")
        fi_df = pd.DataFrame([
            {"特徵": _fi_labels.get(k, k), "重要性": round(v * 100, 1)}
            for k, v in sorted(fi.items(), key=lambda x: x[1], reverse=True)
        ]).set_index("特徵")
        st.bar_chart(fi_df, horizontal=True, color="#e05c5c")
        st.caption("重要性越高，該因素對事故風險影響越大（來自訓練資料學習結果）")

    with col2:
        st.markdown("**模型準確率比較**")
        rf_f1   = metrics.get("rf_macro_f1",   0)
        rule_f1 = metrics.get("rule_macro_f1", 0)
        c1, c2 = st.columns(2)
        c1.metric("Random Forest\nMacro-F1", f"{rf_f1:.3f}")
        c2.metric("規則式模型\nMacro-F1",    f"{rule_f1:.3f}",
                  delta=f"+{rf_f1 - rule_f1:.3f}")

        st.markdown("**關鍵發現**")
        if fi:
            top_k   = _fi_labels.get(max(fi, key=fi.get), "")
            top_pct = max(fi.values()) * 100
            w_pct   = fi.get("weather", 0) * 100
            st.write(f"- **{top_k}**是最重要風險因素（{top_pct:.1f}%）")
            st.write(f"- 天候貢獻度 {w_pct:.1f}%，高於規則式模型預設")
            st.write("- RF 捕捉到行政區 × 時段的非線性交互效果")
            st.write(f"- 訓練集：145,565 筆歷史事故記錄")


def _render_top_risk_combos() -> None:
    """前 15 高頻危險條件組合排行。"""
    st.subheader("⚠️ 高風險條件組合排行（前 15）")
    st.caption("以歷史事故件數排序，顯示最應優先關注的 行政區 × 時段 × 天候 組合。")

    combos, _, total = _load_risk_combos()

    styled = (
        combos[["行政區", "時段", "天候", "事故數", "佔全市%"]]
        .style
        .background_gradient(subset=["事故數"], cmap="YlOrRd")
        .format({"佔全市%": "{:.2f}%", "事故數": "{:,}"})
    )
    st.dataframe(styled, use_container_width=True)
    top1 = combos.iloc[0]
    st.caption(
        f"最高風險組合：{top1['行政區']} × {top1['時段']} × {top1['天候']}，"
        f"歷史事故 {int(top1['事故數']):,} 件（佔全市 {top1['佔全市%']:.2f}%）"
    )


def _render_patrol_coverage() -> None:
    """處方性策略：勤務覆蓋率最優化分析。"""
    st.subheader("📋 處方性策略：勤務覆蓋率最優化")
    st.markdown(
        "**問題：警力有限，如何選擇部署地點才能涵蓋最多事故？**\n\n"
        "每一個「勤務班次」= 在**某個行政區**的**某個小時**安排警力。"
        "系統依歷史事故頻率自動排序，告訴你投入幾班、派去哪裡，效益最高。"
    )

    _, patrol, total = _load_risk_combos()

    st.html("""
<div style="display:flex;justify-content:space-between;white-space:nowrap;
    font-size:13px;font-weight:700;color:#43535d;
    margin-bottom:-6px;padding:0 3px;">
  <span>1 班</span><span>30 班</span>
</div>""")
    n_slots = st.slider("可投入班次數", 1, 30, 5, key="patrol_slots")
    top_n   = patrol.head(n_slots)
    coverage = top_n["事故數"].sum() / total * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("建議勤務場次", f"{n_slots} 場")
    c2.metric("可涵蓋事故比例", f"{coverage:.1f}%")
    c3.metric("對應事故件數", f"{int(top_n['事故數'].sum()):,} 件")
    st.progress(min(coverage / 100, 1.0))

    st.markdown("**建議優先勤務清單**")
    display = top_n[["排名", "行政區", "時段", "事故數", "覆蓋率%"]].copy()
    display["事故數"] = display["事故數"].apply(lambda x: f"{x:,}")
    display["覆蓋率%"] = display["覆蓋率%"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(display, hide_index=True, use_container_width=True)

    # 覆蓋率曲線
    st.markdown("**累積覆蓋率曲線**")
    curve_df = patrol.head(30)[["排名", "覆蓋率%"]].set_index("排名")
    st.line_chart(curve_df, color="#2196f3")
    st.caption("橫軸：勤務場次數；縱軸：可涵蓋的歷史事故比例（%）")

    st.info(
        f"💡 策略建議：集中前 {n_slots} 個場次（{coverage:.1f}% 覆蓋率），"
        f"等同於以最少資源管理最多事故場景，是資源配置效益最高的方案。"
    )


_INTENT_CHARTS: dict[str, list[str]] = {
    "風險預測":     ["weather_hour_heatmap.png", "weather_accidents.png", "hourly_accidents.png"],
    "時段查詢":     ["hourly_accidents.png", "hourly_regression.png", "weekly_accidents.png"],
    "事故熱點查詢": ["district_accidents.png", "hourly_accidents.png"],
    "肇因分析":     ["main_causes.png", "district_accidents.png"],
    "政策建議":     ["district_accidents.png", "main_causes.png", "hourly_accidents.png", "weather_hour_heatmap.png"],
    "民眾出行建議": ["hourly_accidents.png", "weather_accidents.png", "district_accidents.png"],
}


def _unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            output.append(item)
    return output


def _recommend_visual_evidence(result: dict) -> dict:
    """依意圖、問題文字與實體條件推薦圖表/地圖/表格佐證。"""
    intent = result.get("intent", {}).get("intent", "")
    query = result.get("query", {})
    user_input = result.get("user_input", "")

    charts = list(_INTENT_CHARTS.get(intent, []))
    text = f"{user_input} {query.get('weather', '')} {query.get('district', '')}"

    if any(kw in text for kw in ["時段", "時間", "幾點", "早上", "晚上", "下班", "上班", "凌晨"]):
        charts.extend(["hourly_accidents.png", "hourly_regression.png"])
    if any(kw in text for kw in ["行政區", "哪區", "哪個區", "地區", "區域", "熱點", "最多", "排名"]):
        charts.extend(["district_accidents.png"])
    if any(kw in text for kw in ["雨", "天氣", "天候", "霧", "晴", "陰", "風"]):
        charts.extend(["weather_hour_heatmap.png", "weather_accidents.png"])
    if any(kw in text for kw in ["肇因", "原因", "代碼", "闖紅燈", "酒", "車距", "號誌"]):
        charts.extend(["main_causes.png"])
    if "酒" in text:
        charts.extend(["alcohol_accidents.png"])
    if any(kw in text for kw in ["政策", "交通局", "警察", "改善", "勤務", "巡邏", "工程"]):
        charts.extend(["district_accidents.png", "main_causes.png", "hourly_accidents.png"])
    if intent == "民眾出行建議" or any(kw in text for kw in ["路線", "出發", "逢甲", "火車站", "騎", "開車"]):
        charts.extend(["hourly_accidents.png", "weather_accidents.png", "district_accidents.png"])

    chart_paths = [
        BASE_DIR / "charts" / name
        for name in _unique_keep_order(charts)
        if (BASE_DIR / "charts" / name).exists()
    ][:4]

    show_map = intent in {"事故熱點查詢", "政策建議", "民眾出行建議"} or any(
        kw in text for kw in ["熱點", "地圖", "路口", "路線", "逢甲", "火車站", "哪裡", "哪個區"]
    )
    show_table = intent in {"風險預測", "事故熱點查詢", "政策建議", "民眾出行建議"} or bool(query.get("district"))

    return {"charts": chart_paths, "show_map": show_map, "show_table": show_table}


def _filter_accident_df_for_query(query: dict) -> pd.DataFrame:
    df = load_accident_data()
    filtered = df
    if query.get("district"):
        filtered = filtered[filtered["區"] == query["district"]]
    if query.get("hour") is not None:
        filtered = filtered[filtered["hour"] == query["hour"]]
    if query.get("weekday"):
        filtered = filtered[filtered["weekday"] == query["weekday"]]
    if query.get("month") is not None:
        filtered = filtered[filtered["month"] == query["month"]]
    if query.get("weather"):
        filtered = filtered[filtered["天候_str"] == query["weather"]]
    return filtered


def _render_visual_summary_table(result: dict) -> None:
    """在聊天中用小表格補充決策佐證，避免只顯示大圖。"""
    query = result.get("query", {})
    try:
        filtered = _filter_accident_df_for_query(query)
    except Exception as exc:
        st.caption(f"摘要表暫無法產生：{exc}")
        return

    if filtered.empty:
        st.caption("目前條件下沒有足夠資料產生摘要表。")
        return

    col1, col2 = st.columns(2)
    with col1:
        hour_top = (
            filtered["hour"]
            .value_counts()
            .head(5)
            .rename_axis("時段")
            .reset_index(name="事故數")
        )
        hour_top["時段"] = hour_top["時段"].astype(int).astype(str) + "時"
        st.markdown("**高事故時段 Top 5**")
        st.dataframe(hour_top, hide_index=True, use_container_width=True)

    with col2:
        if query.get("district"):
            weather_top = (
                filtered["天候_str"]
                .value_counts()
                .head(5)
                .rename_axis("天候")
                .reset_index(name="事故數")
            )
            st.markdown("**天候分布 Top 5**")
            st.dataframe(weather_top, hide_index=True, use_container_width=True)
        else:
            district_top = (
                filtered["區"]
                .value_counts()
                .head(5)
                .rename_axis("行政區")
                .reset_index(name="事故數")
            )
            st.markdown("**行政區 Top 5**")
            st.dataframe(district_top, hide_index=True, use_container_width=True)


def _render_inline_multimodal_evidence(result: dict) -> None:
    """文字 × 圖表 × 地圖的多模態決策佐證，使用者主動展開。"""
    evidence = _recommend_visual_evidence(result)
    charts = evidence["charts"]
    if not charts and not evidence["show_map"] and not evidence["show_table"]:
        return

    intent = result.get("intent", {}).get("intent", "")
    uid = abs(hash(result.get("user_input", "") + intent + str(result.get("query", {})))) % 100000
    key = f"mm_evidence_{uid}"

    st.caption("🧩 可搭配圖表、表格或地圖檢查這個回答的資料依據。")
    if st.button("📊 顯示多模態決策佐證", key=f"btn_{key}", use_container_width=False):
        st.session_state[key] = not st.session_state.get(key, False)

    if not st.session_state.get(key, False):
        return

    tabs = st.tabs(["圖表", "資料摘要", "地圖/熱點"])

    with tabs[0]:
        if charts:
            cols = st.columns(min(len(charts), 2))
            for i, path in enumerate(charts):
                with cols[i % 2]:
                    caption = _CHART_CAPTIONS.get(path.name, path.stem.replace("_", " "))
                    st.image(str(path), caption=caption, use_container_width=True)
                    usage = _CHART_DECISION_USE.get(path.name)
                    if usage:
                        st.caption(f"決策用途：{usage}")
        else:
            st.info("此問題沒有對應的靜態圖表。")

    with tabs[1]:
        if evidence["show_table"]:
            _render_visual_summary_table(result)
        else:
            st.info("此問題不需要額外資料表佐證。")

    with tabs[2]:
        if evidence["show_map"]:
            st.caption("聊天介面提供精簡地圖；完整地圖與熱點排序請到「決策分析」頁。")
            _render_chat_map_preview(result.get("query", {}))
        else:
            st.info("此問題不需要地圖佐證。")


def _render_chart_gallery() -> None:
    st.subheader("目前已完成 EDA 圖表")
    existing = [path for path in CHART_FILES if path.exists()]
    if not existing:
        st.write("尚未找到圖表檔案。")
        return

    cols = st.columns(3)
    for index, path in enumerate(existing):
        with cols[index % 3]:
            caption = _CHART_CAPTIONS.get(path.name, path.stem.replace("_", " "))
            st.image(str(path), caption=caption, use_container_width=True)


def _render_weather_panel(district: str | None) -> None:
    st.subheader("即時天氣參考")
    if st.button("更新中央氣象署即時天氣", use_container_width=True):
        st.session_state["weather_result"] = fetch_cwa_weather_tool(district)
    if "weather_result" not in st.session_state:
        st.session_state["weather_result"] = fetch_cwa_weather_tool(district)
    _render_weather_result(st.session_state.get("weather_result"))


def _render_weather_result(weather_result: dict | None) -> None:
    if not weather_result:
        return
    if weather_result.get("available"):
        st.success(weather_result.get("summary", "即時天氣資料已取得。"))
    else:
        st.info(weather_result.get("summary", "目前沒有即時天氣資料。"))
        if weather_result.get("data_gap"):
            st.caption(weather_result["data_gap"])


def _render_route_api_result(route_result: dict | None) -> None:
    st.subheader("OSRM 路線參考")
    if not route_result:
        st.info("目前沒有路線查詢結果。")
        return
    if route_result.get("available"):
        st.success(route_result.get("summary"))
        points = route_result.get("route_points") or []
        if points:
            route_df = pd.DataFrame(points)
            st.map(route_df[["lat", "lon"]], use_container_width=True)
    else:
        st.info(route_result.get("summary", "目前無法取得 OSRM 路線。"))
        if route_result.get("data_gap"):
            st.caption(route_result["data_gap"])


def _render_segment_hotspots(filtered: pd.DataFrame) -> dict:
    st.write("路口/路段級熱點聚合")
    segment_result = build_segment_hotspots(filtered, precision=3, top_n=12)
    st.caption(segment_result.get("summary", ""))
    segments = segment_result.get("segments") or []
    if not segments:
        st.info("目前沒有可顯示的路段熱點。")
        return segment_result

    segment_df = pd.DataFrame(segments)
    st.dataframe(
        segment_df[
            ["rank", "district", "lat", "lon", "accident_count", "peak_hour", "top_weather", "risk_level"]
        ].rename(
            columns={
                "rank": "排名",
                "district": "主要行政區",
                "lat": "約略緯度",
                "lon": "約略經度",
                "accident_count": "事故數",
                "peak_hour": "高峰時段",
                "top_weather": "常見天候",
                "risk_level": "風險層級",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.map(segment_df[["lat", "lon"]], use_container_width=True)
    return segment_result


def _render_report_export(
    *,
    title: str,
    query: dict | None = None,
    pipeline_result: dict | None = None,
    route_result: dict | None = None,
    weather_result: dict | None = None,
    segment_result: dict | None = None,
) -> None:
    st.subheader("報告匯出")
    report = export_markdown_report(
        title=title,
        query=query,
        pipeline_result=pipeline_result,
        route_result=route_result,
        weather_result=weather_result,
        segment_result=segment_result,
    )
    st.download_button(
        "下載 Markdown 報告",
        data=report.encode("utf-8"),
        file_name=f"{title}.md",
        mime="text/markdown",
        use_container_width=True,
    )


def _json_safe(value):
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _render_answer_summary_cards(result: dict) -> None:
    summary = _build_answer_summary(result)
    cols = st.columns(4)
    cols[0].metric("風險判斷", summary["risk"])
    cols[1].metric("主要依據", summary["basis"])
    cols[2].metric("建議方向", summary["action"])
    cols[3].metric("資料狀態", summary["data_status"])


def _render_severity_cards(result: dict) -> None:
    """顯示傷亡嚴重度摘要卡片（僅在有風險評分工具結果時出現）。"""
    severity = result.get("tool_results", {}).get("risk_score_tool", {}).get("severity")
    if not severity or not severity.get("accident_count"):
        return
    cols = st.columns(4)
    cols[0].metric("符合條件事故數", f"{severity['accident_count']:,} 件")
    cols[1].metric("死亡人數", f"{severity['deaths']} 人")
    cols[2].metric("受傷人數", f"{severity['injuries']} 人")
    cols[3].metric("嚴重度評估", severity.get("severity_label", "—"))


def _build_answer_summary(result: dict) -> dict[str, str]:
    tool_results = result.get("tool_results", {})
    risk = tool_results.get("risk_score_tool", {}).get("risk", {})
    query = result.get("query", {})
    intent = result.get("intent", {}).get("intent", "查詢")

    risk_label = risk.get("level", "非風險查詢")
    basis_parts = []
    if query.get("district"):
        basis_parts.append(str(query["district"]))
    if query.get("hour") is not None:
        basis_parts.append(f"{query['hour']}時")
    if query.get("weather"):
        basis_parts.append(str(query["weather"]))
    if not basis_parts and "cause_analysis_tool" in tool_results:
        basis_parts.append("主要肇因")
    if not basis_parts and "accident_query_tool" in tool_results:
        basis_parts.append("事故統計")

    action = {
        "風險預測": "避開高風險條件",
        "事故熱點查詢": "優先盤點熱點",
        "時段查詢": "調整尖峰配置",
        "肇因分析": "宣導與執法",
        "政策建議": "資源優先排序",
        "代碼說明": "補充資料理解",
    }.get(intent, "需補充條件")

    return {
        "risk": risk_label,
        "basis": " / ".join(basis_parts[:3]) if basis_parts else intent,
        "action": action,
        "data_status": "歷史資料推估",
    }


def _render_role_action_guidance(result: dict) -> None:
    """永遠同時顯示一般民眾與公家單位兩個建議區塊。"""
    risk = result.get("tool_results", {}).get("risk_score_tool", {}).get("risk", {}).get("level")

    col_pub, col_gov = st.columns(2)

    with col_pub:
        st.markdown("**👤 一般民眾**")
        st.write("- 出發前確認天候與事故高峰時段。")
        st.write("- 風險偏高時延後出發或改用大眾運輸。")
        st.write("- 降低車速、保持安全距離、避免分心駕駛。")
        _render_action_levels("一般民眾", risk)

    with col_gov:
        st.markdown("**🏛️ 公家單位**")
        st.write("- 交通局：盤點高事故路口，調整號誌時序。")
        st.write("- 警察：依高風險時段安排巡邏與取締重點。")
        st.write("- 工程單位：會勘事故密集路段，改善標線視距。")
        _render_action_levels("公家單位", risk)

    _render_limitation_notice()


def _render_action_levels(role: str, risk_level: str | None) -> None:
    if role == "一般民眾":
        rows = [
            {"層級": "立即注意", "行動": "降低速度、增加車距、避免趕路。"},
            {"層級": "出發調整", "行動": "風險偏高時延後出發或改選較安全交通方式。"},
            {"層級": "長期習慣", "行動": "建立常用路線風險意識，避開事故熱點路口。"},
        ]
    else:  # 公家單位
        rows = [
            {"層級": "立即部署", "行動": "針對尖峰或不良天候加強警力與提醒。"},
            {"層級": "短期管理", "行動": "安排巡邏、疏導、宣導與取締違規。"},
            {"層級": "中期改善", "行動": "檢視號誌時序、標線視距與速限設置。"},
            {"層級": "長期追蹤", "行動": "追蹤事故趨勢，評估改善效益。"},
        ]
    if risk_level == "高風險":
        rows[0]["行動"] = "⚠️ 優先處理。" + rows[0]["行動"]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_limitation_notice(message: str | None = None) -> None:
    text = message or "本系統根據歷史事故資料推估，尚未接入即時車流、即時天氣與完整道路設計資料；結果適合作為出行或管理參考，不代表即時事故預測。"
    st.warning(text)


def _render_citizen_summary_cards(result: dict) -> None:
    query = result.get("query", {})
    risk = result.get("risk", {})
    basis = []
    if query.get("origin_district") and query.get("destination_district"):
        basis.append(f"{query['origin_district']}→{query['destination_district']}")
    if query.get("hour") is not None:
        basis.append(f"{query['hour']}時")
    if query.get("weather"):
        basis.append(str(query["weather"]))

    cols = st.columns(4)
    cols[0].metric("出行風險", risk.get("level", "未判定"), f"{risk.get('score', 0)} / 100")
    cols[1].metric("出行情境", " / ".join(basis[:2]) if basis else "未指定")
    cols[2].metric("交通工具", query.get("transport_mode", "未指定"))
    cols[3].metric("資料狀態", "歷史資料提醒")


def _render_map_interpretation(query: dict, filtered: pd.DataFrame, district_counts: pd.DataFrame) -> None:
    st.write("本次地圖解讀")
    top_district = None
    top_count = None
    if not district_counts.empty:
        top_district = district_counts.iloc[0]["行政區"]
        top_count = int(district_counts.iloc[0]["事故筆數"])

    lines = []
    if top_district:
        lines.append(f"{top_district}在目前篩選下事故點位最多，共 {top_count:,} 筆。")
    if query.get("hour") is not None:
        lines.append(f"目前地圖已聚焦於 {query['hour']} 時，可用於觀察尖峰時段熱點。")
    if query.get("weather"):
        lines.append(f"目前地圖已聚焦於天候「{query['weather']}」，適合檢視天候風險位置。")
    if not lines:
        lines.append("目前顯示全資料集事故點位，可先用行政區、時段或天候縮小範圍。")
    for line in lines:
        st.write(f"- {line}")


if __name__ == "__main__":
    main()
