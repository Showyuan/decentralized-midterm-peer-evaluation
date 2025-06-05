#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BASIC_PRECISION 參數最佳化分析工具

分析不同 BASIC_PRECISION 值對學生考試互評系統的影響
重點關注權重計算、聲譽分數計算和系統穩定性
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

from core.vancouver import Graph

class LoggerPrint:
    """自定義日志記錄器，同時輸出到控制台和文件"""
    
    def __init__(self, log_file=None):
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"basic_precision_analysis_{timestamp}.log"
        
        self.log_file = log_file
        
        # 設置日志記錄器
        self.logger = logging.getLogger('BasicPrecisionAnalyzer')
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
    
    def print(self, message):
        """同時記錄到文件和控制台"""
        self.logger.info(message)

class BasicPrecisionAnalyzer:
    """BASIC_PRECISION 參數分析器"""
    
    def __init__(self, logger_print=None):
        if logger_print is None:
            self.logger = LoggerPrint()
        else:
            self.logger = logger_print
        
        # 分析範圍：從 1e-6 到 1e-1
        self.precision_values = np.logspace(-6, -1, 25)
        
        # 存儲分析結果
        self.results = {}
        
        # 學生配置（固定15個學生）
        self.student_names = [
            'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 
            'Henry', 'Iris', 'Jack', 'Kate', 'Leo', 'Maya', 'Nick', 'Olivia'
        ]
        
        # 學生真實能力分佈（固定）
        np.random.seed(42)  # 確保可重現性
        self.true_abilities = np.random.normal(75, 15, 15)
        self.true_abilities = np.clip(self.true_abilities, 0, 100)
        
        # 學生評分變異度（固定）
        self.student_variances = np.random.uniform(0.5, 3.0, 15)
    
    def create_enhanced_graph(self, basic_precision):
        """創建增強圖形對象，使用指定的 basic_precision"""
        # 直接創建 Graph 對象，使用正確的參數
        graph = Graph(basic_precision=basic_precision, use_all_data=True)
        
        # 手動添加學生和作業的評分數據
        # 使用固定的隨機種子確保一致性
        np.random.seed(42)
        
        # 模擬學生對作業的評分
        assignments = ['HW1', 'HW2', 'HW3', 'HW4', 'HW5']
        
        for i, assignment in enumerate(assignments):
            # 每個作業的真實分數（基於固定種子）
            true_grade = 70 + i * 5 + np.random.normal(0, 10)
            true_grade = np.clip(true_grade, 0, 100)
            
            # 每個學生對這個作業的評分
            for j, student_name in enumerate(self.student_names):
                # 基於學生的能力和變異度生成評分
                student_bias = (self.true_abilities[j] - 75) * 0.1  # 能力偏差
                noise = np.random.normal(0, self.student_variances[j])
                grade = true_grade + student_bias + noise
                grade = np.clip(grade, 0, 100)
                
                # 只有部分學生評分每個作業（模擬互評場景）
                if np.random.random() < 0.6:  # 60% 的學生參與評分
                    graph.add_review(student_name, assignment, grade)
        
        return graph
    
    def analyze_system_metrics(self, graph):
        """分析系統指標"""
        
        # 運行 Vancouver 算法
        graph.evaluate_items(n_iterations=20)
        graph.evaluate_users()
        
        # 計算聲譽分數
        reputation_scores = []
        for student_name in self.student_names:
            user = graph.get_user(student_name)
            if user and hasattr(user, 'quality') and user.quality is not None:
                reputation_scores.append(user.quality)
            else:
                reputation_scores.append(0.0)
        
        reputation_scores = np.array(reputation_scores)
        
        # 計算作業成績
        assignment_grades = []
        assignments = ['HW1', 'HW2', 'HW3', 'HW4', 'HW5']
        for assignment in assignments:
            item = graph.get_item(assignment)
            if item and hasattr(item, 'grade') and item.grade is not None:
                assignment_grades.append(item.grade)
            else:
                assignment_grades.append(50.0)
        
        assignment_grades = np.array(assignment_grades)
        
        # 計算用戶偏差和變異數
        user_biases = []
        user_variances = []
        for student_name in self.student_names:
            user = graph.get_user(student_name)
            if user:
                if hasattr(user, 'bias') and user.bias is not None:
                    user_biases.append(abs(user.bias))
                else:
                    user_biases.append(0.0)
                    
                if hasattr(user, 'variance') and user.variance is not None:
                    user_variances.append(user.variance)
                else:
                    user_variances.append(1.0)
            else:
                user_biases.append(0.0)
                user_variances.append(1.0)
        
        user_biases = np.array(user_biases)
        user_variances = np.array(user_variances)
        
        # 系統指標
        metrics = {
            'reputation_mean': np.mean(reputation_scores),
            'reputation_std': np.std(reputation_scores),
            'reputation_range': np.max(reputation_scores) - np.min(reputation_scores),
            'reputation_effective_ratio': np.sum(reputation_scores > 0) / len(reputation_scores),
            
            'grade_mean': np.mean(assignment_grades),
            'grade_std': np.std(assignment_grades),
            'grade_range': np.max(assignment_grades) - np.min(assignment_grades),
            
            'bias_mean': np.mean(user_biases),
            'bias_std': np.std(user_biases),
            'variance_mean': np.mean(user_variances),
            'variance_std': np.std(user_variances),
            
            'system_stability': 1.0 / (1.0 + np.std(user_variances)),
            'discrimination_power': np.std(reputation_scores) / (np.mean(reputation_scores) + 1e-6),
        }
        
        return metrics
    
    def workload_analysis(self, graph):
        """工作負載分析 - 評分分佈統計"""
        grading_counts = {}
        for student_name in self.student_names:
            grading_counts[student_name] = 0
            
        # 統計每個學生的評分次數
        for student_name in self.student_names:
            user = graph.get_user(student_name)
            if user:
                grading_counts[student_name] = len(user.items)
        
        counts = list(grading_counts.values())
        
        if len(counts) == 0 or max(counts) == 0:
            return {
                'min_workload': 0,
                'max_workload': 0,
                'mean_workload': 0.0,
                'std_workload': 0.0,
                'workload_balance': 1.0
            }
        
        return {
            'min_workload': min(counts),
            'max_workload': max(counts),
            'mean_workload': np.mean(counts),
            'std_workload': np.std(counts),
            'workload_balance': 1.0 - (np.std(counts) / np.mean(counts)) if np.mean(counts) > 0 else 1.0
        }
    
    def run_analysis(self):
        """運行完整的 BASIC_PRECISION 分析"""
        
        self.logger.print("=" * 80)
        self.logger.print("開始 BASIC_PRECISION 參數最佳化分析")
        self.logger.print("=" * 80)
        self.logger.print(f"分析範圍: {self.precision_values[0]:.2e} 到 {self.precision_values[-1]:.2e}")
        self.logger.print(f"測試點數量: {len(self.precision_values)}")
        self.logger.print("")
        
        for i, precision in enumerate(self.precision_values):
            self.logger.print(f"分析進度: {i+1}/{len(self.precision_values)} - BASIC_PRECISION = {precision:.2e}")
            
            try:
                # 創建增強圖形
                graph = self.create_enhanced_graph(precision)
                
                # 分析系統指標
                metrics = self.analyze_system_metrics(graph)
                
                # 工作負載分析
                workload = self.workload_analysis(graph)
                
                # 合併結果
                result = {**metrics, **workload}
                
                # 計算綜合得分
                result['composite_score'] = self.calculate_composite_score(result)
                
                # 存儲結果
                self.results[precision] = result
                
                self.logger.print(f"  聲譽有效比率: {result['reputation_effective_ratio']:.3f}")
                self.logger.print(f"  系統穩定性: {result['system_stability']:.3f}")
                self.logger.print(f"  綜合得分: {result['composite_score']:.3f}")
                self.logger.print("")
                
            except Exception as e:
                self.logger.print(f"錯誤：分析 BASIC_PRECISION = {precision:.2e} 時發生錯誤: {str(e)}")
                continue
        
        # 找到最佳參數
        best_precision = self.find_optimal_precision()
        self.logger.print("=" * 80)
        self.logger.print("分析完成！")
        self.logger.print("=" * 80)
        self.logger.print(f"最佳 BASIC_PRECISION 值: {best_precision:.2e}")
        self.logger.print(f"最佳綜合得分: {self.results[best_precision]['composite_score']:.3f}")
        self.logger.print("")
        
        return self.results
    
    def calculate_composite_score(self, result):
        """計算綜合得分"""
        
        # 權重分配
        weights = {
            'reputation_effective_ratio': 0.25,  # 聲譽有效性
            'system_stability': 0.20,            # 系統穩定性
            'discrimination_power': 0.15,        # 區分能力
            'workload_balance': 0.15,            # 工作負載平衡
            'grade_range': 0.10,                 # 成績區分度
            'bias_control': 0.15                 # 偏差控制
        }
        
        # 標準化指標（0-1範圍）
        normalized_metrics = {
            'reputation_effective_ratio': result['reputation_effective_ratio'],
            'system_stability': min(result['system_stability'], 1.0),
            'discrimination_power': min(result['discrimination_power'] / 2.0, 1.0),
            'workload_balance': result['workload_balance'],
            'grade_range': min(result['grade_range'] / 50.0, 1.0),
            'bias_control': max(0, 1.0 - result['bias_mean'] / 10.0)
        }
        
        # 計算加權綜合得分
        composite_score = sum(
            weights[key] * normalized_metrics[key]
            for key in weights.keys()
        )
        
        return composite_score
    
    def find_optimal_precision(self):
        """找到最佳的 BASIC_PRECISION 值"""
        best_score = -1
        best_precision = None
        
        for precision, result in self.results.items():
            if result['composite_score'] > best_score:
                best_score = result['composite_score']
                best_precision = precision
        
        return best_precision
    
    def generate_summary_report(self):
        """生成摘要報告"""
        
        if not self.results:
            return "沒有分析結果可供報告。"
        
        best_precision = self.find_optimal_precision()
        best_result = self.results[best_precision]
        
        report = []
        report.append("=" * 80)
        report.append("BASIC_PRECISION 參數最佳化分析報告")
        report.append("=" * 80)
        report.append("")
        
        # 最佳參數
        report.append("🎯 最佳參數：")
        report.append(f"  BASIC_PRECISION: {best_precision:.2e}")
        report.append(f"  綜合得分: {best_result['composite_score']:.3f}")
        report.append("")
        
        # 關鍵指標
        report.append("📊 關鍵性能指標：")
        report.append(f"  聲譽有效比率: {best_result['reputation_effective_ratio']:.1%}")
        report.append(f"  系統穩定性: {best_result['system_stability']:.3f}")
        report.append(f"  區分能力: {best_result['discrimination_power']:.3f}")
        report.append(f"  工作負載平衡: {best_result['workload_balance']:.3f}")
        report.append("")
        
        # 聲譽系統
        report.append("🏆 聲譽系統表現：")
        report.append(f"  平均聲譽分數: {best_result['reputation_mean']:.3f}")
        report.append(f"  聲譽分數標準差: {best_result['reputation_std']:.3f}")
        report.append(f"  聲譽分數範圍: {best_result['reputation_range']:.3f}")
        report.append("")
        
        # 評分系統
        report.append("📝 評分系統表現：")
        report.append(f"  平均成績: {best_result['grade_mean']:.1f}")
        report.append(f"  成績標準差: {best_result['grade_std']:.3f}")
        report.append(f"  成績範圍: {best_result['grade_range']:.1f}")
        report.append("")
        
        # 偏差控制
        report.append("⚖️ 偏差控制：")
        report.append(f"  平均偏差: {best_result['bias_mean']:.3f}")
        report.append(f"  偏差標準差: {best_result['bias_std']:.3f}")
        report.append(f"  平均變異數: {best_result['variance_mean']:.3f}")
        report.append("")
        
        # 建議
        report.append("💡 建議：")
        if best_precision < 1e-5:
            report.append("  - 使用非常小的 BASIC_PRECISION 值可能會導致數值不穩定")
            report.append("  - 建議監控系統的數值穩定性")
        elif best_precision > 1e-2:
            report.append("  - 較大的 BASIC_PRECISION 值可能會降低系統敏感度")
            report.append("  - 考慮是否需要更精細的權重計算")
        else:
            report.append("  - 當前參數設置在合理範圍內")
            report.append("  - 系統表現良好，建議保持此設置")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

