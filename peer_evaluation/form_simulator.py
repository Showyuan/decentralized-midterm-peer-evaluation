#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的同儕評分表單填寫模擬器
專注於 HTML 表單處理、基本統計摘要和簡單輸出格式

使用方式:
python form_simulator.py --forms-dir ../evaluation_forms --output-dir ../filled_forms
"""

import os
import sys
import random
import re
import argparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from bs4 import BeautifulSoup

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from config_unified import PeerEvaluationConfig


class FormSimulator:
    """簡化的評分表單填寫模擬器 - 專注於核心功能"""
    
    def __init__(self, preset_name: str = None):
        """
        初始化模擬器
        
        Args:
            preset_name: 預設配置名稱
        """
        self.config_manager = PeerEvaluationConfig()
        self.config = self.config_manager.get_config(preset_name)
        self.preset_name = preset_name
        
        # 學生評分風格配置
        self.student_profiles = self._create_student_profiles()
        
        # 基本統計
        self.filled_count = 0
        self.error_count = 0
        
        if self.config["system"]["verbose"]:
            print("簡化同儕評分表單模擬器")
            print("=" * 50)
            if preset_name:
                print(f"使用配置: {preset_name}")
    
    def _create_student_profiles(self) -> Dict[str, Dict]:
        """創建不同學生的評分風格"""
        profiles = {
            # 嚴格型評分者
            "strict": {
                "score_range": (10, 18),
                "score_bias": -2,
                "comment_style": "critical",
                "variance": 1.5
            },
            # 寬鬆型評分者
            "lenient": {
                "score_range": (15, 20),
                "score_bias": 2,
                "comment_style": "positive",
                "variance": 1.0
            },
            # 中性型評分者
            "neutral": {
                "score_range": (12, 18),
                "score_bias": 0,
                "comment_style": "balanced",
                "variance": 2.0
            },
            # 隨機型評分者
            "random": {
                "score_range": (8, 20),
                "score_bias": 0,
                "comment_style": "mixed",
                "variance": 3.0
            }
        }
        return profiles
    
    def _assign_student_profile(self, student_id: str) -> str:
        """為學生分配評分風格"""
        # 根據學生ID的字母決定風格
        first_char = student_id[0].upper()
        if first_char in ['A', 'B', 'C', 'D', 'E']:
            return "strict"
        elif first_char in ['F', 'G', 'H', 'I', 'J']:
            return "lenient"
        elif first_char in ['K', 'L', 'M', 'N', 'O']:
            return "neutral"
        else:
            return "random"
    
    def _generate_score(self, profile_name: str, base_quality: float = 15.0) -> int:
        """
        生成評分
        
        Args:
            profile_name: 評分風格名稱
            base_quality: 基礎品質分數 (0-20)
            
        Returns:
            評分 (0-20)
        """
        profile = self.student_profiles[profile_name]
        
        # 基礎分數 + 偏差 + 隨機變化
        score = base_quality + profile["score_bias"]
        score += random.gauss(0, profile["variance"])
        
        # 限制在評分範圍內
        min_score, max_score = profile["score_range"]
        score = max(min_score, min(max_score, score))
        
        return int(round(score))
    
    def _generate_comment(self, profile_name: str, score: int) -> str:
        """
        生成評語
        
        Args:
            profile_name: 評分風格名稱
            score: 給出的分數
            
        Returns:
            評語文字
        """
        profile = self.student_profiles[profile_name]
        style = profile["comment_style"]
        
        # 基礎評語模板
        positive_comments = [
            "回答很完整，展現了良好的理解能力。",
            "論述清晰，邏輯性強，值得肯定。",
            "內容詳實，分析到位，表現優秀。"
        ]
        
        neutral_comments = [
            "回答基本正確，但可以更詳細一些。",
            "理解大致正確，部分地方可以加強。",
            "內容符合要求，表達還算清楚。"
        ]
        
        critical_comments = [
            "回答不夠完整，需要更深入的分析。",
            "理解有偏差，建議重新整理思路。",
            "內容過於簡略，缺乏具體說明。"
        ]
        
        # 根據風格選擇評語
        if style == "positive":
            return random.choice(positive_comments)
        elif style == "critical":
            return random.choice(critical_comments)
        elif style == "balanced":
            return random.choice(neutral_comments)
        else:  # mixed
            all_comments = positive_comments + neutral_comments + critical_comments
            return random.choice(all_comments)
    
    def fill_form(self, html_file_path: str, output_path: str) -> bool:
        """
        填寫單個HTML表單
        
        Args:
            html_file_path: 原始HTML表單路徑
            output_path: 輸出的已填寫表單路徑
            
        Returns:
            填寫是否成功
        """
        try:
            # 讀取HTML文件
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 從文件名解析評分者ID
            filename = os.path.basename(html_file_path)
            evaluator_match = re.search(r'^([A-Z]\d{2})_evaluation_form_', filename)
            
            if not evaluator_match:
                if self.config["system"]["verbose"]:
                    print(f"警告: 無法從檔案名解析評分者ID: {filename}")
                evaluator_id = "STU00"  # 預設值
            else:
                evaluator_id = evaluator_match.group(1)
            
            # 決定評分風格
            profile_name = self._assign_student_profile(evaluator_id)
            
            # 填寫所有評分輸入欄位
            score_inputs = soup.find_all('input', {'type': 'number'})
            for input_elem in score_inputs:
                name = input_elem.get('name', '')
                if '_score' in name:
                    score = self._generate_score(profile_name)
                    input_elem['value'] = str(score)
            
            # 填寫所有評語輸入欄位
            comment_textareas = soup.find_all('textarea')
            for textarea in comment_textareas:
                name = textarea.get('name', '')
                if '_comment' in name:
                    comment = self._generate_comment(profile_name, 15)  # 使用平均分數
                    textarea.string = comment
            
            # 儲存填寫好的表單
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            self.filled_count += 1
            if self.config["system"]["verbose"]:
                print(f"✓ 已填寫: {filename} (評分風格: {profile_name})")
            
            return True
            
        except Exception as e:
            self.error_count += 1
            if self.config["system"]["verbose"]:
                print(f"✗ 填寫失敗: {html_file_path}, 錯誤: {str(e)}")
            return False
    
    def fill_all_forms(self, forms_dir: str, output_dir: str) -> Tuple[int, int]:
        """
        填寫目錄中所有的HTML表單
        
        Args:
            forms_dir: 表單目錄
            output_dir: 輸出目錄
            
        Returns:
            (成功數量, 錯誤數量)
        """
        if not os.path.exists(forms_dir):
            print(f"錯誤: 表單目錄不存在: {forms_dir}")
            return 0, 0
        
        # 確保輸出目錄存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 重置統計
        self.filled_count = 0
        self.error_count = 0
        
        # 處理所有HTML文件
        html_files = [f for f in os.listdir(forms_dir) if f.endswith('.html')]
        
        if self.config["system"]["verbose"]:
            print(f"\n開始填寫表單...")
            print(f"表單目錄: {forms_dir}")
            print(f"輸出目錄: {output_dir}")
            print(f"找到 {len(html_files)} 個HTML表單")
            print("-" * 50)
        
        for filename in html_files:
            input_path = os.path.join(forms_dir, filename)
            output_path = os.path.join(output_dir, filename)
            self.fill_form(input_path, output_path)
        
        return self.filled_count, self.error_count
    
    def print_summary(self):
        """列印基本統計摘要"""
        print("\n" + "=" * 50)
        print("表單填寫摘要")
        print("=" * 50)
        print(f"成功填寫: {self.filled_count} 個表單")
        print(f"處理失敗: {self.error_count} 個表單")
        print(f"總處理數: {self.filled_count + self.error_count} 個表單")
        
        if self.filled_count + self.error_count > 0:
            success_rate = (self.filled_count / (self.filled_count + self.error_count)) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        print("=" * 50)


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description="簡化的同儕評分表單填寫模擬器")
    parser.add_argument("--forms-dir", required=True, help="評分表單目錄")
    parser.add_argument("--output-dir", required=True, help="已填寫表單輸出目錄")
    parser.add_argument("--preset", help="配置預設 (light, standard, comprehensive, debug)")
    
    args = parser.parse_args()
    
    # 初始化模擬器
    simulator = FormSimulator(preset_name=args.preset)
    
    # 填寫所有表單
    success_count, error_count = simulator.fill_all_forms(args.forms_dir, args.output_dir)
    
    # 顯示摘要
    simulator.print_summary()
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
