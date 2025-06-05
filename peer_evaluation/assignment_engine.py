#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同儕評分分派系統 - 重構版
使用統一配置系統，支援多種分派模式
"""

import os
import sys
import json
import random
from datetime import datetime
from typing import Dict, List, Optional

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from config_unified import PeerEvaluationConfig


class AssignmentEngine:
    """同儕評分分派引擎"""
    
    def __init__(self, preset_name: str = None):
        """
        初始化分派引擎
        
        Args:
            preset_name: 預設配置名稱
        """
        self.config = PeerEvaluationConfig()
        self.preset_name = preset_name
        self.data = None
        self.students = []
        self.questions = {}
        self.question_keys = []
        
        print("同儕評分分派系統")
        print("=" * 50)
        if preset_name:
            print(f"使用配置: {preset_name}")
        
        config_data = self.config.get_config(preset_name)
        assignment_config = config_data["peer_assignment"]
        print(f"每位學生評分數量: {assignment_config['assignments_per_student']} 份")
        print(f"分派模式: {assignment_config['balance_mode']}")
        print(f"允許自我評分: {assignment_config['allow_self_evaluation']}")
        
    def load_data(self, json_file_path: str = None) -> bool:
        """
        載入JSON數據
        
        Args:
            json_file_path: JSON文件路徑，若為None則使用配置文件中的路徑
        """
        if json_file_path is None:
            # 優先使用統一輸出目錄中的文件
            json_file_path = os.path.join(
                self.config.get_unified_output_path("csv_analysis"),
                "midterm_data.json"
            )
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # 提取學生和題目信息
            self.students = list(self.data['students'].keys())
            self.questions = self.data['questions']  # 保存完整的題目字典
            self.question_keys = list(self.data['questions'].keys())  # 保存題目鍵列表
            
            print(f"成功載入數據:")
            print(f"  學生數量: {len(self.students)}")
            print(f"  題目數量: {len(self.question_keys)}")
            print(f"  學生列表: {', '.join(self.students[:10])}{'...' if len(self.students) > 10 else ''}")
            
            return True
            
        except FileNotFoundError:
            print(f"錯誤: 找不到文件 {json_file_path}")
            return False
        except json.JSONDecodeError:
            print(f"錯誤: JSON文件格式錯誤")
            return False
        except Exception as e:
            print(f"錯誤: 載入數據時發生異常 - {e}")
            return False
    
    def validate_assignment_feasibility(self) -> bool:
        """檢查分派可行性"""
        config_data = self.config.get_config(self.preset_name)
        assignment_config = config_data["peer_assignment"]
        total_students = len(self.students)
        assignments_per_student = assignment_config["assignments_per_student"]
        allow_self_evaluation = assignment_config["allow_self_evaluation"]
        
        max_possible = total_students if allow_self_evaluation else total_students - 1
        
        if assignments_per_student > max_possible:
            print(f"錯誤: 每位學生需評分 {assignments_per_student} 份，")
            print(f"但最多只能分派 {max_possible} 份")
            if not allow_self_evaluation:
                print("(不允許自我評分)")
            return False
            
        if assignments_per_student <= 0:
            print(f"錯誤: 每位學生評分數量必須大於 0")
            return False
        
        if config_data["system"]["verbose"]:
            print(f"分派可行性檢查: ✓ 通過")
            print(f"  每位學生評分: {assignments_per_student} 份")
            print(f"  總評分任務數: {assignments_per_student * total_students}")
            print(f"  每份考卷預計被評分次數: {assignments_per_student} 次")
        
        return True
    
    def generate_assignments(self) -> Dict:
        """
        生成同儕評分分派
        
        Returns:
            分派結果字典
        """
        config_data = self.config.get_config(self.preset_name)
        assignment_config = config_data["peer_assignment"]
        balance_mode = assignment_config["balance_mode"]
        
        if balance_mode == "perfect":
            return self._generate_perfect_balanced_assignments()
        elif balance_mode == "random":
            return self._generate_random_assignments()
        elif balance_mode == "weighted":
            return self._generate_weighted_assignments()
        else:
            print(f"警告: 未知的分派模式 '{balance_mode}'，使用完美平衡模式")
            return self._generate_perfect_balanced_assignments()
    
    def _generate_perfect_balanced_assignments(self) -> Dict:
        """生成完美平衡的分派（每個人被評分次數相同）"""
        config_data = self.config.get_config(self.preset_name)
        assignment_config = config_data["peer_assignment"]
        assignments_per_student = assignment_config["assignments_per_student"]
        allow_self_evaluation = assignment_config["allow_self_evaluation"]
        random_seed = assignment_config["random_seed"]
        
        if random_seed is not None:
            random.seed(random_seed)
            if config_data["system"]["verbose"]:
                print(f"使用隨機種子: {random_seed}")
        
        assignments = {}
        
        # 初始化每位學生的分派結果
        for student in self.students:
            assignments[student] = {
                'assigned_papers': [],      # 需要評分的考卷
                'evaluators': []           # 評分自己考卷的人
            }
        
        if config_data["system"]["verbose"]:
            print("\n開始生成完美平衡分派...")
        
        total_students = len(self.students)
        
        # 隨機打亂學生順序以增加隨機性
        shuffled_students = self.students.copy()
        random.shuffle(shuffled_students)
        
        # 使用循環算法：每個人評分接下來的N個人
        for i, evaluator in enumerate(shuffled_students):
            assigned_papers = []
            
            # 從下一個位置開始，循環選擇需要評分的學生
            offset = 1 if not allow_self_evaluation else 0
            while len(assigned_papers) < assignments_per_student:
                target_index = (i + offset) % total_students
                target_student = shuffled_students[target_index]
                
                # 檢查是否允許自我評分
                if allow_self_evaluation or target_student != evaluator:
                    assigned_papers.append(target_student)
                
                offset += 1
                
                # 防止無限循環
                if offset > total_students:
                    break
            
            assignments[evaluator]['assigned_papers'] = assigned_papers
            
            # 更新被評分者的evaluators列表
            for paper_owner in assigned_papers:
                assignments[paper_owner]['evaluators'].append(evaluator)
            
            if config_data["system"]["verbose"]:
                print(f"  {evaluator} 需要評分: {', '.join(assigned_papers)}")
        
        self._analyze_assignments(assignments)
        return assignments
    
    def _generate_random_assignments(self) -> Dict:
        """生成隨機分派"""
        config_data = self.config.get_config(self.preset_name)
        assignment_config = config_data["peer_assignment"]
        assignments_per_student = assignment_config["assignments_per_student"]
        allow_self_evaluation = assignment_config["allow_self_evaluation"]
        random_seed = assignment_config["random_seed"]
        
        if random_seed is not None:
            random.seed(random_seed)
        
        assignments = {}
        
        # 初始化
        for student in self.students:
            assignments[student] = {
                'assigned_papers': [],
                'evaluators': []
            }
        
        if config_data["system"]["verbose"]:
            print("\n開始生成隨機分派...")
        
        for evaluator in self.students:
            # 創建可選擇的學生列表
            available_students = self.students.copy()
            if not allow_self_evaluation:
                available_students.remove(evaluator)
            
            # 隨機選擇需要評分的學生
            assigned_papers = random.sample(available_students, 
                                          min(assignments_per_student, len(available_students)))
            
            assignments[evaluator]['assigned_papers'] = assigned_papers
            
            # 更新被評分者的evaluators列表
            for paper_owner in assigned_papers:
                assignments[paper_owner]['evaluators'].append(evaluator)
            
            if config_data["system"]["verbose"]:
                print(f"  {evaluator} 需要評分: {', '.join(assigned_papers)}")
        
        self._analyze_assignments(assignments)
        return assignments
    
    def _generate_weighted_assignments(self) -> Dict:
        """生成加權分派（可以根據學生表現等因素調整）"""
        # 目前實現與完美平衡相同，未來可以擴展
        config_data = self.config.get_config(self.preset_name)
        if config_data["system"]["verbose"]:
            print("加權分派模式（目前與完美平衡模式相同）")
        return self._generate_perfect_balanced_assignments()
    
    def _analyze_assignments(self, assignments: Dict):
        """分析分派結果統計"""
        config_data = self.config.get_config(self.preset_name)
        if not config_data["system"]["verbose"]:
            return
        
        print("\n分派結果統計:")
        
        total_assignments = sum(len(info['assigned_papers']) for info in assignments.values())
        evaluation_counts = [len(info['evaluators']) for info in assignments.values()]
        
        min_eval = min(evaluation_counts)
        max_eval = max(evaluation_counts)
        avg_eval = sum(evaluation_counts) / len(evaluation_counts)
        
        print(f"  總分派任務數: {total_assignments}")
        print(f"  每份考卷被評分次數:")
        print(f"    最少: {min_eval} 次")
        print(f"    最多: {max_eval} 次")
        print(f"    平均: {avg_eval:.1f} 次")
        
        # 檢查是否平衡
        if min_eval == max_eval:
            print(f"  ✓ 完美平衡：每份考卷都被評分 {min_eval} 次")
        else:
            print(f"  ⚠ 不平衡：相差 {max_eval - min_eval} 次")
        
        # 計算平衡指數
        if avg_eval > 0:
            std_dev = (sum((x - avg_eval)**2 for x in evaluation_counts) / len(evaluation_counts))**0.5
            balance_index = 1 - (std_dev / avg_eval) if avg_eval > 0 else 0
            print(f"  平衡指數: {balance_index:.3f} (越接近1越平衡)")
    
    def export_assignments(self, assignments: Dict, output_dir: str = None) -> str:
        """導出分派結果"""
        if output_dir is None:
            output_dir = self.config.get_unified_output_path("form_generation")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成檔案名稱
        config_data = self.config.get_config(self.preset_name)
        timestamp = datetime.now().strftime(config_data["output"]["timestamp_format"])
        prefix = config_data["output"]["file_prefix"]["assignments"]
        output_file = os.path.join(output_dir, f"{prefix}_{timestamp}.json")
        
        # 準備導出數據
        export_data = {
            'assignments': assignments,
            'questions': self.questions,
        }
        
        # 添加元數據
        config_data = self.config.get_config(self.preset_name)
        if config_data["output"]["include_metadata"]:
            assignment_config = config_data["peer_assignment"]
            export_data['metadata'] = {
                'export_time': datetime.now().isoformat(),
                'total_students': len(self.students),
                'total_questions': len(self.question_keys),
                'assignments_per_student': assignment_config['assignments_per_student'],
                'balance_mode': assignment_config['balance_mode'],
                'allow_self_evaluation': assignment_config['allow_self_evaluation'],
                'random_seed': assignment_config['random_seed'],
                'total_assignments': sum(len(info['assigned_papers']) for info in assignments.values()),
                'config_preset': self.preset_name,
                'source_file': self.config.get_unified_output_path("csv_analysis", "midterm_data.json")
            }
        
        config_data = self.config.get_config(self.preset_name)
        if config_data["system"]["verbose"]:
            print(f"\n導出分派結果到：{output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        if config_data["system"]["verbose"]:
            print(f"導出完成：{output_file}")
        
        return output_file


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='同儕評分分派系統')
    parser.add_argument('--preset', '-p', type=str, choices=['light', 'standard', 'intensive', 'balanced'],
                       help='使用預設配置')
    parser.add_argument('--json', type=str, help='指定JSON數據文件路徑')
    parser.add_argument('--output', '-o', type=str, help='指定輸出目錄')
    
    args = parser.parse_args()
    
    # 創建分派引擎
    engine = AssignmentEngine(args.preset)
    
    # 載入數據
    if not engine.load_data(args.json):
        print("數據載入失敗，程序結束")
        return
    
    # 檢查可行性
    if not engine.validate_assignment_feasibility():
        print("分派不可行，程序結束")
        return
    
    # 生成分派
    assignments = engine.generate_assignments()
    
    # 導出結果
    output_file = engine.export_assignments(assignments, args.output)
    
    if engine.config["system"]["verbose"]:
        print(f"\n分派完成！")
        print(f"輸出文件：{output_file}")


if __name__ == "__main__":
    main()
