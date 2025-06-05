#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
評分表單生成器 - 重構版
使用統一配置系統，支援多種表單樣式
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from config_unified import PeerEvaluationConfig


class FormGenerator:
    """評分表單生成器"""
    
    def __init__(self, preset_name: str = None):
        """
        初始化表單生成器
        
        Args:
            preset_name: 預設配置名稱
        """
        self.config = PeerEvaluationConfig()
        self.preset_name = preset_name
        self.assignment_data = None
        self.original_data = None
        
        config_data = self.config.get_config(self.preset_name)
        if config_data["system"]["verbose"]:
            print("評分表單生成器")
            print("=" * 50)
            if preset_name:
                print(f"使用配置: {preset_name}")
    
    def load_assignment_data(self, assignment_file: str) -> bool:
        """
        載入分派數據
        
        Args:
            assignment_file: 分派結果JSON文件路徑
        """
        try:
            with open(assignment_file, 'r', encoding='utf-8') as f:
                self.assignment_data = json.load(f)
            
            config_data = self.config.get_config(self.preset_name)
            if config_data["system"]["verbose"]:
                print(f"成功載入分派數據:")
                print(f"  總學生數: {self.assignment_data['metadata']['total_students']}")
                print(f"  每人評分: {self.assignment_data['metadata']['assignments_per_student']} 份")
            
            return True
            
        except Exception as e:
            print(f"錯誤: 無法載入分派文件 - {e}")
            return False
    
    def load_original_data(self, json_file_path: str = None) -> bool:
        """
        載入原始考試數據
        
        Args:
            json_file_path: 原始數據JSON文件路徑
        """
        if json_file_path is None:
            # 優先使用元數據中的檔案
            json_file_path = self.assignment_data['metadata']['source_file']
            
            # 如果元數據中的檔案不存在，嘗試找最新的數據檔案
            if not os.path.exists(json_file_path):
                output_dir = self.config.get_directory_path("1_csv_analysis")
                data_files = [f for f in os.listdir(output_dir) 
                             if f.startswith('midterm_data_') and f.endswith('.json')]
                if data_files:
                    # 按時間排序，取最新的
                    data_files.sort(reverse=True)
                    json_file_path = os.path.join(output_dir, data_files[0])
                    config_data = self.config.get_config(self.preset_name)
                    if config_data["system"]["verbose"]:
                        print(f"使用最新的數據檔案: {data_files[0]}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.original_data = json.load(f)
            
            config_data = self.config.get_config(self.preset_name)
            if config_data["system"]["verbose"]:
                print(f"成功載入原始數據: {len(self.original_data['students'])} 位學生")
            
            return True
            
        except Exception as e:
            print(f"錯誤: 無法載入原始數據文件 - {e}")
            return False
    
    def generate_evaluation_form(self, evaluator_id: str, output_dir: str = None) -> str:
        """
        生成評分表單
        
        Args:
            evaluator_id: 評分者ID
            output_dir: 輸出目錄
            
        Returns:
            生成的表單文件路徑
        """
        if evaluator_id not in self.assignment_data['assignments']:
            print(f"錯誤: 找不到評分者 {evaluator_id}")
            return ""
        
        if output_dir is None:
            # 使用統一輸出路徑系統
            output_dir = os.path.join(self.config.get_unified_output_path("form_generation"), "evaluation_forms")
            os.makedirs(output_dir, exist_ok=True)
        
        assigned_papers = self.assignment_data['assignments'][evaluator_id]['assigned_papers']
        questions = self.assignment_data['questions']
        config_data = self.config.get_config(self.preset_name)
        form_config = config_data["evaluation_form"]
        
        # 生成HTML評分表單
        timestamp = datetime.now().strftime(config_data["output"]["timestamp_format"])
        output_file = os.path.join(output_dir, f"{evaluator_id}_evaluation_form_{timestamp}.html")
        
        html_content = self._generate_html_content(evaluator_id, assigned_papers, questions, form_config)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if config_data["system"]["verbose"]:
            print(f"評分表單已生成: {output_file}")
        
        return output_file
    
    def generate_all_forms(self, output_dir: str = None) -> List[str]:
        """
        為所有學生生成評分表單
        
        Args:
            output_dir: 輸出目錄
            
        Returns:
            生成的表單文件路徑列表
        """
        if output_dir is None:
            # 使用統一輸出路徑系統
            output_dir = os.path.join(self.config.get_unified_output_path("form_generation"), "evaluation_forms")
            os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        students = list(self.assignment_data['assignments'].keys())
        
        config_data = self.config.get_config(self.preset_name)
        if config_data["system"]["verbose"]:
            print(f"\n為 {len(students)} 位學生生成評分表單...")
        
        for student_id in students:
            form_file = self.generate_evaluation_form(student_id, output_dir)
            if form_file:
                generated_files.append(form_file)
                if config_data["system"]["verbose"]:
                    print(f"  ✓ {student_id}")
        
        if config_data["system"]["verbose"]:
            print(f"\n完成！共生成 {len(generated_files)} 個評分表單")
            print(f"輸出目錄: {output_dir}")
        
        return generated_files
    
    def _generate_html_content(self, evaluator_id: str, assigned_papers: List[str], 
                              questions: Dict, form_config: Dict) -> str:
        """生成HTML表單內容"""
        
        # CSS樣式
        css_styles = """
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0;
            font-size: 16px;
        }
        .paper {
            border: 2px solid #e1e8ed;
            margin: 30px 0;
            padding: 25px;
            border-radius: 10px;
            background: #fafbfc;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .paper-title {
            background: #4a90e2;
            color: white;
            padding: 15px;
            margin: -25px -25px 20px -25px;
            border-radius: 8px 8px 0 0;
            font-size: 18px;
            font-weight: bold;
        }
        .question {
            background: #f8f9fa;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #007cba;
            border-radius: 5px;
        }
        .question-title {
            font-weight: bold;
            color: #007cba;
            margin-bottom: 10px;
        }
        .question-content {
            color: #555;
            margin-bottom: 10px;
            white-space: pre-wrap;
        }
        .answer {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            white-space: pre-wrap;
            min-height: 80px;
        }
        .score-section {
            margin: 15px 0;
            padding: 15px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
        }
        .score-input {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        .score-input label {
            font-weight: bold;
            margin-right: 10px;
            min-width: 80px;
        }
        .score-input input[type="number"] {
            width: 80px;
            padding: 8px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            text-align: center;
        }
        .score-input input[type="number"]:focus {
            border-color: #007cba;
            outline: none;
        }
        .comment-section {
            margin: 15px 0;
        }
        .comment-section textarea {
            width: 100%;
            min-height: 80px;
            padding: 10px;
            margin: 5px 0;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-family: inherit;
            resize: vertical;
        }
        .comment-section textarea:focus {
            border-color: #007cba;
            outline: none;
        }
        .stats {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
            padding: 5px;
            background: #f1f3f4;
            border-radius: 3px;
        }
        .submit-section {
            background: #e8f5e8;
            border: 2px solid #4caf50;
            padding: 20px;
            margin: 30px 0;
            border-radius: 10px;
            text-align: center;
        }
        .submit-button {
            background: #4caf50;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin: 10px;
        }
        .submit-button:hover {
            background: #45a049;
        }
        @media print {
            .submit-section { display: none; }
        }
        """
        
        # 開始生成HTML
        html_content = f"""<!DOCTYPE html>
<html lang="{form_config['language']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>同儕評分表單 - {evaluator_id}</title>
    <style>{css_styles}</style>
</head>
<body>
    <div class="header">
        <h1>📋 同儕評分表單</h1>
        <p><strong>評分者:</strong> {evaluator_id}</p>
        <p><strong>評分日期:</strong> {datetime.now().strftime('%Y年%m月%d日')}</p>
        <p><strong>需評分考卷數:</strong> {len(assigned_papers)} 份</p>
        <p><strong>評分範圍:</strong> {form_config['scoring_scale']['min_score']}-{form_config['scoring_scale']['max_score']} 分</p>
    </div>
"""
        
        # 為每份分派的考卷生成評分區塊
        for i, paper_owner in enumerate(assigned_papers, 1):
            html_content += f"""
    <div class="paper">
        <div class="paper-title">
            第 {i} 份考卷 - 學生: {paper_owner}
        </div>
"""
            
            # 為每道題目生成評分區塊
            for q_key, q_info in questions.items():
                # 獲取該學生對這道題的回答
                student_answer = self.original_data['students'][paper_owner]['answers'][q_key]
                
                html_content += f"""
        <div class="question">
            <div class="question-title">{q_key}: {q_info['content']}</div>
            <div class="question-content">{q_info['full_content'][:200]}{'...' if len(q_info['full_content']) > 200 else ''}</div>
            
            <div class="answer">
{student_answer['text']}
            </div>
            
            {self._generate_stats_section(student_answer, form_config) if form_config['include_statistics'] else ''}
            
            <div class="score-section">
                <div class="score-input">
                    <label for="{paper_owner}_{q_key}_score">評分:</label>
                    <input type="number" 
                           id="{paper_owner}_{q_key}_score" 
                           name="{paper_owner}_{q_key}_score"
                           min="{form_config['scoring_scale']['min_score']}" 
                           max="{form_config['scoring_scale']['max_score']}"
                           step="{form_config['scoring_scale']['step']}"
                           placeholder="0-{form_config['scoring_scale']['max_score']}">
                    <span style="margin-left: 10px;">/ {form_config['scoring_scale']['max_score']} 分</span>
                </div>
                
                {self._generate_comment_section(paper_owner, q_key, form_config) if form_config['require_comments'] else ''}
            </div>
        </div>
"""
            
            html_content += "    </div>\n"
        
        # 添加提交區塊
        html_content += f"""
    <div class="submit-section">
        <h3>✅ 評分完成確認</h3>
        <p>請確認所有題目都已評分並填寫評語後，儲存此表單並提交。</p>
        <button type="button" class="submit-button" onclick="window.print()">🖨️ 列印表單</button>
        <button type="button" class="submit-button" onclick="alert('請儲存此HTML文件並提交給教師')">💾 完成評分</button>
    </div>
    
    <script>
        // 自動儲存評分進度到localStorage
        function saveProgress() {{
            const formData = {{}};
            document.querySelectorAll('input, textarea').forEach(element => {{
                if (element.value) {{
                    formData[element.name || element.id] = element.value;
                }}
            }});
            localStorage.setItem('evaluation_progress_{evaluator_id}', JSON.stringify(formData));
        }}
        
        // 載入之前的評分進度
        function loadProgress() {{
            const saved = localStorage.getItem('evaluation_progress_{evaluator_id}');
            if (saved) {{
                const formData = JSON.parse(saved);
                Object.keys(formData).forEach(key => {{
                    const element = document.getElementById(key) || document.querySelector(`[name="${{key}}"]`);
                    if (element) {{
                        element.value = formData[key];
                    }}
                }});
            }}
        }}
        
        // 頁面載入時恢復進度，輸入時自動儲存
        window.onload = loadProgress;
        document.addEventListener('input', saveProgress);
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_stats_section(self, answer: Dict, form_config: Dict) -> str:
        """生成統計信息區塊"""
        stats = []
        
        if form_config['show_word_count']:
            stats.append(f"字數: {answer['word_count']}")
        
        if form_config['show_char_count']:
            stats.append(f"字元數: {answer['char_count']}")
        
        if answer['is_empty']:
            stats.append("未作答")
        
        return f'<div class="stats">📊 {" | ".join(stats)}</div>' if stats else ""
    
    def _generate_comment_section(self, paper_owner: str, q_key: str, form_config: Dict) -> str:
        """生成評語區塊"""
        min_length = form_config['comment_min_length']
        return f"""
                <div class="comment-section">
                    <label for="{paper_owner}_{q_key}_comment"><strong>評語:</strong></label>
                    <textarea id="{paper_owner}_{q_key}_comment" 
                              name="{paper_owner}_{q_key}_comment"
                              placeholder="請填寫評語（至少{min_length}個字元）..."
                              minlength="{min_length}"></textarea>
                </div>"""
    
    def show_assignment_summary(self, assignment_file: str):
        """顯示分派摘要"""
        if not self.load_assignment_data(assignment_file):
            return
        
        metadata = self.assignment_data['metadata']
        assignments = self.assignment_data['assignments']
        
        print(f"\n=== 同儕評分分派摘要 ===")
        print(f"總學生數: {metadata['total_students']}")
        print(f"每人評分: {metadata['assignments_per_student']} 份")
        print(f"總評分任務: {metadata['total_assignments']} 個")
        print(f"分派模式: {metadata['balance_mode']}")
        print(f"隨機種子: {metadata['random_seed']}")
        
        # 顯示每個人被評分次數統計
        eval_counts = [len(info['evaluators']) for info in assignments.values()]
        print(f"\n每份考卷被評分次數:")
        print(f"  最少: {min(eval_counts)} 次")
        print(f"  最多: {max(eval_counts)} 次")
        print(f"  平均: {sum(eval_counts)/len(eval_counts):.1f} 次")


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='評分表單生成器')
    parser.add_argument('assignment_file', help='分派結果JSON文件路徑')
    parser.add_argument('--preset', '-p', type=str, choices=['light', 'standard', 'intensive', 'balanced'],
                       help='使用預設配置')
    parser.add_argument('--evaluator', '-e', type=str, help='指定評分者ID生成單一表單')
    parser.add_argument('--output', '-o', type=str, help='指定輸出目錄')
    parser.add_argument('--all', '-a', action='store_true', help='為所有學生生成表單')
    parser.add_argument('--summary', '-s', action='store_true', help='只顯示分派摘要')
    
    args = parser.parse_args()
    
    # 創建表單生成器
    generator = FormGenerator(args.preset)
    
    if args.summary:
        generator.show_assignment_summary(args.assignment_file)
        return
    
    # 載入分派數據
    if not generator.load_assignment_data(args.assignment_file):
        return
    
    # 載入原始數據
    if not generator.load_original_data():
        return
    
    if args.all:
        # 為所有學生生成表單
        generated_files = generator.generate_all_forms(args.output)
        print(f"\n 成功生成 {len(generated_files)} 個評分表單")
    elif args.evaluator:
        # 為指定學生生成表單
        form_file = generator.generate_evaluation_form(args.evaluator, args.output)
        if form_file:
            print(f"\n 成功生成評分表單: {form_file}")
    else:
        print("請指定 --evaluator 生成單一表單或 --all 生成所有表單")


if __name__ == "__main__":
    main()
