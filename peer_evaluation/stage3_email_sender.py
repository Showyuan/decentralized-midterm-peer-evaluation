#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email 發送器 - 批次發送個人化評分邀請信
從資料庫載入學生資料，支援匿名評分保護
"""

import os
import sys
import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from stage0_config_web import WebConfig
    from stage2_db_manager import DatabaseManager
except ImportError:
    from .stage0_config_web import WebConfig
    from .stage2_db_manager import DatabaseManager


class EmailSender:
    """Email 發送器 - 管理評分邀請信的發送"""
    
    def __init__(self, config: WebConfig = None):
        """
        初始化 Email 發送器
        
        Args:
            config: Web 配置物件
        """
        self.config = config or WebConfig()
        self.smtp_config = {
            'host': self.config.SMTP_HOST,
            'port': self.config.SMTP_PORT,
            'use_tls': self.config.SMTP_USE_TLS,
            'username': self.config.SMTP_USERNAME,
            'password': self.config.SMTP_PASSWORD,
            'from_name': self.config.EMAIL_FROM_NAME,
            'from_address': self.config.EMAIL_FROM_ADDRESS
        }
        
        print("Email 發送器初始化")
        print("=" * 60)
        print(f"SMTP 伺服器: {self.smtp_config['host']}:{self.smtp_config['port']}")
        print(f"寄件者: {self.smtp_config['from_name']} <{self.smtp_config['from_address']}>")
        print(f"TLS 加密: {self.smtp_config['use_tls']}")
    
    def create_email_template(self, 
                             student_name: str,
                             evaluation_urls: List[Dict],
                             deadline: str) -> Tuple[str, str]:
        """
        建立 Email 內容（純文字與 HTML 版本）
        
        Args:
            student_name: 學生姓名
            evaluation_urls: 評量 URL 列表
            deadline: 截止日期
            
        Returns:
            Tuple[str, str]: (純文字內容, HTML 內容)
        """
        num_assignments = len(evaluation_urls)
        
        # 建立 URL 列表（匿名評分 - 不顯示被評分者身份）
        url_list_text = "\n".join([
            f"{i+1}. 評分任務 #{i+1}\n   連結: {url['url']}"
            for i, url in enumerate(evaluation_urls)
        ])
        
        url_list_html = "".join([
            f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">
                    <strong>評分任務 #{i+1}</strong>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">
                    <a href="{url['url']}" 
                       style="display: inline-block; background-color: #4CAF50; color: white; 
                              padding: 8px 20px; text-decoration: none; border-radius: 5px; 
                              font-weight: bold;">
                        開始評分 →
                    </a>
                </td>
            </tr>
            """
            for i, url in enumerate(evaluation_urls)
        ])
        
        # === 純文字版本 ===
        text_content = f"""
【區塊鏈導論】期中考互評表單

親愛的 {student_name} 同學，您好：

您的期中考互評表單已準備完成，請點擊以下連結進行評分。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 您的評分任務 ({num_assignments} 份)

{url_list_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ 截止時間：{deadline}

📌 評分須知：
• 每個連結對應一份作業的評分
• 請為每題填寫評分與評語
• 評語請具體且建設性
• 提交後無法修改，請確認後再送出
• 此連結僅供您個人使用，請勿分享
• 本次評分採匿名制，系統不會揭露被評分者身份

⚠️  重要提醒：
• 請認真評分，您的評分將影響他人成績
• 請保持客觀公正，不要猜測被評分者身份
• 如遇技術問題，請聯繫助教

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

此為系統自動發送郵件，請勿直接回覆。

區塊鏈導論課程助教團隊
國立台灣大學資訊工程學系
        """
        
        # === HTML 版本 ===
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>期中考互評通知</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Microsoft JhengHei', 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 24px;">🎓 區塊鏈導論</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px;">期中考互評通知</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px;">
                            <p style="font-size: 16px; color: #333; line-height: 1.6;">
                                親愛的 <strong style="color: #667eea;">{student_name}</strong> 同學，您好：
                            </p>
                            
                            <p style="font-size: 15px; color: #666; line-height: 1.6;">
                                您的期中考互評表單已準備完成，請點擊以下連結進行評分。
                            </p>
                            
                            <!-- Assignments Box -->
                            <div style="background-color: #f9f9f9; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 5px;">
                                <h3 style="margin: 0 0 10px 0; color: #333; font-size: 16px;">
                                    📋 您的評分任務 ({num_assignments} 份)
                                </h3>
                                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 14px; color: #666;">
                                    {url_list_html}
                                </table>
                            </div>
                            
                            <!-- Deadline -->
                            <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center;">
                                <p style="margin: 0; color: #856404; font-size: 15px;">
                                    ⏰ <strong>截止時間：{deadline}</strong>
                                </p>
                            </div>
                            
                            <!-- Instructions -->
                            <div style="margin: 20px 0;">
                                <h3 style="color: #333; font-size: 16px; margin-bottom: 10px;">📌 評分須知：</h3>
                                <ul style="color: #666; font-size: 14px; line-height: 1.8; padding-left: 20px;">
                                    <li>每個連結對應一份作業的評分</li>
                                    <li>請為每題填寫評分與評語</li>
                                    <li>評語請具體且建設性</li>
                                    <li>提交後無法修改，請確認後再送出</li>
                                    <li>此連結僅供您個人使用，請勿分享</li>
                                    <li><strong>本次評分採匿名制，系統不會揭露被評分者身份</strong></li>
                                </ul>
                            </div>
                            
                            <!-- Warning -->
                            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 5px;">
                                <h3 style="color: #721c24; font-size: 16px; margin: 0 0 10px 0;">⚠️ 重要提醒：</h3>
                                <ul style="color: #721c24; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                    <li>請認真評分，您的評分將影響他人成績</li>
                                    <li>請保持客觀公正，不要猜測被評分者身份</li>
                                    <li>如遇技術問題，請聯繫助教</li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                            <p style="margin: 0; font-size: 12px; color: #999; line-height: 1.6;">
                                此為系統自動發送郵件，請勿直接回覆。<br>
                                <strong style="color: #666;">區塊鏈導論課程助教團隊</strong><br>
                                國立台灣大學資訊工程學系
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return text_content.strip(), html_content.strip()
    
    def send_email(self,
                   recipient: str,
                   subject: str,
                   text_content: str,
                   html_content: str,
                   retry: int = 3) -> Tuple[bool, str]:
        """
        發送單封 Email
        
        Args:
            recipient: 收件者 Email
            subject: 主旨
            text_content: 純文字內容
            html_content: HTML 內容
            retry: 失敗重試次數
            
        Returns:
            Tuple[bool, str]: (是否成功, 錯誤訊息)
        """
        for attempt in range(retry):
            try:
                # 建立郵件
                msg = MIMEMultipart('alternative')
                msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_address']}>"
                msg['To'] = recipient
                msg['Subject'] = subject
                
                # 附加純文字與 HTML 版本
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                part2 = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(part1)
                msg.attach(part2)
                
                # 連接 SMTP 伺服器
                if self.smtp_config['use_tls']:
                    server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
                    server.starttls()
                else:
                    server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
                
                # 登入
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                # 發送郵件
                server.send_message(msg)
                server.quit()
                
                return True, ""
                
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"SMTP 認證失敗: {e}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
            except smtplib.SMTPException as e:
                error_msg = f"SMTP 錯誤: {e}"
                print(f"⚠️  嘗試 {attempt + 1}/{retry} 失敗: {error_msg}")
                if attempt < retry - 1:
                    time.sleep(2 ** attempt)  # 指數退避
                else:
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"未知錯誤: {e}"
                print(f"❌ {error_msg}")
                return False, error_msg
        
        return False, "達到最大重試次數"
    
    def load_from_database(self) -> Dict:
        """
        從資料庫載入學生和評量 URL 資料
        
        Returns:
            Dict: 包含學生資訊和評量 URL 的字典
        """
        print("\n" + "="*60)
        print("從資料庫載入學生和評量資料")
        print("="*60)
        
        try:
            db = DatabaseManager()
            
            # 獲取所有學生
            students = db.get_all_students()
            print(f"✅ 載入 {len(students)} 位學生")
            
            # 構建學生資料字典
            urls_data = {}
            
            for student in students:
                student_id = student['student_id']
                student_name = student['student_name']
                email = student.get('email', '')
                
                # 獲取該學生需要評分的所有 tokens
                tokens = db.get_tokens_by_evaluator(student_id)
                
                # 構建評量 URL 列表（匿名評分 - 不包含被評分者身份）
                evaluation_urls = []
                for token in tokens:
                    evaluation_url = {
                        'url': f"{self.config.SERVER_URL}/evaluate?token={token['token']}"
                    }
                    evaluation_urls.append(evaluation_url)
                
                # 只包含有評量任務的學生
                if evaluation_urls:
                    urls_data[student_id] = {
                        'student_name': student_name,
                        'email': email,
                        'evaluation_urls': evaluation_urls
                    }
                    print(f"  {student_id} ({student_name}): {len(evaluation_urls)} 個評量任務")
            
            print(f"\n✅ 載入完成")
            print(f"共 {len(urls_data)} 位學生有評量任務")
            print(f"總計 {sum(len(s['evaluation_urls']) for s in urls_data.values())} 個評量任務")
            
            return urls_data
            
        except Exception as e:
            print(f"❌ 從資料庫載入失敗: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def send_batch_emails(self,
                         test_mode: bool = False,
                         test_email: str = None,
                         delay: float = 1.0) -> Dict:
        """
        批次發送評分邀請信（從資料庫載入）
        
        Args:
            test_mode: 測試模式（只發給測試 Email）
            test_email: 測試 Email 地址
            delay: 每封信之間的延遲（秒）
            
        Returns:
            Dict: 發送結果統計
        """
        print("\n" + "="*60)
        print("批次發送評分邀請信")
        print("="*60)
        
        # 從資料庫載入
        urls_data = self.load_from_database()
        if not urls_data:
            print("❌ 從資料庫載入失敗或無資料")
            return {}
        
        # 測試模式檢查
        if test_mode:
            if not test_email:
                test_email = self.smtp_config['from_address']
            print(f"\n⚠️  測試模式啟用")
            print(f"所有郵件將發送到: {test_email}")
            confirm = input("繼續？(y/n): ").lower().strip()
            if confirm != 'y':
                print("已取消")
                return {}
        
        # 準備發送
        total = len(urls_data)
        success_count = 0
        fail_count = 0
        results = {
            'success': [],
            'failed': [],
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n開始發送 {total} 封郵件...")
        print("-"*60)
        
        # 逐一發送
        for i, (student_id, student_info) in enumerate(urls_data.items(), 1):
            student_name = student_info.get('student_name', student_id)
            student_email = student_info.get('email', '')
            evaluation_urls = student_info.get('evaluation_urls', [])
            
            # 測試模式使用測試 Email
            recipient = test_email if test_mode else student_email
            
            if not recipient:
                print(f"⚠️  [{i}/{total}] {student_id} ({student_name}): 無 Email 地址")
                fail_count += 1
                results['failed'].append({
                    'student_id': student_id,
                    'student_name': student_name,
                    'reason': '無 Email 地址'
                })
                continue
            
            # 建立郵件內容
            subject = f"【區塊鏈導論】期中考互評表單 - 請於 {self.config.EVALUATION_DEADLINE} 前完成"
            text_content, html_content = self.create_email_template(
                student_name=student_name,
                evaluation_urls=evaluation_urls,
                deadline=self.config.EVALUATION_DEADLINE
            )
            
            # 發送郵件
            print(f"[{i}/{total}] 發送到 {student_id} ({student_name}): {recipient}...", end=' ')
            
            success, error = self.send_email(
                recipient=recipient,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
            if success:
                print("✅")
                success_count += 1
                results['success'].append({
                    'student_id': student_id,
                    'student_name': student_name,
                    'email': recipient,
                    'num_urls': len(evaluation_urls)
                })
            else:
                print(f"❌ {error}")
                fail_count += 1
                results['failed'].append({
                    'student_id': student_id,
                    'student_name': student_name,
                    'email': recipient,
                    'reason': error
                })
            
            # 延遲以避免觸發 SMTP 限制
            if i < total:
                time.sleep(delay)
        
        # 顯示結果
        print("\n" + "="*60)
        print("發送完成")
        print("="*60)
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失敗: {fail_count}")
        print(f"📊 成功率: {success_count/total*100:.1f}%")
        
        # 儲存發送記錄
        self.save_send_log(results)
        
        return results
    
    def save_send_log(self, results: Dict, output_dir: str = None) -> str:
        """
        儲存發送記錄
        
        Args:
            results: 發送結果
            output_dir: 輸出目錄
            
        Returns:
            str: 記錄檔案路徑
        """
        if not output_dir:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'workflow_results/3_token_generation'
            )
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(output_dir, f'email_send_log_{timestamp}.json')
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n📝 發送記錄已儲存: {log_file}")
            return log_file
        except Exception as e:
            print(f"⚠️  記錄儲存失敗: {e}")
            return ""
    
    def send_test_email(self, recipient: str = None) -> bool:
        """
        發送測試郵件
        
        Args:
            recipient: 收件者（預設為寄件者）
            
        Returns:
            bool: 是否成功
        """
        if not recipient:
            recipient = self.smtp_config['from_address']
        
        print(f"\n發送測試郵件到: {recipient}")
        
        subject = "【測試】區塊鏈導論 - 期中考互評系統"
        
        # 測試用的評量 URL（匿名，不顯示被評分者身份）
        test_urls = [
            {
                'url': f"{self.config.SERVER_URL}/evaluate?token=test-token-12345"
            },
            {
                'url': f"{self.config.SERVER_URL}/evaluate?token=test-token-67890"
            }
        ]
        
        text_content, html_content = self.create_email_template(
            student_name="測試用戶",
            evaluation_urls=test_urls,
            deadline=self.config.EVALUATION_DEADLINE
        )
        
        success, error = self.send_email(
            recipient=recipient,
            subject=subject,
            text_content=text_content,
            html_content=html_content
        )
        
        if success:
            print("✅ 測試郵件發送成功！")
            return True
        else:
            print(f"❌ 測試郵件發送失敗: {error}")
            return False


def main():
    """主程序 - 命令列介面"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Email 發送器 - 批次發送評分邀請信',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 預覽模式（不實際發送）
  python email_sender.py --dry-run
  
  # 發送給特定學生
  python email_sender.py --student A12345678
  
  # 發送給所有學生
  python email_sender.py --all
  
  # 僅發送給未完成的學生
  python email_sender.py --pending
  
  # 舊版相容: 測試模式
  python email_sender.py --test
  python email_sender.py --batch --test-mode --test-email your@email.com
        """
    )
    
    # 新版參數
    parser.add_argument('--dry-run', action='store_true', help='預覽模式（僅顯示要發送的內容，不實際發送）')
    parser.add_argument('--student', type=str, help='發送給特定學生（輸入學號）')
    parser.add_argument('--all', action='store_true', help='發送給所有學生')
    parser.add_argument('--pending', action='store_true', help='僅發送給尚未使用 Token 的學生')
    
    # 舊版相容參數
    parser.add_argument('--test', action='store_true', help='發送測試郵件（舊版）')
    parser.add_argument('--batch', action='store_true', help='批次發送（舊版）')
    parser.add_argument('--test-mode', action='store_true', help='測試模式（只發給測試 Email）（舊版）')
    parser.add_argument('--test-email', type=str, help='測試 Email 地址')
    parser.add_argument('--delay', type=float, default=1.0, help='每封信之間的延遲（秒）')
    
    args = parser.parse_args()
    
    # 初始化發送器
    sender = EmailSender()
    
    # 驗證配置
    errors = WebConfig.validate()
    if errors:
        print("\n❌ 配置錯誤:")
        for error in errors:
            print(f"  - {error}")
        print("\n請檢查 .env 檔案設定")
        sys.exit(1)
    
    # 初始化資料庫管理器
    db_manager = DatabaseManager()
    
    try:
        # 新版參數處理
        if args.dry_run:
            # 預覽模式：顯示一封範例 Email
            print("\n" + "="*60)
            print("📧 Email 預覽模式")
            print("="*60 + "\n")
            
            # 從資料庫載入學生資料
            urls_data = sender.load_from_database()
            if not urls_data:
                print("❌ 資料庫中沒有評量資料")
                sys.exit(1)
            
            # 取第一位學生作為範例
            sample_student_id = list(urls_data.keys())[0]
            sample_data = urls_data[sample_student_id]
            
            # 生成 Email 內容
            text_content, html_content = sender.create_email_template(
                student_name=sample_data['student_name'],
                evaluation_urls=sample_data['evaluation_urls'],
                deadline=sender.config.EVALUATION_DEADLINE
            )
            
            print(f"📨 範例學生: {sample_student_id} ({sample_data['student_name']})")
            print(f"� Email: {sample_data['email']}")
            print(f"📋 評量任務數: {len(sample_data['evaluation_urls'])}")
            print("\n" + "-"*60)
            print("純文字版本:")
            print("-"*60)
            print(text_content)
            print("\n" + "-"*60)
            print("HTML 版本已生成 (略過顯示)")
            print("-"*60)
            print(f"\n✅ 預覽完成 - 實際會發送給 {len(urls_data)} 位學生")
            
        elif args.student:
            # 發送給特定學生
            print(f"\n📧 發送 Email 給學生: {args.student}")
            
            # 從資料庫載入學生資料
            urls_data = sender.load_from_database()
            
            if args.student not in urls_data:
                print(f"❌ 找不到學生 {args.student} 或該學生沒有評量任務")
                sys.exit(1)
            
            student_data = urls_data[args.student]
            
            # 生成 Email 內容
            text_content, html_content = sender.create_email_template(
                student_name=student_data['student_name'],
                evaluation_urls=student_data['evaluation_urls'],
                deadline=sender.config.EVALUATION_DEADLINE
            )
            
            # 發送 Email
            success, error = sender.send_email(
                recipient=student_data['email'],
                subject="[區塊鏈導論] 期中同儕互評通知",
                text_content=text_content,
                html_content=html_content
            )
            
            if success:
                print(f"✅ Email 已發送給 {args.student} ({student_data['email']})")
            else:
                print(f"❌ 發送失敗: {error}")
                sys.exit(1)
        
        elif args.all:
            # 發送給所有學生 - 使用現有的 send_batch_emails 方法
            print("\n📧 批次發送 Email 給所有學生")
            sender.send_batch_emails(
                test_mode=False,
                test_email=None,
                delay=args.delay
            )
            
        elif args.pending:
            # 僅發送給未使用 Token 的學生
            print("\n📧 發送提醒給尚未完成評量的學生")
            
            # 從資料庫載入所有學生資料
            urls_data = sender.load_from_database()
            if not urls_data:
                print("❌ 資料庫中沒有評量資料")
                sys.exit(1)
            
            # 初始化資料庫管理器以檢查 token 使用狀態
            db_manager = DatabaseManager()
            
            # 篩選出有未使用 token 的學生
            pending_students = {}
            for student_id, student_data in urls_data.items():
                # 檢查該學生是否有未使用的 token
                tokens = db_manager.get_tokens_by_evaluator(student_id)
                has_pending = any(not token['is_used'] for token in tokens)
                
                if has_pending:
                    pending_students[student_id] = student_data
            
            if not pending_students:
                print("✅ 所有學生都已完成評量")
                sys.exit(0)
            
            total = len(pending_students)
            success_count = 0
            failed_count = 0
            
            print(f"準備發送提醒給 {total} 位尚未完成的學生...\n")
            
            for i, (student_id, student_data) in enumerate(pending_students.items(), 1):
                print(f"[{i}/{total}] 提醒 {student_id} ({student_data['student_name']})...", end=" ")
                
                # 生成 Email 內容
                text_content, html_content = sender.create_email_template(
                    student_name=student_data['student_name'],
                    evaluation_urls=student_data['evaluation_urls'],
                    deadline=sender.config.EVALUATION_DEADLINE
                )
                
                # 發送（使用提醒主旨）
                success, error = sender.send_email(
                    recipient=student_data['email'],
                    subject="[區塊鏈導論] 期中同儕互評提醒 - 請盡快完成",
                    text_content=text_content,
                    html_content=html_content
                )
                
                if success:
                    print("✅")
                    success_count += 1
                else:
                    print(f"❌ {error}")
                    failed_count += 1
                
                # 延遲避免被封鎖
                if i < total:
                    time.sleep(args.delay)
            
            print(f"\n📊 提醒發送完成:")
            print(f"  • 成功: {success_count}")
            print(f"  • 失敗: {failed_count}")
        
        # 舊版相容處理
        elif args.test:
            # 發送測試郵件
            sender.send_test_email(args.test_email)
            
        elif args.batch:
            # 批次發送
            sender.send_batch_emails(
                test_mode=args.test_mode,
                test_email=args.test_email,
                delay=args.delay
            )
            
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
