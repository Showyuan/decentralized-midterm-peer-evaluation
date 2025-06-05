#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同儕評分系統 - 統一主控制器
整合完整工作流程管理與命令列介面，提供完整的同儕評分處理流程
"""

import os
import sys
import subprocess
import shutil
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from config_unified import PeerEvaluationConfig
from data_processor import DataProcessor
from assignment_engine import AssignmentEngine
from form_generator import FormGenerator


class PeerEvaluationSystem:
    """統一的同儕評分系統管理器"""
    
    def __init__(self, preset_name: Optional[str] = None):
        """
        初始化系統管理器
        
        Args:
            preset_name: 配置預設名稱
        """
        self.config = PeerEvaluationConfig()
        self.preset_name = preset_name
        
        # 確保輸出目錄存在
        self.config.create_output_dirs(preset_name)
        
        print("同儕評分系統 - 統一主控制器")
        print("=" * 60)
        print(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if preset_name:
            print(f"使用配置: {preset_name}")
        print("=" * 60)
    
    # ==================== 核心流程方法 ====================
    
    # ==================== 單步驟執行方法 ====================
    
    def process_data_only(self, csv_file: str = None) -> str:
        """
        只處理CSV數據
        
        Args:
            csv_file: CSV文件路徑
            
        Returns:
            處理後的JSON文件路徑
        """
        print("處理期中考試數據...")
        processor = DataProcessor(self.preset_name)
        
        if not processor.load_data(csv_file):
            raise Exception("數據載入失敗")
        
        processor.parse_questions()
        processor.parse_students()
        analysis = processor.analyze_submission_patterns()
        
        return processor.export_to_json(analysis=analysis)
    
    def generate_assignments_only(self, json_file: str = None, output_dir: str = None) -> str:
        """
        只生成同儕分派
        
        Args:
            json_file: JSON數據文件路徑
            output_dir: 輸出目錄路徑
            
        Returns:
            分派結果文件路徑
        """
        print("生成同儕評分分派...")
        engine = AssignmentEngine(self.preset_name)
        
        if not engine.load_data(json_file):
            raise Exception("JSON數據載入失敗")
        
        if not engine.validate_assignment_feasibility():
            raise Exception("分派不可行")
        
        assignments = engine.generate_assignments()
        return engine.export_assignments(assignments, output_dir)
    
    def generate_forms_only(self, assignment_file: str, output_dir: str = None) -> List[str]:
        """
        只生成評分表單
        
        Args:
            assignment_file: 分派結果文件路徑
            output_dir: 輸出目錄路徑
            
        Returns:
            表單文件路徑列表
        """
        print("生成評分表單...")
        generator = FormGenerator(self.preset_name)
        
        if not generator.load_assignment_data(assignment_file):
            raise Exception("分派數據載入失敗")
        
        if not generator.load_original_data():
            raise Exception("原始數據載入失敗")
        
        return generator.generate_all_forms(output_dir)
    
    # ==================== 工作流程方法（subprocess調用版本）====================
    
    def run_data_processing(self):
        """運行數據處理（從CSV開始）"""
        print("\n步驟 1: 處理期中考試CSV數據...")
        print("-" * 40)
        
        try:
            # 檢查統一輸出目錄中是否已有處理後的JSON
            unified_output_dir = self.config.get_unified_output_path("csv_analysis")
            json_path = os.path.join(unified_output_dir, "midterm_data.json")
            
            if os.path.exists(json_path):
                print(f"✅ 發現已有處理後的數據: midterm_data.json")
                
                user_input = input("是否重新處理CSV數據？(y/n): ").lower().strip()
                if user_input != 'y':
                    print("跳過數據處理步驟")
                    return True
            
            # 直接使用 DataProcessor 處理 CSV
            print("使用 DataProcessor 處理期中考試CSV數據...")
            
            # 獲取CSV文件路徑
            csv_path = self.config.get_file_path("docs_dir", "Midterm Survey Student Analysis Report.csv")
            if not os.path.exists(csv_path):
                print(f"CSV文件不存在: {csv_path}")
                return False
            
            # 創建數據處理器
            processor = DataProcessor(self.preset_name)
            
            # 載入CSV數據
            print(f"載入CSV文件: {csv_path}")
            raw_data = processor.load_data(csv_path)
            if raw_data is None:
                print("CSV數據載入失敗")
                return False
            
            # 解析題目
            print("解析考試題目...")
            questions = processor.parse_questions()
            if not questions:
                print("題目解析失敗")
                return False
            
            # 解析學生數據
            print("解析學生數據...")
            students = processor.parse_students()
            if not students:
                print("學生數據解析失敗")
                return False
            
            # 分析提交模式
            print("分析提交模式...")
            analysis = processor.analyze_submission_patterns()
            
            # 直接導出到統一輸出目錄
            print("導出處理結果到統一目錄...")
            # unified_output_dir 已經是 workflow_results/1_csv_analysis
            os.makedirs(unified_output_dir, exist_ok=True)
            json_file = processor.export_to_json(unified_output_dir, analysis)
            
            if json_file:
                # 重新命名為統一格式
                final_path = os.path.join(unified_output_dir, "midterm_data.json")
                if json_file != final_path:
                    shutil.move(json_file, final_path)
                
                print(f"✅ CSV數據處理完成: {final_path}")
                
                # 輸出處理摘要
                print(f"處理摘要:")
                print(f"   - 學生數量: {len(students)}")
                print(f"   - 題目數量: {len(questions)}")
                print(f"   - 輸出文件: midterm_data.json")
                
                return True
            else:
                print("JSON數據導出失敗")
                return False
                
        except Exception as e:
            print(f"數據處理執行錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_assignment_generation(self):
        """運行同儕分派生成"""
        print("\n步驟 2: 生成同儕評分分派...")
        print("-" * 40)
        
        try:
            # 檢查統一輸出目錄中是否已有分派文件
            unified_output_dir = self.config.get_unified_output_path("form_generation")
            assignment_path = os.path.join(unified_output_dir, "peer_assignments.json")
            
            if os.path.exists(assignment_path):
                print(f"✅ 發現已有分派文件: peer_assignments.json")
                
                user_input = input("是否重新生成分派？(y/n): ").lower().strip()
                if user_input != 'y':                print("跳過分派生成步驟")
                return True
            
            # 使用直接API調用方式生成分派
            print("生成同儕分派...")
            
            # 獲取處理過的數據文件
            data_path = os.path.join(
                self.config.get_unified_output_path("csv_analysis"),
                "midterm_data.json"
            )
            
            if not os.path.exists(data_path):
                print(f"找不到處理過的數據文件: {data_path}")
                print("   請先執行數據處理步驟")
                return False
            
            # 生成分派
            assignment_file = self.generate_assignments_only(data_path, unified_output_dir)
            
            # 重新命名為統一格式
            if assignment_file != assignment_path:
                shutil.move(assignment_file, assignment_path)
            
            print(f"✅ 同儕分派生成完成: {assignment_path}")
            return True
                
        except Exception as e:
            print(f"分派生成執行錯誤: {e}")
            return False
    
    def run_form_generation(self):
        """運行表單生成"""
        print("\n步驟 3: 生成評分表單...")
        print("-" * 40)
        
        try:
            # 檢查統一輸出目錄中是否已有生成的表單
            unified_output_dir = self.config.get_unified_output_path("form_generation")
            forms_unified_dir = os.path.join(unified_output_dir, "evaluation_forms")
            
            if os.path.exists(forms_unified_dir):
                form_files = [f for f in os.listdir(forms_unified_dir) if f.endswith('.html')]
                if form_files:
                    print(f"✅ 發現已有 {len(form_files)} 個評分表單")
                    
                    user_input = input("是否重新生成表單？(y/n): ").lower().strip()
                    if user_input != 'y':                    print("跳過表單生成步驟")
                    return True
            
            # 創建統一表單輸出目錄
            os.makedirs(forms_unified_dir, exist_ok=True)
            
            # 使用直接API調用方式生成表單
            print("生成評分表單...")
            
            # 獲取分派文件
            assignment_path = os.path.join(unified_output_dir, "peer_assignments.json")
            
            if not os.path.exists(assignment_path):
                print(f"找不到分派文件: {assignment_path}")
                print("   請先執行分派生成步驟")
                return False
            
            # 生成表單
            form_files = self.generate_forms_only(assignment_path, forms_unified_dir)
            
            print(f"✅ 評分表單生成完成")
            print(f"已生成 {len(form_files)} 個表單到統一輸出資料夾")
            return True
                
        except Exception as e:
            print(f"表單生成執行錯誤: {e}")
            return False
    
    def run_form_simulator(self):
        """運行表單模擬器"""
        print("\n步驟 4: 執行表單填寫模擬...")
        print("-" * 40)
        
        try:
            # 獲取統一輸出目錄
            unified_step_dir = self.config.get_unified_output_path("form_simulation")
            filled_unified_dir = os.path.join(unified_step_dir, "filled_forms")
            
            # 檢查統一輸出目錄是否已有填寫的表單
            if os.path.exists(filled_unified_dir):
                filled_forms = [f for f in os.listdir(filled_unified_dir) if f.endswith('.html')]
                if filled_forms:
                    print(f"✅ 統一輸出目錄發現已有 {len(filled_forms)} 個填寫完成的表單")
                    
                    user_input = input("是否重新執行表單填寫？(y/n): ").lower().strip()
                    if user_input != 'y':                    print("跳過表單填寫步驟")
                    return True
            
            # 確保統一輸出目錄存在
            os.makedirs(filled_unified_dir, exist_ok=True)
            
            # 獲取評分表單目錄
            forms_source_dir = os.path.join(
                self.config.get_unified_output_path("form_generation"),
                "evaluation_forms"
            )
            
            if not os.path.exists(forms_source_dir):
                print(f"找不到評分表單目錄: {forms_source_dir}")
                print("   請先執行表單生成步驟")
                return False
            
            # 執行表單模擬器，並指定表單源目錄和輸出目錄參數
            result = subprocess.run([
                sys.executable, "form_simulator.py",
                "--forms-dir", forms_source_dir,
                "--output-dir", filled_unified_dir
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print("✅ 表單填寫完成")
                # 統計填寫完成的表單
                filled_forms = [f for f in os.listdir(filled_unified_dir) if f.endswith('.html')]
                print(f"已生成 {len(filled_forms)} 個填寫表單到統一輸出資料夾")
                return True
            else:
                print(f"表單填寫失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"表單模擬器執行錯誤: {e}")
            return False
    
    def run_result_collector(self):
        """運行結果收集器"""
        print("\n步驟 5: 收集評分結果...")
        print("-" * 40)
        
        try:
            # 獲取統一輸出目錄
            unified_step_dir = self.config.get_unified_output_path("result_evaluation")
            
            # 檢查統一輸出目錄是否已有收集的結果
            results_json_path = os.path.join(unified_step_dir, "evaluation_results.json")
            results_excel_path = os.path.join(unified_step_dir, "evaluation_results.xlsx")
            
            if os.path.exists(results_json_path):
                print("✅ 統一輸出目錄發現已有收集的評分結果")
                
                user_input = input("是否重新收集結果？(y/n): ").lower().strip()
                if user_input != 'y':                print("跳過結果收集步驟")
                return True
            
            # 確保統一輸出目錄存在
            os.makedirs(unified_step_dir, exist_ok=True)
            
            # 獲取填寫完成的表單目錄
            filled_forms_dir = os.path.join(
                self.config.get_unified_output_path("form_simulation"), 
                "filled_forms"
            )
            
            if not os.path.exists(filled_forms_dir):
                print(f"找不到填寫完成的表單目錄: {filled_forms_dir}")
                return False
            
            # 執行結果收集器，使用正確的參數格式
            result = subprocess.run([
                sys.executable, "result_collector_simple.py",
                "--forms-dir", filled_forms_dir,
                "--output-excel", results_excel_path,
                "--output-json", results_json_path
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print("✅ 結果收集完成")
                
                # 檢查並報告生成的檔案
                if os.path.exists(results_json_path):
                    print(f"已生成評分結果: evaluation_results.json")
                
                if os.path.exists(results_excel_path):
                    print(f"已生成Excel報表: evaluation_results.xlsx")
                
                return True
            else:
                print(f"結果收集失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"結果收集器執行錯誤: {e}")
            return False
    
    def run_vancouver_processor(self):
        """運行Vancouver算法處理器"""
        print("\n步驟 6: 執行Vancouver算法...")
        print("-" * 40)
        
        try:
            # 獲取統一輸出目錄
            unified_step_dir = self.config.get_unified_output_path("vancouver_processing")
            
            # 檢查統一輸出目錄是否已有Vancouver結果
            vancouver_files = []
            if os.path.exists(unified_step_dir):
                vancouver_files = [f for f in os.listdir(unified_step_dir) 
                                  if f.startswith("vancouver_results_") and f.endswith(".json")]
            
            if vancouver_files:
                latest_file = sorted(vancouver_files)[-1]
                print(f"✅ 統一輸出目錄發現已有Vancouver結果: {latest_file}")
                
                user_input = input("是否重新執行Vancouver算法？(y/n): ").lower().strip()
                if user_input != 'y':                print("跳過Vancouver算法步驟")
                return True
            
            # 確保統一輸出目錄存在
            os.makedirs(unified_step_dir, exist_ok=True)
            
            # 獲取評分結果文件路徑
            evaluation_results_path = os.path.join(
                self.config.get_unified_output_path("result_evaluation"),
                "evaluation_results.json"
            )
            
            if not os.path.exists(evaluation_results_path):
                print(f"找不到評分結果文件: {evaluation_results_path}")
                print("   請先執行結果收集步驟")
                return False
            
            # 執行Vancouver處理器，使用正確的參數格式
            result = subprocess.run([
                sys.executable, "vancouver_processor.py",
                "--input-file", evaluation_results_path,
                "--output-dir", unified_step_dir
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print("✅ Vancouver算法執行完成")
                
                # 檢查並報告生成的檔案
                vancouver_files = [f for f in os.listdir(unified_step_dir) 
                                  if f.endswith(".json")]
                if vancouver_files:
                    print(f"已生成 {len(vancouver_files)} 個Vancouver結果檔案")
                
                return True
            else:
                print(f"Vancouver算法執行失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Vancouver處理器執行錯誤: {e}")
            return False
    
    def run_verification_report(self):
        """運行驗證報告生成器"""
        print("\n步驟 7: 生成驗證報告...")
        print("-" * 40)
        
        try:
            # 執行驗證報告生成器
            result = subprocess.run([
                sys.executable, "verification_report.py"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print("✅ 驗證報告生成完成")
                return True
            else:
                print(f"驗證報告生成失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"驗證報告生成器執行錯誤: {e}")
            return False
    
    # ==================== 完整工作流程方法 ====================
    
    def run_complete_workflow(self, skip_confirmation=False):
        """運行完整工作流程"""
        print("\n準備執行完整同儕評分工作流程...")
        
        if not skip_confirmation:
            print("\n工作流程包含以下步驟:")
            print("1. CSV數據分析處理")
            print("2. 同儕分派生成")
            print("3. 評分表單生成")
            print("4. 表單填寫模擬")
            print("5. 評分結果收集")
            print("6. Vancouver算法處理")
            print("7. 驗證報告生成")
            
            user_input = input("\n是否繼續執行完整工作流程？(y/n): ").lower().strip()
            if user_input != 'y':
                print("工作流程已取消")
                return False
        
        # 執行各個步驟
        steps = [
            ("CSV數據分析處理", self.run_data_processing),
            ("同儕分派生成", self.run_assignment_generation),
            ("評分表單生成", self.run_form_generation),
            ("表單填寫模擬", self.run_form_simulator),
            ("評分結果收集", self.run_result_collector),
            ("Vancouver算法處理", self.run_vancouver_processor),
            ("驗證報告生成", self.run_verification_report)
        ]
        
        success_count = 0
        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
                else:
                    print(f"{step_name} 失敗，工作流程中斷")
                    break
            except KeyboardInterrupt:
                print(f"\n用戶中斷了工作流程")
                break
            except Exception as e:
                print(f"{step_name} 發生未預期錯誤: {e}")
                break
        
        # 總結結果
        print("\n" + "=" * 60)
        print("工作流程執行總結")
        print("=" * 60)
        print(f"成功完成: {success_count}/{len(steps)} 個步驟")
        
        if success_count == len(steps):
            print("完整工作流程執行成功！")
            self.show_results_summary()
            return True
        else:
            print("部分步驟執行失敗，請檢查錯誤信息")
            return False
    
    # ==================== 顯示和狀態方法 ====================
    
    def show_results_summary(self):
        """顯示結果總結"""
        print("\n生成的文件總結:")
        print("-" * 40)
        
        try:
            # 處理的數據
            data_path = os.path.join(
                self.config.get_unified_output_path("csv_analysis"),
                "midterm_data.json"
            )
            if os.path.exists(data_path):
                print(f"處理的數據: midterm_data.json")
            
            # 分派結果
            assignment_path = os.path.join(
                self.config.get_unified_output_path("form_generation"),
                "peer_assignments.json"
            )
            if os.path.exists(assignment_path):
                print(f"分派結果: peer_assignments.json")
            
            # 評分表單
            forms_dir = os.path.join(
                self.config.get_unified_output_path("form_generation"),
                "evaluation_forms"
            )
            if os.path.exists(forms_dir):
                form_files = [f for f in os.listdir(forms_dir) if f.endswith('.html')]
                print(f"評分表單: {len(form_files)} 個")
            
            # 填寫的表單
            filled_dir = os.path.join(
                self.config.get_unified_output_path("form_simulation"),
                "filled_forms"
            )
            if os.path.exists(filled_dir):
                filled_forms = [f for f in os.listdir(filled_dir) if f.endswith('.html')]
                print(f"填寫完成的表單: {len(filled_forms)} 個")
            
            # 收集的結果
            results_path = os.path.join(
                self.config.get_unified_output_path("result_evaluation"),
                "evaluation_results.json"
            )
            if os.path.exists(results_path):
                print(f"評分結果文件: evaluation_results.json")
            
            # Vancouver結果
            vancouver_dir = self.config.get_unified_output_path("vancouver_processing")
            if os.path.exists(vancouver_dir):
                vancouver_files = [f for f in os.listdir(vancouver_dir) 
                                  if f.startswith("vancouver_results_") and f.endswith(".json")]
                if vancouver_files:
                    latest_file = sorted(vancouver_files)[-1]
                    print(f"Vancouver結果: {latest_file}")
            
                # 驗證報告
                verification_file = os.path.join(vancouver_dir, "vancouver_verification_report.xlsx")
                if os.path.exists(verification_file):
                    print(f"驗證報告: vancouver_verification_report.xlsx")
            
        except Exception as e:
            print(f"結果總結生成錯誤: {e}")
    
    def show_system_status(self):
        """顯示系統狀態和配置"""
        print("系統狀態和配置")
        print("=" * 60)
        
        # 顯示配置信息
        if self.preset_name:
            print(f"當前配置: {self.preset_name}")
        else:
            print("當前配置: 預設")
        
        print(f"檔案路徑:")
        config = self.config.get_config(self.preset_name)
        for key, path in config['paths'].items():
            if key.endswith('_dir') or key in ['input_csv', 'input_json']:
                full_path = self.config.get_path(key, self.preset_name) if key in config['paths'] else path
                exists = "✅" if os.path.exists(full_path) else "X"
                print(f"  {key}: {exists} {full_path}")
        
        print(f"\n同儕分派設定:")
        assignment_config = config['peer_assignment']
        print(f"  每人評分: {assignment_config['assignments_per_student']} 份")
        print(f"  分派模式: {assignment_config['balance_mode']}")
        print(f"  允許自評: {assignment_config['allow_self_evaluation']}")
        print(f"  隨機種子: {assignment_config['random_seed']}")
        
        print(f"\n評分表單設定:")
        form_config = config['evaluation_form']
        print(f"  評分範圍: {form_config['scoring_scale']['min_score']}-{form_config['scoring_scale']['max_score']}")
        print(f"  需要評語: {form_config['require_comments']}")
        print(f"  顯示統計: {form_config['include_statistics']}")
    



def main():
    """主程序"""
    parser = argparse.ArgumentParser(
        description='同儕評分系統統一主控制器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 執行完整流程（推薦）
  python main.py --workflow
  
  # 使用特定配置執行完整流程
  python main.py --workflow --preset standard
  
  # 執行完整工作流程（包含模擬和Vancouver算法）
  python main.py --workflow
  
  # 只處理數據
  python main.py --data-only --csv docs/exam.csv
  
  # 只生成分派
  python main.py --assign-only --json output/data.json
  
  # 只生成表單
  python main.py --forms-only --assignment output/assignments.json
  
  # 顯示系統狀態
  python main.py --status
  
  # 列出可用配置
  python main.py --list-presets
        """
    )
    
    # 預設配置選項
    parser.add_argument('--preset', '-p', type=str, 
                       choices=['light', 'standard', 'comprehensive', 'debug'],
                       help='使用預設配置')
    
    # 執行模式選項
    execution_group = parser.add_mutually_exclusive_group(required=True)
    execution_group.add_argument('--workflow', action='store_true',
                                help='執行完整工作流程（包含模擬和算法）')
    execution_group.add_argument('--data-only', action='store_true',
                                help='只處理CSV數據')
    execution_group.add_argument('--assign-only', action='store_true',
                                help='只生成同儕分派')
    execution_group.add_argument('--forms-only', action='store_true',
                                help='只生成評分表單')
    execution_group.add_argument('--status', action='store_true',
                                help='顯示系統狀態和配置')
    execution_group.add_argument('--list-presets', action='store_true',
                                help='列出可用的預設配置')
    
    # 文件路徑選項
    parser.add_argument('--csv', type=str, help='指定CSV文件路徑')
    parser.add_argument('--json', type=str, help='指定JSON數據文件路徑')
    parser.add_argument('--assignment', type=str, help='指定分派結果文件路徑')
    parser.add_argument('--output', '-o', type=str, help='指定輸出目錄')
    
    args = parser.parse_args()
    
    # 處理列出預設配置
    if args.list_presets:
        print("可用的預設配置:")
        print("- standard: 標準配置")
        return
    
    # 創建系統實例
    system = PeerEvaluationSystem(args.preset)
    
    try:
        if args.status:
            system.show_system_status()
            
        elif args.workflow:
            # 執行完整工作流程
            success = system.run_complete_workflow(skip_confirmation=False)
            sys.exit(0 if success else 1)
            
        elif args.data_only:
            json_file = system.process_data_only(args.csv)
            print(f"\n輸出文件: {json_file}")
            
        elif args.assign_only:
            assignment_file = system.generate_assignments_only(args.json, args.output)
            print(f"\n輸出文件: {assignment_file}")
            
        elif args.forms_only:
            if not args.assignment:
                print("錯誤: --forms-only 需要指定 --assignment 參數")
                return
            form_files = system.generate_forms_only(args.assignment, args.output)
            print(f"\n輸出文件: {len(form_files)} 個表單")
            
    except Exception as e:
        print(f"\n錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
