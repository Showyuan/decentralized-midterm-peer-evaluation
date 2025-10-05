#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token 產生器 - 用於學生認證和評量分配
為每個學生的每份評量任務生成唯一的 Token
"""

import os
import sys
import json
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from stage0_config_unified import PeerEvaluationConfig


@dataclass
class EvaluationToken:
    """評量 Token 資料結構"""
    token: str                      # 唯一 Token (UUID)
    evaluator_id: str               # 評分者學號
    target_id: str                  # 被評分者學號
    questions: List[str]            # 題目列表
    created_at: str                 # 建立時間
    expires_at: str                 # 過期時間
    status: str                     # 狀態: pending, submitted, expired
    submission_time: Optional[str]  # 提交時間
    ip_address: Optional[str]       # 提交 IP
    used: bool                      # 是否已使用
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """檢查 Token 是否有效"""
        if self.used or self.status != 'pending':
            return False
        
        # 檢查是否過期
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() < expires
    
    def mark_as_used(self, ip_address: str = None):
        """標記為已使用"""
        self.used = True
        self.status = 'submitted'
        self.submission_time = datetime.now().isoformat()
        if ip_address:
            self.ip_address = ip_address


class TokenGenerator:
    """Token 產生與管理系統"""
    
    def __init__(self, config: PeerEvaluationConfig = None):
        """
        初始化 Token 產生器
        
        Args:
            config: 統一配置管理器
        """
        self.config = config or PeerEvaluationConfig()
        self.tokens: Dict[str, EvaluationToken] = {}
        
        # 從配置獲取設定
        config_data = self.config.get_config()
        web_config = config_data.get('web', {})
        
        # 設置屬性以保持向後兼容
        self.TOKEN_LENGTH = web_config.get('token_length', 36)
        self.TOKEN_EXPIRY_DAYS = web_config.get('token_expiry_days', 14)
        self.EVALUATION_DEADLINE_DAYS = web_config.get('evaluation_deadline_days', 14)
        self.SERVER_URL = web_config.get('server_url', 'https://ntublockchainintro2025.online')
        
        print("Token 產生器初始化")
        print("=" * 60)
        print(f"Token 過期時間: {self.TOKEN_EXPIRY_DAYS} 天")
        print(f"Token 長度: {self.TOKEN_LENGTH} 字元")
        
    def generate_token(self, 
                      evaluator_id: str, 
                      target_id: str, 
                      questions: List[str]) -> EvaluationToken:
        """
        為單一評量任務生成 Token
        
        Args:
            evaluator_id: 評分者學號
            target_id: 被評分者學號
            questions: 題目列表
            
        Returns:
            EvaluationToken 物件
        """
        # 生成安全的隨機 Token
        if self.TOKEN_LENGTH == 36:
            # 使用 UUID4 (標準 36 字元)
            token_str = str(uuid.uuid4())
        else:
            # 使用 secrets 生成指定長度的 Token
            token_str = secrets.token_urlsafe(self.TOKEN_LENGTH)[:self.TOKEN_LENGTH]
        
        # 計算過期時間
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=self.TOKEN_EXPIRY_DAYS)
        
        # 建立 Token 物件
        token = EvaluationToken(
            token=token_str,
            evaluator_id=evaluator_id,
            target_id=target_id,
            questions=questions,
            created_at=created_at.isoformat(),
            expires_at=expires_at.isoformat(),
            status='pending',
            submission_time=None,
            ip_address=None,
            used=False
        )
        
        # 儲存到內部字典
        self.tokens[token_str] = token
        
        return token
    
    def generate_tokens_from_assignments(self, 
                                        assignments: Dict,
                                        questions: Dict) -> Dict[str, List[EvaluationToken]]:
        """
        從分派結果批次生成所有 Token
        
        Args:
            assignments: 分派結果字典 (來自 assignment_engine.py)
            questions: 題目字典
            
        Returns:
            每位學生的 Token 列表
        """
        student_tokens = {}
        question_list = list(questions.keys())
        
        print("\n開始批次生成 Token...")
        print(f"學生數量: {len(assignments)}")
        
        for evaluator_id, assignment_data in assignments.items():
            tokens = []
            assigned_papers = assignment_data.get('assigned_papers', [])
            
            print(f"\n處理學生: {evaluator_id}")
            print(f"  需要評分: {len(assigned_papers)} 份")
            
            for target_id in assigned_papers:
                # 為每份評量生成 Token
                token = self.generate_token(
                    evaluator_id=evaluator_id,
                    target_id=target_id,
                    questions=question_list
                )
                tokens.append(token)
                
                print(f"    ✓ {evaluator_id} → {target_id}: {token.token[:16]}...")
            
            student_tokens[evaluator_id] = tokens
        
        total_tokens = sum(len(tokens) for tokens in student_tokens.values())
        print(f"\n✓ Token 生成完成")
        print(f"  總計: {total_tokens} 個 Token")
        print(f"  平均每人: {total_tokens / len(assignments):.1f} 個")
        
        return student_tokens
    
    def load_assignments(self, 
                        assignments_file: str = None,
                        base_dir: str = None) -> Tuple[Dict, Dict, Dict]:
        """
        載入分派結果和題目資料
        
        Args:
            assignments_file: 分派結果文件路徑
            base_dir: 基礎目錄 (預設為專案根目錄)
            
        Returns:
            (assignments, questions, students_info) 元組
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if assignments_file is None:
            # 使用配置中的預設路徑
            assignments_file = self.config.get_path('stage2_assignment', 'assignments')
        
        try:
            print(f"\n載入分派結果: {assignments_file}")
            with open(assignments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assignments = data.get('assignments', {})
            questions = data.get('questions', {})
            
            # 嘗試載入學生資料以獲取 email
            students_info = {}
            midterm_data_file = self.config.get_path('stage1_output', 'processed_data')
            
            if os.path.exists(midterm_data_file):
                print(f"載入學生資料: {midterm_data_file}")
                with open(midterm_data_file, 'r', encoding='utf-8') as f:
                    midterm_data = json.load(f)
                    students_info = midterm_data.get('students', {})
                    print(f"✓ 學生資料載入成功 ({len(students_info)} 位學生)")
            else:
                print(f"警告: 找不到學生資料檔案，email 將使用預設值")
            
            print(f"✓ 成功載入")
            print(f"  學生數量: {len(assignments)}")
            print(f"  題目數量: {len(questions)}")
            
            return assignments, questions, students_info
            
        except FileNotFoundError:
            print(f"錯誤: 找不到文件 {assignments_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"錯誤: JSON 格式錯誤 - {e}")
            raise
        except Exception as e:
            print(f"錯誤: 載入失敗 - {e}")
            raise
    
    def validate_token(self, token_str: str) -> Tuple[bool, Optional[EvaluationToken], str]:
        """
        驗證 Token 是否有效
        
        Args:
            token_str: Token 字串
            
        Returns:
            (是否有效, Token物件, 錯誤訊息)
        """
        # 檢查 Token 是否存在
        if token_str not in self.tokens:
            return False, None, "Token 不存在或無效"
        
        token = self.tokens[token_str]
        
        # 檢查是否已使用
        if token.used:
            return False, token, "此 Token 已被使用"
        
        # 檢查是否過期
        expires = datetime.fromisoformat(token.expires_at)
        if datetime.now() > expires:
            token.status = 'expired'
            return False, token, f"Token 已過期 (過期時間: {token.expires_at})"
        
        # 檢查狀態
        if token.status != 'pending':
            return False, token, f"Token 狀態異常: {token.status}"
        
        return True, token, ""
    
    def get_token_info(self, token_str: str) -> Optional[Dict]:
        """
        獲取 Token 詳細資訊
        
        Args:
            token_str: Token 字串
            
        Returns:
            Token 資訊字典或 None
        """
        if token_str not in self.tokens:
            return None
        
        token = self.tokens[token_str]
        info = token.to_dict()
        
        # 添加額外資訊
        info['is_valid'] = token.is_valid()
        info['is_expired'] = datetime.now() > datetime.fromisoformat(token.expires_at)
        
        return info
    
    def export_tokens(self, 
                     student_tokens: Dict[str, List[EvaluationToken]],
                     output_dir: str = None,
                     include_metadata: bool = True) -> str:
        """
        導出所有 Token 到 JSON 文件
        
        Args:
            student_tokens: 學生 Token 字典
            output_dir: 輸出目錄
            include_metadata: 是否包含元數據
            
        Returns:
            輸出文件路徑
        """
        if output_dir is None:
            # 使用配置中的輸出目錄
            output_dir = self.config.ensure_output_dir('stage3_tokens')
        
        # 準備導出數據
        export_data = {}
        
        # 轉換 Token 物件為字典
        for student_id, tokens in student_tokens.items():
            export_data[student_id] = [token.to_dict() for token in tokens]
        
        # 準備完整輸出結構
        output = {
            'tokens': export_data
        }
        
        # 添加元數據
        if include_metadata:
            total_tokens = sum(len(tokens) for tokens in student_tokens.values())
            output['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'total_students': len(student_tokens),
                'total_tokens': total_tokens,
                'tokens_per_student': total_tokens / len(student_tokens) if student_tokens else 0,
                'token_expiry_days': self.TOKEN_EXPIRY_DAYS,
                'token_length': self.TOKEN_LENGTH,
                'config': {
                    'server_url': self.SERVER_URL,
                    'token_expiry_days': self.TOKEN_EXPIRY_DAYS,
                    'evaluation_deadline_days': self.EVALUATION_DEADLINE_DAYS
                }
            }
        
        # 使用配置生成檔案路徑
        timestamp_obj = datetime.now()
        output_file = self.config.get_path('stage3_tokens', 'tokens', timestamp=timestamp_obj)
        
        print(f"\n導出 Token 到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 導出完成")
        print(f"  文件: {output_file}")
        print(f"  大小: {os.path.getsize(output_file) / 1024:.1f} KB")
        
        # 同時導出簡化版本 (僅包含學生ID和Token列表)
        simple_output = {}
        for student_id, tokens in student_tokens.items():
            simple_output[student_id] = {
                'student_id': student_id,
                'tokens': [token.token for token in tokens],
                'targets': [token.target_id for token in tokens],
                'count': len(tokens)
            }
        
        # 生成簡化版檔案路徑
        output_dir = self.config.ensure_output_dir('stage3_tokens')
        timestamp_str = timestamp_obj.strftime('%Y%m%d_%H%M%S')
        simple_file = os.path.join(output_dir, f'tokens_simple_{timestamp_str}.json')
        with open(simple_file, 'w', encoding='utf-8') as f:
            json.dump(simple_output, f, ensure_ascii=False, indent=2)
        
        print(f"  簡化版: {simple_file}")
        
        return output_file
    
    def export_token_urls(self, 
                         student_tokens: Dict[str, List[EvaluationToken]],
                         students_info: Dict = None,
                         output_dir: str = None) -> str:
        """
        導出每個學生的評量 URL 列表
        
        Args:
            student_tokens: 學生 Token 字典
            students_info: 學生資訊字典 (含 email)
            output_dir: 輸出目錄
            
        Returns:
            輸出文件路徑
        """
        if output_dir is None:
            # 使用配置中的輸出目錄
            output_dir = self.config.ensure_output_dir('stage3_tokens')
        
        if students_info is None:
            students_info = {}
        
        # 準備 URL 數據
        url_data = {}
        
        for student_id, tokens in student_tokens.items():
            urls = []
            for token in tokens:
                url = f"{self.SERVER_URL}/eval/{token.token}"
                urls.append({
                    'target': token.target_id,
                    'url': url,
                    'expires': token.expires_at
                })
            
            # 從學生資料中獲取真實 email
            student_info = students_info.get(student_id, {})
            student_email = student_info.get('email', f'{student_id}@example.com')
            student_name = student_info.get('name', student_id)
            
            url_data[student_id] = {
                'student_id': student_id,
                'student_name': student_name,
                'email': student_email,
                'evaluation_urls': urls,
                'total': len(urls),
                'instructions': f'請在 {self.TOKEN_EXPIRY_DAYS} 天內完成所有評量'
            }
        
        # 使用配置生成檔案路徑
        output_file = self.config.get_path('stage3_tokens', 'urls', timestamp=datetime.now())
        
        print(f"\n導出評量 URL 到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(url_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 導出完成: {output_file}")
        
        return output_file
    
    def get_statistics(self, student_tokens: Dict[str, List[EvaluationToken]] = None) -> Dict:
        """
        獲取 Token 統計資訊
        
        Args:
            student_tokens: 學生 Token 字典 (可選，不提供則使用內部 tokens)
            
        Returns:
            統計資訊字典
        """
        if student_tokens:
            all_tokens = [token for tokens in student_tokens.values() for token in tokens]
        else:
            all_tokens = list(self.tokens.values())
        
        if not all_tokens:
            return {
                'total': 0,
                'pending': 0,
                'submitted': 0,
                'expired': 0,
                'valid': 0
            }
        
        # 統計各種狀態
        total = len(all_tokens)
        pending = sum(1 for t in all_tokens if t.status == 'pending')
        submitted = sum(1 for t in all_tokens if t.status == 'submitted')
        expired = sum(1 for t in all_tokens if t.status == 'expired')
        valid = sum(1 for t in all_tokens if t.is_valid())
        
        stats = {
            'total': total,
            'pending': pending,
            'submitted': submitted,
            'expired': expired,
            'valid': valid,
            'completion_rate': (submitted / total * 100) if total > 0 else 0
        }
        
        return stats


def main():
    """主程序 - Token 生成工作流程"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Token 產生器')
    parser.add_argument('--assignments', '-a', type=str,
                       help='分派結果文件路徑')
    parser.add_argument('--output', '-o', type=str,
                       help='輸出目錄')
    parser.add_argument('--expiry-days', type=int, default=14,
                       help='Token 有效天數 (預設: 14)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("同儕評分系統 - Token 產生器")
    print("=" * 60)
    
    # 建立配置
    config = PeerEvaluationConfig()
    
    # 初始化 Token 產生器
    generator = TokenGenerator(config)
    
    # 如果指定了過期天數，更新配置
    if args.expiry_days:
        generator.TOKEN_EXPIRY_DAYS = args.expiry_days
    
    # 載入分派結果
    try:
        assignments, questions, students_info = generator.load_assignments(args.assignments)
    except Exception as e:
        print(f"\n❌ 載入失敗: {e}")
        return 1
    
    # 生成 Token
    student_tokens = generator.generate_tokens_from_assignments(assignments, questions)
    
    # 顯示統計
    stats = generator.get_statistics(student_tokens)
    print(f"\n統計資訊:")
    print(f"  總 Token 數: {stats['total']}")
    print(f"  待處理: {stats['pending']}")
    print(f"  有效 Token: {stats['valid']}")
    
    # 導出結果
    token_file = generator.export_tokens(student_tokens, args.output)
    url_file = generator.export_token_urls(student_tokens, students_info, args.output)
    
    print(f"\n✓ Token 生成完成！")
    print(f"\n輸出文件:")
    print(f"  1. Token 數據: {token_file}")
    print(f"  2. 評量 URL: {url_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
