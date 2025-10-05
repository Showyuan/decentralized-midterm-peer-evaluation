#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫管理器 - 管理 Token、評分提交與日誌
支援 SQLite 資料庫的完整 CRUD 操作
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from stage0_config_web import WebConfig
except ImportError:
    from .stage0_config_web import WebConfig


class DatabaseManager:
    """資料庫管理器 - 管理所有資料庫操作"""
    
    def __init__(self, db_path: str = None, config: WebConfig = None):
        """
        初始化資料庫管理器
        
        Args:
            db_path: 資料庫檔案路徑
            config: Web 配置物件
        """
        self.config = config or WebConfig()
        self.db_path = db_path or self.config.DATABASE_PATH
        
        # 確保資料庫目錄存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        print(f"資料庫管理器初始化")
        print(f"資料庫路徑: {self.db_path}")
        
        # 初始化資料庫
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """
        獲取資料庫連接（使用 context manager）
        
        Yields:
            sqlite3.Connection: 資料庫連接
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 允許通過列名訪問
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self) -> bool:
        """
        初始化資料庫結構
        
        Returns:
            bool: 是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # === Table 1: tokens ===
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tokens (
                        token TEXT PRIMARY KEY,
                        evaluator_id TEXT NOT NULL,
                        evaluator_name TEXT,
                        email TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        questions TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        status TEXT DEFAULT 'pending',
                        is_used BOOLEAN DEFAULT 0,
                        used_at TIMESTAMP,
                        ip_address TEXT,
                        user_agent TEXT
                    )
                """)
                
                # === Table 2: submissions ===
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS submissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token TEXT NOT NULL,
                        evaluator_id TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        question_id TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        comment TEXT,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ip_address TEXT,
                        user_agent TEXT,
                        FOREIGN KEY (token) REFERENCES tokens(token)
                    )
                """)
                
                # === Table 3: submission_logs ===
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS submission_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token TEXT,
                        action TEXT NOT NULL,
                        details TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # === Table 4: students (元數據) ===
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        student_id TEXT PRIMARY KEY,
                        student_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 創建索引以提升查詢效能
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tokens_evaluator 
                    ON tokens(evaluator_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tokens_status 
                    ON tokens(status)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_submissions_token 
                    ON submissions(token)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_submissions_evaluator 
                    ON submissions(evaluator_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_submissions_target 
                    ON submissions(target_id)
                """)
                
                print("✅ 資料庫結構初始化完成")
                return True
                
        except Exception as e:
            print(f"❌ 資料庫初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==================== Token 管理 ====================
    
    def save_token(self, token_data: Dict) -> bool:
        """
        儲存 Token 到資料庫
        
        Args:
            token_data: Token 資料字典
            
        Returns:
            bool: 是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 將 questions 列表轉換為 JSON 字串
                questions_json = json.dumps(token_data.get('questions', []))
                
                cursor.execute("""
                    INSERT INTO tokens (
                        token, evaluator_id, evaluator_name, email, target_id,
                        questions, created_at, expires_at, status, is_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    token_data['token'],
                    token_data['evaluator_id'],
                    token_data.get('evaluator_name', ''),
                    token_data.get('email', ''),
                    token_data['target_id'],
                    questions_json,
                    token_data.get('created_at', datetime.now().isoformat()),
                    token_data['expires_at'],
                    token_data.get('status', 'pending'),
                    token_data.get('used', False)
                ))
                
                return True
                
        except sqlite3.IntegrityError:
            print(f"⚠️  Token 已存在: {token_data['token']}")
            return False
        except Exception as e:
            print(f"❌ Token 儲存失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_tokens_batch(self, tokens: List[Dict]) -> Tuple[int, int]:
        """
        批次儲存 Token
        
        Args:
            tokens: Token 列表
            
        Returns:
            Tuple[int, int]: (成功數量, 失敗數量)
        """
        success_count = 0
        fail_count = 0
        
        for token_data in tokens:
            if self.save_token(token_data):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"批次儲存完成: {success_count} 成功, {fail_count} 失敗")
        return success_count, fail_count
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """
        獲取 Token 資訊
        
        Args:
            token: Token 字串
            
        Returns:
            Optional[Dict]: Token 資訊字典，不存在則返回 None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tokens WHERE token = ?
                """, (token,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            print(f"❌ Token 查詢失敗: {e}")
            return None
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict], str]:
        """
        驗證 Token 是否有效
        
        Args:
            token: Token 字串
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (是否有效, Token資訊, 錯誤訊息)
        """
        token_info = self.get_token_info(token)
        
        if not token_info:
            return False, None, "Token 不存在"
        
        # 檢查是否已使用
        if token_info['is_used']:
            return False, token_info, "Token 已被使用"
        
        # 檢查狀態
        if token_info['status'] != 'pending':
            return False, token_info, f"Token 狀態異常: {token_info['status']}"
        
        # 檢查是否過期
        expires_at = datetime.fromisoformat(token_info['expires_at'])
        if datetime.now() > expires_at:
            return False, token_info, "Token 已過期"
        
        return True, token_info, ""
    
    def mark_token_used(self, token: str, ip_address: str = None, user_agent: str = None) -> bool:
        """
        標記 Token 為已使用
        
        Args:
            token: Token 字串
            ip_address: IP 位址
            user_agent: User Agent
            
        Returns:
            bool: 是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tokens 
                    SET is_used = 1, 
                        status = 'submitted',
                        used_at = ?,
                        ip_address = ?,
                        user_agent = ?
                    WHERE token = ?
                """, (datetime.now().isoformat(), ip_address, user_agent, token))
                
                if cursor.rowcount > 0:
                    print(f"✅ Token 標記為已使用: {token[:8]}...")
                    return True
                else:
                    print(f"⚠️  Token 不存在: {token}")
                    return False
                    
        except Exception as e:
            print(f"❌ Token 標記失敗: {e}")
            return False
    
    def get_tokens_by_evaluator(self, evaluator_id: str) -> List[Dict]:
        """
        獲取評分者的所有 Token
        
        Args:
            evaluator_id: 評分者學號
            
        Returns:
            List[Dict]: Token 列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tokens 
                    WHERE evaluator_id = ?
                    ORDER BY created_at DESC
                """, (evaluator_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ Token 查詢失敗: {e}")
            return []
    
    def get_all_tokens(self, status: str = None) -> List[Dict]:
        """
        獲取所有 Token
        
        Args:
            status: 篩選狀態 (pending, submitted, expired)
            
        Returns:
            List[Dict]: Token 列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute("""
                        SELECT * FROM tokens 
                        WHERE status = ?
                        ORDER BY created_at DESC
                    """, (status,))
                else:
                    cursor.execute("""
                        SELECT * FROM tokens 
                        ORDER BY created_at DESC
                    """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ Token 查詢失敗: {e}")
            return []
    
    # ==================== 評分提交管理 ====================
    
    def save_submission(self, submission_data: Dict) -> Optional[int]:
        """
        儲存評分提交
        
        Args:
            submission_data: 評分資料字典
            
        Returns:
            Optional[int]: 提交 ID，失敗則返回 None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO submissions (
                        token, evaluator_id, target_id, question_id,
                        score, comment, submitted_at, ip_address, user_agent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    submission_data['token'],
                    submission_data['evaluator_id'],
                    submission_data['target_id'],
                    submission_data['question_id'],
                    submission_data['score'],
                    submission_data.get('comment', ''),
                    submission_data.get('submitted_at', datetime.now().isoformat()),
                    submission_data.get('ip_address', ''),
                    submission_data.get('user_agent', '')
                ))
                
                return cursor.lastrowid
                
        except Exception as e:
            print(f"❌ 評分提交失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_submissions_batch(self, submissions: List[Dict]) -> Tuple[int, int]:
        """
        批次儲存評分提交
        
        Args:
            submissions: 評分列表
            
        Returns:
            Tuple[int, int]: (成功數量, 失敗數量)
        """
        success_count = 0
        fail_count = 0
        
        for submission_data in submissions:
            if self.save_submission(submission_data):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"批次提交完成: {success_count} 成功, {fail_count} 失敗")
        return success_count, fail_count
    
    def get_submissions_by_token(self, token: str) -> List[Dict]:
        """
        獲取指定 Token 的所有提交
        
        Args:
            token: Token 字串
            
        Returns:
            List[Dict]: 提交列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM submissions 
                    WHERE token = ?
                    ORDER BY submitted_at ASC
                """, (token,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 提交查詢失敗: {e}")
            return []
    
    def get_submissions_by_evaluator(self, evaluator_id: str) -> List[Dict]:
        """
        獲取評分者的所有提交
        
        Args:
            evaluator_id: 評分者學號
            
        Returns:
            List[Dict]: 提交列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM submissions 
                    WHERE evaluator_id = ?
                    ORDER BY submitted_at DESC
                """, (evaluator_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 提交查詢失敗: {e}")
            return []
    
    def get_submissions_by_target(self, target_id: str) -> List[Dict]:
        """
        獲取被評分者收到的所有評分
        
        Args:
            target_id: 被評分者學號
            
        Returns:
            List[Dict]: 評分列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM submissions 
                    WHERE target_id = ?
                    ORDER BY submitted_at DESC
                """, (target_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 提交查詢失敗: {e}")
            return []
    
    def get_all_submissions(self) -> List[Dict]:
        """
        獲取所有評分提交
        
        Returns:
            List[Dict]: 所有提交列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM submissions 
                    ORDER BY submitted_at DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 提交查詢失敗: {e}")
            return []
    
    # ==================== 日誌管理 ====================
    
    def log_action(self, 
                   action: str, 
                   details: str = None,
                   token: str = None,
                   ip_address: str = None,
                   user_agent: str = None) -> bool:
        """
        記錄操作日誌
        
        Args:
            action: 操作類型 (view, submit, error, etc.)
            details: 詳細資訊
            token: Token (可選)
            ip_address: IP 位址
            user_agent: User Agent
            
        Returns:
            bool: 是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO submission_logs (
                        token, action, details, ip_address, user_agent, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    token,
                    action,
                    details,
                    ip_address,
                    user_agent,
                    datetime.now().isoformat()
                ))
                
                return True
                
        except Exception as e:
            print(f"❌ 日誌記錄失敗: {e}")
            return False
    
    def get_logs(self, 
                 token: str = None, 
                 action: str = None, 
                 limit: int = 100) -> List[Dict]:
        """
        查詢日誌
        
        Args:
            token: Token 篩選 (可選)
            action: 操作類型篩選 (可選)
            limit: 返回數量限制
            
        Returns:
            List[Dict]: 日誌列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if token and action:
                    cursor.execute("""
                        SELECT * FROM submission_logs 
                        WHERE token = ? AND action = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (token, action, limit))
                elif token:
                    cursor.execute("""
                        SELECT * FROM submission_logs 
                        WHERE token = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (token, limit))
                elif action:
                    cursor.execute("""
                        SELECT * FROM submission_logs 
                        WHERE action = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (action, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM submission_logs 
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 日誌查詢失敗: {e}")
            return []
    
    # ==================== 統計與分析 ====================
    
    def get_submission_stats(self) -> Dict[str, Any]:
        """
        獲取提交統計資訊
        
        Returns:
            Dict: 統計資訊字典
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 總 Token 數量
                cursor.execute("SELECT COUNT(*) as count FROM tokens")
                total_tokens = cursor.fetchone()['count']
                
                # 已使用 Token 數量
                cursor.execute("SELECT COUNT(*) as count FROM tokens WHERE is_used = 1")
                used_tokens = cursor.fetchone()['count']
                
                # 待使用 Token 數量
                cursor.execute("SELECT COUNT(*) as count FROM tokens WHERE is_used = 0")
                pending_tokens = cursor.fetchone()['count']
                
                # 總評分提交數量
                cursor.execute("SELECT COUNT(*) as count FROM submissions")
                total_submissions = cursor.fetchone()['count']
                
                # 唯一評分者數量
                cursor.execute("SELECT COUNT(DISTINCT evaluator_id) as count FROM submissions")
                unique_evaluators = cursor.fetchone()['count']
                
                # 唯一被評分者數量
                cursor.execute("SELECT COUNT(DISTINCT target_id) as count FROM submissions")
                unique_targets = cursor.fetchone()['count']
                
                # 計算完成率
                completion_rate = (used_tokens / total_tokens * 100) if total_tokens > 0 else 0
                
                return {
                    'total_tokens': total_tokens,
                    'used_tokens': used_tokens,
                    'pending_tokens': pending_tokens,
                    'completion_rate': round(completion_rate, 2),
                    'total_submissions': total_submissions,
                    'unique_evaluators': unique_evaluators,
                    'unique_targets': unique_targets,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ 統計查詢失敗: {e}")
            return {}
    
    def get_evaluator_progress(self) -> List[Dict]:
        """
        獲取每位評分者的進度
        
        Returns:
            List[Dict]: 評分者進度列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        t.evaluator_id,
                        t.evaluator_name,
                        t.email,
                        COUNT(*) as total_tokens,
                        SUM(CASE WHEN t.is_used = 1 THEN 1 ELSE 0 END) as completed_tokens,
                        ROUND(SUM(CASE WHEN t.is_used = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as completion_rate
                    FROM tokens t
                    GROUP BY t.evaluator_id, t.evaluator_name, t.email
                    ORDER BY completion_rate DESC, t.evaluator_id
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 進度查詢失敗: {e}")
            return []
    
    def get_target_stats(self) -> List[Dict]:
        """
        獲取每位被評分者的統計
        
        Returns:
            List[Dict]: 被評分者統計列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.target_id,
                        COUNT(*) as total_evaluations,
                        COUNT(DISTINCT s.evaluator_id) as unique_evaluators,
                        AVG(s.score) as avg_score,
                        MIN(s.score) as min_score,
                        MAX(s.score) as max_score
                    FROM submissions s
                    GROUP BY s.target_id
                    ORDER BY s.target_id
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 統計查詢失敗: {e}")
            return []
    
    # ==================== 學生管理 ====================
    
    def save_student(self, student_data: Dict) -> bool:
        """
        儲存學生資料
        
        Args:
            student_data: 學生資料字典
            
        Returns:
            bool: 是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO students (
                        student_id, student_name, email, created_at
                    ) VALUES (?, ?, ?, ?)
                """, (
                    student_data['student_id'],
                    student_data['student_name'],
                    student_data['email'],
                    student_data.get('created_at', datetime.now().isoformat())
                ))
                
                return True
                
        except Exception as e:
            print(f"❌ 學生資料儲存失敗: {e}")
            return False
    
    def save_students_batch(self, students: List[Dict]) -> Tuple[int, int]:
        """
        批次儲存學生資料
        
        Args:
            students: 學生列表
            
        Returns:
            Tuple[int, int]: (成功數量, 失敗數量)
        """
        success_count = 0
        fail_count = 0
        
        for student_data in students:
            if self.save_student(student_data):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"批次儲存完成: {success_count} 成功, {fail_count} 失敗")
        return success_count, fail_count
    
    def get_student(self, student_id: str) -> Optional[Dict]:
        """
        獲取學生資料
        
        Args:
            student_id: 學號
            
        Returns:
            Optional[Dict]: 學生資料，不存在則返回 None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM students WHERE student_id = ?
                """, (student_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            print(f"❌ 學生查詢失敗: {e}")
            return None
    
    def get_all_students(self) -> List[Dict]:
        """
        獲取所有學生資料
        
        Returns:
            List[Dict]: 學生列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM students 
                    ORDER BY student_id
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 學生查詢失敗: {e}")
            return []
    
    # ==================== 工具函數 ====================
    
    def export_to_json(self, output_path: str = None) -> str:
        """
        導出所有資料到 JSON
        
        Args:
            output_path: 輸出路徑
            
        Returns:
            str: 導出的檔案路徑
        """
        try:
            data = {
                'tokens': self.get_all_tokens(),
                'submissions': self.get_all_submissions(),
                'students': self.get_all_students(),
                'stats': self.get_submission_stats(),
                'exported_at': datetime.now().isoformat()
            }
            
            if not output_path:
                output_path = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 資料導出成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 資料導出失敗: {e}")
            return ""
    
    def clear_database(self, confirm: bool = False) -> bool:
        """
        清空資料庫（危險操作！）
        
        Args:
            confirm: 必須為 True 才執行
            
        Returns:
            bool: 是否成功
        """
        if not confirm:
            print("⚠️  清空資料庫需要確認參數 confirm=True")
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM submissions")
                cursor.execute("DELETE FROM tokens")
                cursor.execute("DELETE FROM submission_logs")
                cursor.execute("DELETE FROM students")
                
                print("✅ 資料庫已清空")
                return True
                
        except Exception as e:
            print(f"❌ 資料庫清空失敗: {e}")
            return False
    
    def print_database_info(self):
        """列印資料庫資訊"""
        print("\n" + "="*60)
        print("資料庫資訊")
        print("="*60)
        print(f"資料庫路徑: {self.db_path}")
        print(f"資料庫大小: {os.path.getsize(self.db_path) / 1024:.2f} KB")
        
        stats = self.get_submission_stats()
        print(f"\n統計資訊:")
        print(f"  總 Token 數: {stats.get('total_tokens', 0)}")
        print(f"  已使用: {stats.get('used_tokens', 0)}")
        print(f"  待使用: {stats.get('pending_tokens', 0)}")
        print(f"  完成率: {stats.get('completion_rate', 0)}%")
        print(f"  總評分: {stats.get('total_submissions', 0)}")
        print(f"  評分者: {stats.get('unique_evaluators', 0)} 人")
        print(f"  被評分者: {stats.get('unique_targets', 0)} 人")
        print("="*60 + "\n")


def main():
    """測試與示範"""
    print("資料庫管理器測試")
    print("="*60)
    
    # 初始化資料庫
    db = DatabaseManager()
    
    # 顯示資料庫資訊
    db.print_database_info()
    
    # 測試 Token 操作
    print("\n測試 Token 操作:")
    test_token = {
        'token': 'test-token-12345',
        'evaluator_id': 'A01',
        'evaluator_name': '測試學生',
        'email': 'test@example.com',
        'target_id': 'B02',
        'questions': ['Q1', 'Q2', 'Q3'],
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now().replace(hour=23, minute=59, second=59)).isoformat(),
        'status': 'pending',
        'used': False
    }
    
    if db.save_token(test_token):
        print("✅ Token 儲存成功")
        
        # 驗證 Token
        is_valid, token_info, error = db.validate_token('test-token-12345')
        if is_valid:
            print(f"✅ Token 驗證通過")
        else:
            print(f"❌ Token 驗證失敗: {error}")
    
    # 測試評分提交
    print("\n測試評分提交:")
    test_submission = {
        'token': 'test-token-12345',
        'evaluator_id': 'A01',
        'target_id': 'B02',
        'question_id': 'Q1',
        'score': 18,
        'comment': '回答完整且深入',
        'ip_address': '127.0.0.1',
        'user_agent': 'Test Browser'
    }
    
    submission_id = db.save_submission(test_submission)
    if submission_id:
        print(f"✅ 評分提交成功，ID: {submission_id}")
    
    # 測試日誌記錄
    print("\n測試日誌記錄:")
    if db.log_action(
        action='test',
        details='This is a test log',
        token='test-token-12345',
        ip_address='127.0.0.1'
    ):
        print("✅ 日誌記錄成功")
    
    # 顯示統計
    print("\n最新統計:")
    db.print_database_info()
    
    print("\n測試完成！")


if __name__ == '__main__':
    main()
