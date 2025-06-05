#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同儕評分系統統一配置文件
支援所有相關功能模組的配置管理
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

class PeerEvaluationConfig:
    """同儕評分系統配置管理器"""
    
    def __init__(self):
        """初始化配置"""
        # 基礎路徑配置
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.base_dir)
        
        # 預設配置
        self._config = {
            # === 檔案路徑配置 ===
            "paths": {
                "input_csv": "workflow_results/1_csv_analysis/Midterm Survey Student Analysis Report.csv",
                "input_json": "workflow_results/1_csv_analysis/midterm_data.json",
                "output_dir": "workflow_results",
                "docs_dir": "docs",
                # 統一輸出資料夾下的子目錄
                "evaluation_forms_dir": "workflow_results/2_form_generation/evaluation_forms",
                "filled_forms_dir": "workflow_results/3_form_simulation/filled_forms",
                "collected_results_dir": "workflow_results/4_result_evaluation/collected_results",
                "vancouver_results_dir": "workflow_results/5_vancouver_processing/vancouver_results",
                "logs_dir": "workflow_results/logs",
                "verification_reports_dir": "workflow_results/5_vancouver_processing/verification_reports",
                # 檔案名稱配置
                "evaluation_results_file": "evaluation_results.json",
                "vancouver_results_file": "vancouver_results.json",
                # 統一輸出資料夾
                "unified_output_dir": "workflow_results",
                "step_output_prefix": {
                    "csv_analysis": "1_csv_analysis",
                    "form_generation": "2_form_generation",
                    "form_simulation": "3_form_simulation", 
                    "result_evaluation": "4_result_evaluation",
                    "vancouver_processing": "5_vancouver_processing"
                }
            },
            
            # === 數據處理配置 ===
            "data_processing": {
                "encoding": "utf-8-sig",
                "max_score_per_question": 20,
                "include_analysis": True,
                "export_format": "json"
            },
            
            # === 同儕評分分派配置 ===
            "peer_assignment": {
                "assignments_per_student": 4,
                "random_seed": 12345,
                "allow_self_evaluation": False,
                "balance_mode": "perfect",
                "min_evaluators_per_paper": None,
                "max_evaluators_per_paper": None
            },
            
            # === 評分表單配置 ===
            "evaluation_form": {
                "language": "zh-TW",
                "include_statistics": True,
                "show_word_count": True,
                "show_char_count": True,
                "scoring_scale": {
                    "min_score": 0,
                    "max_score": 20,
                    "step": 1
                },
                "require_comments": True,
                "comment_min_length": 10
            },
            
            # === 結果收集器配置 ===
            "result_collector": {
                "extract_comments": True,
                "calculate_statistics": True,
                "export_formats": ["json", "xlsx"],
                "include_metadata": True,
                "validate_scores": True,
                "score_range_check": True
            },
            
            # === Vancouver算法配置 ===
            "vancouver_algorithm": {
                "R_max": 1.0,
                "v_G": 8.0,
                "alpha": 0.1,
                "N": 4,
                "n_iterations": 25,
                "scoring_method": "sum",
                "enable_protection": True,
                "reputation_threshold": 0.3
            },
            
            # === 輸出配置 ===
            "output": {
                "show_details": True,
                "timestamp_format": "%Y%m%d_%H%M%S",
                "file_prefix": {
                    "processed_data": "midterm_data",
                    "assignments": "peer_assignments",
                    "evaluation_form": "evaluation_form",
                    "filled_forms": "filled",
                    "collected_results": "evaluation_results",
                    "vancouver_results": "vancouver_results",
                    "vancouver_report": "vancouver_report",
                    "verification_report": "vancouver_verification_report",
                    "analysis_report": "analysis_report"
                },
                "include_metadata": True,
                "save_intermediate_results": True
            },
            
            # === 系統配置 ===
            "system": {
                "verbose": True,
                "debug": False,
                "log_level": "INFO",
                "backup_files": True,
                "create_dirs": True
            }
        }
        
        # 預設配置集
        self._presets = {
            "light": {
                "description": "輕量評分模式",
                "peer_assignment": {
                    "assignments_per_student": 3
                },
                "evaluation_form": {
                    "require_comments": False
                },
                "vancouver_algorithm": {
                    "n_iterations": 15
                }
            },
            "standard": {
                "description": "標準評分模式",
                "peer_assignment": {
                    "assignments_per_student": 4
                },
                "vancouver_algorithm": {
                    "n_iterations": 25
                }
            },
            "comprehensive": {
                "description": "全面評分模式",
                "peer_assignment": {
                    "assignments_per_student": 5
                },
                "evaluation_form": {
                    "comment_min_length": 50
                },
                "vancouver_algorithm": {
                    "n_iterations": 35,
                    "alpha": 0.15
                }
            },
            "debug": {
                "description": "除錯模式",
                "system": {
                    "verbose": True,
                    "debug": True,
                    "log_level": "DEBUG"
                },
                "vancouver_algorithm": {
                    "n_iterations": 10
                }
            }
        }
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """遞歸合併配置字典"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_config(self, preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取配置
        
        Args:
            preset_name: 預設配置名稱
            
        Returns:
            完整配置字典
        """
        if preset_name is None:
            return self._config.copy()
        
        if preset_name not in self._presets:
            raise ValueError(f"未知的預設配置: {preset_name}")
        
        preset_config = self._presets[preset_name].copy()
        preset_config.pop("description", None)
        
        return self._merge_configs(self._config, preset_config)
    
    def get_path(self, path_key: str, preset_name: Optional[str] = None, absolute: bool = True) -> str:
        """
        獲取路徑
        
        Args:
            path_key: 路徑鍵值
            preset_name: 預設配置名稱
            absolute: 是否返回絕對路徑
            
        Returns:
            路徑字符串
        """
        config = self.get_config(preset_name)
        
        if path_key in config["paths"]:
            path = config["paths"][path_key]
            if absolute and not os.path.isabs(path):
                return os.path.join(self.project_root, path)
            return path
        else:
            raise KeyError(f"路徑鍵 '{path_key}' 不存在")
    
    def get_directory_path(self, dir_key: str, preset_name: Optional[str] = None) -> str:
        """
        獲取目錄路徑
        
        Args:
            dir_key: 目錄鍵值
            preset_name: 預設配置名稱
            
        Returns:
            目錄絕對路徑
        """
        return self.get_path(dir_key, preset_name, absolute=True)
    
    def get_file_path(self, dir_key: str, filename: str, preset_name: Optional[str] = None) -> str:
        """
        獲取檔案路徑
        
        Args:
            dir_key: 目錄鍵值
            filename: 檔案名稱
            preset_name: 預設配置名稱
            
        Returns:
            檔案絕對路徑
        """
        dir_path = self.get_directory_path(dir_key, preset_name)
        return os.path.join(dir_path, filename)
    
    def get_unified_output_path(self, step_name: str, filename: str = None, preset_name: Optional[str] = None) -> str:
        """
        獲取統一輸出路徑
        
        Args:
            step_name: 步驟名稱 (csv_analysis, form_generation, form_simulation, result_evaluation, vancouver_processing)
            filename: 檔案名稱
            preset_name: 預設配置名稱
            
        Returns:
            統一輸出路徑
        """
        config = self.get_config(preset_name)
        unified_dir = self.get_directory_path("unified_output_dir", preset_name)
        
        # 處理使用舊名稱 "2_form_generation" 等情況
        # 先去除可能的數字前綴 (如 "2_form_generation" -> "form_generation")
        clean_step_name = step_name
        if step_name and step_name[0].isdigit() and "_" in step_name:
            clean_step_name = step_name.split("_", 1)[1]  # 取下劃線後的部分
            
        if step_name in config["paths"]["step_output_prefix"]:
            step_prefix = config["paths"]["step_output_prefix"][step_name]
            step_dir = os.path.join(unified_dir, step_prefix)
        elif clean_step_name in config["paths"]["step_output_prefix"]:
            step_prefix = config["paths"]["step_output_prefix"][clean_step_name]
            step_dir = os.path.join(unified_dir, step_prefix)
        else:
            # 嘗試直接使用步驟名稱作為目錄，方便擴展
            print(f"警告: 步驟名稱 '{step_name}' 未在配置中定義，將使用預設命名")
            step_dir = os.path.join(unified_dir, step_name)
        
        # 確保目錄存在
        os.makedirs(step_dir, exist_ok=True)
        
        if filename:
            return os.path.join(step_dir, filename)
        return step_dir
    
    def copy_to_unified_output(self, source_path: str, step_name: str, new_filename: str = None, preset_name: Optional[str] = None) -> str:
        """
        複製檔案到統一輸出資料夾
        
        Args:
            source_path: 來源檔案路徑
            step_name: 步驟名稱
            new_filename: 新檔案名稱（可選）
            preset_name: 預設配置名稱
            
        Returns:
            目標檔案路徑
        """
        import shutil
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"來源檔案不存在: {source_path}")
        
        # 決定目標檔案名稱
        if new_filename is None:
            new_filename = os.path.basename(source_path)
        
        # 獲取目標路徑
        target_path = self.get_unified_output_path(step_name, new_filename, preset_name)
        
        # 複製檔案
        shutil.copy2(source_path, target_path)
        
        return target_path
    
    def create_output_dirs(self, preset_name: Optional[str] = None):
        """創建輸出目錄"""
        config = self.get_config(preset_name)
        
        if config["system"]["create_dirs"]:
            dirs_to_create = [
                "output_dir",
                "filled_forms_dir", 
                # "logs_dir",
                "unified_output_dir"  # 新增統一輸出目錄
            ]
            
            for dir_key in dirs_to_create:
                if dir_key in config["paths"]:
                    dir_path = self.get_path(dir_key, preset_name, absolute=True)
                    os.makedirs(dir_path, exist_ok=True)
            
            # 創建統一輸出的子目錄
            for step_name in config["paths"]["step_output_prefix"]:
                step_dir = self.get_unified_output_path(step_name, preset_name=preset_name)
                # get_unified_output_path 已經會創建目錄，所以這裡不需要額外創建
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        self._config = self._merge_configs(self._config, updates)
    
    def add_preset(self, name: str, preset_config: Dict[str, Any]):
        """添加新的預設配置"""
        self._presets[name] = preset_config
    
    def list_presets(self) -> Dict[str, str]:
        """列出所有可用的預設配置"""
        return {name: preset.get("description", "無描述") 
                for name, preset in self._presets.items()}
    
    def print_config(self, preset_name: Optional[str] = None):
        """列印配置信息"""
        config = self.get_config(preset_name)
        print("\n=== 同儕評分系統配置 ===")
        
        if preset_name:
            print(f"預設配置: {preset_name}")
            print(f"描述: {self._presets[preset_name].get('description', '無描述')}")
        
        print(f"\n檔案路徑:")
        for key, path in config["paths"].items():
            abs_path = self.get_path(key, preset_name, absolute=True)
            print(f"  {key}: {abs_path}")
        
        print(f"\nVancouver算法參數:")
        for key, value in config["vancouver_algorithm"].items():
            print(f"  {key}: {value}")
        
        print(f"\n系統設定:")
        for key, value in config["system"].items():
            print(f"  {key}: {value}")

# 全局配置實例
_config_instance = PeerEvaluationConfig()

def get_config(preset_name: Optional[str] = None) -> Dict[str, Any]:
    """全局配置獲取函數"""
    return _config_instance.get_config(preset_name)

def get_path(path_key: str, preset_name: Optional[str] = None, absolute: bool = True) -> str:
    """全局路徑獲取函數"""
    return _config_instance.get_path(path_key, preset_name, absolute)

def get_full_path(path_key: str, filename: str = None, preset_name: Optional[str] = None) -> str:
    """全局完整路徑獲取函數"""
    return _config_instance.get_full_path(path_key, filename, preset_name)

def create_output_dirs(preset_name: Optional[str] = None):
    """全局目錄創建函數"""
    return _config_instance.create_output_dirs(preset_name)

def print_config(preset_name: Optional[str] = None):
    """全局配置打印函數"""
    return _config_instance.print_config(preset_name)

def list_presets() -> Dict[str, str]:
    """全局預設配置列表函數"""
    return _config_instance.list_presets()
