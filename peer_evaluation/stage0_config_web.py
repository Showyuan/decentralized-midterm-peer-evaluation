#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 化評分系統配置 - 簡化核心版本
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 載入 .env 文件
load_dotenv()

# 取得專案根目錄（peer_evaluation/ 的上層目錄）
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)


class WebConfig:
    """Web 系統核心配置"""
    
    # === Server 配置 ===
    SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.getenv('SERVER_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')
    
    # === Token 配置 ===
    TOKEN_EXPIRY_DAYS = int(os.getenv('TOKEN_EXPIRY_DAYS', 14))
    TOKEN_LENGTH = 36  # UUID4 標準長度
    
    # === 資料庫配置 ===
    DATABASE_PATH = os.getenv(
        'DATABASE_PATH', 
        os.path.join(_project_root, 'workflow_results/4_database/evaluation.db')
    )
    
    # === Email 配置 ===
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'True').lower() == 'true'
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', '區塊鏈導論助教')
    EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', '')
    
    # === 評分截止時間 ===
    EVALUATION_DEADLINE_DAYS = int(os.getenv('EVALUATION_DEADLINE_DAYS', 7))
    EVALUATION_DEADLINE = os.getenv(
        'EVALUATION_DEADLINE',
        (datetime.now() + timedelta(days=EVALUATION_DEADLINE_DAYS)).strftime('%Y-%m-%d 23:59:59')
    )
    
    # === 安全性配置 ===
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # === 管理介面 ===
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'change-me-in-production')
    
    @classmethod
    def validate(cls):
        """驗證必要配置"""
        errors = []
        
        if cls.EMAIL_ENABLED:
            if not cls.SMTP_USERNAME:
                errors.append("SMTP_USERNAME 未設定")
            if not cls.SMTP_PASSWORD:
                errors.append("SMTP_PASSWORD 未設定")
            if not cls.EMAIL_FROM_ADDRESS:
                errors.append("EMAIL_FROM_ADDRESS 未設定")
        
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production' and not cls.DEBUG:
            errors.append("請設定 SECRET_KEY 環境變數")
        
        return errors


if __name__ == '__main__':
    # 測試配置
    print("Web 配置測試")
    print(f"SERVER_URL: {WebConfig.SERVER_URL}")
    print(f"EMAIL_FROM: {WebConfig.EMAIL_FROM_ADDRESS}")
    print(f"TOKEN_EXPIRY: {WebConfig.TOKEN_EXPIRY_DAYS} 天")
    
    errors = WebConfig.validate()
    if errors:
        print("\n配置錯誤:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 配置正常")

