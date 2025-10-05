#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫管理 CLI 工具 - 快速查看與管理資料庫
"""

import os
import sys
import argparse
from datetime import datetime

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from stage2_db_manager import DatabaseManager


def show_info(db: DatabaseManager):
    """顯示資料庫資訊"""
    db.print_database_info()


def show_tokens(db: DatabaseManager, status: str = None, limit: int = 10):
    """顯示 Token 列表"""
    print("\n" + "="*80)
    print(f"Token 列表{f' (狀態: {status})' if status else ''}")
    print("="*80)
    
    tokens = db.get_all_tokens(status=status)
    
    if not tokens:
        print("無 Token 資料")
        return
    
    # 顯示表頭
    print(f"{'Token (前8碼)':<15} {'評分者':<8} {'被評分者':<8} {'狀態':<10} {'過期時間':<20}")
    print("-"*80)
    
    # 顯示資料
    for i, token in enumerate(tokens[:limit]):
        token_short = token['token'][:8] + '...'
        expires = token['expires_at'][:19] if token['expires_at'] else 'N/A'
        
        print(f"{token_short:<15} {token['evaluator_id']:<8} {token['target_id']:<8} "
              f"{token['status']:<10} {expires:<20}")
    
    if len(tokens) > limit:
        print(f"\n... 還有 {len(tokens) - limit} 筆資料")
    
    print(f"\n總計: {len(tokens)} 個 Token")


def show_progress(db: DatabaseManager):
    """顯示評分進度"""
    print("\n" + "="*80)
    print("評分者進度")
    print("="*80)
    
    progress = db.get_evaluator_progress()
    
    if not progress:
        print("無進度資料")
        return
    
    # 顯示表頭
    print(f"{'學號':<8} {'姓名':<12} {'Email':<30} {'完成':<8} {'完成率':<8}")
    print("-"*80)
    
    # 顯示資料
    for p in progress:
        email_short = p['email'][:27] + '...' if len(p['email']) > 30 else p['email']
        print(f"{p['evaluator_id']:<8} {p['evaluator_name']:<12} {email_short:<30} "
              f"{p['completed_tokens']}/{p['total_tokens']:<6} {p['completion_rate']}%")
    
    # 顯示統計
    total_tokens = sum(p['total_tokens'] for p in progress)
    completed_tokens = sum(p['completed_tokens'] for p in progress)
    avg_completion = (completed_tokens / total_tokens * 100) if total_tokens > 0 else 0
    
    print("-"*80)
    print(f"總計: {len(progress)} 位評分者, 完成率: {avg_completion:.1f}%")


def show_submissions(db: DatabaseManager, limit: int = 10):
    """顯示評分提交"""
    print("\n" + "="*80)
    print("評分提交記錄")
    print("="*80)
    
    submissions = db.get_all_submissions()
    
    if not submissions:
        print("無提交資料")
        return
    
    # 顯示表頭
    print(f"{'ID':<6} {'評分者':<8} {'被評分者':<8} {'題目':<6} {'分數':<6} {'時間':<20}")
    print("-"*80)
    
    # 顯示資料
    for sub in submissions[:limit]:
        time = sub['submitted_at'][:19] if sub['submitted_at'] else 'N/A'
        print(f"{sub['id']:<6} {sub['evaluator_id']:<8} {sub['target_id']:<8} "
              f"{sub['question_id']:<6} {sub['score']:<6} {time:<20}")
    
    if len(submissions) > limit:
        print(f"\n... 還有 {len(submissions) - limit} 筆資料")
    
    print(f"\n總計: {len(submissions)} 筆提交")


def show_target_stats(db: DatabaseManager):
    """顯示被評分者統計"""
    print("\n" + "="*80)
    print("被評分者統計")
    print("="*80)
    
    stats = db.get_target_stats()
    
    if not stats:
        print("無統計資料")
        return
    
    # 顯示表頭
    print(f"{'被評分者':<10} {'評分數':<8} {'評分者數':<10} {'平均分':<8} {'最低分':<8} {'最高分':<8}")
    print("-"*80)
    
    # 顯示資料
    for s in stats:
        avg = f"{s['avg_score']:.1f}" if s['avg_score'] else 'N/A'
        print(f"{s['target_id']:<10} {s['total_evaluations']:<8} {s['unique_evaluators']:<10} "
              f"{avg:<8} {s['min_score']:<8} {s['max_score']:<8}")
    
    print(f"\n總計: {len(stats)} 位被評分者")


def show_logs(db: DatabaseManager, action: str = None, limit: int = 20):
    """顯示日誌"""
    print("\n" + "="*80)
    print(f"操作日誌{f' (操作: {action})' if action else ''}")
    print("="*80)
    
    logs = db.get_logs(action=action, limit=limit)
    
    if not logs:
        print("無日誌資料")
        return
    
    # 顯示表頭
    print(f"{'ID':<6} {'操作':<10} {'Token (前8碼)':<15} {'詳情':<30} {'時間':<20}")
    print("-"*80)
    
    # 顯示資料
    for log in logs:
        token_short = (log['token'][:8] + '...') if log['token'] else 'N/A'
        details = log['details'][:27] + '...' if log['details'] and len(log['details']) > 30 else (log['details'] or '')
        time = log['timestamp'][:19] if log['timestamp'] else 'N/A'
        
        print(f"{log['id']:<6} {log['action']:<10} {token_short:<15} {details:<30} {time:<20}")
    
    print(f"\n總計: 顯示最近 {len(logs)} 筆日誌")


def export_data(db: DatabaseManager, output_path: str = None):
    """導出資料"""
    print("\n導出資料到 JSON...")
    file_path = db.export_to_json(output_path)
    
    if file_path:
        print(f"✅ 導出成功: {file_path}")
    else:
        print("❌ 導出失敗")


def clear_data(db: DatabaseManager, confirm_text: str):
    """清空資料庫"""
    if confirm_text != 'YES':
        print("❌ 清空資料庫需要輸入確認文字 'YES'")
        return
    
    print("\n⚠️  清空資料庫...")
    if db.clear_database(confirm=True):
        print("✅ 資料庫已清空")
    else:
        print("❌ 清空失敗")


def main():
    """主程序"""
    parser = argparse.ArgumentParser(
        description='資料庫管理 CLI 工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 顯示資料庫資訊
  python db_cli.py --info
  
  # 顯示 Token 列表
  python db_cli.py --tokens
  
  # 顯示評分進度
  python db_cli.py --progress
  
  # 顯示評分提交
  python db_cli.py --submissions
  
  # 顯示被評分者統計
  python db_cli.py --target-stats
  
  # 顯示日誌
  python db_cli.py --logs
  
  # 導出資料
  python db_cli.py --export output.json
  
  # 清空資料庫（危險！）
  python db_cli.py --clear YES
        """
    )
    
    parser.add_argument('--db-path', '-d', type=str, help='資料庫路徑')
    parser.add_argument('--info', '-i', action='store_true', help='顯示資料庫資訊')
    parser.add_argument('--tokens', '-t', action='store_true', help='顯示 Token 列表')
    parser.add_argument('--progress', '-p', action='store_true', help='顯示評分進度')
    parser.add_argument('--submissions', '-s', action='store_true', help='顯示評分提交')
    parser.add_argument('--target-stats', action='store_true', help='顯示被評分者統計')
    parser.add_argument('--logs', '-l', action='store_true', help='顯示日誌')
    parser.add_argument('--export', '-e', type=str, metavar='FILE', help='導出資料到 JSON')
    parser.add_argument('--clear', type=str, metavar='YES', help='清空資料庫（需輸入 YES 確認）')
    parser.add_argument('--status', choices=['pending', 'submitted', 'expired'], help='Token 狀態篩選')
    parser.add_argument('--action', choices=['view', 'submit', 'error'], help='日誌操作類型篩選')
    parser.add_argument('--limit', type=int, default=10, help='顯示數量限制')
    
    args = parser.parse_args()
    
    # 如果沒有任何參數，顯示資訊
    if not any([args.info, args.tokens, args.progress, args.submissions, 
                args.target_stats, args.logs, args.export, args.clear]):
        args.info = True
    
    # 初始化資料庫
    db = DatabaseManager(db_path=args.db_path)
    
    # 執行命令
    try:
        if args.info:
            show_info(db)
        
        if args.tokens:
            show_tokens(db, status=args.status, limit=args.limit)
        
        if args.progress:
            show_progress(db)
        
        if args.submissions:
            show_submissions(db, limit=args.limit)
        
        if args.target_stats:
            show_target_stats(db)
        
        if args.logs:
            show_logs(db, action=args.action, limit=args.limit)
        
        if args.export:
            export_data(db, args.export)
        
        if args.clear:
            clear_data(db, args.clear)
    
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
