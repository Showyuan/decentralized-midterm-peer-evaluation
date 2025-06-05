#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vancouver算法結果驗證器
驗證Q1~Q5分數加總計算的正確性
"""

import json
import pandas as pd
import numpy as np
import os

def verify_score_calculation():
    """驗證分數計算的正確性"""
    # 載入統一配置
    from config_unified import PeerEvaluationConfig
    config = PeerEvaluationConfig()
    
    print("🔍 驗證Vancouver算法分數計算...")
    print("=" * 60)
    
    # 載入原始評分數據
    # 實際文件位置在 workflow_results/4_result_evaluation/ 目錄下
    evaluation_results_path = config.get_unified_output_path("result_evaluation", "evaluation_results.json")
    with open(evaluation_results_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 載入Vancouver算法結果（動態尋找最新結果文件）
    # 實際文件位置在 workflow_results/5_vancouver_processing/ 目錄下
    vancouver_results_dir = config.get_unified_output_path("vancouver_processing")
    vancouver_files = [f for f in os.listdir(vancouver_results_dir) if f.startswith("vancouver_results_") and f.endswith(".json")]
    if not vancouver_files:
        print("❌ 錯誤: 找不到Vancouver結果文件")
        return
    
    # 使用最新的結果文件
    latest_file = sorted(vancouver_files)[-1]
    vancouver_results_path = os.path.join(vancouver_results_dir, latest_file)
    print(f"📂 使用Vancouver結果文件: {latest_file}")
    
    with open(vancouver_results_path, 'r', encoding='utf-8') as f:
        vancouver_results = json.load(f)
    
    print("📊 原始數據統計:")
    print(f"   - 評分者數量: {original_data['summary_stats']['total_evaluators']}")
    print(f"   - 評分總數: {original_data['summary_stats']['total_evaluations']}")
    print(f"   - 原始平均分: {original_data['summary']['overall_stats']['mean']:.2f} (單題平均)")
    
    # 重新計算加總分數來驗證
    print("\n🧮 重新計算Q1~Q5加總分數...")
    
    total_scores_by_evaluatee = {}
    evaluation_counts = {}
    
    for evaluation in original_data['evaluation_data']:
        evaluator_id = evaluation['evaluator_id']
        
        for evaluatee_id, eval_data in evaluation['evaluations'].items():
            # 計算Q1~Q5的總分，使用實際的details結構
            total_score = 0
            for q_num in range(1, 6):
                score_key = f"{evaluatee_id}_Q{q_num}_score"
                if score_key in eval_data['details']:
                    score = eval_data['details'][score_key]
                    total_score += score
            
            # 記錄每個被評分者的所有總分
            if evaluatee_id not in total_scores_by_evaluatee:
                total_scores_by_evaluatee[evaluatee_id] = []
                evaluation_counts[evaluatee_id] = 0
            
            total_scores_by_evaluatee[evaluatee_id].append(total_score)
            evaluation_counts[evaluatee_id] += 1
    
    # 計算統計數據
    print("✅ 加總分數統計:")
    all_total_scores = []
    for scores in total_scores_by_evaluatee.values():
        all_total_scores.extend(scores)
    
    print(f"   - 分數範圍: {min(all_total_scores)} ~ {max(all_total_scores)}")
    print(f"   - 平均總分: {np.mean(all_total_scores):.2f}")
    print(f"   - 標準差: {np.std(all_total_scores):.2f}")
    
    # 比較Vancouver算法結果
    print("\n🎯 Vancouver算法最終結果:")
    print(f"   - 平均最終成績: {vancouver_results['summary_statistics']['avg_final_grade']:.2f}")
    print(f"   - 平均共識分數: {vancouver_results['summary_statistics']['avg_consensus_score']:.2f}")
    print(f"   - 平均聲譽分數: {vancouver_results['summary_statistics']['avg_reputation']:.3f}")
    print(f"   - 使用保護機制: {vancouver_results['summary_statistics']['protection_used_count']} 人")
    
    # 創建詳細比較報告
    print("\n📋 詳細學生成績比較:")
    print("=" * 120)
    print(f"{'學生ID':<6} {'原始Q1~Q5均分':<15} {'加總分數均值':<15} {'Vancouver共識':<15} {'最終成績':<12} {'聲譽分數':<10} {'保護機制':<8}")
    print("-" * 120)
    
    comparison_data = []
    
    # 計算每個學生的原始單題平均分
    student_question_scores = {}  # {student_id: {Q1: [scores], Q2: [scores], ...}}
    
    # 收集所有學生的單題分數
    for evaluation in original_data['evaluation_data']:
        for evaluatee_id, eval_data in evaluation['evaluations'].items():
            if evaluatee_id not in student_question_scores:
                student_question_scores[evaluatee_id] = {f'Q{i}': [] for i in range(1, 6)}
            
            for q_num in range(1, 6):
                score_key = f"{evaluatee_id}_Q{q_num}_score"
                if score_key in eval_data['details']:
                    score = eval_data['details'][score_key]
                    student_question_scores[evaluatee_id][f'Q{q_num}'].append(score)
    
    for student_id in sorted(total_scores_by_evaluatee.keys()):
        # 計算原始單題平均分
        all_question_scores = []
        for q_num in range(1, 6):
            q_key = f'Q{q_num}'
            if q_key in student_question_scores[student_id]:
                all_question_scores.extend(student_question_scores[student_id][q_key])
        
        original_avg = np.mean(all_question_scores) if all_question_scores else 0
        
        # 加總分數的平均
        total_scores_avg = np.mean(total_scores_by_evaluatee[student_id])
        
        # Vancouver結果
        vancouver_grade = vancouver_results['final_grades'][student_id]
        consensus_score = vancouver_grade['consensus_score']
        final_grade = vancouver_grade['final_grade']
        reputation = vancouver_grade['reputation']
        protection_used = "是" if vancouver_grade['protection_used'] else "否"
        
        print(f"{student_id:<6} {original_avg:<15.2f} {total_scores_avg:<15.2f} {consensus_score:<15.2f} "
              f"{final_grade:<12.2f} {reputation:<10.3f} {protection_used:<8}")
        
        comparison_data.append({
            'student_id': student_id,
            'original_avg_per_question': original_avg,
            'total_score_avg': total_scores_avg,
            'expected_total': original_avg * 5,  # 預期的總分（單題均分 × 5）
            'vancouver_consensus': consensus_score,
            'vancouver_final': final_grade,
            'reputation': reputation,
            'protection_used': vancouver_grade['protection_used']
        })
    
    # 驗證計算正確性
    print("\n🔬 計算正確性驗證:")
    all_correct = True
    
    for data in comparison_data:
        expected = data['expected_total']
        actual = data['total_score_avg']
        diff = abs(expected - actual)
        
        if diff > 0.01:  # 允許微小的浮點誤差
            print(f"⚠️  {data['student_id']}: 預期總分 {expected:.2f}, 實際總分 {actual:.2f}, 差異 {diff:.2f}")
            all_correct = False
    
    if all_correct:
        print("✅ 所有學生的分數計算都正確！")
    
    # 分析Vancouver算法效果
    print("\n📈 Vancouver算法效果分析:")
    
    # 計算原始分數的標準差vs Vancouver共識分數的標準差
    original_total_avgs = [d['total_score_avg'] for d in comparison_data]
    vancouver_consensus = [d['vancouver_consensus'] for d in comparison_data]
    vancouver_final = [d['vancouver_final'] for d in comparison_data]
    
    print(f"   - 原始總分標準差: {np.std(original_total_avgs):.2f}")
    print(f"   - Vancouver共識分數標準差: {np.std(vancouver_consensus):.2f}")
    print(f"   - Vancouver最終成績標準差: {np.std(vancouver_final):.2f}")
    
    # 排名變化分析
    original_ranking = sorted(comparison_data, key=lambda x: x['total_score_avg'], reverse=True)
    vancouver_ranking = sorted(comparison_data, key=lambda x: x['vancouver_final'], reverse=True)
    
    print(f"\n🏆 排名變化分析:")
    print(f"   前5名 (原始總分): {', '.join([d['student_id'] for d in original_ranking[:5]])}")
    print(f"   前5名 (Vancouver): {', '.join([d['student_id'] for d in vancouver_ranking[:5]])}")
    
    # 保存比較報告
    df = pd.DataFrame(comparison_data)
    verification_report_path = config.get_unified_output_path("vancouver_processing", "vancouver_verification_report.xlsx")
    df.to_excel(verification_report_path, index=False)
    print(f"\n💾 詳細比較報告已保存到: {verification_report_path}")

if __name__ == "__main__":
    verify_score_calculation()
