#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最佳 N 值計算的理論依據
Statistical and Practical Foundations for Optimal N Selection

本文檔詳細解釋了在學生互評系統中，如何根據班級規模、作業類型和品質要求
來計算最佳評審數量 N 的理論依據和實務考量。
"""

import numpy as np
import matplotlib.pyplot as plt

class StatisticalFoundations:
    """統計學理論基礎"""
    
    @staticmethod
    def central_limit_theorem_demo():
        """中央極限定理演示：為什麼 N≥3 是最低要求"""
        print("📊 中央極限定理與最少評審數量")
        print("=" * 60)
        
        print("理論基礎：")
        print("• 當 N≥30 時，中央極限定理強力生效")
        print("• 當 N≥3 時，開始顯現正態分布趨勢")
        print("• 當 N=1-2 時，無法進行有效的統計推論")
        
        # 模擬不同 N 值下的估計精度
        true_score = 85.0
        individual_variance = 100.0  # 個人評分方差
        
        print("\nN 值對估計精度的影響：")
        print("N 值 | 標準誤差 | 95%信賴區間 | 統計效力")
        print("-" * 50)
        
        for n in range(1, 11):
            standard_error = np.sqrt(individual_variance / n)
            confidence_interval = 1.96 * standard_error  # 95% CI
            statistical_power = "很低" if n < 3 else "低" if n < 5 else "中等" if n < 7 else "高"
            
            print(f" {n:2d}  |   {standard_error:6.2f}   |   ±{confidence_interval:5.2f}    | {statistical_power}")
    
    @staticmethod
    def variance_reduction_analysis():
        """方差縮減分析：多評審者的統計優勢"""
        print("\n📉 方差縮減效應分析")
        print("=" * 60)
        
        print("統計學原理：")
        print("• 獨立評分的平均值方差：σ²/N")
        print("• 標準誤差：σ/√N")
        print("• 方差縮減比例：1/N")
        
        # 計算不同 N 值的方差縮減
        base_variance = 100.0
        print("\nN 值的方差縮減效果：")
        print("N 值 | 方差縮減 | 精度提升 | 邊際效益")
        print("-" * 45)
        
        previous_variance = base_variance
        for n in range(1, 11):
            variance = base_variance / n
            precision_improvement = np.sqrt(base_variance / variance)
            marginal_benefit = (previous_variance - variance) / base_variance * 100
            previous_variance = variance
            
            print(f" {n:2d}  |   {variance:6.1f}   |   {precision_improvement:4.1f}x   |   {marginal_benefit:5.1f}%")
    
    @staticmethod
    def confidence_interval_analysis():
        """信賴區間分析：品質要求與 N 值的關係"""
        print("\n🎯 信賴區間與品質要求")
        print("=" * 60)
        
        print("品質要求對應的統計標準：")
        print("• 基本品質：80% 信賴區間 → N≥2")
        print("• 標準品質：90% 信賴區間 → N≥3")
        print("• 高品質：95% 信賴區間 → N≥5")
        print("• 關鍵品質：99% 信賴區間 → N≥7")
        
        # 計算不同信賴水準所需的最小 N
        confidence_levels = [0.80, 0.90, 0.95, 0.99]
        z_scores = [1.28, 1.645, 1.96, 2.576]
        
        print("\n品質等級與最小 N 值要求：")
        print("品質等級  | 信賴水準 | Z分數 | 建議最小N | 實務最小N")
        print("-" * 55)
        
        for i, (conf, z) in enumerate(zip(confidence_levels, z_scores)):
            quality_levels = ["基本", "標準", "高", "關鍵"]
            theoretical_n = max(2, int(np.ceil((z / 1.0) ** 2)))  # 假設容許誤差為1
            practical_n = [2, 3, 5, 7][i]  # 實務建議值
            
            print(f"{quality_levels[i]:8} |   {conf:.0%}   | {z:5.3f} |     {theoretical_n:2d}     |     {practical_n:2d}")

class PracticalConsiderations:
    """實務考量因素"""
    
    @staticmethod
    def workload_analysis():
        """工作負擔分析：學生能力與動機考量"""
        print("\n⚖️ 工作負擔與學習效果平衡")
        print("=" * 60)
        
        print("教育心理學考量：")
        print("• 認知負荷理論：過多評審降低品質")
        print("• 動機理論：適度負擔維持參與度")
        print("• 學習效果：評審他人作品提升自身能力")
        
        # 分析不同 N 值的工作負擔
        print("\nN 值對學生工作負擔的影響：")
        print("N 值 | 時間成本 | 認知負擔 | 參與動機 | 學習效果")
        print("-" * 55)
        
        workload_data = [
            (1, "很低", "很低", "很高", "很低"),
            (2, "低", "低", "高", "低"),
            (3, "中等", "中等", "高", "中等"),
            (4, "中高", "中等", "中等", "高"),
            (5, "高", "高", "中等", "高"),
            (6, "很高", "高", "低", "中等"),
            (8, "過高", "很高", "很低", "低"),
        ]
        
        for n, time, cognitive, motivation, learning in workload_data:
            print(f" {n:2d}  |   {time:4s}   |   {cognitive:4s}   |   {motivation:4s}   |   {learning:4s}")
    
    @staticmethod
    def assignment_complexity_analysis():
        """作業複雜度分析：不同類型作業的評審需求"""
        print("\n📝 作業類型與評審複雜度")
        print("=" * 60)
        
        print("作業類型影響因素：")
        print("• 評分標準明確性")
        print("• 主觀判斷成分")
        print("• 評審所需專業知識")
        print("• 評分一致性難度")
        
        assignment_data = [
            ("選擇題作業", "很高", "很低", "很低", "很高", 2),
            ("計算題作業", "高", "低", "低", "高", 3),
            ("程式設計作業", "中等", "中等", "中等", "中等", 3),
            ("論文報告", "低", "高", "高", "低", 5),
            ("創意專案", "很低", "很高", "高", "很低", 6),
            ("藝術作品", "很低", "很高", "中等", "很低", 6),
        ]
        
        print("\n作業類型對 N 值需求的影響：")
        print("作業類型      | 標準明確性 | 主觀成分 | 專業需求 | 一致性 | 建議N")
        print("-" * 70)
        
        for assignment, clarity, subjectivity, expertise, consistency, n in assignment_data:
            print(f"{assignment:12} |   {clarity:6s}   |  {subjectivity:4s}  |  {expertise:4s}  | {consistency:4s} |  {n:2d}")
    
    @staticmethod
    def class_size_effects():
        """班級規模效應：社會動力學考量"""
        print("\n👥 班級規模的社會動力學效應")
        print("=" * 60)
        
        print("班級規模影響因素：")
        print("• 同儕壓力與社會期望")
        print("• 匿名性程度")
        print("• 評分者多樣性")
        print("• 社會懈怠效應")
        
        size_effects = [
            ("< 10人", "小班制", "高同儕壓力", "低匿名性", "低多樣性", "低懈怠", "降低N"),
            ("10-30人", "標準班制", "中等壓力", "中等匿名性", "中等多樣性", "中等懈怠", "標準N"),
            ("30-50人", "大班制", "低壓力", "高匿名性", "高多樣性", "中等懈怠", "略增N"),
            ("50+人", "超大班制", "很低壓力", "很高匿名性", "很高多樣性", "高懈怠", "顯著增N"),
        ]
        
        print("\n班級規模對 N 值調整的建議：")
        print("班級規模    | 類型      | 同儕壓力   | 匿名性     | 多樣性     | 懈怠程度 | N值調整")
        print("-" * 85)
        
        for size, type_name, pressure, anonymity, diversity, laziness, adjustment in size_effects:
            print(f"{size:10} | {type_name:8} | {pressure:8} | {anonymity:8} | {diversity:8} | {laziness:6} | {adjustment}")

class NOptimizationTheory:
    """N 值優化理論"""
    
    @staticmethod
    def mathematical_foundation():
        """數學基礎：最佳 N 值的理論計算"""
        print("\n🔢 N 值優化的數學基礎")
        print("=" * 60)
        
        print("目標函數：最小化總成本 = 統計成本 + 工作負擔成本")
        print("Total_Cost(N) = Statistical_Cost(N) + Workload_Cost(N)")
        print()
        print("其中：")
        print("• Statistical_Cost(N) = k₁ × σ²/N  (統計誤差成本)")
        print("• Workload_Cost(N) = k₂ × N        (工作負擔成本)")
        print("• k₁, k₂ 為權重係數")
        
        # 計算最佳 N 值
        k1 = 100  # 統計誤差權重
        k2 = 10   # 工作負擔權重
        variance = 100
        
        print(f"\n範例計算 (k₁={k1}, k₂={k2}, σ²={variance})：")
        print("N 值 | 統計成本 | 工作成本 | 總成本 | 邊際成本變化")
        print("-" * 60)
        
        previous_total = float('inf')
        optimal_n = 1
        min_cost = float('inf')
        
        for n in range(1, 11):
            stat_cost = k1 * variance / n
            work_cost = k2 * n
            total_cost = stat_cost + work_cost
            marginal_change = total_cost - previous_total
            
            if total_cost < min_cost:
                min_cost = total_cost
                optimal_n = n
            
            print(f" {n:2d}  |  {stat_cost:7.1f}  |  {work_cost:7.1f}  | {total_cost:7.1f} | {marginal_change:+8.1f}")
            previous_total = total_cost
        
        print(f"\n理論最佳 N 值：{optimal_n} (總成本：{min_cost:.1f})")
        
        # 解析解
        analytical_n = np.sqrt(k1 * variance / k2)
        print(f"解析解最佳 N：{analytical_n:.2f}")
    
    @staticmethod
    def adaptive_algorithm():
        """自適應演算法：動態 N 值調整"""
        print("\n🔄 自適應 N 值調整演算法")
        print("=" * 60)
        
        print("演算法原理：")
        print("1. 初始設定：基於作業類型設定基礎 N 值")
        print("2. 班級調整：根據班級規模調整係數")
        print("3. 品質調整：根據品質要求調整係數")
        print("4. 邊界約束：確保 N 在合理範圍內")
        
        print("\n調整公式：")
        print("N_optimal = ceil(N_base × size_factor × quality_factor)")
        print("N_final = max(2, min(N_optimal, class_size-1, 10))")
        
        # 示範計算
        test_cases = [
            ("homework", 25, "standard", 3, 1.0, 1.0),
            ("exam", 15, "high", 4, 0.8, 1.2),
            ("project", 40, "critical", 5, 1.2, 1.5),
            ("essay", 8, "standard", 6, 0.7, 1.0),
        ]
        
        print("\n實際計算範例：")
        print("作業類型  | 班級 | 品質要求 | 基礎N | 規模係數 | 品質係數 | 最佳N")
        print("-" * 70)
        
        for assignment, class_size, quality, base_n, size_factor, quality_factor in test_cases:
            optimal_n = int(np.ceil(base_n * size_factor * quality_factor))
            final_n = max(2, min(optimal_n, class_size - 1, 10))
            
            print(f"{assignment:8} | {class_size:2d}人 | {quality:8} |  {base_n:2d}  |   {size_factor:.1f}    |   {quality_factor:.1f}    |  {final_n:2d}")

def generate_recommendation_matrix():
    """生成 N 值建議矩陣"""
    print("\n📋 N 值建議矩陣")
    print("=" * 60)
    
    assignment_types = ["homework", "exam", "programming", "project", "essay"]
    class_sizes = [5, 15, 25, 40, 60]
    quality_levels = ["basic", "standard", "high", "critical"]
    
    print("建議 N 值矩陣 (作業類型 × 班級規模)：")
    print("(假設標準品質要求)")
    print()
    
    # 構建表格標題
    header = "作業類型\\班級規模  |"
    for size in class_sizes:
        header += f"  {size:2d}人"
    print(header)
    print("-" * len(header))
    
    base_n_values = {"homework": 3, "exam": 4, "programming": 3, "project": 5, "essay": 6}
    
    for assignment in assignment_types:
        row = f"{assignment:15s} |"
        base_n = base_n_values[assignment]
        
        for size in class_sizes:
            if size < 10:
                size_factor = 0.8
            elif size < 30:
                size_factor = 1.0
            elif size < 50:
                size_factor = 1.2
            else:
                size_factor = 1.4
            
            optimal_n = int(np.ceil(base_n * size_factor))
            final_n = max(2, min(optimal_n, size - 1, 10))
            row += f"   {final_n:2d}"
        print(row)

def main():
    """主函數：展示所有理論依據"""
    print("🎓 學生互評系統最佳 N 值計算的理論依據")
    print("=" * 80)
    print("Statistical and Practical Foundations for Optimal N Selection")
    print("in Peer Assessment Systems")
    print()
    
    # 統計學基礎
    StatisticalFoundations.central_limit_theorem_demo()
    StatisticalFoundations.variance_reduction_analysis()
    StatisticalFoundations.confidence_interval_analysis()
    
    # 實務考量
    PracticalConsiderations.workload_analysis()
    PracticalConsiderations.assignment_complexity_analysis()
    PracticalConsiderations.class_size_effects()
    
    # 優化理論
    NOptimizationTheory.mathematical_foundation()
    NOptimizationTheory.adaptive_algorithm()
    
    # 建議矩陣
    generate_recommendation_matrix()
    
    print("\n" + "=" * 80)
    print("📚 理論依據總結：")
    print("1. 統計學基礎：中央極限定理、方差縮減、信賴區間")
    print("2. 教育心理學：認知負荷理論、動機理論、學習效果")
    print("3. 社會動力學：同儕壓力、匿名性、社會懈怠效應")
    print("4. 最佳化理論：成本效益分析、多目標優化")
    print("5. 實務約束：時間限制、能力限制、參與度維持")
    
    print("\n💡 關鍵原則：")
    print("• 統計可靠性：N≥3 保證基本統計意義")
    print("• 實務可行性：N≤8 避免過度工作負擔")
    print("• 動態調整：根據具體情況靈活調整")
    print("• 持續監控：評估效果並優化參數")

if __name__ == "__main__":
    main()