# 可視化函數
def plot_analysis_results(results, save_path=None):
    """繪製完整的分析結果圖表（英文版）"""
    
    # 提取數據
    precisions = list(results.keys())
    
    # 創建 2x3 子圖
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('BASIC_PRECISION Parameter Analysis Results', fontsize=16, fontweight='bold')
    
    # 子圖1: 綜合性能
    ax1 = axes[0, 0]
    composite_scores = [results[p]['composite_score'] for p in precisions]
    reputation_ratios = [results[p]['reputation_effective_ratio'] for p in precisions]
    
    ax1.semilogx(precisions, composite_scores, 'b-o', linewidth=2, markersize=6, label='Composite Score')
    ax1.semilogx(precisions, reputation_ratios, 'r--s', linewidth=2, markersize=5, label='Effective Reputation Ratio')
    ax1.set_xlabel('BASIC_PRECISION')
    ax1.set_ylabel('Score / Ratio')
    ax1.set_title('Overall System Performance')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1.1)
    
    # 子圖2: 聲譽分佈統計
    ax2 = axes[0, 1]
    rep_means = [results[p]['reputation_mean'] for p in precisions]
    rep_stds = [results[p]['reputation_std'] for p in precisions]
    
    ax2.semilogx(precisions, rep_means, 'g-o', linewidth=2, markersize=6, label='Mean Reputation')
    ax2_twin = ax2.twinx()
    ax2_twin.semilogx(precisions, rep_stds, 'orange', linestyle='--', marker='s', 
                      linewidth=2, markersize=5, label='Reputation Std Dev')
    
    ax2.set_xlabel('BASIC_PRECISION')
    ax2.set_ylabel('Mean Reputation', color='g')
    ax2_twin.set_ylabel('Standard Deviation', color='orange')
    ax2.set_title('Reputation Distribution Statistics')
    ax2.grid(True, alpha=0.3)
    
    # 合併圖例
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # 子圖3: 系統穩定性
    ax3 = axes[0, 2]
    stabilities = [results[p]['system_stability'] for p in precisions]
    workload_balances = [results[p]['workload_balance'] for p in precisions]
    
    ax3.semilogx(precisions, stabilities, 'purple', linestyle='-', marker='o', 
                 linewidth=2, markersize=6, label='System Stability')
    ax3.semilogx(precisions, workload_balances, 'brown', linestyle='--', marker='s', 
                 linewidth=2, markersize=5, label='Workload Balance')
    
    ax3.set_xlabel('BASIC_PRECISION')
    ax3.set_ylabel('Stability Score')
    ax3.set_title('System Stability Metrics')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 1.1)
    
    # 子圖4: 偏差控制
    ax4 = axes[1, 0]
    bias_means = [results[p]['bias_mean'] for p in precisions]
    variance_means = [results[p]['variance_mean'] for p in precisions]
    
    ax4.semilogx(precisions, bias_means, 'red', linestyle='-', marker='o', 
                 linewidth=2, markersize=6, label='Mean Bias')
    ax4_twin = ax4.twinx()
    ax4_twin.semilogx(precisions, variance_means, 'blue', linestyle='--', marker='s', 
                      linewidth=2, markersize=5, label='Mean Variance')
    
    ax4.set_xlabel('BASIC_PRECISION')
    ax4.set_ylabel('Mean Bias', color='red')
    ax4_twin.set_ylabel('Mean Variance', color='blue')
    ax4.set_title('Bias and Variance Control')
    ax4.grid(True, alpha=0.3)
    
    # 合併圖例
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # 子圖5: 區分能力
    ax5 = axes[1, 1]
    discrimination_powers = [results[p]['discrimination_power'] for p in precisions]
    grade_ranges = [results[p]['grade_range'] for p in precisions]
    
    ax5.semilogx(precisions, discrimination_powers, 'teal', linestyle='-', marker='o', 
                 linewidth=2, markersize=6, label='Discrimination Power')
    ax5_twin = ax5.twinx()
    ax5_twin.semilogx(precisions, grade_ranges, 'navy', linestyle='--', marker='s', 
                      linewidth=2, markersize=5, label='Grade Range')
    
    ax5.set_xlabel('BASIC_PRECISION')
    ax5.set_ylabel('Discrimination Power', color='teal')
    ax5_twin.set_ylabel('Grade Range', color='navy')
    ax5.set_title('Discrimination Ability')
    ax5.grid(True, alpha=0.3)
    
    # 合併圖例
    lines1, labels1 = ax5.get_legend_handles_labels()
    lines2, labels2 = ax5_twin.get_legend_handles_labels()
    ax5.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # 子圖6: 聲譽分數範圍
    ax6 = axes[1, 2]
    rep_ranges = [results[p]['reputation_range'] for p in precisions]
    grade_stds = [results[p]['grade_std'] for p in precisions]
    
    ax6.semilogx(precisions, rep_ranges, 'darkgreen', linestyle='-', marker='o', 
                 linewidth=2, markersize=6, label='Reputation Range')
    ax6_twin = ax6.twinx()
    ax6_twin.semilogx(precisions, grade_stds, 'maroon', linestyle='--', marker='s', 
                      linewidth=2, markersize=5, label='Grade Std Dev')
    
    ax6.set_xlabel('BASIC_PRECISION')
    ax6.set_ylabel('Reputation Range', color='darkgreen')
    ax6_twin.set_ylabel('Grade Std Dev', color='maroon')
    ax6.set_title('Score Distribution Range')
    ax6.grid(True, alpha=0.3)
    
    # 合併圖例
    lines1, labels1 = ax6.get_legend_handles_labels()
    lines2, labels2 = ax6_twin.get_legend_handles_labels()
    ax6.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"圖表已保存至: {save_path}")
    
    plt.show()

