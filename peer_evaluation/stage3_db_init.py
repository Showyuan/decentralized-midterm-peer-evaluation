#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫初始化腳本 - 創建資料庫並導入 Tokens
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from stage2_db_manager import DatabaseManager
from stage0_config_unified import PeerEvaluationConfig


def find_latest_token_file(tokens_dir: str) -> str:
    """
    找到最新的 token 文件
    
    Args:
        tokens_dir: Token 目錄路徑
        
    Returns:
        最新的 token 文件路徑
    """
    token_files = list(Path(tokens_dir).glob("evaluation_tokens_*.json"))
    if not token_files:
        raise FileNotFoundError(f"在 {tokens_dir} 中找不到 token 文件")
    
    # 按修改時間排序，返回最新的
    latest_file = max(token_files, key=lambda p: p.stat().st_mtime)
    return str(latest_file)


def load_student_data(data_file: str) -> dict:
    """
    載入學生資料
    
    Args:
        data_file: 學生資料文件路徑
        
    Returns:
        學生資料字典
    """
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('students', {})


def import_tokens_to_db(db_manager: DatabaseManager, token_file: str, students_data: dict):
    """
    將 tokens 導入資料庫
    
    Args:
        db_manager: 資料庫管理器
        token_file: Token 文件路徑
        students_data: 學生資料
    """
    print(f"\n📥 讀取 Token 文件: {token_file}")
    
    with open(token_file, 'r', encoding='utf-8') as f:
        token_data = json.load(f)
    
    tokens_dict = token_data.get('tokens', {})
    
    print(f"✓ 找到 {len(tokens_dict)} 位學生的 Tokens")
    
    # 首先導入學生資料到 students 表
    print(f"\n📥 導入學生資料到 students 表...")
    student_count = 0
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        for student_id, student_info in students_data.items():
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO students (student_id, student_name, email)
                    VALUES (?, ?, ?)
                """, (
                    student_id,
                    student_info.get('name', student_id),
                    student_info.get('email', f'{student_id}@example.com')
                ))
                if cursor.rowcount > 0:
                    student_count += 1
            except Exception as e:
                print(f"⚠️  學生 {student_id} 插入失敗: {e}")
        conn.commit()
    
    print(f"✓ 成功導入 {student_count} 位學生資料")
    
    # 準備批次導入的 token 列表
    tokens_to_import = []
    
    for evaluator_id, tokens in tokens_dict.items():
        # 獲取學生資訊
        student_info = students_data.get(evaluator_id, {})
        evaluator_name = student_info.get('name', evaluator_id)
        email = student_info.get('email', f'{evaluator_id}@example.com')
        
        for token_obj in tokens:
            token_dict = {
                'token': token_obj['token'],
                'evaluator_id': evaluator_id,
                'evaluator_name': evaluator_name,
                'email': email,
                'target_id': token_obj['target_id'],
                'questions': token_obj['questions'],
                'created_at': token_obj['created_at'],
                'expires_at': token_obj['expires_at'],
                'status': token_obj.get('status', 'pending'),
                'used': token_obj.get('used', False)
            }
            tokens_to_import.append(token_dict)
    
    # 批次導入 tokens
    print(f"\n⏳ 導入 {len(tokens_to_import)} 個 Tokens 到資料庫...")
    success_count, fail_count = db_manager.save_tokens_batch(tokens_to_import)
    
    print(f"\n✅ Token 導入完成:")
    print(f"   • 成功: {success_count} 個")
    print(f"   • 失敗/已存在: {fail_count} 個")
    print(f"   • 總計: {len(tokens_to_import)} 個")


def main():
    """主函數"""
    print("=" * 60)
    print("資料庫初始化與 Token 導入")
    print("=" * 60)
    
    # 載入配置
    config = PeerEvaluationConfig()
    
    try:
        # 檢查資料庫是否已存在且有資料
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "workflow_results/4_database/evaluation.db"
        )
        
        db_exists = os.path.exists(db_path)
        tokens_exist = False
        
        if db_exists:
            print(f"\n⚠️  檢測到資料庫已存在: {db_path}")
            # 檢查是否有 tokens
            import sqlite3
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM tokens')
                token_count = cursor.fetchone()[0]
                conn.close()
                
                if token_count > 0:
                    tokens_exist = True
                    print(f"   資料庫中已有 {token_count} 個 Tokens")
                    print("\n" + "=" * 60)
                    print("⚠️  資料庫已存在且包含資料")
                    print("=" * 60)
                    print("\n選項:")
                    print("  1. 跳過初始化 (保留現有資料)")
                    print("  2. 重新初始化 (會清空所有資料)")
                    print("  3. 僅導入新 Tokens (保留現有 Tokens)")
                    
                    choice = input("\n請選擇 [1/2/3, 預設=1]: ").strip() or "1"
                    
                    if choice == "1":
                        print("\n✅ 跳過初始化，保留現有資料")
                        print(f"\n資料庫位置: {db_path}")
                        print(f"Token 數量: {token_count}")
                        return 0
                    elif choice == "2":
                        print("\n⚠️  將刪除現有資料庫並重新初始化...")
                        confirm = input("確定要繼續嗎? [y/N]: ").strip().lower()
                        if confirm != 'y':
                            print("❌ 操作已取消")
                            return 0
                        os.remove(db_path)
                        print("✅ 舊資料庫已刪除")
                    elif choice == "3":
                        print("\n✅ 將導入新 Tokens (跳過已存在的)")
                        # 繼續執行，但不重新初始化資料庫
                    else:
                        print("❌ 無效的選項")
                        return 1
            except Exception as e:
                print(f"   檢查資料庫時出錯: {e}")
                print("   將繼續初始化...")
        
        # 1. 初始化資料庫管理器 (會自動創建資料庫)
        if not db_exists or not tokens_exist:
            print("\n🔧 初始化資料庫...")
        else:
            print("\n🔧 連接資料庫...")
        
        db_manager = DatabaseManager()
        
        if not db_exists:
            print(f"✅ 資料庫創建成功: {db_manager.db_path}")
        else:
            print(f"✅ 資料庫連接成功: {db_manager.db_path}")
        
        # 2. 找到最新的 token 文件
        tokens_dir = config.ensure_output_dir('stage3_tokens')
        token_file = find_latest_token_file(tokens_dir)
        
        # 3. 載入學生資料
        print("\n📚 載入學生資料...")
        student_data_file = config.get_path('stage1_output', 'processed_data')
        students_data = load_student_data(student_data_file)
        print(f"✓ 載入 {len(students_data)} 位學生資料")
        
        # 4. 導入 tokens
        import_tokens_to_db(db_manager, token_file, students_data)
        
        # 5. 顯示資料庫統計
        print("\n" + "=" * 60)
        print("📊 資料庫統計")
        print("=" * 60)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Token 統計
            cursor.execute("SELECT COUNT(*) FROM tokens")
            total_tokens = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tokens WHERE status = 'pending'")
            pending_tokens = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tokens WHERE is_used = 1")
            used_tokens = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tokens WHERE datetime(expires_at) < datetime('now')")
            expired_tokens = cursor.fetchone()[0]
            
            # 提交統計
            cursor.execute("SELECT COUNT(*) FROM submissions")
            total_submissions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT evaluator_id) FROM tokens")
            unique_evaluators = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT target_id) FROM tokens")
            unique_targets = cursor.fetchone()[0]
        
        print(f"  • Token 總數: {total_tokens}")
        print(f"  • 待使用: {pending_tokens}")
        print(f"  • 已使用: {used_tokens}")
        print(f"  • 已過期: {expired_tokens}")
        print(f"  • 提交總數: {total_submissions}")
        print(f"  • 評分者數: {unique_evaluators}")
        print(f"  • 被評者數: {unique_targets}")
        
        print("\n" + "=" * 60)
        print("✅ 資料庫初始化完成")
        print("=" * 60)
        print(f"\n資料庫位置: {db_manager.db_path}")
        print(f"Web 管理頁面: https://ntublockchainintro2025.online")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ 錯誤: {e}")
        print("   請先執行 stage2_token_generator.py 生成 tokens")
        return 1
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
