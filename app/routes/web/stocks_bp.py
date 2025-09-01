from flask import Blueprint, render_template, jsonify
from db import get_connection
from datetime import datetime, timedelta

# 블루프린트 생성
stocks_bp = Blueprint('stocks_bp', __name__)

# 특정 날짜(2025년 7월 29일)의 데이터를 가져와서 평균값을 계산하는 함수
def get_sentiment_for_specific_date():
    # 7월 29일의 시작과 끝 시간을 설정
    start_time = datetime(2025, 7, 29, 0, 0, 0)  # 2025년 7월 29일 00:00:00
    end_time = start_time + timedelta(days=1)  # 2025년 7월 30일 00:00:00 (하루 뒤)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT stock_sentiment_score
                FROM stock_sentiment_analysis_results
                WHERE analysis_datetime >= %s
                  AND analysis_datetime < %s
            """, (start_time, end_time))

            rows = cursor.fetchall()

            if rows:
                avg_sentiment_score = sum(row['stock_sentiment_score'] for row in rows) / len(rows)
                return avg_sentiment_score
            else:
                return None  # 데이터가 없을 경우 None 반환
    finally:
        conn.close()

# 메인 페이지 라우트
@stocks_bp.route('/')
def index():
    avg_sentiment_score = get_sentiment_for_specific_date()  # 수정된 함수 호출
    return render_template('index.html', avg_sentiment_score=avg_sentiment_score)

# 실시간으로 평균값을 반환하는 라우트 (AJAX 호출용)
@stocks_bp.route('/get_average_sentiment')
def get_average_sentiment():
    avg_sentiment_score = get_sentiment_for_specific_date()  # 수정된 함수 호출
    return jsonify({"avg_sentiment_score": avg_sentiment_score})
