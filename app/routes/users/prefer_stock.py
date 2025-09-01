from flask import Blueprint, render_template, request, redirect, url_for, session, json, jsonify
from db import get_connection
from app.services.stock.data_loader import searching_stock_db
from app.services.stock.chart_utils import get_recent_stock_prices, generate_mini_chart_svg # chart_utils에서 임포트

stock_list = searching_stock_db()

bp = Blueprint('users_prefer_stock_bp', __name__)

# 사용자 선호주식 리스트 조회 함수
# 현재가, 전일비 (가격 변동), 거래량, 미니차트(SVG) 정보를 포함하여 반환합니다.
def get_user_stock_display_db(userid):
    conn = get_connection()
    cursor = conn.cursor()

    # live_data 테이블을 사용하고, execution_price를 close_price로 별칭 지정
    cursor.execute("""
        SELECT
            t.stock_code,
            t.stock_name,
            t.execution_price AS close_price, -- execution_price를 close_price로 별칭
            t.price_change,
            t.volume
        FROM (
            SELECT
                p.stock_code,
                ld.stock_name,  -- live_data의 stock_name
                ld.execution_price,  -- live_data의 execution_price
                ld.price_change, -- live_data의 price_change
                ld.volume,       -- live_data의 volume
                ROW_NUMBER() OVER (PARTITION BY p.stock_code ORDER BY ld.date DESC, ld.time DESC) as rn
            FROM prefer_stock p
            JOIN live_data ld ON p.stock_code = ld.stock_code -- live_data 테이블 조인
            WHERE p.user_id = (SELECT id FROM users WHERE userid=%s)
        ) AS t
        WHERE t.rn = 1;
    """, (userid,))
    user_stocks = cursor.fetchall()
    conn.close()

    result_list = []
    for row in user_stocks:
        stock_code = row['stock_code']
        price = row['close_price'] # close_price 별칭으로 기존 코드 유지
        price_change = row['price_change']
        volume = row['volume']

        # 등락 부호 (🔺/🔻/🟡) 결정 및 색상 클래스
        change_icon = ''
        change_color = ''
        if price_change is not None:
            if price_change > 0:
                change_icon = '🔺'
                change_color = 'signal-up'
            elif price_change < 0:
                change_icon = '🔻'
                change_color = 'signal-down'
            else:
                change_icon = '🟡'
                change_color = 'signal-neutral'

        # chart_utils의 공통 함수 사용 (내부에서 live_data 사용)
        recent_prices = get_recent_stock_prices(stock_code, 7) # 최근 7일치 종가 데이터
        mini_chart_svg = generate_mini_chart_svg(recent_prices) # SVG 생성

        result_list.append({
            'name': row['stock_name'],
            'code': stock_code,
            'price': f"{price:,}" if price is not None else 'N/A',
            'price_change_amount': f"{change_icon}{abs(price_change):,}" if price_change is not None else 'N/A',
            'change_color_class': change_color,
            'volume': f"{volume:,}" if volume is not None else 'N/A',
            'mini_chart_svg': mini_chart_svg # 생성된 SVG 문자열을 JSON에 포함
        })
    return result_list

# 특정 종목의 상세 정보를 가져오는 함수
def get_stock_detail_db(stock_code):
    conn = get_connection()
    cursor = conn.cursor()
    stock_code = str(stock_code).zfill(6) # 코드 형식 맞추기

    try:
        # live_data 테이블을 사용하고, execution_price를 close_price로 별칭 지정
        cursor.execute("""
            SELECT
                ld.stock_name,
                ld.execution_price AS close_price, -- execution_price를 close_price로 별칭
                ld.price_change,
                ld.volume
            FROM live_data ld                       -- live_data 테이블 사용
            WHERE ld.stock_code = %s
            ORDER BY ld.date DESC, ld.time DESC     -- live_data의 날짜와 시간 사용
            LIMIT 1;
        """, (stock_code,))
        detail_data = cursor.fetchone()

        if not detail_data:
            return None

        current_price = detail_data['close_price'] # close_price 별칭으로 기존 코드 유지
        price_change = detail_data['price_change']
        percentage_change = None
        if price_change is not None and current_price is not None:
            previous_close = current_price - price_change
            if previous_close != 0: # 0으로 나누는 것 방지
                percentage_change = (price_change / previous_close) * 100

        # 뉴스 데이터 가져오기 (company_news 테이블 활용) - 이 부분은 stock_data나 live_data에 종속되지 않음
        news_list = []
        stock_name = detail_data['stock_name']
        cursor.execute("""
            SELECT title, link
            FROM company_news
            WHERE stock_name = %s
            ORDER BY date DESC
            LIMIT 5; -- 최신 뉴스 5개 가져오기
        """, (stock_name,))
        news_rows = cursor.fetchall()
        for news_row in news_rows:
            news_list.append({
                'title': news_row['title'],
                'link': news_row['link']
            })

        # chart_utils의 공통 함수 사용 (내부에서 live_data 사용)
        recent_prices = get_recent_stock_prices(stock_code, 30) # 예: 최근 30일치 상세 차트 데이터

        change_icon = ''
        change_color = ''
        if price_change is not None:
            if price_change > 0:
                change_icon = '🔺'
                change_color = 'signal-up'
            elif price_change < 0:
                change_icon = '<span style="color: blue;">🔻</span>'
                change_color = 'signal-down'
            else:
                change_icon = '🟡'
                change_color = 'signal-neutral'

        # Sentiment data (assuming it's calculated elsewhere or placeholder)
        # Placeholder for sentiment scores, replace with actual model output
        overall_positive_score = 0.0
        overall_negative_score = 0.0
        # 예시: 삼성전자는 긍정, 다른 종목은 부정 (임시)
        if "삼성전자" in stock_name:
            overall_positive_score = 1.25
            overall_negative_score = 0.30
        else:
            overall_positive_score = 0.40
            overall_negative_score = 1.80

        return {
            'code': stock_code,
            'name': detail_data['stock_name'],
            'price': detail_data['close_price'], # close_price 별칭으로 기존 코드 유지
            'price_change': detail_data['price_change'],
            'percentage_change': percentage_change,
            'volume': detail_data['volume'],
            'signal': '데이터 없음',
            'change_icon': change_icon,
            'change_color_class': change_color,
            'chart_data': recent_prices,
            'news': news_list,
            'sentiment': {
                'overall_positive_score': overall_positive_score,
                'overall_negative_score': overall_negative_score,
            }
        }
    finally:
        conn.close()

