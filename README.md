# 台中市交通事故風險預測與決策支援系統

本專案為「智慧決策支援系統（IDSS）」與「自然語言處理（NLP）」課程期末專題，建置一套以自然語言問答為入口的交通事故風險預測與決策支援平台。系統以台中市 2024 年交通事故開放資料為核心，整合 Random Forest 風險模型、中文自然語言理解、BM25 知識檢索、即時天氣與車流資料，提供一般民眾與公家單位不同視角的交通安全建議。

## 專案特色

- 自然語言問答：支援「西屯區現在開車危險嗎」、「哪個時段從逢甲去火車站比較安全」等口語查詢。
- 交通風險預測：使用 Random Forest 模型預測行政區、時段、天候、星期與月份條件下的事故風險。
- 即時情境整合：未指定條件時，自動帶入目前時間、中央氣象署天氣與車流狀態。
- 決策支援分析：提供事故熱點、天候時段熱力圖、肇因分析、勤務覆蓋率與策略建議。
- 多模態決策佐證：聊天回答可展開相關圖表、資料摘要與事故地圖，形成文字、圖表、表格、地圖整合展示。
- NLP 評估實驗：包含 30 題標註測試集，可評估意圖辨識與實體擷取表現。
- 角色化回答：一般民眾偏向出行建議，公家單位偏向政策、勤務與工程改善建議。

## 系統架構

```text
使用者自然語言提問
        │
        ▼
中文前處理與 NLU
        │
        ├─ 規則式意圖辨識
        ├─ LLM 語義解析
        └─ 地標/行政區/時段/天候/交通工具擷取
        │
        ▼
多代理人決策管線
        │
        ├─ 風險預測工具
        ├─ 事故查詢工具
        ├─ 肇因分析工具
        ├─ 路線出行建議工具
        └─ BM25 RAG 知識檢索
        │
        ▼
Random Forest 模型 + 即時天氣/車流資料
        │
        ▼
LLM 事實卡片生成與回答整理
        │
        ▼
Streamlit 互動式介面
        │
        └─ 多模態佐證：文字回答 + 圖表 + 摘要表 + 地圖
```

## 主要技術

| 類別 | 技術內容 |
|---|---|
| 前端介面 | Streamlit |
| 中文 NLP | jieba 斷詞、規則式 NLU、Few-shot LLM Parsing |
| 回答生成 | Ollama + Qwen3 4B、本機 LLM 事實卡片生成 |
| 資訊檢索 | BM25、同義詞擴展、交通事故知識庫 |
| 機器學習 | Random Forest、Label Encoding、特徵重要性分析 |
| 決策支援 | 描述性分析、預測性分析、處方性分析、勤務覆蓋率 |
| 多模態展示 | 自然語言回答、統計圖表、資料表、GPS 熱點地圖 |
| 外部資料 | 中央氣象署 CWA API、TDX 車流資料、OSRM 路線估算 |

## 資料來源

- 台中市政府警察局交通事故開放資料，民國 113 年（2024 年）1 至 12 月。
- 中央氣象署 CWA OpenData API。
- 交通部 TDX 車輛偵測器資料。
- OSRM 路線服務。

本 repo 不包含 `.env`，API 金鑰需由使用者自行建立。

## 快速開始

### 1. 下載專案

此專案包含 Git LFS 模型檔，請先安裝 Git LFS。

```bash
git lfs install
git clone https://github.com/Pang-Yiyi/taichung-traffic-idss-nlp.git
cd taichung-traffic-idss-nlp
```

### 2. 安裝 Python 套件

```bash
pip install streamlit pandas numpy scikit-learn rank_bm25 jieba joblib requests python-dotenv
```

### 3. 安裝與啟動本機 LLM

請先安裝 Ollama，並下載本專案使用的模型。

```bash
ollama pull qwen3:4b
ollama serve
```

若 Ollama 已在背景執行，可略過 `ollama serve`。

### 4. 建立 `.env`

複製範本：

```bash
copy .env.example .env
```

填入自己的 API 金鑰與 LLM 設定：

```env
CWA_API_KEY=your_cwa_api_key
CLIENT_ID=your_tdx_client_id
CLIENT_SECRET=your_tdx_client_secret
ENABLE_LOCAL_LLM=1
LLM_BACKEND=ollama
LLM_MODEL=qwen3:4b
```

### 5. 啟動系統

```bash
streamlit run app.py
```

開啟瀏覽器：

```text
http://localhost:8501
```

## 資料夾結構

