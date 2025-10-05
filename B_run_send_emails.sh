#!/bin/bash
#####################################################################
# 去中心化同儕互評系統 - 發送評量通知 Email
# 讀取資料庫中的 Tokens 並發送評量連結給學生
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
DB_FILE="$PROJECT_DIR/workflow_results/4_database/evaluation.db"

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
    log_header "去中心化同儕互評系統 - 發送評量通知"
    
    START_TIME=$(date +%s)
    
    # 檢查資料庫是否存在
    if [ ! -f "$DB_FILE" ]; then
        log_error "資料庫不存在: $DB_FILE"
        log_info "請先執行: ./run_setup_and_init.sh"
        exit 1
    fi
    
    # 檢查 Token 數量
    cd "$PEER_EVAL_DIR"
    
    log_step "檢查資料庫狀態..."
    token_stats=$(python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/home/sophia_liang/decentralized-midterm-peer-evaluation/workflow_results/4_database/evaluation.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM tokens')
total = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM tokens WHERE is_used = 0')
pending = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT evaluator_id) FROM tokens')
students = cursor.fetchone()[0]

conn.close()

print(f"{total}|{pending}|{students}")
EOF
)
    
    IFS='|' read -r total_tokens pending_tokens total_students <<< "$token_stats"
    
    log_info "Token 總數: $total_tokens"
    log_info "待使用: $pending_tokens"
    log_info "學生數: $total_students"
    
    if [ "$total_tokens" -eq 0 ]; then
        log_error "資料庫中沒有 Tokens"
        log_info "請先執行: ./run_setup_and_init.sh"
        exit 1
    fi
    
    echo ""
    log_header "Email 發送選項"
    
    echo -e "${CYAN}發送模式：${NC}"
    echo -e "  1️⃣  測試模式 (僅顯示要發送的內容，不實際發送)"
    echo -e "  2️⃣  發送給特定學生 (輸入學號)"
    echo -e "  3️⃣  發送給所有學生"
    echo -e "  4️⃣  僅發送給尚未使用 Token 的學生"
    echo -e ""
    
    read -p "$(echo -e ${YELLOW}請選擇模式 [1/2/3/4, 預設=1]: ${NC})" mode
    mode=${mode:-1}
    
    case $mode in
        1)
            log_info "測試模式 - 預覽 Email 內容"
            log_step "執行 stage3_email_sender.py --dry-run..."
            if python3 stage3_email_sender.py --dry-run; then
                log_success "測試完成"
            else
                log_error "測試失敗"
                exit 1
            fi
            ;;
        2)
            echo ""
            read -p "$(echo -e ${YELLOW}請輸入學生學號: ${NC})" student_id
            if [ -z "$student_id" ]; then
                log_error "學號不能為空"
                exit 1
            fi
            log_step "發送 Email 給學生: $student_id"
            if python3 stage3_email_sender.py --student "$student_id"; then
                log_success "Email 發送完成"
            else
                log_error "Email 發送失敗"
                exit 1
            fi
            ;;
        3)
            echo ""
            log_warning "即將發送 Email 給所有 $total_students 位學生"
            read -p "$(echo -e ${YELLOW}確定要繼續嗎? [y/N]: ${NC})" -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "操作已取消"
                exit 0
            fi
            log_step "發送 Email 給所有學生..."
            if python3 stage3_email_sender.py --all; then
                log_success "Email 批次發送完成"
            else
                log_error "Email 發送失敗"
                exit 1
            fi
            ;;
        4)
            pending_students=$(python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/home/sophia_liang/decentralized-midterm-peer-evaluation/workflow_results/4_database/evaluation.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(DISTINCT evaluator_id) FROM tokens WHERE is_used = 0')
print(cursor.fetchone()[0])
conn.close()
EOF
)
            echo ""
            log_warning "即將發送提醒 Email 給 $pending_students 位尚未完成評量的學生"
            read -p "$(echo -e ${YELLOW}確定要繼續嗎? [y/N]: ${NC})" -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "操作已取消"
                exit 0
            fi
            log_step "發送提醒 Email..."
            if python3 stage3_email_sender.py --pending; then
                log_success "提醒 Email 發送完成"
            else
                log_error "Email 發送失敗"
                exit 1
            fi
            ;;
        *)
            log_error "無效的選項"
            exit 1
            ;;
    esac
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # 顯示當前狀態
    echo ""
    log_header "📊 當前狀態"
    
    python3 << 'EOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/home/sophia_liang/decentralized-midterm-peer-evaluation/workflow_results/4_database/evaluation.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM tokens WHERE is_used = 1')
completed = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM submissions')
submissions = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT evaluator_id) FROM submissions')
completed_students = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT evaluator_id) FROM tokens')
total_students = cursor.fetchone()[0]

conn.close()

print(f"  • 已完成評量學生: {completed_students}/{total_students}")
print(f"  • 已使用 Token: {completed}/{80}")
print(f"  • 收到的評分: {submissions}")
print(f"  • 完成率: {completed_students/total_students*100:.1f}%")
EOF
    
    echo ""
    log_header "✅ 完成"
    log_info "執行時間: ${DURATION} 秒"
    
    echo -e "\n${CYAN}💡 下一步：${NC}"
    echo -e "  • 追蹤進度: ${BLUE}https://ntublockchainintro2025.online${NC}"
    echo -e "  • 查看統計: ${BLUE}cd peer_evaluation && python3 tool_db_cli.py --stats${NC}"
    echo -e "  • 收集結果: ${BLUE}./run_collect_and_grade.sh${NC}"
    
    cd "$PROJECT_DIR"
}

main "$@"