# 선호주식 등록 함수 (변경 없음)
def add_favorite_db(userid, stock_code):
    conn = get_connection()
    cursor = conn.cursor()
    stock_code = str(stock_code).zfill(6)

    # 해당 종목 존재 여부 확인 (live_data에서 확인하도록 변경)
    cursor.execute("""
        SELECT 1
        FROM live_data -- stock_data 대신 live_data에서 종목 존재 여부 확인
        WHERE stock_code=%s LIMIT 1
    """, (stock_code,))
    if not cursor.fetchone():
        conn.close()
        return False, "해당 종목이 존재하지 않습니다."

    # 중복 체크
    cursor.execute("""
        SELECT COUNT(*) AS cnt
        FROM prefer_stock
        WHERE user_id = (SELECT id FROM users WHERE userid=%s)
        AND stock_code=%s
    """, (userid, stock_code))
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
        return False, "이미 등록된 종목입니다."

    # 등록
    cursor.execute("""
        INSERT INTO prefer_stock (user_id, stock_code)
        VALUES ((SELECT id FROM users WHERE userid=%s), %s)
    """, (userid, stock_code))
    conn.commit()
    conn.close()
    return True, None

# 선호주식 삭제 함수 (변경 없음)
def delete_favorite_db(userid, stock_code):
    conn = get_connection()
    cursor = conn.cursor()
    stock_code = str(stock_code).zfill(6)

    cursor.execute("""
        DELETE FROM prefer_stock
        WHERE user_id = (SELECT id FROM users WHERE userid=%s)
        AND stock_code = %s
    """, (userid, stock_code))
    conn.commit()
    conn.close()
    return True

@bp.route('/prefer_stock', methods=['GET', 'POST'])
def prefer_stock():
    if 'user' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        return redirect(url_for('users_login_bp.login'))

    userid = session['user']

    if request.method == 'POST':
        stock_code = request.form.get('stock_code', '').strip()
        if not stock_code:
            stock_display = get_user_stock_display_db(userid)
            return jsonify({
                'success': False,
                'stock_display': stock_display,
                'error': "종목코드가 비었습니다."
            }), 400

        success, error = add_favorite_db(userid, stock_code)

        stock_display = get_user_stock_display_db(userid)

        return jsonify({
            'success': bool(success),
            'stock_display': stock_display,
            'error': error
        })

    # --- GET 요청 처리 로직 ---
    stock_display = get_user_stock_display_db(userid)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'stock_display': stock_display
        })

    return render_template(
        'prefer_stock.html',
        stock_display=stock_display,
        stock_list_json=json.dumps(stock_list, ensure_ascii=False)
    )


@bp.route('/prefer_stock/delete/<stock_code>', methods=['POST'])
def delete_prefer_stock(stock_code):
    if 'user' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'stock_display': [], 'error': '로그인이 필요합니다.'}), 401
        return redirect(url_for('users_login_bp.login'))

    userid = session['user']
    result = delete_favorite_db(userid, stock_code)
    stock_display = get_user_stock_display_db(userid)

    return jsonify({
        'success': bool(result),
        'stock_display': stock_display
    })

# 특정 종목의 상세 정보를 제공하는 API 엔드포인트
@bp.route('/api/stock_detail/<stock_code>', methods=['GET'])
def get_stock_detail(stock_code):
    if 'user' not in session:
        return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401

    detail_data = get_stock_detail_db(stock_code) # 위에서 정의한 함수 호출

    if detail_data:
        return jsonify({'success': True, 'detail': detail_data})
    else:
        return jsonify({'success': False, 'error': '해당 종목의 상세 정보를 찾을 수 없습니다.'}), 404