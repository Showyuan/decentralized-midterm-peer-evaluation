#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
$\bar{v}_G$ 值最佳化分析工具

分析不同 $\bar{v}_G$ 值對學生考試互評系統的影響
重點關注聲譽分數計算和系統穩定性
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import logging
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from examples.student_grading_examples import EnhancedGraph, StudentGradingConfig
from core.vancouver import Graph

class LoggerPrint:
    """自定義日志記錄器，同時輸出到控制台和文件"""
    
    def __init__(self, log_file=None):
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"vg_analysis_{timestamp}.log"
        
        self.log_file = log_file
        
        # 設置日志記錄器
        self.logger = logging.getLogger('VGAnalyzer')
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的處理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 文件處理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 設置格式
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 記錄開始時間
        self.logger.info(f"🔬 Vancouver 算法 $\\bar{{v}}_G$ 參數分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)
    
    def print(self, *args, **kwargs):
        """替代print函數，同時輸出到控制台和日志文件"""
        message = ' '.join(str(arg) for arg in args)
        self.logger.info(message)
    
    def close(self):
        """關閉日志記錄器"""
        self.logger.info(f"\n📁 分析結果已保存到: {self.log_file}")
        self.logger.info(f"⏰ 分析完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

class VGAnalyzer:
    """$\bar{v}_G$ 值分析器 - 基於合理變異數標準的分析"""
    
    def __init__(self, log_file=None):
        self.test_data = self._generate_test_data()
        self.logger_print = LoggerPrint(log_file)
        # 替換print函數為自定義的日志記錄函數
        self.print = self.logger_print.print
    
    def _generate_test_data(self, reviews_per_student=4):
        """生成測試數據 - 模擬真實考試情境，確保每個學生評改相同數量的考卷"""
        # 模擬一個15人班級的考試互評情況
        test_scores = []
        
        # 定義學生類型及其特性（基於實際評分誤差對應的變異數）
        # ±2分誤差→變異數2, ±3分誤差→變異數4, ±4分誤差→變異數7, ±5分誤差→變異數10
        student_types = {
            "優秀學生": {"quality": 90, "variance": 3.0, "count": 3},    # ±2-3分誤差，變異數2-4
            "良好學生": {"quality": 80, "variance": 7.0, "count": 5},    # ±3-4分誤差，變異數4-7
            "一般學生": {"quality": 70, "variance": 12.0, "count": 4},   # ±4-5分誤差，變異數7-12
            "困難學生": {"quality": 60, "variance": 20.0, "count": 2},   # ±5-7分誤差，變異數12-20
            "極限學生": {"quality": 55, "variance": 25.0, "count": 1}    # ±5分誤差，變異數~25（測試極限）
        }
        
        # 生成學生列表
        students = []
        student_id = 1
        for student_type, props in student_types.items():
            for i in range(props["count"]):
                students.append({
                    "name": f"學生{student_id:02d}",
                    "type": student_type,
                    "true_quality": props["quality"] + np.random.normal(0, 3),
                    "eval_variance": props["variance"]
                })
                student_id += 1
        
        n_students = len(students)
        
        # 確保每個學生評改相同數量的考卷
        # 創建評改分配矩陣 - 每個學生評改 reviews_per_student 份考卷
        review_assignments = []
        
        for i, reviewer in enumerate(students):
            # 為每個評分者隨機選擇要評的考卷（不能評自己的）
            available_students = [j for j in range(n_students) if j != i]
            assigned_exams = np.random.choice(available_students, size=reviews_per_student, replace=False)
            
            for exam_owner_idx in assigned_exams:
                exam_owner = students[exam_owner_idx]
                exam_id = f"exam_{exam_owner['name']}"
                
                # 基於真實質量生成評分，使用評分者的標準差（非變異數）
                true_score = exam_owner["true_quality"]
                reviewer_std = np.sqrt(reviewer["eval_variance"])  # 變異數開根號得到標準差
                
                # 評分者能力影響評分準確性（基礎評分偏差）
                if reviewer["type"] == "優秀學生":
                    base_bias = np.random.normal(0, 1.0)  # 小幅隨機偏差
                elif reviewer["type"] == "良好學生":
                    base_bias = np.random.normal(0, 1.5)  # 中等隨機偏差
                elif reviewer["type"] == "一般學生":
                    base_bias = np.random.normal(0, 2.0)  # 較大隨機偏差
                elif reviewer["type"] == "困難學生":
                    base_bias = np.random.normal(0, 2.5)  # 最大隨機偏差
                else:  # 極限學生
                    base_bias = np.random.normal(0, 3.0)  # 極大隨機偏差
                
                # 最終評分 = 真實分數 + 評分者特定誤差 + 基礎偏差
                observed_score = true_score + np.random.normal(0, reviewer_std) + base_bias
                observed_score = max(0, min(100, observed_score))  # 限制在0-100範圍
                
                test_scores.append((reviewer["name"], exam_id, observed_score))
        
        return test_scores, students
    
    def analyze_vg_impact(self, vg_values=None):
        """分析不同 $\bar{v}_G$ 值的影響"""
        if vg_values is None:
            vg_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0]
        
        results = {}
        test_scores, students = self.test_data
        
        self.print("🔍 分析不同 $\\bar{v}_G$ 值對考試互評系統的影響")
        self.print("=" * 80)
        
        # 首先說明計算方式
        self._explain_calculation_methods()
        
        # 顯示實驗設置
        self.print(f"📊 實驗設置:")
        self.print(f"   學生人數: {len(students)}")
        self.print(f"   評分記錄數: {len(test_scores)}")
        self.print(f"   每位學生評改: {len(test_scores) // len(students)} 份考卷")
        self.print()
        
        for vg in vg_values:
            self.print(f"\n📊 測試 $\\bar{{v}}_G$ = {vg}")
            
            # 創建測試系統
            config = StudentGradingConfig.get_config()
            config['v_G'] = vg
            grading_system = EnhancedGraph(**config)
            
            # 添加評分數據
            for reviewer, exam_id, score in test_scores:
                grading_system.add_peer_review(reviewer, exam_id, score)
            
            # 運行評估
            grading_system.evaluate_items(n_iterations=20)
            grading_system.evaluate_users()
            grading_system.calculate_reputation_scores()
            grading_system.calculate_incentive_weights()
            
            # 計算系統指標
            metrics = self._calculate_system_metrics(grading_system, students)
            results[vg] = metrics
            
            self.print(f"   λ = R_max/v_G = {config['R_max']}/{vg} = {config['R_max']/vg:.3f}")
            self.print(f"   聲譽分數範圍: [{metrics['rep_min']:.3f}, {metrics['rep_max']:.3f}]")
            self.print(f"   平均聲譽: {metrics['rep_mean']:.3f}")
            self.print(f"   聲譽標準差: {metrics['rep_std']:.3f}")
            self.print(f"   有效聲譽者比例: {metrics['effective_rep_ratio']:.1%}")
            self.print(f"   成績差異度: {metrics['grade_dispersion']:.3f}")
            
            # 對關鍵的vG值顯示詳細結果
            if vg in [2.0, 4.0, 6.0]:
                self._display_detailed_results(grading_system, vg, metrics)
        
        return results
    
    def _calculate_system_metrics(self, grading_system, students):
        """計算系統性能指標"""
        reputations = []
        variances = []
        incentive_weights = []
        grades = []
        
        for user in grading_system.users:
            if hasattr(user, 'reputation'):
                reputations.append(user.reputation)
            if hasattr(user, 'variance') and user.variance is not None:
                variances.append(user.variance)
            if hasattr(user, 'incentive_weight'):
                incentive_weights.append(user.incentive_weight)
        
        for item in grading_system.items:
            if hasattr(item, 'grade') and item.grade is not None:
                grades.append(item.grade)
        
        # 計算有效聲譽者比例（聲譽 > 0.1）
        effective_rep_count = sum(1 for r in reputations if r > 0.1)
        effective_rep_ratio = effective_rep_count / len(reputations) if reputations else 0
        
        return {
            'rep_min': min(reputations) if reputations else 0,
            'rep_max': max(reputations) if reputations else 0,
            'rep_mean': np.mean(reputations) if reputations else 0,
            'rep_std': np.std(reputations) if reputations else 0,
            'effective_rep_ratio': effective_rep_ratio,
            'var_mean': np.mean(variances) if variances else 0,
            'var_std': np.std(variances) if variances else 0,
            'grade_dispersion': np.std(grades) if grades else 0,
            'incentive_mean': np.mean(incentive_weights) if incentive_weights else 0,
        }
    
    def _calculate_composite_score(self, metrics):
        """計算綜合評分，用於比較不同 vG 值的效果"""
        # 基於多個指標計算綜合分數
        
        # 1. 聲譽分佈指標 (權重: 30%)
        # 理想情況：平均聲譽適中(0.4-0.7)，有適度分散(std 0.1-0.3)
        rep_mean_score = 1.0 - abs(metrics['rep_mean'] - 0.55) / 0.55  # 最佳值0.55
        rep_std_score = min(1.0, metrics['rep_std'] / 0.2)  # 適度分散
        reputation_score = (rep_mean_score + rep_std_score) / 2
        
        # 2. 有效聲譽者比例 (權重: 25%)
        # 理想情況：60%-90%的評分者有有效聲譽
        effective_ratio_score = min(1.0, metrics['effective_rep_ratio'] / 0.8)
        if metrics['effective_rep_ratio'] > 0.9:
            effective_ratio_score *= 0.9  # 過高也不好，可能表示懲罰不足
        
        # 3. 變異數控制能力 (權重: 20%)
        # 理想情況：變異數有適度分散，但不會過大
        var_control_score = 1.0 / (1.0 + metrics['var_mean'] / 10.0)  # 控制變異數不要過大
        
        # 4. 系統穩定性 (權重: 15%)
        # 理想情況：各項指標都有穩定的數值
        stability_score = 1.0 / (1.0 + metrics['rep_std'] * 2)  # 聲譽分散度不要過大
        
        # 5. 成績區分度 (權重: 10%)
        # 理想情況：能夠適度區分不同水平的作品
        grade_discrimination_score = min(1.0, metrics['grade_dispersion'] / 15.0)
        
        # 計算加權綜合分數
        composite_score = (
            reputation_score * 0.30 +
            effective_ratio_score * 0.25 +
            var_control_score * 0.20 +
            stability_score * 0.15 +
            grade_discrimination_score * 0.10
        )
        
        return max(0.0, min(1.0, composite_score))  # 限制在 [0, 1] 範圍

    def find_optimal_vg(self, vg_range=(0.5, 8.0), resolution=30):
        """尋找最佳 $\bar{v}_G$ 值"""
        self.print("\n🎯 尋找最佳 $\\bar{v}_G$ 值")
        self.print("=" * 50)
        
        vg_values = np.linspace(vg_range[0], vg_range[1], resolution)
        
        # 進行分析
        results = self.analyze_vg_impact(vg_values)
        
        # 計算綜合得分
        scores = {}
        for vg, metrics in results.items():
            scores[vg] = self._calculate_composite_score(metrics)
        
        # 找到最佳值
        optimal_vg = max(scores.keys(), key=lambda k: scores[k])
        
        self.print(f"\n✅ 推薦的最佳 $\\bar{{v}}_G$ 值: {optimal_vg:.2f}")
        self.print(f"   綜合得分: {scores[optimal_vg]:.3f}")
        self.print(f"   對應 λ 值: {1.0/optimal_vg:.3f}")
        
        optimal_metrics = results[optimal_vg]
        self.print(f"\n📈 最佳配置下的系統特性:")
        self.print(f"   聲譽分數範圍: [{optimal_metrics['rep_min']:.3f}, {optimal_metrics['rep_max']:.3f}]")
        self.print(f"   平均聲譽: {optimal_metrics['rep_mean']:.3f}")
        self.print(f"   聲譽區分度: {optimal_metrics['rep_std']:.3f}")
        self.print(f"   有效聲譽者比例: {optimal_metrics['effective_rep_ratio']:.1%}")
        
        return optimal_vg, results
    
    def theoretical_analysis(self):
        """理論分析 $\bar{v}_G$ 的作用機制"""
        self.print("\n📚 $\\bar{v}_G$ 參數理論分析")
        self.print("=" * 60)
        
        self.print(f"""
🔧 $\\bar{{v}}_G$ 參數的數學意義:

1. **定義**: $\\bar{{v}}_G$ 是誤差容忍上限，代表系統能接受的最大評分變異數

2. **在聲譽計算中的作用**:
   - 聲譽公式: $R_j = \\max(0, R_{{max}} - \\lambda \\cdot \\sqrt{{\\hat{{v}}_j}})$
   - 其中 $\\lambda = \\frac{{R_{{max}}}}{{\\bar{{v}}_G}}$ 是懲罰斜率

3. **參數影響**:
   - $\\bar{{v}}_G$ ↑ → $\\lambda$ ↓ → 對高變異數評分者懲罰較輕
   - $\\bar{{v}}_G$ ↓ → $\\lambda$ ↑ → 對高變異數評分者懲罰較重

4. **考試情境的特殊考量**:
   - 考試評分相對客觀，變異數通常較小
   - 需要平衡嚴格性和包容性
   - 過小的 $\\bar{{v}}_G$ 可能導致過度懲罰
   - 過大的 $\\bar{{v}}_G$ 可能無法有效區分評分質量
   - 透過合理的變異數標準設定，可減少對容忍度機制的依賴
        """)
        
        # 計算不同變異數下的聲譽值
        self.print("\n📊 不同 $\\bar{v}_G$ 值下的聲譽計算示例:")
        vg_examples = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        
        # 表格標題行
        header = "評分者變異數 |"
        for vg in vg_examples:
            header += f" v_G={vg:<4.1f} |"
        self.print(header)
        
        # 分隔線
        separator = "-" * len(header)
        self.print(separator)
        
        # 數據行
        variances = [0.2, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0, 12.0, 15.0, 20.0, 25.0]
        for var in variances:
            row = f"     {var:4.1f}      |"
            for vg in vg_examples:
                lambda_val = 1.0 / vg
                reputation = max(0, 1.0 - lambda_val * np.sqrt(var))
                row += f" {reputation:6.3f} |"
            self.print(row)
        
        # 變異數標準分析
        self.print(f"\n🎯 調整後的變異數標準分析:")
        self.print(f"""
📈 **合理的變異數範圍**:
   - 優秀學生 (±2-3分誤差): 變異數 2-4
   - 良好學生 (±3-4分誤差): 變異數 4-7  
   - 一般學生 (±4-5分誤差): 變異數 7-12
   - 困難學生 (±5-7分誤差): 變異數 12-20

🔬 **實驗設計改進**:
   - 確保每位學生評改相同數量({len(self.test_data[0]) // len(self.test_data[1])})的考卷
   - 使用基於實際誤差範圍的變異數標準
   - 避免因評改數量不均造成的偏差
   - 提供更公平的聲譽計算基礎
   - 減少對額外容忍度機制的依賴
        """)
    
    def generate_recommendations(self, optimal_vg):
        """生成 $\bar{v}_G$ 值使用建議"""
        self.print(f"\n💡 $\\bar{{v}}_G$ = {optimal_vg:.2f} 的使用建議")
        self.print("=" * 60)
        
        lambda_val = 1.0 / optimal_vg
        
        self.print(f"""
🎯 **建議配置**:
   - $\\bar{{v}}_G$ = {optimal_vg:.2f}
   - $\\lambda$ = {lambda_val:.3f}
   - 每位學生評改: {len(self.test_data[0]) // len(self.test_data[1])} 份考卷
   
📋 **適用場景**:
   - {len(self.test_data[1])}人左右的班級考試互評
   - 每份考卷由多人評分
   - 評分標準相對明確的客觀試題
   - 需要公平分配評改工作量的情境
   
⚙️  **參數調整指南**:
   - 如果評分者整體水平較高 → 可適當降低 $\\bar{{v}}_G$ (提高要求)
   - 如果評分標準較主觀 → 可適當提高 $\\bar{{v}}_G$ (更包容)
   - 如果班級規模較小(<20人) → 建議提高 $\\bar{{v}}_G$ (避免過度懲罰)
   - 如果班級規模較大(>50人) → 可降低 $\\bar{{v}}_G$ (提高區分度)
        """)
        
        self.print(f"""
🔍 **監控指標**:
   - 有效聲譽者比例應在 60%-90% 之間
   - 聲譽分數應有適度分散(標準差 0.1-0.3)
   - 平均聲譽不應過低(<0.3)或過高(>0.8)
   - 評改工作量分配應該均勻
   
📊 **工作量分配檢查**:
   - 確認每位學生評改的考卷數量相同
   - 監控評改分配的隨機性和公平性
   - 避免特定學生負擔過重或過輕
   
🎯 **變異數標準檢查**:
   - 實際評分變異數應在合理範圍內（2-20）
   - 評分誤差範圍應控制在±2-7分
   - 避免極端的評分差異影響系統穩定性
        """)
        
    def workload_analysis(self):
        """分析評改工作量分配"""
        test_scores, students = self.test_data
        
        self.print(f"\n📊 評改工作量分配分析")
        self.print("=" * 50)
        
        # 統計每位學生的評改數量
        reviewer_counts = {}
        examinee_counts = {}
        
        for reviewer, exam_id, score in test_scores:
            reviewer_counts[reviewer] = reviewer_counts.get(reviewer, 0) + 1
            examinee = exam_id.replace("exam_", "")
            examinee_counts[examinee] = examinee_counts.get(examinee, 0) + 1
        
        # 評改數量統計
        review_counts = list(reviewer_counts.values())
        examined_counts = list(examinee_counts.values())
        
        self.print(f"📝 評改工作量分析:")
        self.print(f"   每位學生評改考卷數: {np.mean(review_counts):.1f} ± {np.std(review_counts):.2f}")
        self.print(f"   評改數量範圍: {min(review_counts)} - {max(review_counts)}")
        self.print(f"   工作量均勻度: {'良好' if np.std(review_counts) < 0.1 else '需改善'}")
        
        self.print(f"\n📋 被評改狀況:")
        self.print(f"   每份考卷被評次數: {np.mean(examined_counts):.1f} ± {np.std(examined_counts):.2f}")
        self.print(f"   被評次數範圍: {min(examined_counts)} - {max(examined_counts)}")
        self.print(f"   評審覆蓋均勻度: {'良好' if np.std(examined_counts) < 0.5 else '需改善'}")
        
        # 檢查工作量平衡
        if np.std(review_counts) < 0.1:
            self.print(f"\n✅ 工作量分配達到理想狀態，每位學生評改數量一致")
        else:
            self.print(f"\n⚠️  工作量分配有改善空間，建議調整分配算法")
    
    def _explain_calculation_methods(self):
        """說明聲譽和成績差異度的計算方式"""
        self.print("\n📊 計算方式說明")
        self.print("=" * 60)
        
        self.print("""
🔢 **聲譽計算公式**:
   R_j = max(0, R_max - λ × √(σ_j²))
   
   其中:
   - R_j: 評分者j的聲譽分數
   - R_max: 最大聲譽值 (通常為1.0)
   - λ: 懲罰係數 = R_max / v̄_G
   - σ_j²: 評分者j的評分變異數
   - √(σ_j²): 評分者j的評分標準差

📈 **成績差異度計算**:
   成績差異度 = std(所有作品的最終成績)
   
   其中:
   - 每個作品的最終成績由多位評分者的加權平均得出
   - 權重基於評分者的聲譽分數
   - 較高差異度表示系統能更好區分作品質量

🎯 **有效聲譽者比例**:
   有效聲譽者比例 = (聲譽 > 0.1的評分者數量) / 總評分者數量
   
   - 聲譽 > 0.1 視為「有效」評分者
   - 理想比例為60%-90%，過低表示過度懲罰，過高表示懲罰不足
        """)

    def _display_detailed_results(self, grading_system, vg, metrics):
        """顯示詳細的個別學生結果"""
        self.print(f"\n📋 vG = {vg:.2f} 時各學生的詳細表現:")
        self.print("-" * 80)
        
        # 顯示學生聲譽詳情
        self.print("🏆 學生聲譽排行:")
        user_details = []
        for user in grading_system.users:
            if hasattr(user, 'reputation') and hasattr(user, 'variance'):
                user_details.append({
                    'name': user.name,
                    'reputation': user.reputation,
                    'variance': user.variance if user.variance is not None else 0,
                    'std_dev': np.sqrt(user.variance) if user.variance is not None else 0
                })
        
        # 按聲譽排序
        user_details.sort(key=lambda x: x['reputation'], reverse=True)
        
        self.print("   排名  姓名     聲譽    變異數   標準差   計算過程")
        self.print("   ----  ----     ----    -----   -----   --------")
        
        for i, user in enumerate(user_details[:10]):  # 只顯示前10名
            lambda_val = 1.0 / vg
            penalty = lambda_val * user['std_dev']
            reputation_calc = max(0, 1.0 - penalty)
            
            self.print(f"   {i+1:2d}.  {user['name']}   {user['reputation']:.3f}   {user['variance']:6.1f}   {user['std_dev']:5.2f}   "
                      f"max(0, 1.0 - {lambda_val:.3f}×{user['std_dev']:.2f}) = {reputation_calc:.3f}")
        
        if len(user_details) > 10:
            self.print(f"   ... (還有 {len(user_details)-10} 位學生)")
        
        # 顯示作品成績詳情
        self.print(f"\n📝 作品成績分佈:")
        item_grades = []
        for item in grading_system.items:
            if hasattr(item, 'grade') and item.grade is not None:
                item_grades.append({
                    'name': item.name,
                    'grade': item.grade
                })
        
        # 按成績排序
        item_grades.sort(key=lambda x: x['grade'], reverse=True)
        
        self.print("   排名  作品名稱    最終成績")
        self.print("   ----  --------    --------")
        
        for i, item in enumerate(item_grades[:10]):  # 只顯示前10名
            self.print(f"   {i+1:2d}.  {item['name']}      {item['grade']:6.2f}")
        
        if len(item_grades) > 10:
            self.print(f"   ... (還有 {len(item_grades)-10} 個作品)")
        
        # 計算並顯示成績差異度
        grades = [item['grade'] for item in item_grades]
        if grades:
            grade_mean = np.mean(grades)
            grade_std = np.std(grades)
            self.print(f"\n   成績統計: 平均 = {grade_mean:.2f}, 標準差 = {grade_std:.2f}")
            grade_sample = [f'{g:.1f}' for g in grades[:5]]
            self.print(f"   成績差異度計算: std([{', '.join(grade_sample)}...]) = {grade_std:.3f}")
    
    def plot_analysis_results(self, results, optimal_vg):
        """Create comprehensive visualization of vG analysis results in English"""
        # Import seaborn safely with fallback
        try:
            import seaborn as sns
            sns.set_style("whitegrid")
            plt.style.use('default')
        except ImportError:
            plt.style.use('default')
        
        # Configure matplotlib for better rendering
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['figure.dpi'] = 100
        
        # Extract data from results
        vg_values = sorted(results.keys())
        metrics_data = {
            'rep_mean': [results[vg]['rep_mean'] for vg in vg_values],
            'rep_std': [results[vg]['rep_std'] for vg in vg_values],
            'effective_rep_ratio': [results[vg]['effective_rep_ratio'] for vg in vg_values],
            'grade_dispersion': [results[vg]['grade_dispersion'] for vg in vg_values],
            'rep_min': [results[vg]['rep_min'] for vg in vg_values],
            'rep_max': [results[vg]['rep_max'] for vg in vg_values]
        }
        
        # Calculate composite scores
        composite_scores = []
        for vg in vg_values:
            score = self._calculate_composite_score(results[vg])
            composite_scores.append(score)
        
        # Create the main figure with subplots
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle('Vancouver Algorithm vG Parameter Optimization Analysis (15-Student Class Setup)', 
                     fontsize=14, fontweight='bold', y=0.98)
        
        # 1. Composite Score vs vG
        ax1 = plt.subplot(2, 3, 1)
        plt.plot(vg_values, composite_scores, 'b-', linewidth=2, marker='o', markersize=4)
        plt.axvline(x=optimal_vg, color='red', linestyle='--', alpha=0.7, 
                   label=f'Optimal vG = {optimal_vg:.2f}')
        optimal_score = self._calculate_composite_score(results[optimal_vg])
        plt.axhline(y=optimal_score, color='red', linestyle='--', alpha=0.7)
        plt.scatter([optimal_vg], [optimal_score], color='red', s=100, zorder=5)
        plt.xlabel('vG Value')
        plt.ylabel('Composite Score')
        plt.title('Overall System Performance')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # 2. Reputation Statistics
        ax2 = plt.subplot(2, 3, 2)
        plt.plot(vg_values, metrics_data['rep_mean'], 'g-', linewidth=2, marker='s', 
                markersize=4, label='Mean Reputation')
        plt.plot(vg_values, metrics_data['rep_std'], 'orange', linewidth=2, marker='^', 
                markersize=4, label='Reputation Std Dev')
        plt.axvline(x=optimal_vg, color='red', linestyle='--', alpha=0.7)
        plt.axhline(y=0.55, color='gray', linestyle=':', alpha=0.5, label='Ideal Mean (0.55)')
        plt.axhline(y=0.25, color='gray', linestyle=':', alpha=0.5, label='Ideal Std (0.25)')
        plt.xlabel('vG Value')
        plt.ylabel('Reputation Score')
        plt.title('Reputation Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 3. Effective Reputation Ratio
        ax3 = plt.subplot(2, 3, 3)
        effective_percentages = [ratio * 100 for ratio in metrics_data['effective_rep_ratio']]
        plt.plot(vg_values, effective_percentages, 'purple', linewidth=2, marker='D', markersize=4)
        plt.axvline(x=optimal_vg, color='red', linestyle='--', alpha=0.7)
        plt.axhspan(60, 90, alpha=0.2, color='green', label='Ideal Range (60%-90%)')
        plt.xlabel('vG Value')
        plt.ylabel('Effective Reputation Ratio (%)')
        plt.title('System Coverage')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 4. Lambda (Penalty Coefficient) vs vG
        ax4 = plt.subplot(2, 3, 4)
        lambda_values = [1.0/vg for vg in vg_values]
        plt.plot(vg_values, lambda_values, 'brown', linewidth=2, marker='x', markersize=6)
        plt.axvline(x=optimal_vg, color='red', linestyle='--', alpha=0.7)
        optimal_lambda = 1.0/optimal_vg
        plt.scatter([optimal_vg], [optimal_lambda], color='red', s=100, zorder=5)
        plt.xlabel('vG Value')
        plt.ylabel('Lambda (Penalty Coefficient)')
        plt.title('Penalty Mechanism Strength')
        plt.grid(True, alpha=0.3)
        
        # 5. Grade Dispersion
        ax5 = plt.subplot(2, 3, 5)
        plt.plot(vg_values, metrics_data['grade_dispersion'], 'teal', linewidth=2, marker='h', markersize=4)
        plt.axvline(x=optimal_vg, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('vG Value')
        plt.ylabel('Grade Dispersion (Std Dev)')
        plt.title('Grade Discrimination Ability')
        plt.grid(True, alpha=0.3)
        
        # 6. Reputation Range
        ax6 = plt.subplot(2, 3, 6)
        plt.fill_between(vg_values, metrics_data['rep_min'], metrics_data['rep_max'], 
                        alpha=0.3, color='skyblue', label='Reputation Range')
        plt.plot(vg_values, metrics_data['rep_max'], 'b-', linewidth=1.5, label='Max Reputation')
        plt.plot(vg_values, metrics_data['rep_min'], 'b--', linewidth=1.5, label='Min Reputation')
        plt.axvline(x=optimal_vg, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('vG Value')
        plt.ylabel('Reputation Score')
        plt.title('Reputation Score Range')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vg_analysis_visualization_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        self.print(f"\n📊 Visualization saved as: {filename}")
        plt.show()
        
        return filename
    
    def plot_detailed_comparison(self, results):
        """Create detailed comparison of key vG values"""
        # Key vG values to compare
        key_vg_values = [2.0, 4.0, 6.0, 8.0]
        available_keys = [vg for vg in key_vg_values if vg in results]
        
        if len(available_keys) < 2:
            self.print("Not enough data points for detailed comparison")
            return None
        
        # Extract metrics for comparison
        comparison_data = {}
        for vg in available_keys:
            comparison_data[vg] = results[vg]
        
        # Create comparison chart
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Detailed Comparison of Key vG Values', fontsize=14, fontweight='bold')
        
        # 1. Reputation Statistics Comparison
        vg_labels = [f'vG={vg}' for vg in available_keys]
        rep_means = [comparison_data[vg]['rep_mean'] for vg in available_keys]
        rep_stds = [comparison_data[vg]['rep_std'] for vg in available_keys]
        effective_ratios = [comparison_data[vg]['effective_rep_ratio'] * 100 for vg in available_keys]
        
        x_pos = np.arange(len(available_keys))
        width = 0.35
        
        ax1.bar(x_pos - width/2, rep_means, width, label='Mean Reputation', alpha=0.8)
        ax1.bar(x_pos + width/2, rep_stds, width, label='Reputation Std Dev', alpha=0.8)
        ax1.set_xlabel('vG Value')
        ax1.set_ylabel('Reputation Score')
        ax1.set_title('Reputation Statistics')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(vg_labels)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Effective Reputation Ratio
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        bars = ax2.bar(vg_labels, effective_ratios, color=colors[:len(available_keys)], alpha=0.8)
        ax2.axhline(y=60, color='green', linestyle='--', alpha=0.7, label='Min Ideal (60%)')
        ax2.axhline(y=90, color='green', linestyle='--', alpha=0.7, label='Max Ideal (90%)')
        ax2.set_xlabel('vG Value')
        ax2.set_ylabel('Effective Reputation Ratio (%)')
        ax2.set_title('System Coverage Comparison')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, ratio in zip(bars, effective_ratios):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{ratio:.1f}%', ha='center', va='bottom')
        
        # 3. Penalty Coefficient (Lambda)
        lambda_values = [1.0/vg for vg in available_keys]
        ax3.plot(available_keys, lambda_values, 'ro-', linewidth=2, markersize=8)
        ax3.set_xlabel('vG Value')
        ax3.set_ylabel('Lambda (Penalty Coefficient)')
        ax3.set_title('Penalty Mechanism Strength')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels
        for vg, lambda_val in zip(available_keys, lambda_values):
            ax3.annotate(f'{lambda_val:.3f}', (vg, lambda_val), 
                        textcoords="offset points", xytext=(0,10), ha='center')
        
        # 4. Composite Score Comparison
        composite_scores = [self._calculate_composite_score(comparison_data[vg]) for vg in available_keys]
        bars = ax4.bar(vg_labels, composite_scores, color=colors[:len(available_keys)], alpha=0.8)
        ax4.set_xlabel('vG Value')
        ax4.set_ylabel('Composite Score')
        ax4.set_title('Overall Performance Score')
        ax4.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, score in zip(bars, composite_scores):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{score:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save the plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vg_detailed_comparison_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        self.print(f"📊 Detailed comparison saved as: {filename}")
        plt.show()
        
        return filename

    def generate_comprehensive_analysis(self, include_plots=True):
        """Run complete analysis with optional plotting"""
        self.print("\n🚀 Starting Comprehensive vG Parameter Analysis")
        self.print("=" * 60)
        
        # First, check workload distribution
        self.workload_analysis()
        
        # Run theoretical analysis
        self.theoretical_analysis()
        
        # Find optimal vG with plotting
        optimal_vg, results = self.find_optimal_vg()
        
        if include_plots:
            self.print("\n📊 Generating Visualizations...")
            try:
                # Create main analysis plots
                main_plot = self.plot_analysis_results(results, optimal_vg)
                
                # Create detailed comparison
                detail_plot = self.plot_detailed_comparison(results)
                
                self.print(f"✅ Analysis complete with visualizations")
                
            except Exception as e:
                self.print(f"⚠️ Plotting failed: {e}")
                self.print("Analysis data is still available in results")
        
        return optimal_vg, results

def main():
    """主函數 - 基於調整後變異數標準的vG參數分析"""
    analyzer = VGAnalyzer()
    
    # 運行完整的綜合分析（包含英文畫圖功能）
    optimal_vg, results = analyzer.generate_comprehensive_analysis(include_plots=True)
    
    # 生成建議
    analyzer.generate_recommendations(optimal_vg)
    
    # 更新配置建議
    analyzer.print(f"\n🔧 建議更新 StudentGradingConfig 中的配置:")
    analyzer.print(f"   V_G_EXAM = {optimal_vg:.2f}  # 最佳化後的考試誤差容忍上限")
    analyzer.print(f"   每位學生評改考卷數: {len(analyzer.test_data[0]) // len(analyzer.test_data[1])}  # 確保工作量均等")
    
    # 實驗總結
    analyzer.print(f"\n📋 實驗總結:")
    analyzer.print(f"   • 分析了{len(analyzer.test_data[1])}位學生的評分行為")
    analyzer.print(f"   • 每位學生評改{len(analyzer.test_data[0]) // len(analyzer.test_data[1])}份考卷，工作量均等")
    analyzer.print(f"   • 使用調整後的變異數標準，無需額外容忍度機制")
    analyzer.print(f"   • 推薦使用 vG = {optimal_vg:.2f}")
    analyzer.print(f"   • 變異數標準更貼近實際評分情況")
    
    # 關閉日志記錄器
    analyzer.logger_print.close()

if __name__ == "__main__":
    main()
