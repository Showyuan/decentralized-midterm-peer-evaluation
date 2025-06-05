#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的同儕評分結果收集器
專注於 HTML 表單處理、基本統計摘要和簡單輸出格式

使用方式:
python result_collector.py --forms-dir ../simple_filled_forms --output-file results.xlsx
"""

import os
import sys
import re
import json
import argparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from config_unified import PeerEvaluationConfig


class ResultCollector:
    """簡化的評分結果收集器 - 專注於核心功能"""
    
    def __init__(self, preset_name: str = None):
        """
        初始化收集器
        
        Args:
            preset_name: 預設配置名稱
        """
        self.config_manager = PeerEvaluationConfig()
        self.config = self.config_manager.get_config(preset_name)
        self.preset_name = preset_name
        
        # 收集的數據
        self.evaluation_data = []
        self.summary_stats = {}
        
        if self.config["system"]["verbose"]:
            print("簡化同儕評分結果收集器")
            print("=" * 50)
            if preset_name:
                print(f"使用配置: {preset_name}")
    
    def extract_form_data(self, html_file_path: str) -> Dict:
        """
        從單個HTML表單提取評分數據
        
        Args:
            html_file_path: HTML表單路徑
            
        Returns:
            提取的評分數據
        """
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 從文件名解析信息
            filename = os.path.basename(html_file_path)
            evaluator_match = re.search(r'^([A-Z]\d{2})_evaluation_form_', filename)
            
            if not evaluator_match:
                if self.config["system"]["verbose"]:
                    print(f"警告: 無法從檔案名解析評分者ID: {filename}")
                return {}
            
            evaluator_id = evaluator_match.group(1)
            
            # 提取評分數據
            form_data = {
                "evaluator_id": evaluator_id,
                "filename": filename,
                "scores": {},
                "comments": {},
                "evaluations": {},  # 添加 evaluations 字段，符合 vancouver_processor.py 的預期
                "timestamp": datetime.now().isoformat()
            }
            
            # 提取分數
            score_inputs = soup.find_all('input', {'type': 'number'})
            for input_elem in score_inputs:
                name = input_elem.get('name', '')
                value = input_elem.get('value', '')
                if '_score' in name and value:
                    try:
                        form_data["scores"][name] = int(value)
                    except ValueError:
                        form_data["scores"][name] = 0
            
            # 提取評語
            comment_textareas = soup.find_all('textarea')
            for textarea in comment_textareas:
                name = textarea.get('name', '')
                content = textarea.string or textarea.text or ''
                if '_comment' in name and content.strip():
                    form_data["comments"][name] = content.strip()
            
            return form_data
            
        except Exception as e:
            if self.config["system"]["verbose"]:
                print(f"✗ 提取失敗: {html_file_path}, 錯誤: {str(e)}")
            return {}
    
    def collect_all_forms(self, forms_dir: str) -> List[Dict]:
        """
        收集目錄中所有表單的數據
        
        Args:
            forms_dir: 已填寫表單目錄
            
        Returns:
            所有表單數據列表
        """
        if not os.path.exists(forms_dir):
            print(f"錯誤: 表單目錄不存在: {forms_dir}")
            return []
        
        self.evaluation_data = []
        
        # 處理所有HTML文件
        html_files = [f for f in os.listdir(forms_dir) if f.endswith('.html')]
        
        if self.config["system"]["verbose"]:
            print(f"\n開始收集評分數據...")
            print(f"表單目錄: {forms_dir}")
            print(f"找到 {len(html_files)} 個HTML表單")
            print("-" * 50)
        
        for filename in html_files:
            file_path = os.path.join(forms_dir, filename)
            form_data = self.extract_form_data(file_path)
            
            if form_data:
                # 從分數欄位名稱中提取被評分者ID (格式: {evaluatee_id}_Q{number}_score)
                evaluatees = {}
                scores = form_data.get("scores", {})
                
                for score_name, score_value in scores.items():
                    # 解析格式如 "C03_Q1_score"
                    match = re.match(r'^([A-Z]\d{2})_Q\d+_score$', score_name)
                    if match:
                        evaluatee_id = match.group(1)
                        if evaluatee_id not in evaluatees:
                            evaluatees[evaluatee_id] = []
                        evaluatees[evaluatee_id].append(score_value)
                
                # 為每個被評分者計算平均分數並構建 evaluations 結構
                form_data["evaluations"] = {}
                for evaluatee_id, score_list in evaluatees.items():
                    avg_score = sum(score_list) / len(score_list) if score_list else 0
                    form_data["evaluations"][evaluatee_id] = {
                        "score": avg_score,
                        "details": {q: s for q, s in scores.items() if q.startswith(f"{evaluatee_id}_")}
                    }
                
                self.evaluation_data.append(form_data)
                if self.config["system"]["verbose"]:
                    score_count = len(form_data.get("scores", {}))
                    comment_count = len(form_data.get("comments", {}))
                    print(f"✓ {filename}: {score_count} 個分數, {comment_count} 個評語")
        
        # 生成基本統計
        self._generate_summary_stats()
        
        return self.evaluation_data
    
    def _generate_summary_stats(self):
        """生成基本統計摘要"""
        if not self.evaluation_data:
            self.summary_stats = {}
            return
        
        # 收集所有分數
        all_scores = []
        score_by_question = {}
        
        for form_data in self.evaluation_data:
            for question, score in form_data.get("scores", {}).items():
                all_scores.append(score)
                if question not in score_by_question:
                    score_by_question[question] = []
                score_by_question[question].append(score)
        
        # 計算統計
        # 收集所有評分者
        evaluators = set()
        for form_data in self.evaluation_data:
            if 'evaluator_id' in form_data:
                evaluators.add(form_data['evaluator_id'])
        
        # 計算平均分數
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        self.summary_stats = {
            "total_forms": len(self.evaluation_data),
            "total_scores": len(all_scores),
            "total_evaluators": len(evaluators),  # 添加評分者數量
            "total_evaluations": len(self.evaluation_data),  # 添加評分總數
            "average_score": avg_score,
            "min_score": min(all_scores) if all_scores else 0,
            "max_score": max(all_scores) if all_scores else 0,
            "score_by_question": {},
            "overall_stats": {  # 添加 overall_stats 以兼容 Vancouver 處理器
                "mean": avg_score,
                "min": min(all_scores) if all_scores else 0,
                "max": max(all_scores) if all_scores else 0
            }
        }
        
        # 每個問題的統計
        for question, scores in score_by_question.items():
            self.summary_stats["score_by_question"][question] = {
                "count": len(scores),
                "average": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores)
            }
    
    def export_to_excel(self, output_file: str):
        """
        匯出到Excel文件
        
        Args:
            output_file: 輸出文件路徑
        """
        if not self.evaluation_data:
            print("警告: 沒有數據可以匯出")
            return
        
        # 準備數據 - 基本資料視圖（每個評分者一行）
        evaluator_rows = []
        for form_data in self.evaluation_data:
            row = {
                "評分者ID": form_data.get("evaluator_id", ""),
                "檔案名稱": form_data.get("filename", ""),
                "時間戳記": form_data.get("timestamp", "")
            }
            
            # 添加分數欄位 - 使用更清楚的欄位名稱
            for question, score in form_data.get("scores", {}).items():
                # 將 "C03_Q1_score" 格式轉換為更清楚的欄位名稱
                if question.endswith('_score'):
                    # 去掉 "_score" 後綴，保留原始格式
                    clean_name = question[:-6]  # 移除 "_score"
                    row[clean_name] = score
                else:
                    row[question] = score
            
            # 添加評語欄位 - 使用更清楚的欄位名稱  
            for question, comment in form_data.get("comments", {}).items():
                # 將 "C03_Q1_comment" 格式轉換為更清楚的欄位名稱
                if question.endswith('_comment'):
                    # 去掉 "_comment" 後綴，並加上 "評語_" 前綴
                    clean_name = question[:-8]  # 移除 "_comment" 
                    row[f"評語_{clean_name}"] = comment
                else:
                    row[f"評語_{question}"] = comment
            
            evaluator_rows.append(row)
        
        # 準備學生分數摘要（每位被評分學生一行）
        student_scores = {}
        for form_data in self.evaluation_data:
            evaluator_id = form_data.get("evaluator_id", "")
            
            # 從分數欄位解析被評分者ID
            for question, score in form_data.get("scores", {}).items():
                if '_Q' in question and question.endswith('_score'):
                    parts = question.split('_Q')
                    if len(parts) >= 2:
                        student_id = parts[0]
                        q_num = parts[1].split('_')[0]  # 例如從 "1_score" 獲取 "1"
                        
                        if student_id not in student_scores:
                            student_scores[student_id] = {"學生ID": student_id, "評分次數": 0, "總分": 0, "平均分": 0}
                            
                            # 初始化每個問題的欄位
                            for i in range(1, 6):  # Q1到Q5
                                student_scores[student_id][f"Q{i}_總分"] = 0
                                student_scores[student_id][f"Q{i}_次數"] = 0
                                student_scores[student_id][f"Q{i}_平均"] = 0
                        
                        # 累加分數
                        student_scores[student_id]["評分次數"] += 1
                        student_scores[student_id]["總分"] += score
                        
                        # 更新特定問題的分數
                        if q_num.isdigit():
                            student_scores[student_id][f"Q{q_num}_總分"] += score
                            student_scores[student_id][f"Q{q_num}_次數"] += 1
            
        # 計算平均分
        for student_id, data in student_scores.items():
            if data["評分次數"] > 0:
                data["平均分"] = round(data["總分"] / data["評分次數"], 2)
                
                # 計算每個問題的平均分
                for i in range(1, 6):  # Q1到Q5
                    if data[f"Q{i}_次數"] > 0:
                        data[f"Q{i}_平均"] = round(data[f"Q{i}_總分"] / data[f"Q{i}_次數"], 2)
        
        # 創建DataFrame
        df_evaluators = pd.DataFrame(evaluator_rows)
        df_students = pd.DataFrame(list(student_scores.values()))
        
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 主要數據表 (評分者視圖)
            df_evaluators.to_excel(writer, sheet_name='評分數據', index=False)
            
            # 學生摘要表 (被評分者視圖)
            if not df_students.empty:
                df_students.to_excel(writer, sheet_name='學生分數摘要', index=False)
            
            # 統計摘要表
            if self.summary_stats:
                summary_data = []
                summary_data.append(["總表單數", self.summary_stats.get("total_forms", 0)])
                summary_data.append(["總分數數", self.summary_stats.get("total_scores", 0)])
                summary_data.append(["平均分數", round(self.summary_stats.get("average_score", 0), 2)])
                summary_data.append(["最低分數", self.summary_stats.get("min_score", 0)])
                summary_data.append(["最高分數", self.summary_stats.get("max_score", 0)])
                
                summary_df = pd.DataFrame(summary_data, columns=['項目', '數值'])
                summary_df.to_excel(writer, sheet_name='統計摘要', index=False)
        
        if self.config["system"]["verbose"]:
            print(f"✓ 數據已匯出到: {output_file}")
    
    def export_to_json(self, output_file: str):
        """
        匯出到JSON文件
        
        Args:
            output_file: 輸出文件路徑
        """
        if not self.evaluation_data:
            print("警告: 沒有數據可以匯出")
            return
        
        # 準備輸出數據
        output_data = {
            "summary": self.summary_stats,
            "summary_stats": self.summary_stats,  # 添加額外的鍵以兼容 vancouver_processor.py
            "evaluation_data": self.evaluation_data,
            "export_timestamp": datetime.now().isoformat()
        }
        
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        if self.config["system"]["verbose"]:
            print(f"✓ 數據已匯出到: {output_file}")
    
    def print_summary(self):
        """列印基本統計摘要"""
        print("\n" + "=" * 50)
        print("評分數據收集摘要")
        print("=" * 50)
        
        if not self.summary_stats:
            print("沒有收集到任何數據")
            return
        
        print(f"總表單數: {self.summary_stats.get('total_forms', 0)}")
        print(f"總分數數: {self.summary_stats.get('total_scores', 0)}")
        print(f"平均分數: {self.summary_stats.get('average_score', 0):.2f}")
        print(f"分數範圍: {self.summary_stats.get('min_score', 0)} - {self.summary_stats.get('max_score', 0)}")
        
        # 顯示各問題統計
        if self.summary_stats.get("score_by_question"):
            print("\n各問題統計:")
            for question, stats in self.summary_stats["score_by_question"].items():
                print(f"  {question}: 平均 {stats['average']:.2f} (範圍: {stats['min']}-{stats['max']})")
        
        print("=" * 50)


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description="簡化的同儕評分結果收集器")
    parser.add_argument("--forms-dir", required=True, help="已填寫表單目錄")
    parser.add_argument("--output-file", help="輸出文件路徑 (.xlsx 或 .json) (已棄用，請使用 --output-excel 或 --output-json)")
    parser.add_argument("--output-excel", help="Excel輸出文件路徑 (.xlsx)")
    parser.add_argument("--output-json", help="JSON輸出文件路徑 (.json)")
    parser.add_argument("--preset", help="配置預設 (light, standard, comprehensive, debug)")
    
    args = parser.parse_args()
    
    # 初始化收集器
    collector = ResultCollector(preset_name=args.preset)
    
    # 收集所有表單數據
    evaluation_data = collector.collect_all_forms(args.forms_dir)
    
    if not evaluation_data:
        print("錯誤: 沒有收集到任何數據")
        return 1
    
    # 處理新的輸出參數
    if args.output_excel:
        collector.export_to_excel(args.output_excel)
    
    if args.output_json:
        collector.export_to_json(args.output_json)
        
    # 支持舊版參數（如果提供）
    if not (args.output_excel or args.output_json) and args.output_file:
        # 根據文件副檔名決定輸出格式
        if args.output_file.endswith('.xlsx'):
            collector.export_to_excel(args.output_file)
        elif args.output_file.endswith('.json'):
            collector.export_to_json(args.output_file)
        else:
            print("錯誤: 不支援的輸出格式，請使用 .xlsx 或 .json")
            return 1
            
    # 如果沒有提供任何輸出參數
    if not (args.output_excel or args.output_json or args.output_file):
        print("錯誤: 必須提供至少一個輸出參數 (--output-excel 或 --output-json)")
        return 1
    
    # 顯示摘要
    collector.print_summary()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