def plot_detailed_comparison(results, save_path=None):
    """繪製詳細對比圖表"""
    
    precisions = list(results.keys())
    
    # 創建 2x2 子圖進行詳細對比
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('BASIC_PRECISION Detailed Performance Comparison', fontsize=16, fontweight='bold')
    
    # 子圖1: 核心性能指標對比
    ax1 = axes[0, 0]
    composite_scores = [results[p]['composite_score'] for p in precisions]
    reputation_ratios = [results[p]['reputation_effective_ratio'] for p in precisions]
    stabilities = [results[p]['system_stability'] for p in precisions]
    
    ax1.semilogx(precisions, composite_scores, 'b-o', linewidth=2, markersize=6, label='Composite Score')
    ax1.semilogx(precisions, reputation_ratios, 'r--s', linewidth=2, markersize=5, label='Effective Reputation')
    ax1.semilogx(precisions, stabilities, 'g-.^', linewidth=2, markersize=5, label='System Stability')
    
    ax1.set_xlabel('BASIC_PRECISION')
    ax1.set_ylabel('Performance Score')
    ax1.set_title('Core Performance Metrics')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1.1)
    
    # 子圖2: 數值穩定性分析
    ax2 = axes[0, 1]
    variance_means = [results[p]['variance_mean'] for p in precisions]
    bias_means = [results[p]['bias_mean'] for p in precisions]
    
    ax2.loglog(precisions, variance_means, 'purple', linestyle='-', marker='o', 
               linewidth=2, markersize=6, label='Mean Variance')
    ax2.loglog(precisions, np.array(bias_means) + 1e-6, 'orange', linestyle='--', marker='s', 
               linewidth=2, markersize=5, label='Mean Bias')
    
    ax2.set_xlabel('BASIC_PRECISION')
    ax2.set_ylabel('Numerical Values')
    ax2.set_title('Numerical Stability Analysis')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 子圖3: 系統響應敏感度
    ax3 = axes[1, 0]
    discrimination_powers = [results[p]['discrimination_power'] for p in precisions]
    rep_stds = [results[p]['reputation_std'] for p in precisions]
    
    ax3.semilogx(precisions, discrimination_powers, 'teal', linestyle='-', marker='o', 
                 linewidth=2, markersize=6, label='Discrimination Power')
    ax3.semilogx(precisions, rep_stds, 'navy', linestyle='--', marker='s', 
                 linewidth=2, markersize=5, label='Reputation Std Dev')
    
    ax3.set_xlabel('BASIC_PRECISION')
    ax3.set_ylabel('Sensitivity Measure')
    ax3.set_title('System Response Sensitivity')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 子圖4: 工作負載與平衡性
    ax4 = axes[1, 1]
    workload_balances = [results[p]['workload_balance'] for p in precisions]
    grade_ranges = [results[p]['grade_range'] / 50.0 for p in precisions]  # 標準化
    
    ax4.semilogx(precisions, workload_balances, 'brown', linestyle='-', marker='o', 
                 linewidth=2, markersize=6, label='Workload Balance')
    ax4.semilogx(precisions, grade_ranges, 'darkred', linestyle='--', marker='s', 
                 linewidth=2, markersize=5, label='Grade Range (norm.)')
    
    ax4.set_xlabel('BASIC_PRECISION')
    ax4.set_ylabel('Balance Score')
    ax4.set_title('Load Balance & Distribution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"詳細對比圖表已保存至: {save_path}")
    
    plt.show()

def generate_comprehensive_analysis(with_plots=True):
    """生成完整的 BASIC_PRECISION 分析"""
    
    # 創建分析器
    logger = LoggerPrint()
    analyzer = BasicPrecisionAnalyzer(logger)
    
    # 運行分析
    results = analyzer.run_analysis()
    
    # 生成報告
    report = analyzer.generate_summary_report()
    logger.print(report)
    
    # 可視化結果
    if with_plots and results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 綜合分析圖表
        plot_save_path = f"basic_precision_analysis_visualization_{timestamp}.png"
        plot_analysis_results(results, plot_save_path)
        
        # 詳細對比圖表
        detailed_save_path = f"basic_precision_detailed_comparison_{timestamp}.png"
        plot_detailed_comparison(results, detailed_save_path)
    
    return results, analyzer

def main():
    """主函數"""
    print("開始 BASIC_PRECISION 參數最佳化分析...")
    results, analyzer = generate_comprehensive_analysis(with_plots=True)
    
    if results:
        print("\n分析完成！請查看生成的圖表和日誌文件。")
    else:
        print("\n分析失敗，請檢查錯誤信息。")

if __name__ == "__main__":
    main()
