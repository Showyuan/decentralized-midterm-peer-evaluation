#!/bin/bash
#####################################################################
# 去中心化同儕互評系統 - 階段 1-3 快速設置腳本
# 用於系統初始化和 Web 服務啟動（不包含結果收集）
#####################################################################

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
PROJECT_DIR="/home/sophia_liang/decentralized-midterm-peer-evaluation"
PEER_EVAL_DIR="$PROJECT_DIR/peer_evaluation"
DOCS_DIR="$PROJECT_DIR/docs"
CSV_FILE="$DOCS_DIR/Midterm Survey Student Analysis Report.csv"

log_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"
}

log_step() { echo -e "${BLUE}▶ $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

main() {
    clear
    log_header "去中心化同儕互評系統 - 快速設置 (階段 1-3)"
    
    echo -e "${CYAN}執行內容：${NC}"
    echo -e "  1️⃣  數據準備 (CSV → JSON)"
    echo -e "  2️⃣  任務分配 (隨機分配評分對象)"
    echo -e "  3️⃣  Token 生成 (創建評分連結)"
    echo -e "  4️⃣  資料庫初始化與 Token 導入"
    echo -e "  5️⃣  Web 服務啟動檢查"
    echo -e ""
    
    START_TIME=$(date +%s)
    
    # ===== 階段 1: 數據準備 =====
    log_header "階段 1: 數據準備"
    log_step "執行 stage1_data_processor.py..."
    cd "$PEER_EVAL_DIR"
    
    if python3 stage1_data_processor.py; then
        log_success "數據處理完成"
        student_count=$(python3 -c "import json; print(len(json.load(open('../workflow_results/1_data_preparation/midterm_data.json')).get('students', {})))")
        log_info "學生數量: $student_count"
    else
        log_error "數據處理失敗"
        exit 1
    fi
    
    # ===== 階段 2.1: 任務分配 =====
    log_header "階段 2.1: 任務分配"
    log_step "執行 stage2_assignment_engine.py..."
    
    if python3 stage2_assignment_engine.py; then
        log_success "任務分配完成"
        assignment_count=$(python3 -c "import json; data=json.load(open('../workflow_results/2_assignment/peer_assignments.json')); print(sum(len(v) for v in data.get('assignments', {}).values()))")
        log_info "總評分任務: $assignment_count"
    else
        log_error "任務分配失敗"
        exit 1
    fi
    
    # ===== 階段 2.2: Token 生成 =====
    log_header "階段 2.2: Token 生成"
    log_step "執行 stage2_token_generator.py..."
    
    if python3 stage2_token_generator.py; then
        log_success "Token 生成完成"
        TOKEN_FILE=$(ls -t ../workflow_results/3_token_generation/evaluation_tokens_*.json | head -n 1)
        token_count=$(python3 -c "import json; print(len(json.load(open('$TOKEN_FILE'))))")
        log_info "Token 數量: $token_count"
        log_success "Token 檔案: $TOKEN_FILE"
    else
        log_error "Token 生成失敗"
        exit 1
    fi
    
    # ===== 階段 2.3: 資料庫初始化 =====
    log_header "階段 2.3: 資料庫初始化與 Token 導入"
    
    DB_FILE="$PROJECT_DIR/workflow_results/4_database/evaluation.db"
    
    # 檢查資料庫是否已存在
    if [ -f "$DB_FILE" ]; then
        log_warning "資料庫已存在"
        
        # 檢查 Token 數量
        existing_tokens=$(python3 << 'EOF'
import sqlite3
try:
    conn = sqlite3.connect('/home/sophia_liang/decentralized-midterm-peer-evaluation/workflow_results/4_database/evaluation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tokens')
    print(cursor.fetchone()[0])
    conn.close()
except:
    print(0)
EOF
)
        
        if [ "$existing_tokens" -gt 0 ]; then
            log_info "現有 Tokens: $existing_tokens"
            echo -e "\n${YELLOW}選項:${NC}"
            echo -e "  1. 跳過資料庫初始化 (保留現有資料)"
            echo -e "  2. 執行 stage3_db_init.py (互動式選擇)"
            echo -e ""
            read -p "$(echo -e ${YELLOW}請選擇 [1/2, 預設=1]: ${NC})" -n 1 -r
            echo
            
            if [[ ! $REPLY =~ ^[2]$ ]]; then
                log_info "跳過資料庫初始化，保留現有 ${existing_tokens} 個 Tokens"
            else
                log_step "執行 stage3_db_init.py..."
                if python3 stage3_db_init.py; then
                    log_success "資料庫操作完成"
                else
                    log_error "資料庫操作失敗"
                    exit 1
                fi
            fi
        else
            log_info "資料庫為空，將執行初始化"
            log_step "執行 stage3_db_init.py..."
            if python3 stage3_db_init.py; then
                log_success "資料庫初始化完成"
            else
                log_error "資料庫初始化失敗"
                exit 1
            fi
        fi
    else
        log_step "執行 stage3_db_init.py..."
        if python3 stage3_db_init.py; then
            log_success "資料庫初始化完成"
        else
            log_error "資料庫初始化失敗"
            exit 1
        fi
    fi
    
    # 顯示最終資料庫統計
    echo ""
    python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/home/sophia_liang/decentralized-midterm-peer-evaluation/workflow_results/4_database/evaluation.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM tokens')
token_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM submissions')
submission_count = cursor.fetchone()[0]
print(f"✅ Tokens 總數: {token_count}")
print(f"ℹ️  提交數: {submission_count}")
conn.close()
EOF
    
    # ===== 階段 3: Web 服務更新 =====
    log_header "階段 3: Web 服務更新"
    
    if sudo systemctl is-active --quiet peereval.service; then
        log_success "Web 服務正在運行"
        
        # 重啟服務以載入最新資料
        log_step "重啟 Web 服務以更新資料..."
        if sudo systemctl restart peereval.service; then
            sleep 2
            if sudo systemctl is-active --quiet peereval.service; then
                log_success "Web 服務已重啟"
                
                # 驗證服務回應
                if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ | grep -q "200"; then
                    log_success "HTTP 回應正常"
                    log_info "管理頁面: https://ntublockchainintro2025.online"
                    
                    # 觸發首頁資料更新
                    log_step "更新首頁統計資料..."
                    curl -s http://localhost:5000/ > /dev/null && log_success "首頁資料已更新"
                else
                    log_warning "HTTP 回應異常"
                fi
            else
                log_error "Web 服務重啟失敗"
            fi
        else
            log_error "無法重啟 Web 服務"
        fi
    else
        log_warning "Web 服務未運行"
        read -p "$(echo -e ${YELLOW}是否啟動 Web 服務？ [y/N]: ${NC})" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl start peereval.service
            sleep 2
            if sudo systemctl is-active --quiet peereval.service; then
                log_success "Web 服務已啟動"
                
                # 驗證服務回應
                if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ | grep -q "200"; then
                    log_success "HTTP 回應正常"
                    log_info "管理頁面: https://ntublockchainintro2025.online"
                else
                    log_warning "HTTP 回應異常"
                fi
            else
                log_error "Web 服務啟動失敗"
            fi
        fi
    fi
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # ===== 總結 =====
    log_header "✅ 設置完成"

    log_info "執行時間: ${DURATION} 秒"
    
    cd "$PROJECT_DIR"
}

main "$@"