```text
.
├── app.py                         # Streamlit 主程式
├── agents.py                      # 多代理人決策管線與 NLU 主控
├── llm_orchestrator.py            # LLM 回答生成與事實卡片整理
├── risk_model.py                  # 風險評分與 RF 模型推論
├── train_risk_model.py            # RF 模型訓練與比較
├── text_preprocessor.py           # 中文前處理、地標與交通工具解析
├── nlu_parser.py                  # LLM 語義解析
├── bm25_rag.py                    # BM25 知識檢索
├── analysis_tools.py              # 事故查詢、肇因分析、政策建議
├── external_api_tools.py          # CWA、TDX、OSRM 外部資料整合
├── data_loader.py                 # 事故資料讀取與前處理
├── rf_risk_model.pkl              # 訓練完成的 Random Forest 模型（Git LFS）
├── nlp_evaluation.py              # NLP 評估腳本
├── nlp_eval_dataset.json          # NLP 評估測試集
├── knowledge_base.json            # RAG 知識庫
├── DataSets/                      # 台中市 2024 年事故資料
├── charts/                        # EDA 與決策分析圖表
├── NLP期末專題報告.md              # NLP 課程報告
├── IDSS期末專題報告.md             # IDSS 課程報告
├── .env.example                   # 環境變數範本
└── .gitignore
```

## 核心模組說明

| 模組 | 說明 |
|---|---|
| `app.py` | Streamlit UI，包含智慧問答、民眾出行輔助與決策分析頁。 |
| `agents.py` | 控制一次問答的完整流程，包含意圖辨識、條件補齊、工具規劃與工具執行。 |
| `risk_model.py` | 優先使用 RF 模型預測風險；模型不可用時退回規則式評分。 |
| `llm_orchestrator.py` | 將工具結果整理成事實卡片，再交給 LLM 生成自然、聚焦的回答。 |
| `text_preprocessor.py` | 處理 jieba 斷詞、台中地標對行政區映射與出行條件解析。 |
| `bm25_rag.py` | 提供交通事故代碼、肇因與安全知識的 BM25 檢索。 |
| `external_api_tools.py` | 串接 CWA 天氣、TDX 車流與 OSRM 路線資料，並處理資料新鮮度。 |

## 多模態決策佐證

聊天介面不是只輸出文字。當系統完成回答後，會依據問題意圖、關鍵字與擷取條件，自動推薦可佐證的視覺化內容。使用者點擊「顯示多模態決策佐證」後，可查看：

- 圖表：例如行政區事故排名、每小時事故分布、天候與時段熱力圖、主要肇因圖。
- 資料摘要：例如高事故時段 Top 5、行政區 Top 5、天候分布。
- 地圖/熱點：以 GPS 事故點位呈現查詢條件下的事故分布。

此功能定位為「文字 × 圖表 × 表格 × 地圖」的多模態決策支援，不是影像辨識模型。它的目的是讓使用者可以從自然語言回答延伸到可檢查的資料證據，提升 IDSS 的可解釋性與展示完整度。

## 模型與評估

### Random Forest 風險模型

模型使用 2024 年台中市事故資料訓練，特徵包含：

- 行政區
- 小時
- 星期
- 月份
- 天候

目前模型表現：

| 模型 | Accuracy | Macro-F1 |
|---|---:|---:|
| Random Forest | 88.8% | 0.855 |
| 規則式基線 | 49.1% | 0.328 |

重新訓練：

```bash
python train_risk_model.py
```

### NLP 評估

測試集位於 `nlp_eval_dataset.json`，包含 30 題標註案例，涵蓋風險預測、熱點查詢、肇因分析、政策建議、出行建議、超出範圍等意圖。

重新執行評估：

```bash
python nlp_evaluation.py
```

評估結果會產生：

```text
nlp_eval_results.json
nlp_eval_report.md
```

這兩個檔案為產出結果，預設不納入 Git。

## Demo 問題

| 類型 | 範例問題 |
|---|---|
| 即時風險 | 西屯區現在開車危險嗎 |
| 情境風險 | 西屯區星期五晚上六點雨天危險嗎 |
| 出行建議 | 現在從逢甲騎機車去火車站危險嗎 |
| 安全時段 | 哪個時段從逢甲出發去火車站比較安全 |
| 熱點查詢 | 台中市哪個行政區事故最多 |
| 肇因分析 | 最常見的肇事原因是什麼 |
| 政策建議 | 如果我是交通局應該優先改善什麼 |
| 代碼說明 | 肇事因素代碼 07 是什麼 |
| 邊界案例 | 台北市事故最多哪個行政區 |

## 分享給組員使用

若只想讓組員操作網頁，不需要讓組員安裝環境，可在本機啟動 Streamlit 後使用 Cloudflare Tunnel 分享臨時網址。

```bash
python start_cloudflare_share.py
```

程式會啟動 Streamlit 與 Cloudflare Tunnel，並將公開網址寫入：

```text
cloudflare_share_url.txt
```

臨時網址在關閉 tunnel 或電腦休眠後會失效。

## 注意事項

- `.env` 不應提交到 Git。
- `rf_risk_model.pkl` 使用 Git LFS 管理，下載專案前請先安裝 Git LFS。
- `DataSets/` 與 `rf_risk_model.pkl` 是系統可直接運作的重要檔案。
- TDX 車流資料若過期，系統會自動改用歷史時段推估。
- 本系統分析基礎為 2024 年台中市歷史事故資料，實際出行仍需遵守交通安全規則。

## 報告文件

- `NLP期末專題報告.md`：自然語言處理課程成果報告。
- `IDSS期末專題報告.md`：智慧決策支援系統課程成果報告。

兩份報告分別說明 NLP 技術流程、IDSS 架構、模型設計、評估實驗與系統限制。
