# Vancouver 同儕評分系統

基於 Vancouver 算法實現的完整同儕評分系統，提供從資料處理、分派生成到評分分析的整體解決方案。

## 📋 專案概述

本系統實現了完整的 Vancouver 算法應用於同儕評分場景，主要提供：
- 學生考試資料處理與分析
- 自動生成同儕評分分派
- 產生評分表單與收集結果
- 使用 Vancouver 算法處理評分資料
- 生成詳細的分析報告

## 📁 專案結構

```
vancouver/
├── core/                          # 核心算法實現
├── analysis/                      # 分析工具和模型
├── peer_evaluation/               # 同儕評分系統
│   ├── main.py                    # 主控制器
│   ├── data_processor.py          # 數據處理器
│   ├── assignment_engine.py       # 分派生成引擎  
│   ├── form_generator.py          # 評分表單生成器
│   ├── form_simulator.py          # 表單填寫模擬器
│   ├── result_collector_simple.py # 結果收集器
│   ├── vancouver_processor.py     # Vancouver算法處理器
│   ├── verification_report.py     # 驗證報告生成器
│   └── config_unified.py          # 統一配置文件
├── docs/                          # 文件資料夾
├── workflow_results/              # 工作流程產出
└── logs/                          # 日志記錄
```

## 🚀 使用 peer_evaluation 測試系統

peer_evaluation 目錄是一個完整的同儕評分測試系統，提供了從資料處理到 Vancouver 算法應用的全流程解決方案。

### 基本使用方式

#### 1. 互動式選單模式（推薦新手使用）

執行互動式選單，選擇要運行的功能：

```bash
python peer_evaluation/main.py --menu
```

這將顯示一個互動式選單，您可以按數字鍵選擇各種功能：
- 數據處理
- 生成同儕分派
- 產生評分表單
- 模擬表單填寫
- 收集評分結果
- 執行 Vancouver 算法
- 生成驗證報告

#### 2. 完整自動化流程

##### a. 基礎流程（資料處理→分派→表單生成）
```bash
python peer_evaluation/main.py --full
```

##### b. 完整工作流程（包含模擬填寫和 Vancouver 算法）
```bash
python peer_evaluation/main.py --workflow
```

##### c. 自動執行完整流程（無互動確認）
```bash
python peer_evaluation/main.py --auto
```

#### 3. 單步驟執行模式

單獨執行特定步驟：

```bash
# 只處理CSV數據
python peer_evaluation/main.py --data-only --csv docs/Midterm\ Survey\ Student\ Analysis\ Report.csv

# 只生成同儕分派
python peer_evaluation/main.py --assign-only --json workflow_results/1_csv_analysis/midterm_data.json

# 只生成評分表單
python peer_evaluation/main.py --forms-only --assignment workflow_results/2_form_generation/peer_assignments.json
```

### 預設配置使用

系統支援多種預設配置，以適應不同測試場景：

```bash
# 查看所有可用配置
python peer_evaluation/main.py --list-presets

# 使用指定配置執行完整流程
python peer_evaluation/main.py --full --preset standard
```

可用配置包括：
- `light`: 輕量級配置，適合快速測試
- `standard`: 標準配置，一般測試場景 
- `comprehensive`: 綜合配置，進行詳細測試
- `debug`: 調試配置，提供額外日誌

### 查看系統狀態與結果

```bash
# 查看系統配置與狀態
python peer_evaluation/main.py --status
```

### 工作流程輸出

完整工作流程會依序產生以下輸出：
1. **CSV 數據分析**：處理考試數據，生成 JSON 格式的結構化數據
2. **同儕分派**：生成同儕評分分派表
3. **評分表單**：生成 HTML 格式的評分表單
4. **表單模擬**：模擬填寫評分表單
5. **結果收集**：收集並整理評分結果
6. **Vancouver 處理**：使用 Vancouver 算法處理評分數據
7. **驗證報告**：產生詳細的分析報告

所有結果都保存在 `workflow_results/` 目錄中，按步驟分類整理。

## 資料格式說明

### 輸入資料

- **學生考試資料**：CSV 格式，包含學生資訊和答題數據
- **評分表單**：HTML 格式，用於同儕評分

### 輸出資料

- **同儕分派表**：JSON 格式，描述誰評價誰
- **評分結果**：JSON/Excel 格式，包含原始評分數據
- **Vancouver 結果**：JSON 格式，包含算法處理後的結果
- **驗證報告**：Excel 格式，包含詳細分析

## 進階功能

### 自定義工作流程

您可以修改 `config_unified.py` 文件來自定義各種參數：
- 文件路徑設定
- 評分尺度設定
- 分派策略設定
- Vancouver 參數設定

### 算法參數調優

針對 Vancouver 算法的參數調整，可以修改以下設定：
- `vG_value`：Vancouver 算法的關鍵參數，影響群體一致性測量
- `tolerance`：容忍度，影響異常評分的識別
- `iterations`：迭代次數，影響結果精確度

## 實用技巧

1. **使用預設配置**：新使用者建議從 `light` 或 `standard` 配置開始
2. **檢查輸出目錄**：所有結果都按步驟保存在 `workflow_results/` 目錄
3. **查看錯誤訊息**：若出現問題，系統會顯示詳細的錯誤信息
4. **資料備份**：重要資料建議手動備份到 `workflow_results_backup/` 目錄

---

*本系統實現了完整的 Vancouver 算法，並提供了全面的同儕評分解決方案，適用於教育機構、研究團體和需要進行同儕評估的任何場景。*
