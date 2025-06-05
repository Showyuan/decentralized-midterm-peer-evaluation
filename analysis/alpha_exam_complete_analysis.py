#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALPHA_EXAM Parameter Comprehensive Analysis Tool

Complete analysis and visualization tool for ALPHA_EXAM parameter optimization
in peer assessment systems using the Vancouver algorithm.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import Dict, List, Tuple, Any
import json
import os
import sys
from datetime import datetime

# Set visualization style
sns.set_style("whitegrid")
plt.style.use('default')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.student_grading_examples import EnhancedGraph

class AlphaExamCompleteAnalyzer:
    """Complete ALPHA_EXAM Parameter Analyzer with Visualization"""
    
    def __init__(self, alpha_range: Tuple[float, float] = (0.1, 0.9), n_points: int = 9):
        """
        Initialize analyzer
        
        Args:
            alpha_range: ALPHA_EXAM parameter range (min, max)
            n_points: Number of analysis points
        """
        self.alpha_values = np.linspace(alpha_range[0], alpha_range[1], n_points)
        self.results = {}
        
        # Vancouver algorithm fixed parameters (Based on analysis optimization)
        self.fixed_params = {
            'BASIC_PRECISION': 0.001,
            'N_ITERATIONS': 25,
            'R_MAX': 1.0,            # 最大聲譽值
            'V_G_EXAM': 6.0,         # 考試的誤差容忍上限 (基於分析最佳化)
            'N_EXAM': 4              # 考試互評的評審數量 (建議範圍: 3-6)
        }
        
    def create_enhanced_graph(self, alpha_exam: float) -> EnhancedGraph:
        """
        Create enhanced graph with specified ALPHA_EXAM value
        
        Args:
            alpha_exam: ALPHA_EXAM parameter value
            
        Returns:
            Configured EnhancedGraph instance
        """
        return EnhancedGraph(
            basic_precision=self.fixed_params['BASIC_PRECISION'],
            R_max=self.fixed_params['R_MAX'],
            v_G=self.fixed_params['V_G_EXAM'],
            alpha=alpha_exam,
            N=self.fixed_params['N_EXAM']
        )
    
    def simulate_exam_scenario(self, graph: EnhancedGraph, n_students: int = 15, 
                             n_exams: int = 5, random_seed: int = 42) -> Dict[str, Any]:
        """
        Simulate exam scenario
        
        Args:
            graph: EnhancedGraph instance
            n_students: Number of students
            n_exams: Number of exams
            random_seed: Random seed
            
        Returns:
            Dictionary containing simulation results
        """
        np.random.seed(random_seed)
        
        # Generate true student abilities (0-100)
        true_abilities = np.random.normal(75, 15, n_students)
        true_abilities = np.clip(true_abilities, 0, 100)
        
        # Add nodes for each student
        student_ids = []
        for i in range(n_students):
            student_id = f"student_{i+1:02d}"
            student_ids.append(student_id)
        
        # Simulate n_exams peer assessment rounds
        # Each student submits their work and evaluates others' work
        for exam_idx in range(n_exams):
            exam_name = f"exam_{exam_idx+1}"
            
            # Each student submits their own work score (based on true ability + noise)
            for i, student_id in enumerate(student_ids):
                noise = np.random.normal(0, 5)  # Exam noise
                score = true_abilities[i] + noise
                score = np.clip(score, 0, 100)
                
                # Student submits their work
                submission_id = f"{exam_name}_{student_id}"
                graph.add_student_submission(student_id, submission_id, score)
            
            # Simulate peer assessments (each student evaluates others' work)
            for evaluator_idx, evaluator_id in enumerate(student_ids):
                for evaluated_idx, evaluated_id in enumerate(student_ids):
                    if evaluator_id != evaluated_id:
                        # Evaluation score based on true ability difference and evaluator ability
                        evaluator_ability = true_abilities[evaluator_idx]
                        evaluated_ability = true_abilities[evaluated_idx]
                        
                        # Evaluation accuracy correlated with evaluator ability
                        accuracy = 0.7 + 0.3 * (evaluator_ability / 100)
                        noise = np.random.normal(0, 10 * (1 - accuracy))
                        
                        evaluation_score = evaluated_ability + noise
                        evaluation_score = np.clip(evaluation_score, 0, 100)
                        
                        # Add peer review
                        submission_id = f"{exam_name}_{evaluated_id}"
                        graph.add_peer_review(evaluator_id, submission_id, evaluation_score)
        
        return {
            'student_ids': student_ids,
            'true_abilities': true_abilities,
            'n_students': n_students,
            'n_exams': n_exams
        }
    
    def analyze_system_metrics(self, graph: EnhancedGraph, scenario_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Analyze system performance metrics
        
        Args:
            graph: EnhancedGraph instance
            scenario_data: Scenario simulation data
            
        Returns:
            System performance metrics dictionary
        """
        student_ids = scenario_data['student_ids']
        true_abilities = scenario_data['true_abilities']
        
        # Execute complete evaluation pipeline including reputation system
        final_grades = graph.evaluate_with_reputation(n_iterations=self.fixed_params['N_ITERATIONS'])
        
        # Extract values - use final grades
        final_grade_values = []
        consensus_values = []
        incentive_values = []
        reputation_values = []
        
        for student_id in student_ids:
            if student_id in final_grades:
                grade_info = final_grades[student_id]
                final_grade_values.append(grade_info['final_grade'])
                consensus_values.append(grade_info['consensus_score'])
                incentive_values.append(grade_info['incentive_weight'])
                reputation_values.append(grade_info['reputation'])
            else:
                # Default values if student has no grade data
                final_grade_values.append(50.0)
                consensus_values.append(50.0)
                incentive_values.append(0.5)
                reputation_values.append(0.5)
        
        # Calculate correlations
        final_correlation = np.corrcoef(true_abilities, final_grade_values)[0, 1] if len(final_grade_values) > 1 else 0
        consensus_correlation = np.corrcoef(true_abilities, consensus_values)[0, 1] if len(consensus_values) > 1 else 0
        reputation_correlation = np.corrcoef(true_abilities, reputation_values)[0, 1] if len(reputation_values) > 1 else 0
        
        # Handle NaN values
        final_correlation = final_correlation if not np.isnan(final_correlation) else 0
        consensus_correlation = consensus_correlation if not np.isnan(consensus_correlation) else 0
        reputation_correlation = reputation_correlation if not np.isnan(reputation_correlation) else 0
        
        # Calculate distribution statistics
        final_std = np.std(final_grade_values)
        final_mean = np.mean(final_grade_values)
        
        # Calculate incentive mechanism impact
        incentive_impact = np.std(incentive_values) / (np.mean(incentive_values) + 1e-8)
        
        return {
            'final_correlation': final_correlation,
            'consensus_correlation': consensus_correlation,
            'reputation_correlation': reputation_correlation,
            'final_grade_std': final_std,
            'final_grade_mean': final_mean,
            'incentive_impact': incentive_impact,
            'grade_range': max(final_grade_values) - min(final_grade_values) if final_grade_values else 0,
            'system_stability': 1.0 - (final_std / (final_mean + 1e-8))
        }
    
    def calculate_composite_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate composite score
        
        Args:
            metrics: System performance metrics
            
        Returns:
            Composite score (0-100)
        """
        # Weight settings
        weights = {
            'final_correlation': 0.4,      # Final grade correlation with true ability
            'consensus_correlation': 0.2,   # Consensus score correlation
            'reputation_correlation': 0.15, # Reputation system correlation
            'system_stability': 0.15,      # System stability
            'incentive_impact': 0.1        # Incentive mechanism impact (moderate is best)
        }
        
        # Normalize metrics
        normalized_metrics = {}
        normalized_metrics['final_correlation'] = max(0, metrics['final_correlation'])
        normalized_metrics['consensus_correlation'] = max(0, metrics['consensus_correlation'])
        normalized_metrics['reputation_correlation'] = max(0, metrics['reputation_correlation'])
        normalized_metrics['system_stability'] = max(0, min(1, metrics['system_stability']))
        
        # Incentive impact optimal value is in moderate range
        incentive_optimal = 0.3
        incentive_diff = abs(metrics['incentive_impact'] - incentive_optimal)
        normalized_metrics['incentive_impact'] = max(0, 1 - incentive_diff / incentive_optimal)
        
        # Calculate weighted total score
        composite_score = sum(weights[key] * normalized_metrics[key] for key in weights.keys())
        return composite_score * 100
    
    def run_alpha_analysis(self, n_students: int = 15, n_exams: int = 5, 
                          random_seed: int = 42) -> Dict[str, Any]:
        """
        Execute complete ALPHA_EXAM analysis
        
        Args:
            n_students: Number of students
            n_exams: Number of exams
            random_seed: Random seed
            
        Returns:
            Complete analysis results
        """
        print("開始 ALPHA_EXAM 參數分析...")
        print(f"分析範圍: {self.alpha_values[0]:.1f} ~ {self.alpha_values[-1]:.1f}")
        print(f"分析點數: {len(self.alpha_values)}")
        print(f"學生數量: {n_students}, 考試數量: {n_exams}")
        
        results = {
            'alpha_values': self.alpha_values.tolist(),
            'metrics': [],
            'composite_scores': [],
            'detailed_results': {}
        }
        
        for i, alpha in enumerate(self.alpha_values):
            print(f"\n分析進度: {i+1}/{len(self.alpha_values)} (ALPHA_EXAM = {alpha:.1f})")
            
            # Create graph and run simulation
            graph = self.create_enhanced_graph(alpha)
            scenario_data = self.simulate_exam_scenario(graph, n_students, n_exams, random_seed)
            
            # Analyze system metrics
            metrics = self.analyze_system_metrics(graph, scenario_data)
            composite_score = self.calculate_composite_score(metrics)
            
            # Store results
            results['metrics'].append(metrics)
            results['composite_scores'].append(composite_score)
            results['detailed_results'][alpha] = {
                'metrics': metrics,
                'composite_score': composite_score,
                'scenario_data': scenario_data
            }
            
            print(f"  綜合評分: {composite_score:.2f}")
            print(f"  最終成績相關性: {metrics['final_correlation']:.3f}")
        
        # Find best parameters
        best_idx = np.argmax(results['composite_scores'])
        best_alpha = self.alpha_values[best_idx]
        best_score = results['composite_scores'][best_idx]
        
        results['best_alpha'] = best_alpha
        results['best_score'] = best_score
        results['best_metrics'] = results['metrics'][best_idx]
        
        print(f"\n=== 分析完成 ===")
        print(f"最佳 ALPHA_EXAM: {best_alpha:.1f}")
        print(f"最佳綜合評分: {best_score:.2f}")
        
        self.results = results
        return results

    def create_comprehensive_dashboard(self, output_dir: str = None):
        """
        Create comprehensive analysis dashboard
        
        Args:
            output_dir: Output directory
        """
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        if not self.results:
            print("未找到分析結果。請先運行分析。")
            return
            
        # Create figure with 2 subplots only
        fig = plt.figure(figsize=(16, 8))
        
        # # 1. Main performance metrics trend
        # ax1 = plt.subplot(3, 3, 1)
        # self._plot_main_metrics_trend(ax1)
        
        # 2. Composite score trend
        ax2 = plt.subplot(1, 2, 1)
        self._plot_composite_score_trend(ax2)
        
        # # 3. Correlation analysis
        # ax3 = plt.subplot(3, 3, 3)
        # self._plot_correlation_analysis(ax3)
        
        # # 4. System stability analysis
        # ax4 = plt.subplot(3, 3, 4)
        # self._plot_stability_analysis(ax4)
        
        # # 5. Incentive mechanism impact
        # ax5 = plt.subplot(3, 3, 5)
        # self._plot_incentive_impact(ax5)
        
        # # 6. Parameter sensitivity analysis
        # ax6 = plt.subplot(3, 3, 6)
        # self._plot_parameter_sensitivity(ax6)
        
        # # 7. Optimal parameter range
        # ax7 = plt.subplot(3, 3, 7)
        # self._plot_optimal_range(ax7)
        
        # 8. Grade distribution comparison
        ax8 = plt.subplot(1, 2, 2)
        self._plot_grade_distribution(ax8)
        
        # # 9. System performance radar chart
        # ax9 = plt.subplot(3, 3, 9, projection='polar')
        # self._plot_performance_radar(ax9)
        
        # Adjust layout
        plt.tight_layout(pad=3.0)
        plt.suptitle('ALPHA_EXAM Parameter Analysis - Selected Charts', fontsize=14, y=0.98)
        
        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_path = os.path.join(output_dir, f'alpha_exam_complete_dashboard_{timestamp}.png')
        plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
        print(f"儀表板已保存至: {dashboard_path}")
        
        plt.show()
        
        # Generate detailed report
        self._generate_detailed_report(output_dir)
        
    def _plot_main_metrics_trend(self, ax):
        """Plot main performance metrics trend"""
        final_correlations = [m['final_correlation'] for m in self.results['metrics']]
        consensus_correlations = [m['consensus_correlation'] for m in self.results['metrics']]
        reputation_correlations = [m['reputation_correlation'] for m in self.results['metrics']]
        
        ax.plot(self.alpha_values, final_correlations, 'o-', label='Final Grade Correlation', linewidth=2)
        ax.plot(self.alpha_values, consensus_correlations, 's-', label='Consensus Score Correlation', linewidth=2)
        ax.plot(self.alpha_values, reputation_correlations, '^-', label='Reputation System Correlation', linewidth=2)
        
        ax.set_xlabel('ALPHA_EXAM Parameter Value')
        ax.set_ylabel('Correlation Coefficient')
        ax.set_title('Main Performance Metrics Trend')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    def _plot_composite_score_trend(self, ax):
        """Plot composite score trend"""
        composite_scores = np.array(self.results['composite_scores'])
        ax.plot(self.alpha_values, composite_scores, 'ro-', linewidth=3, markersize=8)
        
        # Mark best point
        best_idx = np.argmax(composite_scores)
        best_alpha = self.alpha_values[best_idx]
        best_score = composite_scores[best_idx]
        
        ax.plot(best_alpha, best_score, 'g*', markersize=15, label=f'Best: α={best_alpha:.1f}')
        ax.annotate(f'Best: {best_score:.2f}', 
                   xy=(best_alpha, best_score), 
                   xytext=(10, 10), 
                   textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        ax.set_xlabel('ALPHA_EXAM Parameter Value')
        ax.set_ylabel('Composite Score')
        ax.set_title('Composite Score Trend')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    def _plot_correlation_analysis(self, ax):
        """Plot correlation analysis"""
        correlations = np.array([
            [m['final_correlation'] for m in self.results['metrics']],
            [m['consensus_correlation'] for m in self.results['metrics']],
            [m['reputation_correlation'] for m in self.results['metrics']]
        ])
        
        im = ax.imshow(correlations, cmap='RdYlBu_r', aspect='auto', vmin=0, vmax=1)
        ax.set_xticks(range(len(self.alpha_values)))
        ax.set_xticklabels([f'{a:.1f}' for a in self.alpha_values])
        ax.set_yticks(range(3))
        ax.set_yticklabels(['Final Grade', 'Consensus Score', 'Reputation System'])
        ax.set_xlabel('ALPHA_EXAM Parameter Value')
        ax.set_title('Correlation Heatmap')
        
        # Add value labels
        for i in range(3):
            for j in range(len(self.alpha_values)):
                text = ax.text(j, i, f'{correlations[i, j]:.3f}',
                             ha="center", va="center", color="black", fontsize=8)
        
        plt.colorbar(im, ax=ax, shrink=0.8)
        
    def _plot_stability_analysis(self, ax):
        """Plot system stability analysis"""
        stabilities = [m['system_stability'] for m in self.results['metrics']]
        std_devs = [m['final_grade_std'] for m in self.results['metrics']]
        
        ax2 = ax.twinx()
        
        line1 = ax.plot(self.alpha_values, stabilities, 'b-o', label='System Stability')
        line2 = ax2.plot(self.alpha_values, std_devs, 'r-s', label='Standard Deviation')
        
        ax.set_xlabel('ALPHA_EXAM Parameter Value')
        ax.set_ylabel('Stability Coefficient', color='b')
        ax2.set_ylabel('Grade Standard Deviation', color='r')
        ax.set_title('System Stability Analysis')
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='center right')
        
        ax.grid(True, alpha=0.3)
        
    def _plot_incentive_impact(self, ax):
        """Plot incentive mechanism impact"""
        incentive_impacts = [m['incentive_impact'] for m in self.results['metrics']]
        
        ax.bar(self.alpha_values, incentive_impacts, alpha=0.7, color='orange')
        ax.axhline(y=0.3, color='red', linestyle='--', label='Ideal Range')
        ax.axhline(y=0.5, color='red', linestyle='--')
        
        ax.set_xlabel('ALPHA_EXAM Parameter Value')
        ax.set_ylabel('Incentive Impact Coefficient')
        ax.set_title('Incentive Mechanism Impact Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    def _plot_parameter_sensitivity(self, ax):
        """Plot parameter sensitivity analysis"""
        # Calculate coefficient of variation for each metric
        metrics_names = ['final_correlation', 'consensus_correlation', 'reputation_correlation', 'system_stability']
        sensitivities = []
        
        for metric_name in metrics_names:
            values = [m[metric_name] for m in self.results['metrics']]
            cv = np.std(values) / (np.mean(values) + 1e-8)  # Coefficient of variation
            sensitivities.append(cv)
        
        colors = ['skyblue', 'lightgreen', 'orange', 'pink']
        bars = ax.bar(range(len(metrics_names)), sensitivities, color=colors, alpha=0.8)
        
        ax.set_xticks(range(len(metrics_names)))
        ax.set_xticklabels(['Final Correlation', 'Consensus Correlation', 'Reputation Correlation', 'System Stability'], rotation=45)
        ax.set_ylabel('Sensitivity Coefficient')
        ax.set_title('Parameter Sensitivity Analysis')
        
        # Add value labels
        for bar, sensitivity in zip(bars, sensitivities):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                   f'{sensitivity:.4f}', ha='center', va='bottom')
        
        ax.grid(True, alpha=0.3)
        
    def _plot_optimal_range(self, ax):
        """Plot optimal parameter range"""
        composite_scores = np.array(self.results['composite_scores'])
        # Calculate 95% confidence interval
        threshold = np.max(composite_scores) * 0.95
        optimal_indices = np.where(composite_scores >= threshold)[0]
        
        ax.plot(self.alpha_values, composite_scores, 'b-o', linewidth=2, markersize=6)
        ax.axhline(y=threshold, color='red', linestyle='--', label=f'95% Threshold: {threshold:.2f}')
        
        # Mark optimal range
        if len(optimal_indices) > 0:
            optimal_alphas = self.alpha_values[optimal_indices]
            optimal_scores = composite_scores[optimal_indices]
            ax.scatter(optimal_alphas, optimal_scores, color='red', s=100, 
                      label=f'Optimal Range: {optimal_alphas[0]:.1f}-{optimal_alphas[-1]:.1f}', zorder=5)
        
        ax.set_xlabel('ALPHA_EXAM Parameter Value')
        ax.set_ylabel('Composite Score')
        ax.set_title('Optimal Parameter Range Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    def _plot_grade_distribution(self, ax):
        """Plot grade distribution comparison"""
        # Compare grade ranges under different ALPHA values
        grade_ranges = [m['grade_range'] for m in self.results['metrics']]
        final_means = [m['final_grade_mean'] for m in self.results['metrics']]
        
        scatter = ax.scatter(self.alpha_values, grade_ranges, c=final_means, cmap='viridis', s=100, alpha=0.8)
        
        ax.set_xlabel('ALPHA_EXAM Parameter Value')
        ax.set_ylabel('Grade Range')
        ax.set_title('Grade Distribution Analysis')
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
        cbar.set_label('Average Grade')
        
        ax.grid(True, alpha=0.3)
        
    def _plot_performance_radar(self, ax):
        """Plot system performance radar chart"""
        composite_scores = np.array(self.results['composite_scores'])
        # Select best and worst ALPHA values for comparison
        best_idx = np.argmax(composite_scores)
        worst_idx = np.argmin(composite_scores)
        
        metrics_names = ['Final Correlation', 'Consensus Correlation', 'Reputation Correlation', 'System Stability', 'Incentive Appropriateness']
        
        best_metrics = self.results['metrics'][best_idx]
        worst_metrics = self.results['metrics'][worst_idx]
        
        # Normalize incentive appropriateness (closer to 0.3 is better)
        def normalize_incentive(value):
            return max(0, 1 - abs(value - 0.3) / 0.3)
        
        best_values = [
            best_metrics['final_correlation'],
            best_metrics['consensus_correlation'], 
            best_metrics['reputation_correlation'],
            best_metrics['system_stability'],
            normalize_incentive(best_metrics['incentive_impact'])
        ]
        
        worst_values = [
            worst_metrics['final_correlation'],
            worst_metrics['consensus_correlation'],
            worst_metrics['reputation_correlation'], 
            worst_metrics['system_stability'],
            normalize_incentive(worst_metrics['incentive_impact'])
        ]
        
        # Set angles
        angles = np.linspace(0, 2 * np.pi, len(metrics_names), endpoint=False).tolist()
        best_values += best_values[:1]  # Close the shape
        worst_values += worst_values[:1]
        angles += angles[:1]
        
        # Plot radar chart
        ax.plot(angles, best_values, 'o-', linewidth=2, 
               label=f'Best (α={self.alpha_values[best_idx]:.1f})', color='green')
        ax.fill(angles, best_values, alpha=0.25, color='green')
        
        ax.plot(angles, worst_values, 'o-', linewidth=2, 
               label=f'Worst (α={self.alpha_values[worst_idx]:.1f})', color='red')
        ax.fill(angles, worst_values, alpha=0.25, color='red')
        
        # Set labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics_names)
        ax.set_ylim(0, 1)
        ax.set_title('System Performance Radar Chart')
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
    def _generate_detailed_report(self, output_dir: str):
        """Generate detailed analysis report"""
        report = {
            'analysis_summary': self._create_analysis_summary(),
            'optimal_parameters': self._analyze_optimal_parameters(),
            'performance_insights': self._extract_performance_insights(),
            'recommendations': self._generate_recommendations()
        }
        
        # Save JSON report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f'alpha_exam_complete_report_{timestamp}.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Generate Markdown report
        markdown_report = self._create_markdown_report(report)
        markdown_path = os.path.join(output_dir, f'alpha_exam_complete_report_{timestamp}.md')
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"詳細報告已保存至:")
        print(f"  JSON: {report_path}")
        print(f"  Markdown: {markdown_path}")
        
        return report
        
    def _create_analysis_summary(self):
        """Create analysis summary"""
        composite_scores = np.array(self.results['composite_scores'])
        best_idx = np.argmax(composite_scores)
        best_alpha = self.alpha_values[best_idx]
        best_score = composite_scores[best_idx]
        
        return {
            'best_alpha': float(best_alpha),
            'best_composite_score': float(best_score),
            'alpha_range_analyzed': [float(self.alpha_values[0]), float(self.alpha_values[-1])],
            'total_configurations_tested': len(self.alpha_values),
            'performance_variation': {
                'max_score': float(np.max(composite_scores)),
                'min_score': float(np.min(composite_scores)),
                'score_range': float(np.max(composite_scores) - np.min(composite_scores)),
                'std_deviation': float(np.std(composite_scores))
            }
        }
    
    def _analyze_optimal_parameters(self):
        """Analyze optimal parameters"""
        composite_scores = np.array(self.results['composite_scores'])
        threshold = np.max(composite_scores) * 0.95
        optimal_indices = np.where(composite_scores >= threshold)[0]
        optimal_alphas = self.alpha_values[optimal_indices]
        
        return {
            'optimal_range': {
                'min_alpha': float(optimal_alphas[0]) if len(optimal_alphas) > 0 else None,
                'max_alpha': float(optimal_alphas[-1]) if len(optimal_alphas) > 0 else None,
                'range_width': float(optimal_alphas[-1] - optimal_alphas[0]) if len(optimal_alphas) > 0 else 0
            },
            'sensitivity_analysis': self._calculate_parameter_sensitivity(),
            'stability_across_range': self._analyze_stability_across_range()
        }
    
    def _calculate_parameter_sensitivity(self):
        """Calculate parameter sensitivity"""
        metrics_names = ['final_correlation', 'consensus_correlation', 'reputation_correlation', 'system_stability']
        sensitivities = {}
        
        for metric_name in metrics_names:
            values = [m[metric_name] for m in self.results['metrics']]
            sensitivity = np.std(values) / (np.mean(values) + 1e-8)
            sensitivities[metric_name] = float(sensitivity)
            
        return sensitivities
    
    def _analyze_stability_across_range(self):
        """Analyze stability across the range"""
        stabilities = [m['system_stability'] for m in self.results['metrics']]
        
        return {
            'mean_stability': float(np.mean(stabilities)),
            'stability_trend': 'decreasing' if stabilities[-1] < stabilities[0] else 'increasing',
            'stability_variance': float(np.var(stabilities))
        }
    
    def _extract_performance_insights(self):
        """Extract performance insights"""
        correlations = [m['final_correlation'] for m in self.results['metrics']]
        reputations = [m['reputation_correlation'] for m in self.results['metrics']]
        incentives = [m['incentive_impact'] for m in self.results['metrics']]
        
        return {
            'correlation_with_true_ability': {
                'max_correlation': float(np.max(correlations)),
                'min_correlation': float(np.min(correlations)),
                'correlation_stability': float(np.std(correlations))
            },
            'incentive_mechanism_analysis': {
                'optimal_incentive_alpha': float(self.alpha_values[np.argmin([abs(i - 0.3) for i in incentives])]),
                'incentive_impact_range': [float(np.min(incentives)), float(np.max(incentives))],
                'deviation_from_ideal': float(np.mean([abs(i - 0.3) for i in incentives]))
            },
            'reputation_system_effectiveness': {
                'reputation_effectiveness': float(np.mean(reputations)),
                'reputation_consistency': float(1 - np.std(reputations)),
                'best_reputation_alpha': float(self.alpha_values[np.argmax(reputations)])
            }
        }
    
    def _generate_recommendations(self):
        """Generate recommendations"""
        composite_scores = np.array(self.results['composite_scores'])
        best_idx = np.argmax(composite_scores)
        best_alpha = self.alpha_values[best_idx]
        best_score = composite_scores[best_idx]
        
        correlations = [m['final_correlation'] for m in self.results['metrics']]
        best_corr_idx = np.argmax(correlations)
        best_corr_alpha = self.alpha_values[best_corr_idx]
        best_correlation = correlations[best_corr_idx]
        
        return [
            {
                'type': '主要建議',
                'recommendation': f'建議使用 ALPHA_EXAM = {best_alpha:.1f}，此參數值在綜合評估中表現最佳',
                'rationale': f'獲得綜合評分 {best_score:.2f}'
            },
            {
                'type': '相關性建議',
                'recommendation': f'若優先考慮與真實能力的相關性，建議使用 ALPHA_EXAM = {best_corr_alpha:.1f}',
                'rationale': f'此參數值提供最高的相關性: {best_correlation:.3f}'
            }
        ]
    
    def _create_markdown_report(self, report: dict):
        """Create Markdown report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown = f"""# ALPHA_EXAM 參數分析報告

## 分析摘要

- **最佳 ALPHA_EXAM 參數**: {report['analysis_summary']['best_alpha']:.1f}
- **最佳綜合評分**: {report['analysis_summary']['best_composite_score']:.2f}
- **分析範圍**: {report['analysis_summary']['alpha_range_analyzed'][0]:.1f} ~ {report['analysis_summary']['alpha_range_analyzed'][1]:.1f}
- **測試配置數量**: {report['analysis_summary']['total_configurations_tested']}

### 性能變異統計

- **最高評分**: {report['analysis_summary']['performance_variation']['max_score']:.2f}
- **最低評分**: {report['analysis_summary']['performance_variation']['min_score']:.2f}
- **評分範圍**: {report['analysis_summary']['performance_variation']['score_range']:.2f}
- **標準差**: {report['analysis_summary']['performance_variation']['std_deviation']:.2f}

## 最佳參數分析

- **最佳範圍**: {report['optimal_parameters']['optimal_range']['min_alpha']:.1f} ~ {report['optimal_parameters']['optimal_range']['max_alpha']:.1f}
- **範圍寬度**: {report['optimal_parameters']['optimal_range']['range_width']:.1f}

## 建議

"""
        
        for i, rec in enumerate(report['recommendations'], 1):
            markdown += f"""### {i}. {rec['type']}

**建議**: {rec['recommendation']}

**理由**: {rec['rationale']}

"""
        
        markdown += f"""

---

*報告生成時間: {timestamp}*
"""
        
        return markdown


def run_complete_analysis(output_dir: str = None):
    """
    Execute complete ALPHA_EXAM parameter analysis with visualization
    
    Args:
        output_dir: Output directory path
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create analyzer
    analyzer = AlphaExamCompleteAnalyzer(alpha_range=(0.1, 0.9), n_points=9)
    
    # Execute analysis
    results = analyzer.run_alpha_analysis(n_students=15, n_exams=5)
    
    # Create visualization dashboard
    analyzer.create_comprehensive_dashboard(output_dir)
    
    print(f"\n=== 完整分析已完成 ===")
    print(f"最佳 ALPHA_EXAM: {results['best_alpha']:.1f}")
    print(f"最佳綜合評分: {results['best_score']:.2f}")
    
    return results


if __name__ == "__main__":
    # Execute complete analysis
    results = run_complete_analysis()
