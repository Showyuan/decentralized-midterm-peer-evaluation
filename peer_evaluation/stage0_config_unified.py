#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同儕評分系統統一配置文件
僅包含 Web 流程實際使用的配置項
"""

import os
from typing import Dict, Any, Optional


class PeerEvaluationConfig:
    """同儕評分系統配置管理器"""
    
    def __init__(self):
        """初始化配置"""
        # 基礎路徑
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.base_dir)
        
        # 配置
        self._config = {
            # 路徑配置
            "paths": {
                # 輸入路徑
                "input_csv": "docs/Midterm Survey Student Analysis Report.csv",
                
                # 輸出目錄
                "output_base": "workflow_results",
                "stage1_output": "workflow_results/1_data_preparation",
                "stage2_assignment": "workflow_results/2_assignment",
                "stage3_tokens": "workflow_results/3_token_generation",
                "stage4_database": "workflow_results/4_database",
                "stage5_results": "workflow_results/5_evaluation_results",
                "stage6_vancouver": "workflow_results/6_vancouver_results",
                "stage7_reports": "workflow_results/7_final_reports",
            },
            
            # 檔名配置
            "filenames": {
                # Stage 1: 數據準備
                "processed_data": "midterm_data.json",
                "data_summary": "data_summary.txt",
                
                # Stage 2: 任務分配與 Token
                "assignments": "peer_assignments.json",
                "tokens": "evaluation_tokens_{timestamp}.json",
                "urls": "evaluation_urls_{timestamp}.json",
                "tokens_simple": "tokens_simple_{timestamp}.json",
                
                # Stage 4: 資料庫
                "database": "evaluation.db",
                
                # Stage 5: 結果收集
                "evaluation_results_json": "evaluation_results.json",
                "evaluation_results_xlsx": "evaluation_results.xlsx",
                "vancouver_input": "vancouver_input.json",
                
                # Stage 6: Vancouver 處理
                "vancouver_results_json": "vancouver_results_{timestamp}.json",
                "vancouver_results_xlsx": "vancouver_results_{timestamp}.xlsx",
                
                # Stage 7: 驗證報告
                "verification_report": "vancouver_verification_report.xlsx",
            },
            
            # 數據處理配置
            "data_processing": {
                "encoding": "utf-8-sig",
                "export_format": "json",
                "max_score_per_question": 20  # 每題最高分數
            },
            
            # 同儕評分分派配置
            "peer_assignment": {
                "assignments_per_student": 4,           # 每位學生評分 4 位同學
                "random_seed": 42,                       # 隨機種子（可重現）
                "allow_self_evaluation": False,          # 不允許自我評分
                "balance_mode": "perfect"                # 完美平衡模式
            },
            
            # Vancouver 演算法配置
            "vancouver_algorithm": {
                "R_max": 1.0,                           # 最大聲譽值
                "v_G": 8.0,                             # 聲譽閾值
                "alpha": 0.1,                           # 學習率
                "N": 4,                                 # 每個答案的評分者數量
                "n_iterations": 25,                     # 迭代次數
                "basic_precision": 0.0001               # 收斂精度
            },
            
            # 輸出配置
            "output": {
                "timestamp_format": "%Y%m%d_%H%M%S",
                "include_metadata": True
            },
            
            # 系統配置
            "system": {
                "verbose": True,
                "create_dirs": True
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """獲取配置"""
        return self._config.copy()
    
    def get(self, key: str, default=None) -> Any:
        """獲取配置項"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_path(self, path_key: str, filename_key: str = None, **kwargs) -> str:
        """
        獲取完整的檔案路徑
        
        Args:
            path_key: 路徑配置鍵 (如 'stage1_output')
            filename_key: 檔名配置鍵 (如 'processed_data')，可選
            **kwargs: 用於格式化的額外參數 (如 timestamp)
        
        Returns:
            完整的檔案路徑
        """
        # 獲取目錄路徑
        dir_path = self.get(f'paths.{path_key}')
        if dir_path is None:
            raise KeyError(f"Path key '{path_key}' not found in config")
        
        full_path = os.path.join(self.project_root, dir_path)
        
        # 如果提供了檔名鍵，組合完整路徑
        if filename_key:
            filename = self.get(f'filenames.{filename_key}')
            if filename is None:
                raise KeyError(f"Filename key '{filename_key}' not found in config")
            
            # 格式化檔名（如果包含 {timestamp} 等佔位符）
            if kwargs:
                filename = filename.format(**kwargs)
            
            full_path = os.path.join(full_path, filename)
        
        return full_path
    
    def get_input_csv_path(self) -> str:
        """獲取輸入 CSV 檔案路徑"""
        csv_path = self.get('paths.input_csv')
        return os.path.join(self.project_root, csv_path)
    
    def ensure_output_dir(self, path_key: str) -> str:
        """
        確保輸出目錄存在
        
        Args:
            path_key: 路徑配置鍵
        
        Returns:
            目錄的完整路徑
        """
        dir_path = self.get_path(path_key)
        if self.get('system.create_dirs'):
            os.makedirs(dir_path, exist_ok=True)
        return dir_path
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        self._config.update(updates)


# 全局配置實例
_config_instance = PeerEvaluationConfig()


def get_config() -> Dict[str, Any]:
    """全局配置獲取函數"""
    return _config_instance.get_config()


def get(key: str, default=None) -> Any:
    """全局配置項獲取函數"""
    return _config_instance.get(key, default)


if __name__ == "__main__":
    # 測試
    config = PeerEvaluationConfig()
    print("配置項測試:")
    print(f"  評分數量: {config.get('peer_assignment.assignments_per_student')}")
    print(f"  Vancouver R_max: {config.get('vancouver_algorithm.R_max')}")
    print(f"  輸出時間格式: {config.get('output.timestamp_format')}")
    
    print("\n路徑測試:")
    print(f"  輸入 CSV: {config.get_input_csv_path()}")
    print(f"  Stage1 輸出目錄: {config.get_path('stage1_output')}")
    print(f"  Stage1 資料檔: {config.get_path('stage1_output', 'processed_data')}")
    
    from datetime import datetime
    timestamp = datetime.now().strftime(config.get('output.timestamp_format'))
    print(f"  Token 檔案: {config.get_path('stage3_tokens', 'tokens', timestamp=timestamp)}")
