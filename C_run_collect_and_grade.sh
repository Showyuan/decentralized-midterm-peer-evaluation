#!/bin/bash
#####################################################################
# 去中心化同儕互評系統 - 收集結果與成績計算
# 從資料庫收集評分結果，執行 Vancouver 算法計算最終成績
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
    log_header "去中心化同儕互評系統 - 結果收集與成績計算"
    
    echo -e "${CYAN}執行內容：${NC}"
    echo -e "  4️⃣  收集評分結果 (從資料庫)"
    echo -e "  5️⃣  Vancouver 算法處理"
    echo -e "  6️⃣  生成驗證報告"
    echo -e "  7️⃣  匯出最終成績"
    echo -e ""
    
    START_TIME=$(date +%s)
    
    # 檢查資料庫是否存在
    if [ ! -f "$DB_FILE" ]; then
        log_error "資料庫不存在: $DB_FILE"
        log_info "請先執行: ./run_setup_and_init.sh"
        exit 1
    fi
    
    cd "$PEER_EVAL_DIR"
    
    # ===== 檢查資料完整性 =====
    log_header "檢查資料完整性"
    
    log_step "檢查資料庫狀態..."
    stats=$(python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/home/sophia_liang/decentralized-midterm-peer-evaluation/workflow_results/4_database/evaluation.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM tokens')
total_tokens = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM tokens WHERE is_used = 1')
used_tokens = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM submissions')
submissions = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT evaluator_id) FROM submissions')
completed_students = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT evaluator_id) FROM tokens')
total_students = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT target_id) FROM submissions')
evaluated_students = cursor.fetchone()[0]

conn.close()

print(f"{total_tokens}|{used_tokens}|{submissions}|{completed_students}|{total_students}|{evaluated_students}")
EOF
)
    
    IFS='|' read -r total_tokens used_tokens submissions completed_students total_students evaluated_students <<< "$stats"
    
    echo ""
    log_info "Token 總數: $total_tokens"
    log_info "已使用 Token: $used_tokens"
    log_info "收到的評分: $submissions"
    log_info "已完成學生: $completed_students / $total_students"
    log_info "被評學生: $evaluated_students / $total_students"
    
    completion_rate=$(python3 -c "print(f'{$completed_students/$total_students*100:.1f}')")
    echo ""
    log_info "完成率: ${completion_rate}%"
    
    if [ "$submissions" -eq 0 ]; then
        log_error "資料庫中沒有任何評分資料"
        log_info "請等待學生完成評分，或使用測試工具填充資料"
        log_info "測試填充: cd peer_evaluation && python3 tool_db_cli.py --random-fill"
        exit 1
    fi
    
    # 詢問是否繼續
    if [ "$completed_students" -lt "$total_students" ]; then
        echo ""
        log_warning "還有 $((total_students - completed_students)) 位學生尚未完成評分"
        read -p "$(echo -e ${YELLOW}是否要繼續處理現有資料? [y/N]: ${NC})" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作已取消"
            log_info "等待更多學生完成後再執行"
            exit 0
        fi
    fi
    
    # ===== 階段 4: 收集結果 =====
    log_header "階段 4: 收集評分結果"
    log_step "執行 stage4_result_collector_web.py..."
    
    if python3 -c "
from stage4_result_collector_web import ResultCollectorWeb
collector = ResultCollectorWeb()
results = collector.collect_results()
json_path = collector.export_to_json(results)
excel_path = collector.export_to_excel(results)
vancouver_path = collector.export_for_vancouver(results)
print(f'\n✅ 結果收集完成')
print(f'   • JSON: {json_path}')
print(f'   • Excel: {excel_path}')
print(f'   • Vancouver 輸入: {vancouver_path}')
"; then
        log_success "評分結果已匯出"
        
        # 統計資訊
        result_count=$(python3 -c "import json; data=json.load(open('../workflow_results/5_evaluation_results/evaluation_results.json')); print(data['metadata']['total_evaluations'])")
        log_info "評分記錄數: $result_count"
    else
        log_error "結果收集失敗"
        exit 1
    fi
    
    # ===== 階段 5: Vancouver 算法 =====
    log_header "階段 5: Vancouver 算法處理"
    log_step "執行 stage5_vancouver_processor.py..."
    
    if python3 stage5_vancouver_processor.py; then
        log_success "Vancouver 算法處理完成"
        
        # 找到最新的結果文件
        VANCOUVER_FILE=$(ls -t ../workflow_results/6_vancouver_results/vancouver_results_*.json 2>/dev/null | head -n 1)
        if [ -n "$VANCOUVER_FILE" ]; then
            log_success "Vancouver 結果: $(basename $VANCOUVER_FILE)"
            
            # 顯示部分統計
            python3 << EOF
import json
with open('$VANCOUVER_FILE', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
stats = data.get('summary_statistics', {})
print(f"\n📊 Vancouver 統計:")
print(f"   • 平均最終成績: {stats.get('avg_final_grade', 0):.2f}")
print(f"   • 標準差: {stats.get('std_final_grade', 0):.2f}")
print(f"   • 平均共識分數: {stats.get('avg_consensus_score', 0):.2f}")
print(f"   • 平均聲譽分數: {stats.get('avg_reputation', 0):.3f}")
print(f"   • 保護機制使用: {stats.get('protection_used_count', 0)} 人")
EOF
        fi
    else
        log_error "Vancouver 處理失敗"
        exit 1
    fi
    
    # ===== 階段 6: 驗證報告 =====
    log_header "階段 6: 生成驗證報告"
    log_step "執行 stage5_verification_report.py..."
    
    if python3 stage5_verification_report.py; then
        log_success "驗證報告生成完成"
        log_info "報告位置: workflow_results/7_final_reports/vancouver_verification_report.xlsx"
    else
        log_warning "驗證報告生成失敗（可能缺少比較數據）"
    fi
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # ===== 總結 =====
    log_header "✅ 處理完成"
    
    echo -e "${GREEN}成績計算完成！${NC}\n"
    
    echo -e "${CYAN}📁 生成的檔案：${NC}"
    echo -e "  • workflow_results/5_evaluation_results/evaluation_results.json"
    echo -e "  • workflow_results/5_evaluation_results/evaluation_results.xlsx"
    echo -e "  • workflow_results/6_vancouver_results/vancouver_results_*.json"
    echo -e "  • workflow_results/6_vancouver_results/vancouver_results_*.xlsx"
    echo -e "  • workflow_results/7_final_reports/vancouver_verification_report.xlsx"
    
    echo -e "\n${CYAN}📊 最終成績檔案：${NC}"
    LATEST_VANCOUVER_EXCEL=$(ls -t ../workflow_results/6_vancouver_results/vancouver_results_*.xlsx 2>/dev/null | head -n 1)
    if [ -n "$LATEST_VANCOUVER_EXCEL" ]; then
        echo -e "  ${GREEN}$(basename $LATEST_VANCOUVER_EXCEL)${NC}"
        log_info "完整路徑: $LATEST_VANCOUVER_EXCEL"
    fi
    
    echo -e "\n${CYAN}💡 後續步驟：${NC}"
    echo -e "  • 查看 Excel 成績單"
    echo -e "  • 檢查驗證報告確認計算正確性"
    echo -e "  • 匯出成績到校務系統"
    
    log_info "執行時間: ${DURATION} 秒"
    
    cd "$PROJECT_DIR"
}

main "$@"
