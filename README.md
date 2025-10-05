# 去中心化期中考同儕互評系統

> **專案狀態：** ✅ 生產就緒  
> **最後更新：** 2025-10-06  
> **版本：** v2.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Status](https://img.shields.io/badge/Status-Production-success.svg)](https://ntublockchainintro2025.online/)

---

## 📋 目錄

- [專案概述](#專案概述)
- [系統架構](#系統架構)
- [快速開始](#快速開始)
- [完整工作流程](#完整工作流程)
- [自動化腳本](#自動化腳本)
- [技術規格](#技術規格)
- [故障排除](#故障排除)
- [常見問題](#常見問題)

---

## 專案概述

### �� 核心目標

將傳統的手動期中考評分流程，轉變為**線上去中心化同儕互評系統**，透過 Vancouver 演算法消除評分偏差，確保評分的公平性與客觀性。

### ✨ 核心功能

- ✅ **去中心化評分** - Vancouver 演算法自動調整評分偏差
- ✅ **完整匿名保護** - 評分者不知道被評分者身份
- ✅ **Web 評分介面** - 現代化的線上評分體驗
- ✅ **自動化流程** - Token 生成、Email 發送、結果收集全自動
- ✅ **即時監控** - 管理儀表板追蹤所有學生的提交進度
- ✅ **安全機制** - Token 驗證、一次性使用、IP 記錄

### 📊 系統特色

**學生端：**
- 📧 收到個人化評分連結 (4 個評分任務)
- 🔗 點擊連結即可開始評分
- 📝 查看被評分者的完整答案
- ⭐ 對每題評分 (Q1-Q5) + 撰寫評語
- ✅ 提交後即時確認

**管理端：**
- 📊 即時監控所有學生提交狀態
- �� 自動發送提醒給未完成者
- 📈 完整的統計分析
- 📄 多格式成績報表 (JSON, Excel)
- 🔍 驗證報告確保計算正確性

---

## 快速開始

### 前置需求

- Python 3.10+
- SQLite 3
- Gmail 帳號 (用於發送 Email)
- Linux Server (建議 Ubuntu 20.04+)

### 安裝步驟

```bash
# 1. Clone 專案
git clone https://github.com/Showyuan/decentralized-midterm-peer-evaluation.git
cd decentralized-midterm-peer-evaluation

# 2. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 設定環境變數
cp .env.example .env
nano .env  # 編輯 SMTP 設定

# 5. 初始化系統
./run_setup_and_init.sh
```

### 快速執行

```bash
# 完整流程 (三步驟)
./run_setup_and_init.sh      # 1. 初始化系統
./run_send_emails.sh          # 2. 發送評分通知
# ... 等待學生完成評分 ...
./run_collect_and_grade.sh   # 3. 收集並計算成績
```

---

## 完整工作流程

### 階段 1: 系統初始化

**腳本**: `./run_setup_and_init.sh`

**執行內容**:
1. 📄 讀取學生資料 (CSV → JSON)
2. 🎲 隨機分配評分任務 (每人評 4 份)
3. 🔑 生成評量 Token (UUID 唯一認證)
4. 💾 建立 SQLite 資料庫
5. 📊 導入 Tokens 和學生資料
6. 🌐 重啟 Web 服務

**輸出檔案**:
```
workflow_results/
├── 1_data_preparation/
│   └── midterm_data.json
├── 2_assignment/
│   └── peer_assignments.json
├── 3_token_generation/
│   ├── evaluation_tokens_*.json
│   └── evaluation_urls_*.json
└── 4_database/
    └── evaluation.db
```

### 階段 2: 發送評分通知

**腳本**: `./run_send_emails.sh`

**發送模式**:

| 模式 | 說明 | 用途 |
|------|------|------|
| **1. 測試模式** | 預覽內容，不實際發送 | 確認格式 |
| **2. 單一學生** | 指定學號發送 | 測試或補發 |
| **3. 全部學生** | 批次發送給所有人 | 正式通知 |
| **4. 未完成者** | 僅發送給尚未評分者 | 提醒通知 |

### 階段 3: 收集結果與計算成績

**腳本**: `./run_collect_and_grade.sh`

**執行內容**:
1. 📊 檢查資料完整性
2. 📥 從資料庫收集評分結果
3. 📄 生成多格式報表
4. �� 執行 Vancouver 演算法
5. 📊 生成驗證報告

**輸出檔案**:
```
workflow_results/
├── 5_evaluation_results/
│   ├── evaluation_results.json
│   ├── evaluation_results.xlsx
│   └── vancouver_input.json
├── 6_vancouver_results/
│   ├── vancouver_results_*.json
│   └── vancouver_results_*.xlsx  ⭐ 最終成績單
└── 7_final_reports/
    └── vancouver_verification_report.xlsx
```

---

## 自動化腳本

### 腳本說明

| 腳本 | 階段 | 功能 | 執行時機 |
|------|------|------|----------|
| `run_setup_and_init.sh` | 1 | 系統初始化 | 首次部署或重置 |
| `run_send_emails.sh` | 2 | 發送通知 | 開始評分或提醒 |
| `run_collect_and_grade.sh` | 3 | 收集成績 | 評分完成後 |

### 典型使用場景

#### 場景 A: 首次部署系統

```bash
./run_setup_and_init.sh      # 初始化
./run_send_emails.sh          # 測試模式確認
./run_send_emails.sh          # 正式發送
# 訪問: https://ntublockchainintro2025.online/ 監控進度
./run_collect_and_grade.sh   # 收集成績
```

#### 場景 B: 提醒未完成者

```bash
cd peer_evaluation
python3 tool_db_cli.py --stats  # 檢查進度
cd ..
./run_send_emails.sh            # 選擇模式 4
```

---

## 技術規格

### 技術堆疊

- **Python 3.10+** - 主要開發語言
- **Flask 3.0+** - Web 框架
- **SQLite 3** - 資料庫
- **Nginx** - 反向代理
- **Let's Encrypt** - SSL 憑證

### 資料庫結構

```sql
-- Tokens 表
CREATE TABLE tokens (
    token TEXT PRIMARY KEY,
    evaluator_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    questions TEXT NOT NULL,
    is_used BOOLEAN DEFAULT 0,
    ...
);

-- Submissions 表
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    token TEXT NOT NULL,
    question_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    comment TEXT,
    ...
);
```

### Vancouver 演算法

**核心參數**:
```python
R_max = 1.0      # 最大聲譽值
v_G = 8.0        # 全域變異數
α = 0.1          # 激勵權重
N = 4            # 每人評分數
```

---

## 故障排除

### 問題 1: Web 服務無法啟動

```bash
sudo systemctl status peereval
sudo journalctl -u peereval -f
sudo systemctl restart peereval
```

### 問題 2: 資料庫鎖定

```bash
sudo systemctl stop peereval
python3 tool_db_cli.py --stats
sudo systemctl start peereval
```

### 問題 3: Email 發送失敗

檢查 `.env` 中的 SMTP 設定，確認使用「應用程式專用密碼」。

---

## 常見問題

### Q1: 學生忘記評分連結怎麼辦？

**A:** 重新發送 Email 或從 `evaluation_urls_*.json` 查找。

### Q2: Token 過期了怎麼辦？

**A:** 在資料庫中延長 `expires_at` 時間。

### Q3: 如何防止學生互相分享 Token？

**A:** 系統已內建保護：一次性使用、IP 記錄、過期機制。

---

## 目錄結構

```
decentralized-midterm-peer-evaluation/
├── README.md
├── requirements.txt
├── run_setup_and_init.sh
├── run_send_emails.sh
├── run_collect_and_grade.sh
├── peer_evaluation/
│   ├── stage0_config_unified.py
│   ├── stage1_data_processor.py
│   ├── stage2_assignment_engine.py
│   ├── stage2_token_generator.py
│   ├── stage3_email_sender.py
│   ├── stage3_web_server.py
│   ├── stage4_result_collector_web.py
│   ├── stage5_vancouver_processor.py
│   └── templates/
└── workflow_results/
    ├── 1_data_preparation/
    ├── 2_assignment/
    ├── 3_token_generation/
    ├── 4_database/
    ├── 5_evaluation_results/
    ├── 6_vancouver_results/
    └── 7_final_reports/
```

---

## 授權條款

本專案採用 MIT License

---

## 聯絡資訊

**專案連結**: [https://github.com/Showyuan/decentralized-midterm-peer-evaluation](https://github.com/Showyuan/decentralized-midterm-peer-evaluation)

**線上系統**: [https://ntublockchainintro2025.online/](https://ntublockchainintro2025.online/)

---

**文件版本**: 2.0  
**最後更新**: 2025-10-06  
**維護狀態**: 持續維護中 ✅
