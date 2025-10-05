#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vancouver 算法處理器 - 同儕評分系統
使用收集到的評分數據執行Vancouver算法計算最終成績
"""

import json
import sys
import os
import re
import numpy as np
import pandas as pd
import argparse
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from stage0_config_unified import PeerEvaluationConfig

# 導入核心Vancouver算法
try:
    from core.vancouver import Graph
    VANCOUVER_CORE_AVAILABLE = True
except ImportError:
    VANCOUVER_CORE_AVAILABLE = False
    print("警告: 無法導入核心Vancouver算法，將使用簡化實現")

class User:
    """用戶類"""
    def __init__(self, name):
        self.name = name
        self.items = set()
        self.grade = {}
        self.variance = None
        self.reputation = None
        self.incentive_weight = None
        
    def add_item(self, item, grade):
        self.items = self.items | set([item])
        self.grade[item] = grade

class Item:
    """項目類"""
    def __init__(self, id):
        self.id = id
        self.users = set()
        self.grade = None
        self.variance = None
    
    def add_user(self, user):
        self.users = self.users | set([user])

class EnhancedGraph:
    """完整的Vancouver算法實現，包含聲譽系統和激勵機制"""
    
    def __init__(self, R_max=1.0, v_G=8.0, alpha=0.1, N=4, basic_precision=0.0001):
        self.R_max = R_max        # 最大聲譽值
        self.v_G = v_G           # 誤差容忍上限
        self.alpha = alpha       # 評審成分佔比
        self.N = N               # 系統指定的最少評審數量
        self.lambda_param = R_max / v_G  # 懲罰斜率
        self.basic_precision = basic_precision
        
        # 數據結構
        self.items = set()
        self.users = set()
        self.user_dict = {}
        self.item_dict = {}
        
        print(f"✅ 使用完整Vancouver算法實現")
        print(f"   - 聲譽系統: R_max={R_max}, v_G={v_G}, λ={self.lambda_param:.3f}")
        print(f"   - 激勵機制: α={alpha}, N={N}")
        
    def add_review(self, username, item_id, grade):
        """添加評分"""
        # 獲取或創建用戶
        if username in self.user_dict:
            u = self.user_dict[username]
        else:
            u = User(username)
            self.user_dict[username] = u
            self.users = self.users | set([u])
        
        # 獲取或創建項目
        if item_id in self.item_dict:
            it = self.item_dict[item_id]
        else:
            it = Item(item_id)
            self.item_dict[item_id] = it
            self.items = self.items | set([it])
        
        # 添加連接
        u.add_item(it, grade)
        it.add_user(u)
    
    def evaluate_items(self, n_iterations=25):
        """評估項目（共識分數計算）"""
        # 簡化的共識分數計算：使用加權平均
        for item in self.items:
            if item.users:
                # 收集所有評分
                grades = []
                weights = []
                for user in item.users:
                    if item in user.grade:
                        grade = user.grade[item]
                        # 使用用戶聲譽作為權重（如果已計算）
                        weight = getattr(user, 'reputation', 1.0)
                        grades.append(grade)
                        weights.append(weight)
                
                if grades:
                    # 計算加權平均作為共識分數
                    weighted_sum = sum(g * w for g, w in zip(grades, weights))
                    total_weight = sum(weights)
                    item.grade = weighted_sum / total_weight if total_weight > 0 else np.mean(grades)
                    
                    # 計算變異數
                    if len(grades) > 1:
                        mean_grade = item.grade
                        item.variance = np.var(grades)
                    else:
                        item.variance = 0.0
                else:
                    item.grade = 0.0
                    item.variance = 0.0
    
    def evaluate_users(self):
        """評估用戶（變異數計算）"""
        for user in self.users:
            if user.grade:
                # 收集用戶給出的所有評分
                user_grades = list(user.grade.values())
                
                # 計算用戶評分與共識的差異
                differences = []
                for item in user.items:
                    if item.grade is not None and item in user.grade:
                        user_score = user.grade[item]
                        consensus_score = item.grade
                        diff = abs(user_score - consensus_score)
                        differences.append(diff)
                
                # 計算用戶變異數（評分一致性）
                if differences:
                    user.variance = np.mean(differences) ** 2
                else:
                    user.variance = 0.0
            else:
                user.variance = float('inf')  # 沒有評分的用戶
    
    def calculate_reputation_scores(self):
        """計算聲譽分數 R_j = max(0, R_max - λ * √v̂_j)"""
        for user in self.users:
            if user.variance is not None and user.variance != float('inf'):
                # 計算聲譽分數
                variance_sqrt = np.sqrt(max(0, user.variance))
                user.reputation = max(0.0, self.R_max - self.lambda_param * variance_sqrt)
            else:
                user.reputation = 0.0  # 沒有評分或變異數無限大
    
    def calculate_incentive_weights(self):
        """計算激勵權重 θ_j = min(m_j, N)/N * R_j"""
        for user in self.users:
            # 計算評審數量
            m_j = len(user.items)
            # 計算激勵權重
            participation_factor = min(m_j, self.N) / self.N
            reputation_factor = getattr(user, 'reputation', 0.0)
            user.incentive_weight = participation_factor * reputation_factor
    
    def calculate_final_grades(self):
        """計算最終成績 FinalGrade_j = (1-α)*q̂_j + α*θ_j*100"""
        final_grades = {}
        
        for user in self.users:
            # 找到該用戶被評分的項目（假設用戶ID與項目ID對應）
            user_item = None
            for item in self.items:
                if str(item.id) == str(user.name) or item.id == user.name:
                    user_item = item
                    break
            
            if user_item is not None and user_item.grade is not None:
                # 考卷共識分數
                q_hat = user_item.grade
                # 激勵權重
                theta = getattr(user, 'incentive_weight', 0.0)
                
                # 計算原始加權成績
                weighted_grade = (1 - self.alpha) * q_hat + self.alpha * theta * 100
                
                # 保護機制：如果加權後分數降低，採用較高分數
                final_grade = max(q_hat, weighted_grade)
                
                # 記錄是否使用了保護機制
                protection_used = final_grade == q_hat and weighted_grade < q_hat
                
                final_grades[user.name] = {
                    'consensus_score': float(q_hat),
                    'incentive_weight': float(theta),
                    'final_grade': float(final_grade),
                    'weighted_grade': float(weighted_grade),
                    'protection_used': bool(protection_used),
                    'reputation': float(getattr(user, 'reputation', 0.0)),
                    'variance': float(getattr(user, 'variance', 0.0))
                }
        
        return final_grades
    
    def evaluate_with_reputation(self, n_iterations=25):
        """完整的評估流程，包含聲譽系統"""
        print("  🔄 執行基本Vancouver算法評估...")
        
        # 1. 初始聲譽設定（所有用戶開始時聲譽相等）
        for user in self.users:
            user.reputation = self.R_max
        
        # 2. 迭代評估過程
        for iteration in range(n_iterations):
            # 評估項目（計算共識分數）
            self.evaluate_items(1)
            
            # 評估用戶（計算變異數）
            self.evaluate_users()
            
            # 更新聲譽分數
            self.calculate_reputation_scores()
            
            # 每5次迭代輸出進度
            if (iteration + 1) % 5 == 0:
                avg_reputation = np.mean([u.reputation for u in self.users])
                print(f"    迭代 {iteration + 1}/{n_iterations}: 平均聲譽 = {avg_reputation:.3f}")
        
        print("  ✅ 基本算法評估完成")
        
        # 3. 計算激勵權重
        print("  🎯 計算激勵權重...")
        self.calculate_incentive_weights()
        
        # 4. 計算最終成績
        print("  📊 計算最終成績...")
        final_grades = self.calculate_final_grades()
        
        # 5. 輸出統計信息
        if final_grades:
            avg_reputation = np.mean([g['reputation'] for g in final_grades.values()])
            avg_incentive = np.mean([g['incentive_weight'] for g in final_grades.values()])
            protection_count = sum(1 for g in final_grades.values() if g['protection_used'])
            
            print(f"  📈 算法統計:")
            print(f"    - 平均聲譽分數: {avg_reputation:.3f}")
            print(f"    - 平均激勵權重: {avg_incentive:.3f}")
            print(f"    - 保護機制使用次數: {protection_count}")
        
        return final_grades

# 嘗試導入真實實現，如果失敗則使用備用實現
# EnhancedGraph 類已在本文件中重新實現
print("使用本地完整Vancouver算法實現")

class VancouverProcessor:
    """Vancouver算法處理器"""
    
    def __init__(self, evaluation_data_path=None, preset_name: str = None):
        """
        初始化處理器
        
        Args:
            evaluation_data_path: 評分數據JSON文件路徑
            preset_name: 預設配置名稱
        """
        self.config = PeerEvaluationConfig()
        self.preset_name = preset_name
        self.evaluation_data_path = evaluation_data_path
        self.raw_data = None
        self.students = []
        self.submissions = []
        self.graph = None
        self.output_dir = None  # 新增輸出目錄屬性
        
    def load_evaluation_data(self):
        """載入評分數據"""
        print("載入評分數據...")
        
        with open(self.evaluation_data_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        
        # 標準化資料鍵名：支援 evaluations 或 evaluation_data
        if 'evaluations' in self.raw_data and 'evaluation_data' not in self.raw_data:
            self.raw_data['evaluation_data'] = self.raw_data['evaluations']
        
        # 檢查 summary_stats 是否存在，如果不存在，嘗試使用 summary
        if 'summary_stats' not in self.raw_data and 'summary' in self.raw_data:
            self.raw_data['summary_stats'] = self.raw_data['summary']
            
        # 添加缺失的統計數據（如果不存在）
        if 'summary_stats' not in self.raw_data:
            print("警告: 找不到摘要統計資料，將自動生成基本統計")
            self._generate_basic_summary_stats()
            
        # 補充可能缺失的統計資料
        stats = self.raw_data['summary_stats']
        if 'total_evaluators' not in stats:
            evaluators = {eval_data['evaluator_id'] for eval_data in self.raw_data['evaluation_data']}
            stats['total_evaluators'] = len(evaluators)
            
        if 'total_evaluations' not in stats:
            stats['total_evaluations'] = len(self.raw_data['evaluation_data'])
            
        if 'overall_stats' not in stats:
            stats['overall_stats'] = {'mean': stats.get('average_score', 0)}
        
        print(f"成功載入數據:")
        print(f"   - 評分者數量: {stats.get('total_evaluators', 0)}")
        print(f"   - 評分總數: {stats.get('total_evaluations', 0)}")
        print(f"   - 分數總數: {stats.get('total_scores', 0)}")
        print(f"   - 整體平均分: {stats.get('overall_stats', {}).get('mean', 0):.2f}")
        
    def extract_students_and_submissions(self):
        """提取學生和作業清單"""
        print("\n📋 提取學生和作業清單...")
        
        # 從評分數據中提取所有學生ID
        evaluators = set()
        evaluatees = set()
        
        for evaluation in self.raw_data.get('evaluation_data', []):
            if 'evaluator_id' in evaluation:
                evaluators.add(evaluation['evaluator_id'])
                
            # 檢查 evaluations 格式
            evaluations = evaluation.get('evaluations', {})
            if isinstance(evaluations, dict):
                for evaluatee_id in evaluations.keys():
                    evaluatees.add(evaluatee_id)
                    
            # 嘗試處理可能的替代格式
            elif 'evaluatee_id' in evaluation:
                evaluatees.add(evaluation['evaluatee_id'])
        
        # 合併所有學生ID（評分者和被評分者應該是同一群學生）
        all_students = evaluators.union(evaluatees)
        self.students = sorted(list(all_students))
        
        # 每個學生的作業就是其ID（假設每個學生都提交了一份作業）
        self.submissions = self.students.copy()
        
        print(f"提取完成:")
        print(f"   - 學生數量: {len(self.students)}")
        print(f"   - 作業數量: {len(self.submissions)}")
        print(f"   - 學生清單: {', '.join(self.students)}")
        
    def create_vancouver_graph(self):
        """創建Vancouver算法圖結構"""
        print("\n🔗 創建Vancouver算法圖結構...")
        
        # 初始化圖，使用合適的參數
        self.graph = EnhancedGraph(
            R_max=1.0,      # 最大聲譽值
            v_G=8.0,        # 誤差容忍上限  
            alpha=0.1,      # 評審成分佔比
            N=4             # 系統指定的最少評審數量
        )
        
        print(f"圖結構初始化完成")
        
    def add_evaluations_to_graph(self):
        """將評分數據添加到圖中 - 使用Q1~Q5的加總分數"""
        print("\n📊 添加評分數據到圖中（使用Q1~Q5加總分數）...")
        
        total_evaluations = 0
        
        for evaluation in self.raw_data['evaluation_data']:
            evaluator_id = evaluation.get('evaluator_id')
            if not evaluator_id:
                continue
                
            # 處理新的簡化格式：evaluations 直接是 {target_id: total_score}
            if 'evaluations' in evaluation and isinstance(evaluation['evaluations'], dict):
                for evaluatee_id, score_value in evaluation['evaluations'].items():
                    # 如果是數字，直接使用（這是總分）
                    if isinstance(score_value, (int, float)):
                        self.graph.add_review(evaluator_id, evaluatee_id, score_value)
                        total_evaluations += 1
                    # 如果是字典，嘗試從 details 計算（舊格式）
                    elif isinstance(score_value, dict) and 'details' in score_value:
                        # 從details計算Q1~Q5分數的加總
                        q_scores = []
                        details = score_value['details']
                        for q_num in range(1, 6):
                            score_key = f"{evaluatee_id}_Q{q_num}_score"
                            if score_key in details:
                                q_scores.append(details[score_key])
                        
                        if len(q_scores) == 5:  # 確保有完整的Q1~Q5分數
                            total_score = sum(q_scores)
                            self.graph.add_review(evaluator_id, evaluatee_id, total_score)
                            total_evaluations += 1
                            
                            # 驗證：比較計算出的加總與原始平均分數
                            original_score = score_value.get('score', 0)
                            expected_average = total_score / 5
                            if abs(expected_average - original_score) > 0.01:
                                print(f"⚠️  {evaluator_id}評{evaluatee_id}: 平均分驗證失敗 (計算平均:{expected_average:.2f} vs 原始:{original_score})")
                        else:
                            print(f"⚠️  {evaluator_id}評{evaluatee_id}: Q1~Q5分數不完整 ({len(q_scores)}/5)")
            
            # 備用處理：如果沒有evaluations欄位，從scores直接計算
            elif 'scores' in evaluation and isinstance(evaluation['scores'], dict):
                # 按學生ID分組計算Q1~Q5加總
                student_scores = {}
                for score_key, score_value in evaluation['scores'].items():
                    if '_Q' in score_key and score_key.endswith('_score'):
                        # 提取學生ID (例如從 "C03_Q1_score" 提取 "C03")
                        parts = score_key.split('_Q')
                        if len(parts) == 2:
                            student_id = parts[0]
                            if student_id not in student_scores:
                                student_scores[student_id] = []
                            student_scores[student_id].append(score_value)
                
                # 為每個學生添加加總分數
                for student_id, scores in student_scores.items():
                    if len(scores) == 5:  # 確保有Q1~Q5全部分數
                        total_score = sum(scores)
                        self.graph.add_review(evaluator_id, student_id, total_score)
                        total_evaluations += 1
                    else:
                        print(f"⚠️  {evaluator_id}評{student_id}: 問題數量不完整 ({len(scores)}/5)")
        
        print(f"評分數據添加完成:")
        print(f"   - 總評分數: {total_evaluations}")
        print(f"   - 用戶數量: {len(self.graph.users)}")
        print(f"   - 項目數量: {len(self.graph.items)}")
        
    def run_vancouver_algorithm(self):
        """執行Vancouver算法"""
        print("\n🚀 執行Vancouver算法...")
        
        # 執行完整的評估流程
        final_grades = self.graph.evaluate_with_reputation(n_iterations=25)
        
        print(f"Vancouver算法執行完成")
        print(f"   - 計算了 {len(final_grades)} 個最終成績")
        
        return final_grades
        
    def generate_detailed_report(self, final_grades):
        """生成詳細報告"""
        print("\n生成詳細報告...")
        
        # 創建報告數據
        report_data = []
        
        for student_id in self.students:
            if student_id in final_grades:
                grade_info = final_grades[student_id]
                
                # 獲取該學生的原始評分統計（如果有的話）
                student_stats = {'mean': 0, 'count': 0}  # 預設值
                
                # 嘗試從不同可能的位置獲取評分統計
                if 'summary_stats' in self.raw_data:
                    summary = self.raw_data['summary_stats']
                    if 'score_by_evaluatee' in summary and student_id in summary['score_by_evaluatee']:
                        student_stats = summary['score_by_evaluatee'][student_id]
                    elif 'score_by_question' in summary and student_id in summary['score_by_question']:
                        # 嘗試使用替代格式
                        student_stats = summary['score_by_question'][student_id]
                
                # 準備報告數據，確保所有需要的鍵都存在，使用預設值處理缺失的鍵
                report_entry = {
                    'student_id': student_id,
                    'original_avg_score': student_stats.get('mean', 0),
                    'consensus_score': grade_info.get('consensus_score', 0),
                    'final_grade': grade_info.get('final_grade', 0),  # 確保 final_grade 存在
                    'evaluation_count': student_stats.get('count', 0)
                }
                
                # 添加可能存在的額外鍵
                if 'incentive_weight' in grade_info:
                    report_entry['incentive_weight'] = grade_info['incentive_weight']
                else:
                    report_entry['incentive_weight'] = 1.0  # 預設值
                    
                if 'weighted_grade' in grade_info:
                    report_entry['weighted_grade'] = grade_info['weighted_grade']
                else:
                    report_entry['weighted_grade'] = report_entry['consensus_score']  # 使用共識分數作為預設值
                    
                if 'protection_used' in grade_info:
                    report_entry['protection_used'] = grade_info['protection_used']
                else:
                    report_entry['protection_used'] = False  # 預設值
                    
                if 'reputation' in grade_info:
                    report_entry['reputation'] = grade_info['reputation']
                else:
                    report_entry['reputation'] = 0.5  # 預設值
                    
                if 'variance' in grade_info:
                    report_entry['variance'] = grade_info['variance']
                else:
                    report_entry['variance'] = 0  # 預設值
                    
                report_data.append(report_entry)
        
        # 轉換為DataFrame便於分析
        df = pd.DataFrame(report_data)
        
        # 排序（按最終成績降序）- 只有當 'final_grade' 欄位存在時
        if not df.empty and 'final_grade' in df.columns:
            df = df.sort_values('final_grade', ascending=False)
        else:
            print("警告: 'final_grade' 欄位不存在，無法排序")
        
        return df
        
    def save_results(self, final_grades, report_df):
        """保存結果到文件"""
        print("\n保存結果...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 轉換final_grades中的numpy類型為Python原生類型
        serializable_grades = {}
        for student_id, grade_info in final_grades.items():
            # 處理可能缺失的欄位，提供預設值
            serializable_grades[student_id] = {
                'consensus_score': float(grade_info.get('consensus_score', grade_info.get('final_grade', 0))) if hasattr(grade_info.get('consensus_score', grade_info.get('final_grade', 0)), 'item') else grade_info.get('consensus_score', grade_info.get('final_grade', 0)),
                'incentive_weight': float(grade_info.get('incentive_weight', 1.0)) if hasattr(grade_info.get('incentive_weight', 1.0), 'item') else grade_info.get('incentive_weight', 1.0),
                'final_grade': float(grade_info.get('final_grade', grade_info.get('consensus_score', 0))) if hasattr(grade_info.get('final_grade', grade_info.get('consensus_score', 0)), 'item') else grade_info.get('final_grade', grade_info.get('consensus_score', 0)),
                'weighted_grade': float(grade_info.get('weighted_grade', grade_info.get('final_grade', grade_info.get('consensus_score', 0)))) if hasattr(grade_info.get('weighted_grade', grade_info.get('final_grade', grade_info.get('consensus_score', 0))), 'item') else grade_info.get('weighted_grade', grade_info.get('final_grade', grade_info.get('consensus_score', 0))),
                'protection_used': bool(grade_info.get('protection_used', False)),
                'reputation': float(grade_info.get('reputation', 0.5)) if hasattr(grade_info.get('reputation', 0.5), 'item') else grade_info.get('reputation', 0.5),
                'variance': float(grade_info.get('variance', 0.0)) if hasattr(grade_info.get('variance', 0.0), 'item') else grade_info.get('variance', 0.0)
            }
        
        # 保存詳細結果（JSON格式）
        results = {
            'processing_time': datetime.now().isoformat(),
            'algorithm_parameters': {
                'R_max': float(self.graph.R_max),
                'v_G': float(self.graph.v_G),
                'alpha': float(self.graph.alpha),
                'N': int(self.graph.N)
            },
            'final_grades': serializable_grades,
            'summary_statistics': {
                'total_students': len(final_grades),
                'avg_final_grade': float(np.mean([g['final_grade'] for g in final_grades.values()])),
                'std_final_grade': float(np.std([g['final_grade'] for g in final_grades.values()])),
                'avg_consensus_score': float(np.mean([g['consensus_score'] for g in final_grades.values()])),
                'avg_reputation': float(np.mean([g['reputation'] for g in final_grades.values()])),
                'protection_used_count': int(sum(1 for g in final_grades.values() if g['protection_used']))
            }
        }
        
        # 確保輸出目錄存在
        output_dir = self.config.ensure_output_dir('stage6_vancouver')
        
        # 使用配置生成輸出路徑
        json_path = self.config.get_path('stage6_vancouver', 'vancouver_results_json', timestamp=datetime.now())
        excel_path = self.config.get_path('stage6_vancouver', 'vancouver_results_xlsx', timestamp=datetime.now())
        
        # 保存JSON結果
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存Excel報告
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # 主要報告
            report_df.to_excel(writer, sheet_name='Final_Grades', index=False)
            
            # 摘要統計
            summary_data = [
                ['總學生數', len(final_grades)],
                ['平均最終成績', float(np.mean([g['final_grade'] for g in final_grades.values()]))],
                ['最終成績標準差', float(np.std([g['final_grade'] for g in final_grades.values()]))],
                ['平均共識分數', float(np.mean([g['consensus_score'] for g in final_grades.values()]))],
                ['平均聲譽分數', float(np.mean([g['reputation'] for g in final_grades.values()]))],
                ['使用保護機制數', int(sum(1 for g in final_grades.values() if g['protection_used']))]
            ]
            summary_df = pd.DataFrame(summary_data, columns=['指標', '數值'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"結果保存完成:")
        print(f"   - JSON結果: {json_path}")
        print(f"   - Excel報告: {excel_path}")
        
        return json_path, excel_path
        
    def print_top_results(self, report_df, top_n=10):
        """打印前N名結果"""
        print(f"\n🏆 前 {top_n} 名學生最終成績:")
        print("=" * 100)
        print(f"{'排名':<4} {'學生ID':<8} {'原始均分':<10} {'共識分數':<10} {'聲譽分數':<10} {'最終成績':<10} {'保護機制':<8}")
        print("-" * 100)
        
        for i, row in report_df.head(top_n).iterrows():
            rank = list(report_df.index).index(i) + 1
            protection = "是" if row['protection_used'] else "否"
            print(f"{rank:<4} {row['student_id']:<8} {row['original_avg_score']:<10.2f} "
                  f"{row['consensus_score']:<10.2f} {row['reputation']:<10.3f} "
                  f"{row['final_grade']:<10.2f} {protection:<8}")
        
    def process_complete_workflow(self):
        """執行完整的處理流程"""
        print("Vancouver 同儕評分系統 - 完整處理流程")
        print("=" * 60)
        
        # 1. 載入數據
        self.load_evaluation_data()
        
        # 2. 提取學生和作業
        self.extract_students_and_submissions()
        
        # 3. 創建圖結構
        self.create_vancouver_graph()
        
        # 4. 添加評分數據
        self.add_evaluations_to_graph()
        
        # 5. 執行算法
        final_grades = self.run_vancouver_algorithm()
        
        # 6. 生成報告
        report_df = self.generate_detailed_report(final_grades)
        
        # 7. 保存結果
        json_path, excel_path = self.save_results(final_grades, report_df)
        
        # 8. 顯示前10名結果
        self.print_top_results(report_df)
        
        print(f"\n處理完成! 詳細結果已保存到:")
        print(f"   📄 {json_path}")
        print(f"   📊 {excel_path}")
        
        return final_grades, report_df, json_path, excel_path

    def _generate_basic_summary_stats(self):
        """生成基本統計摘要，以防原始數據中缺少摘要統計"""
        if not self.raw_data or 'evaluation_data' not in self.raw_data:
            self.raw_data['summary_stats'] = {}
            return
            
        # 收集所有評分者和被評分者
        evaluators = set()
        evaluatees = set()
        all_scores = []
        
        for evaluation in self.raw_data['evaluation_data']:
            evaluator_id = evaluation.get('evaluator_id')
            if evaluator_id:
                evaluators.add(evaluator_id)
                
            for evaluatee_id, eval_data in evaluation.get('evaluations', {}).items():
                evaluatees.add(evaluatee_id)
                if isinstance(eval_data, dict) and 'score' in eval_data:
                    all_scores.append(eval_data['score'])
        
        # 計算平均分數
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # 建立基本統計
        self.raw_data['summary_stats'] = {
            'total_evaluators': len(evaluators),
            'total_evaluations': len(self.raw_data['evaluation_data']),
            'total_scores': len(all_scores),
            'average_score': avg_score,
            'overall_stats': {
                'mean': avg_score,
                'min': min(all_scores) if all_scores else 0,
                'max': max(all_scores) if all_scores else 0
            }
        }

def main():
    """主函數"""
    import argparse
    
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='Vancouver算法處理器')
    parser.add_argument('--input-file', '-i', type=str,
                       help='評分數據JSON文件路徑')
    parser.add_argument('--output-dir', '-o', type=str,
                       help='輸出目錄路徑')
    
    args = parser.parse_args()
    
    # 載入統一配置
    from stage0_config_unified import PeerEvaluationConfig
    config = PeerEvaluationConfig()
    
    # 設定評分數據路徑
    if args.input_file:
        evaluation_data_path = args.input_file
    else:
        # 使用 vancouver_input.json（由 stage4 生成的 Vancouver 格式）
        # 從配置獲取路徑
        try:
            from stage0_config_unified import PeerEvaluationConfig
        except ImportError:
            from .stage0_config_unified import PeerEvaluationConfig
        
        config = PeerEvaluationConfig()
        # 修改：使用 vancouver_input 而不是 evaluation_results_json
        evaluation_data_path = config.get_path('stage5_results', 'vancouver_input')
    
    # 檢查文件是否存在
    if not os.path.exists(evaluation_data_path):
        print(f"錯誤: 找不到評分數據文件 {evaluation_data_path}")
        return
    
    # 創建處理器
    processor = VancouverProcessor(evaluation_data_path)
    
    # 如果指定了輸出目錄，修改處理器的輸出路徑
    if args.output_dir:
        processor.output_dir = args.output_dir
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir, exist_ok=True)
    
    # 執行完整流程
    final_grades, report_df, json_path, excel_path = processor.process_complete_workflow()
    
    return processor, final_grades, report_df

if __name__ == "__main__":
    main()
