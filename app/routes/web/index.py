import time
from flask import Blueprint, render_template, session, current_app, jsonify
import pymysql
import pymysql.cursors
from db import get_connection
from app.services.stock.chart_utils import get_recent_stock_prices, generate_mini_chart_svg

bp = Blueprint('web_index_bp', __name__)

@bp.route('/')
def index():
    total_start_time = time.time()
    conn = get_connection()
    try:
        user = session.get('user')
        is_login = user is not None

        if is_login:
            # --- 로그인 사용자 로직 ---
            db_start_time = time.time()

            market_data = {}
            promising_stocks, failing_stocks = [], []
            market_summary = {'positive': '긍정적인 분석 결과가 없습니다.'}
            reference_time = None

            with conn.cursor() as cursor:
                # 시장 심리 지수 및 요약 부분
                cursor.execute("SELECT * FROM market_analysis ORDER BY date DESC LIMIT 1")
                db_market_data = cursor.fetchone()
                if db_market_data:
                    market_data = db_market_data
                    positive_count = market_data.get('positive', 0)
                    negative_count = market_data.get('negative', 0)
                    neutral_count = market_data.get('neutral', 0)
                    total_comments = market_data.get('total_comments', 0)
                    ratios = {'positive': 0, 'negative': 0, 'neutral': 0}
                    if total_comments > 0:
                        ratios['positive'] = round((positive_count / total_comments) * 100)
                        ratios['negative'] = round((negative_count / total_comments) * 100)
                        ratios['neutral'] = round((neutral_count / total_comments) * 100)
                    market_data['ratios'] = ratios

                # ⭐ [핵심 수정] WHERE 절을 삭제하여 심리상태와 관계없이 가장 최신 이유를 가져옴
                cursor.execute("SELECT reason FROM market_analysis ORDER BY date DESC LIMIT 1")
                latest_reason_record = cursor.fetchone()
                if latest_reason_record:
                    market_summary['positive'] = latest_reason_record['reason']

                cursor.execute("SELECT MAX(date) as max_date FROM stock_sentiment")
                max_date_result = cursor.fetchone()
                if not max_date_result or not max_date_result['max_date']:
                    return render_template("index_.html", is_login=is_login, user=user, market_data=market_data, market_summary=market_summary, promising_stocks=[], failing_stocks=[], reference_time=None)

                max_date = max_date_result['max_date']

                if max_date:
                    reference_time = max_date.strftime('%Y-%m-%d %H:%M') + " 기준"

                # 최적화된 쿼리 (이전과 동일)
                promising_query = """
                    SELECT
                        ss.stock_code, ss.score, ss.reason, ss.positive, ss.negative, ss.neutral,
                        sd.stock_name, sd.close_price, sd.price_change
                    FROM
                        stock_sentiment AS ss
                    JOIN
                        stock_data AS sd ON ss.stock_code = sd.stock_code COLLATE utf8mb4_unicode_ci
                    JOIN
                        (SELECT stock_code, MAX(date) AS max_date
                         FROM stock_data GROUP BY stock_code) AS latest_sd
                         ON sd.stock_code = latest_sd.stock_code COLLATE utf8mb4_unicode_ci AND sd.date = latest_sd.max_date
                    WHERE
                        ss.date = %s AND ss.score >= 75
                    ORDER BY
                        ss.score DESC
                    LIMIT 3;
                """
                cursor.execute(promising_query, (max_date,))
                promising_stocks_raw = cursor.fetchall()

                failing_query = """
                    SELECT
                        ss.stock_code, ss.score, ss.reason, ss.positive, ss.negative, ss.neutral,
                        sd.stock_name, sd.close_price, sd.price_change
                    FROM
                        stock_sentiment AS ss
                    JOIN
                        stock_data AS sd ON ss.stock_code = sd.stock_code COLLATE utf8mb4_unicode_ci
                    JOIN
                        (SELECT stock_code, MAX(date) AS max_date
                         FROM stock_data GROUP BY stock_code) AS latest_sd
                         ON sd.stock_code = latest_sd.stock_code COLLATE utf8mb4_unicode_ci AND sd.date = latest_sd.max_date
                    WHERE
                        ss.date = %s AND ss.score <= 35
                    ORDER BY
                        ss.score ASC
                    LIMIT 3;
                """
                cursor.execute(failing_query, (max_date,))
                failing_stocks_raw = cursor.fetchall()

                # 데이터 가공 (이전과 동일)
                for stock in promising_stocks_raw:
                    change = stock['price_change']
                    previous_close = stock['close_price'] - change
                    change_rate_val = (change / previous_close * 100) if previous_close != 0 else 0
                    score = stock['score']
                    if score >= 75: sentiment_text, sentiment_class = "매우 긍정", "positive"
                    else: sentiment_text, sentiment_class = "긍정", "positive"
                    reason_text = stock.get('reason', '')
                    keywords = [word for word in reason_text.replace(",", " ").split() if word.startswith('#')]
                    promising_stocks.append({
                        'name': stock['stock_name'], 'currentPrice': f"{stock['close_price']:,}원",
                        'changeRate': f"{change_rate_val:+.2f}%", 'aiSentiment': sentiment_class,
                        'aiSentimentText': sentiment_text, 'reason': stock['reason'],
                        'sentiment_details': { 'score': stock['score'], 'ratios': {'positive': stock.get('positive', 0),'negative': stock.get('negative', 0),'neutral': stock.get('neutral', 0)},'keywords': keywords }
                    })

                for stock in failing_stocks_raw:
                    change = stock['price_change']
                    previous_close = stock['close_price'] - change
                    change_rate_val = (change / previous_close * 100) if previous_close != 0 else 0
                    score = stock['score']
                    if score <= 35: sentiment_text, sentiment_class = "매우 부정", "negative"
                    else: sentiment_text, sentiment_class = "부정적", "negative"
                    reason_text = stock.get('reason', '')
                    keywords = [word for word in reason_text.replace(",", " ").split() if word.startswith('#')]
                    failing_stocks.append({
                        'name': stock['stock_name'], 'currentPrice': f"{stock['close_price']:,}원",
                        'changeRate': f"{change_rate_val:+.2f}%", 'aiSentiment': sentiment_class,
                        'aiSentimentText': sentiment_text, 'reason': stock['reason'],
                        'sentiment_details': { 'score': stock['score'], 'ratios': {'positive': stock.get('positive', 0),'negative': stock.get('negative', 0),'neutral': stock.get('neutral', 0)},'keywords': keywords }
                    })

            db_end_time = time.time()
            current_app.logger.info(f"DB 및 데이터 처리 소요 시간: {db_end_time - db_start_time:.4f}초")
            render_start_time = time.time()

            response = render_template("index_.html",
                is_login=is_login, user=user, market_data=market_data,
                market_summary=market_summary,
                promising_stocks=promising_stocks,
                failing_stocks=failing_stocks,
                reference_time=reference_time
            )

            render_end_time = time.time()
            current_app.logger.info(f"템플릿 렌더링 소요 시간: {render_end_time - render_start_time:.4f}초")
            total_end_time = time.time()
            current_app.logger.info(f"=== 총 페이지 로딩 소요 시간: {total_end_time - total_start_time:.4f}초 ===")
            return response

        else:
            # --- 비로그인 사용자 로직 (이전과 동일) ---
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(date) AS max_date FROM live_data")
                latest_date_row = cursor.fetchone()
                if not latest_date_row or not latest_date_row['max_date']:
                    return render_template('index.html', is_login=False, user=None, stocks_hot=[], stocks_cold=[])
                max_date = latest_date_row['max_date']
                cursor.execute("""SELECT stock_name, stock_code, execution_price AS close_price, price_change, volume FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY time DESC) as rn FROM live_data WHERE date = %s) AS latest WHERE rn = 1 AND price_change > 0 ORDER BY volume DESC, price_change DESC LIMIT 20""", (max_date,))
                all_hot_rows = cursor.fetchall()
                cursor.execute("""SELECT stock_name, stock_code, execution_price AS close_price, price_change, volume FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY time DESC) as rn FROM live_data WHERE date = %s) AS latest WHERE rn = 1 AND price_change < 0 ORDER BY volume ASC, price_change ASC LIMIT 20""", (max_date,))
                all_cold_rows = cursor.fetchall()
                stocks_hot = []; added_hot_names = set()
                for row in all_hot_rows:
                    if len(stocks_hot) >= 5: break
                    name = row['stock_name']
                    if name not in added_hot_names:
                        price_change = row['price_change']
                        change_str = f'▲ {abs(price_change):,}' if price_change > 0 else (f'▼ {abs(price_change):,}' if price_change < 0 else '0')
                        change_color = 'red' if price_change > 0 else ('blue' if price_change < 0 else 'gray')
                        price_data_for_chart = get_recent_stock_prices(row['stock_code'], 7)
                        mini_chart_svg = generate_mini_chart_svg(price_data_for_chart)
                        stocks_hot.append({'name': name, 'code': row['stock_code'], 'price': row['close_price'], 'volume': row['volume'], 'change_str': change_str, 'change_color': change_color, 'mini_chart_svg': mini_chart_svg})
                        added_hot_names.add(name)
                stocks_cold = []; added_cold_names = set()
                for row in all_cold_rows:
                    if len(stocks_cold) >= 5: break
                    name = row['stock_name']
                    if name not in added_cold_names:
                        price_change = row['price_change']
                        change_str = f'▲ {abs(price_change):,}' if price_change > 0 else (f'▼ {abs(price_change):,}' if price_change < 0 else '0')
                        change_color = 'red' if price_change > 0 else ('blue' if price_change < 0 else 'gray')
                        price_data_for_chart = get_recent_stock_prices(row['stock_code'], 7)
                        mini_chart_svg = generate_mini_chart_svg(price_data_for_chart)
                        stocks_cold.append({'name': name, 'code': row['stock_code'], 'price': row['close_price'], 'volume': row['volume'], 'change_str': change_str, 'change_color': change_color, 'mini_chart_svg': mini_chart_svg})
                        added_cold_names.add(name)
            return render_template('index.html', is_login=is_login, user=user, stocks_hot=stocks_hot, stocks_cold=stocks_cold)
    finally:
        if conn:
            conn.close()

@bp.route('/api/market-sentiment-trend')
def market_sentiment_trend():
    conn = get_connection()
    chart_data = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT DATE(date) AS report_date, AVG(score) AS daily_score FROM market_analysis WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) GROUP BY DATE(date) ORDER BY report_date ASC;""")
            db_chart_data = cursor.fetchall()
            for row in db_chart_data:
                chart_data.append({'date': row['report_date'].strftime('%m-%d'), 'score': round(row['daily_score'], 1)})
    except Exception as e:
        current_app.logger.error(f"Error in market_sentiment_trend API: {e}")
    finally:
        if conn:
            conn.close()
    return jsonify(chart_data)