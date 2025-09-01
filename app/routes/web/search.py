from flask import Blueprint, request, redirect, url_for, render_template, current_app, session, jsonify
from app.services.stock.data_loader import stock_data_db, searching_stock_db, news_data_db, analyze_stock_data

import pandas as pd
import json, math


bp = Blueprint('stocks_search_bp', __name__)

# 앱 시작 시 DB 데이터를 메모리에 로드 (캐싱)
stock_data_df, _ = stock_data_db()
stock_list = searching_stock_db()
news_data_df = news_data_db()

@bp.route('/search', methods=['GET', 'POST'])
def search():
    # (search 함수는 수정할 필요 없음)
    if 'user' not in session: return redirect(url_for('users_login_bp.login'))
    query = (request.args.get('search') or request.form.get('search') or '').strip()
    if not query: return render_template('search.html', user=session.get('user'), search_query='', price_chart_data_json='[]', stock_name_for_chart='', related_stocks=[], error_message="검색어가 제공되지 않았습니다.", search_result_name=None, search_result_code=None)
    price_chart_data, stock_name_for_chart, related_stocks, error_message, search_result_name, search_result_code, raw_price_data = [], "", [], None, None, None, []
    if query:
        session['last_search'] = query
        search_query_upper = query.upper()
        exact_match_df_rows = stock_list[stock_list['종목명'].str.upper() == search_query_upper]
        if not exact_match_df_rows.empty:
            found_stock_name, found_stock_code = exact_match_df_rows['종목명'].iloc[0], exact_match_df_rows['주식코드'].iloc[0]
            search_result_name, search_result_code, stock_name_for_chart = found_stock_name, found_stock_code, found_stock_name
            stock_news_df = pd.merge(stock_data_df, news_data_df, on=['종목명', '날짜'], how='left')
            analysis_results = analyze_stock_data(stock_news_df, found_stock_name)
            raw_price_data = analysis_results.get('price_data') if analysis_results else []
            price_chart_data = sanitize_price_data(raw_price_data)
            if not price_chart_data: error_message = f'"{query}" 종목의 유효한 주가 데이터를 찾을 수 없습니다.'
            all_unique_stocks = stock_list['종목명'].dropna().unique().tolist()
            related_stocks = [name for name in all_unique_stocks if search_query_upper in name.upper() and name.upper() != search_query_upper][:5]
        else:
            error_message = f'"{query}"에 해당하는 종목을 찾을 수 없습니다.'
            all_unique_stocks = stock_list['종목명'].dropna().unique().tolist()
            related_stocks = [name for name in all_unique_stocks if search_query_upper in name.upper()][:10]
    price_chart_data_json = json.dumps(price_chart_data, ensure_ascii=False)
    return render_template('search.html', user=session.get('user'), search_query=query, price_chart_data_json=price_chart_data_json, stock_name_for_chart=stock_name_for_chart, related_stocks=related_stocks, error_message=error_message, search_result_name=search_result_name, search_result_code=search_result_code)

def sanitize_price_data(data):
    safe_data, seen_dates = [], set()
    for item in data:
        try:
            date, close = str(item.get("날짜", "")), item.get("종가", None)
            if date and isinstance(close, (int, float)) and not math.isnan(close) and date not in seen_dates:
                safe_data.append({"날짜": date, "종가": round(close, 2)})
                seen_dates.add(date)
        except Exception as e:
            current_app.logger.warning(f"sanitize_price_data 오류: {e}")
    return safe_data


@bp.route('/api/news')
def api_news():
    NEWS_LIMIT = 10
    company_name = request.args.get('company_name', '').strip()
    if not company_name:
        return jsonify({'error': '종목명이 필요합니다.'}), 400

    if news_data_df is None:
        return jsonify({'error': '뉴스 데이터를 불러올 수 없습니다.'}), 500

    try:
        company_news_df = news_data_df[news_data_df['종목명'].str.upper() == company_name.upper()]

        company_news_df_with_title = company_news_df.dropna(subset=['제목'])

        if company_news_df_with_title.empty:
            return jsonify({'news_articles': [], 'message': f"'{company_name}'에 대한 뉴스를 찾을 수 없습니다."})

        # data_loader에서 이미 날짜 타입으로 만들어주므로, pd.to_datetime은 필요 없습니다.
        sorted_news_df = company_news_df_with_title.sort_values(by='날짜', ascending=False)

        latest_news_df = sorted_news_df.head(NEWS_LIMIT)

        news_articles = latest_news_df.to_dict('records')

        return jsonify({'news_articles': news_articles})

    except Exception as e:
        current_app.logger.error(f"뉴스 데이터 처리 중 오류: {e}", exc_info=True)
        return jsonify({'error': '뉴스 데이터를 처리하는 중 오류가 발생했습니다.'}), 500