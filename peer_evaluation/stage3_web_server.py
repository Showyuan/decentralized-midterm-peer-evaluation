#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 評分系統 - Flask 伺服器
提供線上評分表單介面
"""

from flask import Flask, jsonify, render_template, render_template_string, request
from datetime import datetime
import os
import json

# 匯入配置和資料庫管理
try:
    from .stage0_config_web import WebConfig
    from .stage2_db_manager import DatabaseManager
except ImportError:
    from stage0_config_web import WebConfig
    from stage2_db_manager import DatabaseManager

app = Flask(__name__)
app.config['SECRET_KEY'] = WebConfig.SECRET_KEY

# 初始化資料庫管理器
db_manager = DatabaseManager()

def load_questions():
    """
    載入題目資料
    
    Returns:
        Dict: 題目字典 {question_id: question_data}
    """
    try:
        assignments_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'workflow_results/2_assignment/peer_assignments.json'
        )
        
        with open(assignments_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('questions', {})
    except Exception as e:
        print(f"❌ 載入題目失敗: {e}")
        return {}

def load_student_answers(student_id):
    """
    載入特定學生的答案
    
    Args:
        student_id: 學生 ID (例如 'A01', 'B02')
    
    Returns:
        Dict: 學生答案字典 {question_id: answer_data}
    """
    try:
        midterm_data_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'workflow_results/1_data_preparation/midterm_data.json'
        )
        
        with open(midterm_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            students = data.get('students', {})
            
            if student_id in students:
                return students[student_id].get('answers', {})
            else:
                print(f"❌ 找不到學生 {student_id} 的資料")
                return {}
    except Exception as e:
        print(f"❌ 載入學生答案失敗: {e}")
        return {}


# 簡單的首頁 HTML（用於測試，實際會使用模板）
HOME_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>期中考互評系統</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            text-align: center;
        }
        h1 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        .status {
            background: #e8f5e9;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #4caf50;
        }
        .status h2 {
            color: #2e7d32;
            margin-bottom: 10px;
        }
        .info {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: left;
        }
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ddd;
        }
        .info-item:last-child { border-bottom: none; }
        .label { font-weight: bold; color: #666; }
        .value { color: #333; }
        .footer {
            margin-top: 30px;
            color: #999;
            font-size: 0.9em;
        }
        .badge {
            display: inline-block;
            padding: 5px 10px;
            background: #4caf50;
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 區塊鏈導論</h1>
        <h2>期中考互評系統</h2>
        
        <div class="status">
            <h2>✅ 系統運行中</h2>
            <span class="badge">v1.0</span>
        </div>
        
        <div class="info">
            <div class="info-item">
                <span class="label">伺服器時間:</span>
                <span class="value">{{ server_time }}</span>
            </div>
            <div class="info-item">
                <span class="label">系統狀態:</span>
                <span class="value">正常運行</span>
            </div>
            <div class="info-item">
                <span class="label">評分截止:</span>
                <span class="value">{{ deadline }}</span>
            </div>
        </div>
        
        <div class="footer">
            <p>國立台灣大學 資訊工程學系</p>
            <p>Powered by Vancouver Algorithm</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """管理儀表板首頁 - 顯示所有學生提交狀態"""
    try:
        # 載入學生資料
        midterm_data_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'workflow_results/1_data_preparation/midterm_data.json'
        )
        with open(midterm_data_file, 'r', encoding='utf-8') as f:
            midterm_data = json.load(f)
            students_data = midterm_data['students']
        
        # 取得所有 tokens
        all_tokens = db_manager.get_all_tokens()
        
        # 統計每個學生的提交狀態
        student_stats = {}
        for token in all_tokens:
            evaluator_id = token['evaluator_id']
            if evaluator_id not in student_stats:
                student_stats[evaluator_id] = {
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'last_submission': None
                }
            
            student_stats[evaluator_id]['total'] += 1
            if token['is_used']:
                student_stats[evaluator_id]['completed'] += 1
                # 更新最後提交時間
                if token['used_at']:
                    if not student_stats[evaluator_id]['last_submission'] or \
                       token['used_at'] > student_stats[evaluator_id]['last_submission']:
                        student_stats[evaluator_id]['last_submission'] = token['used_at']
            else:
                student_stats[evaluator_id]['pending'] += 1
        
        # 準備學生列表資料
        students_list = []
        for student_id, student_data in sorted(students_data.items()):
            stats = student_stats.get(student_id, {'total': 0, 'completed': 0, 'pending': 0, 'last_submission': None})
            completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            # 格式化最後提交時間
            last_submission = None
            if stats['last_submission']:
                try:
                    dt = datetime.fromisoformat(stats['last_submission'])
                    last_submission = dt.strftime('%m/%d %H:%M')
                except:
                    last_submission = stats['last_submission'][:16]
            
            students_list.append({
                'student_id': student_id,
                'name': student_data.get('name', 'Unknown'),
                'total': stats['total'],
                'completed': stats['completed'],
                'pending': stats['pending'],
                'completion_rate': completion_rate,
                'last_submission': last_submission
            })
        
        # 排序：完成率低的在前面（需要關注）
        students_list.sort(key=lambda x: (x['completion_rate'], x['student_id']))
        
        # 計算總體統計
        total_tokens = len(all_tokens)
        completed_tokens = sum(1 for t in all_tokens if t['is_used'])
        pending_tokens = total_tokens - completed_tokens
        completion_rate = (completed_tokens / total_tokens * 100) if total_tokens > 0 else 0
        tasks_per_student = total_tokens // len(students_data) if len(students_data) > 0 else 0
        
        overall_stats = {
            'total_students': len(students_data),
            'total_tokens': total_tokens,
            'completed_tokens': completed_tokens,
            'pending_tokens': pending_tokens,
            'completion_rate': completion_rate,
            'tasks_per_student': tasks_per_student
        }
        
        return render_template('dashboard.html',
            students=students_list,
            stats=overall_stats,
            deadline=WebConfig.EVALUATION_DEADLINE,
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except Exception as e:
        print(f"❌ 載入儀表板失敗: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>載入失敗</h1><p>{str(e)}</p>", 500

@app.route('/health')
def health():
    """健康檢查端點"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'peer-evaluation-system',
        'version': '1.0.0'
    })

