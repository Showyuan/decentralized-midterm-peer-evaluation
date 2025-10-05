#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期中考試數據處理器 - 重構版
使用統一配置系統
"""

import os
import sys
import json
import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from stage0_config_unified import PeerEvaluationConfig


class DataProcessor:
    """期中考試數據處理器"""
    
    def __init__(self, preset_name: str = None):
        """
        初始化處理器
        
        Args:
            preset_name: 預設配置名稱（已棄用，保留用於向後兼容）
        """
        self.config_manager = PeerEvaluationConfig()
        self.config = self.config_manager.get_config()
        self.preset_name = preset_name
        self.raw_data = None
        self.students = {}
        self.questions = {}
        
        if self.config["system"]["verbose"]:
            print("期中考試數據處理器")
            print("=" * 50)
            if preset_name:
                print(f"使用配置: {preset_name}")
        
    def load_data(self, csv_file_path: str = None) -> pd.DataFrame:
        """
        載入CSV數據
        
        Args:
            csv_file_path: CSV文件路徑，若為None則使用預設路徑
        """
        if csv_file_path is None:
            # 從配置獲取 CSV 路徑
            csv_file_path = self.config_manager.get_input_csv_path()
        
        try:
            encoding = self.config["data_processing"]["encoding"]
            self.raw_data = pd.read_csv(csv_file_path, encoding=encoding)
            
            if self.config["system"]["verbose"]:
                print(f"成功載入數據：{len(self.raw_data)} 條記錄")
                print(f"CSV欄位數量：{len(self.raw_data.columns)}")
                print("CSV欄位名稱：")
                for i, col in enumerate(self.raw_data.columns):
                    print(f"   {i+1:2d}. {col}")
            
            return self.raw_data
            
        except Exception as e:
            print(f"載入數據失敗：{e}")
            return None
    
    def parse_questions(self) -> Dict:
        """解析考試題目"""
        if self.raw_data is None:
            print("請先載入數據")
            return {}
        
        # 從列名中提取問題
        question_columns = [col for col in self.raw_data.columns if col.startswith('335')]
        
        if self.config["system"]["verbose"]:
            print(f"\n找到 {len(question_columns)} 道題目：")
        
        for i, col in enumerate(question_columns, 1):
            # 提取問題ID和內容
            match = re.match(r'(\d+):\s*(.*)', col)
            if match:
                question_id = match.group(1)
                question_content = match.group(2)
                
                # 統一使用配置中的最高分數
                max_score = self.config["data_processing"]["max_score_per_question"]
                
                # 截取內容預覽
                content_preview = question_content[:80] + "..." if len(question_content) > 80 else question_content
                
                self.questions[f"Q{i}"] = {
                    'id': question_id,
                    'content': content_preview,
                    'full_content': question_content,
                    'max_score': max_score,
                    'column': col
                }
                
                if self.config["system"]["verbose"]:
                    print(f"   Q{i}: [{question_id}] {content_preview} (滿分: {max_score})")
        
        if self.config["system"]["verbose"]:
            print(f"解析完成：{len(self.questions)} 道題目")
        
        return self.questions
    
    def parse_students(self) -> Dict:
        """解析學生數據"""
        if self.raw_data is None:
            print("請先載入數據")
            return {}
        
        if self.config["system"]["verbose"]:
            print(f"\n解析學生數據...")
        
        for index, row in self.raw_data.iterrows():
            student_id = row['id']
            student_name = row['name']
            
            # 讀取 email（Web 系統需要）
            student_email = row['email'] if 'email' in row.index and pd.notna(row['email']) else ''
            
            # 解析學生的答案
            answers = {}
            for q_key, q_info in self.questions.items():
                answer_text = str(row[q_info['column']]) if pd.notna(row[q_info['column']]) else ""
                
                # 計算統計信息
                is_empty = (answer_text == "" or answer_text == "nan")
                word_count = len(answer_text.split()) if not is_empty else 0
                char_count = len(answer_text) if not is_empty else 0
                
                answers[q_key] = {
                    'text': answer_text if not is_empty else "",
                    'word_count': word_count,
                    'char_count': char_count,
                    'is_empty': is_empty
                }
            
            # 安全地獲取提交時間和嘗試次數，處理不同的列名
            submitted_time = None
            if 'submitted' in row.index:
                submitted_time = row['submitted']
            elif 'submitted_time' in row.index:
                submitted_time = row['submitted_time']
            
            attempt = None
            if 'attempt' in row.index:
                attempt = row['attempt']
            
            self.students[student_id] = {
                'name': student_name,
                'id': student_id,
                'email': student_email,
                'answers': answers,
                'submitted_time': submitted_time,
                'attempt': attempt
            }
            
            # 輸出學生基本信息
            if self.config["system"]["verbose"]:
                total_words = sum(ans['word_count'] for ans in answers.values())
                email_info = f" <{student_email}>" if student_email else ""
                print(f"   {student_id} ({student_name}{email_info}): 總字數 {total_words} 字")
        
        if self.config["system"]["verbose"]:
            print(f"解析完成：{len(self.students)} 位學生")
        
        return self.students
    
    def analyze_submission_patterns(self) -> Dict:
        """分析學生提交模式"""
        if not self.students:
            print("請先解析學生數據")
            return {}
        
        if self.config["system"]["verbose"]:
            print(f"\n分析提交模式...")
        
        analysis = {
            'submission_stats': {},
            'answer_length_stats': {},
            'question_response_rates': {}
        }
        
        # 提交時間分析
        submission_times = []
        for student_data in self.students.values():
            submitted_time = student_data.get('submitted_time')
            if submitted_time is not None and str(submitted_time) != 'nan' and submitted_time != '':
                submission_times.append(submitted_time)
        
        analysis['submission_stats'] = {
            'total_submissions': len(submission_times),
            'submission_rate': f"{len(submission_times)}/{len(self.students)} ({len(submission_times)/len(self.students)*100:.1f}%)"
        }
        
        # 各題回答長度統計
        for q_key in self.questions.keys():
            lengths = []
            response_count = 0
            
            for student_data in self.students.values():
                answer = student_data['answers'][q_key]
                if not answer['is_empty']:
                    lengths.append(answer['char_count'])
                    response_count += 1
            
            if lengths:
                analysis['answer_length_stats'][q_key] = {
                    'response_count': response_count,
                    'response_rate': f"{response_count}/{len(self.students)} ({response_count/len(self.students)*100:.1f}%)",
                    'avg_length': sum(lengths) / len(lengths),
                    'min_length': min(lengths),
                    'max_length': max(lengths)
                }
            else:
                analysis['answer_length_stats'][q_key] = {
                    'response_count': 0,
                    'response_rate': "0/0 (0.0%)",
                    'avg_length': 0,
                    'min_length': 0,
                    'max_length': 0
                }
        
        # 輸出分析結果
        if self.config["system"]["verbose"]:
            print(f"   提交統計: {analysis['submission_stats']['submission_rate']}")
            print(f"   各題回答情況:")
            for q_key, stats in analysis['answer_length_stats'].items():
                print(f"     {q_key}: {stats['response_rate']}, 平均長度: {stats['avg_length']:.0f} 字元")
        
        return analysis
    
    def export_to_json(self, output_dir: str = None, analysis: Dict = None) -> str:
        """導出數據到JSON格式"""
        if not self.students or not self.questions:
            print("請先解析數據")
            return ""
        
        if output_dir is None:
            # 從配置獲取輸出路徑和檔名
            output_dir = self.config_manager.ensure_output_dir('stage1_output')
            output_file = self.config_manager.get_path('stage1_output', 'processed_data')
        else:
            # 如果指定了輸出目錄，使用配置的檔名
            filename = self.config_manager.get('filenames.processed_data')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, filename)
    
        # 準備導出數據
        export_data = {
            'questions': self.questions,
            'students': self.students
        }
        
        # 添加元數據
        if self.config["output"]["include_metadata"]:
            export_data['metadata'] = {
                'export_time': datetime.now().isoformat(),
                'total_students': len(self.students),
                'total_questions': len(self.questions),
                'processing_summary': f"共處理 {len(self.students)} 位學生的 {len(self.questions)} 道題目",
                'config_preset': self.preset_name,
                'max_score_per_question': self.config["data_processing"]["max_score_per_question"]
            }
        
        # 如果有分析數據，加入到export_data中
        if analysis:
            export_data['analysis'] = analysis
        
        if self.config["system"]["verbose"]:
            print(f"\n導出JSON數據到：{output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        if self.config["system"]["verbose"]:
            print(f"導出完成：{output_file}")
        
        return output_file


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='期中考試數據處理器')
    parser.add_argument('--preset', '-p', type=str, choices=['light', 'standard', 'intensive', 'balanced'],
                       help='使用預設配置')
    parser.add_argument('--csv', type=str, help='指定CSV文件路徑')
    parser.add_argument('--output', '-o', type=str, help='指定輸出目錄')
    
    args = parser.parse_args()
    
    # 創建處理器
    processor = DataProcessor(args.preset)
    
    # 載入數據
    raw_data = processor.load_data(args.csv)
    if raw_data is None:
        print("數據載入失敗，程序結束")
        return
    
    # 解析問題和學生
    questions = processor.parse_questions()
    if not questions:
        print("題目解析失敗，程序結束")
        return
    
    students = processor.parse_students()
    if not students:
        print("學生數據解析失敗，程序結束")
        return
    
    # 分析提交模式
    analysis = processor.analyze_submission_patterns()
    
    # 導出JSON數據
    if processor.config["system"]["verbose"]:
        print(f"\n導出處理結果...")
    
    json_file = processor.export_to_json(args.output, analysis)
    
    if processor.config["system"]["verbose"]:
        print(f"\n處理完成！")
        print(f"共處理 {len(students)} 位學生的 {len(questions)} 道題目")
        print(f"輸出文件：{json_file}")


if __name__ == "__main__":
    main()