@app.route('/api/status')
def status():
    """系統狀態 API"""
    return jsonify({
        'server': {
            'url': WebConfig.SERVER_URL,
            'host': WebConfig.SERVER_HOST,
            'port': WebConfig.SERVER_PORT,
            'debug': WebConfig.DEBUG
        },
        'features': {
            'email': WebConfig.EMAIL_ENABLED,
            'admin': WebConfig.ADMIN_ENABLED
        },
        'evaluation': {
            'deadline': WebConfig.EVALUATION_DEADLINE
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/evaluate')
def evaluation_form():
    """
    評分表單頁面
    使用 query parameter: /evaluate?token=xxx
    """
    token = request.args.get('token')
    
    if not token:
        return jsonify({
            'error': 'Missing Token',
            'message': '缺少 Token 參數'
        }), 400
    
    try:
        # 驗證 Token
        is_valid, token_info, error_msg = db_manager.validate_token(token)
        
        # 檢查是否已提交（即使 is_valid=False，如果是因為已使用，也要顯示已提交頁面）
        if token_info and token_info.get('is_used'):
            return render_template('already_submitted.html',
                submitted_at=token_info['used_at'],
                server_url=WebConfig.SERVER_URL
            )
        
        # 其他錯誤（不存在、過期等）
        if not is_valid:
            return render_template('error.html',
                error_title='Token 無效',
                error_message=error_msg,
                server_url=WebConfig.SERVER_URL
            ), 403
        
        # 載入題目
        questions_ids = json.loads(token_info['questions'])
        questions_data = load_questions()
        
        # 載入被評分者的答案
        target_answers = load_student_answers(token_info['target_id'])
        
        # 準備表單資料（包含題目、答案和配分）
        questions_with_answers = []
        for qid in questions_ids:
            if qid in questions_data:
                question = questions_data[qid].copy()
                # 重要：使用正確的 question_id (Q1-Q5)，而不是原始的數字ID
                # 這樣前端提交時會使用Q1-Q5，而不是335725-335729
                question['id'] = qid  # 覆寫原來的數字ID，使用Q1, Q2, ... Q5
                
                # 加入被評分者的答案
                answer = target_answers.get(qid, {})
                answer_text = answer.get('text', '').strip()
                
                # 如果答案為空，顯示提示訊息
                if not answer_text:
                    answer_text = '（此題無作答或答案為空白）'
                
                question['student_answer'] = answer_text
                question['answer_word_count'] = answer.get('word_count', 0)
                question['answer_is_empty'] = answer.get('is_empty', True)
                questions_with_answers.append(question)
        
        # 準備表單資料
        form_data = {
            'token': token,
            'evaluator_name': token_info['evaluator_name'],
            'target_id': token_info['target_id'],  # 僅後端使用，不顯示給學生
            'questions': questions_with_answers,
            'deadline': WebConfig.EVALUATION_DEADLINE
        }
        
        # 記錄查看日誌
        db_manager.log_action(
            token=token,
            action='view',
            details='查看評分表單',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return render_template('evaluation_form.html', **form_data)
        
    except Exception as e:
        print(f"❌ 表單載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html',
            error_title='系統錯誤',
            error_message='載入評分表單時發生錯誤，請聯繫助教',
            server_url=WebConfig.SERVER_URL
        ), 500


@app.route('/api/submit', methods=['POST'])
def submit_evaluation():
    """
    接收評分提交
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '無效的請求資料'}), 400
        
        token = data.get('token')
        submissions = data.get('submissions')  # [{question_id, score, comment}, ...]
        
        if not token or not submissions:
            return jsonify({'error': '缺少必要欄位'}), 400
        
        # 驗證 Token
        is_valid, token_info, error_msg = db_manager.validate_token(token)
        
        if not is_valid:
            return jsonify({'error': error_msg}), 403
        
        # 檢查是否已提交
        if token_info['is_used']:
            return jsonify({'error': '此 Token 已被使用'}), 400
        
        # 儲存評分
        evaluator_id = token_info['evaluator_id']
        target_id = token_info['target_id']
        
        submission_ids = []
        for sub in submissions:
            submission_id = db_manager.save_submission({
                'token': token,
                'evaluator_id': evaluator_id,
                'target_id': target_id,
                'question_id': sub['question_id'],
                'score': sub['score'],
                'comment': sub.get('comment', ''),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent')
            })
            submission_ids.append(submission_id)
        
        # 標記 Token 為已使用
        db_manager.mark_token_used(
            token=token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # 記錄提交日誌
        db_manager.log_action(
            token=token,
            action='submit',
            details=f'提交 {len(submissions)} 個評分',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': True,
            'message': '評分提交成功',
            'submission_ids': submission_ids
        })
        
    except Exception as e:
        print(f"❌ 評分提交失敗: {e}")
        import traceback
        traceback.print_exc()
        
        # 記錄錯誤日誌
        if 'token' in locals():
            db_manager.log_action(
                token=token,
                action='error',
                details=f'提交失敗: {str(e)}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        
        return jsonify({'error': '提交失敗，請稍後再試'}), 500


@app.route('/success')
def submission_success():
    """提交成功頁面"""
    return render_template('submission_success.html',
        server_url=WebConfig.SERVER_URL
    )


@app.errorhandler(404)
def not_found(error):
    """404 錯誤處理"""
    return jsonify({
        'error': 'Not Found',
        'message': '請求的資源不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 錯誤處理"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': '伺服器發生錯誤'
    }), 500

def main():
    """主函數"""
    print("\n" + "="*60)
    print("🚀 期中考互評系統 Web Server")
    print("="*60)
    print(f"📍 URL: {WebConfig.SERVER_URL}")
    print(f"🌐 監聽: {WebConfig.SERVER_HOST}:{WebConfig.SERVER_PORT}")
    print(f"🔧 除錯模式: {WebConfig.DEBUG}")
    print("="*60 + "\n")
    
    # 運行 Flask 應用
    app.run(
        host=WebConfig.SERVER_HOST,
        port=WebConfig.SERVER_PORT,
        debug=WebConfig.DEBUG
    )

if __name__ == '__main__':
    main()
