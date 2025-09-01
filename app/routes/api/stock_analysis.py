from flask import Blueprint, request, jsonify
from app.services.stock.data_loader import news_data_db
bp = Blueprint('api_stock_analysis', __name__, url_prefix='/api')

@bp.route('/analyze', methods=['GET'])
def get_stock_analysis():
    """
    쿼리 파라미터로 받은 종목명에 대해 주가 데이터와 뉴스 기사를 JSON 형태로 반환합니다.
    예상 URL: /api/analyze?company_name=삼성전자
    """
    company_name = request.args.get('company_name')

    if not company_name:
        return jsonify({'error': '종목명(company_name) 파라미터가 필요합니다.'}), 400

    # news_data_db() 함수 호출로 데이터프레임 가져오기
    news_data_df = news_data_db()

    if news_data_df is None or news_data_df.empty:
        return jsonify({'error': '뉴스 데이터가 로드되지 않았습니다.'}), 500

    # 종목명 정제 (소문자 + 공백 제거 처리와 일치시켜야 함)
    company_name = company_name.strip().upper()

    # 해당 종목에 대한 데이터 필터링
    filtered_df = news_data_df[news_data_df['종목명'] == company_name]

    if filtered_df.empty:
        return jsonify({'error': f"'{company_name}'에 대한 데이터를 찾을 수 없습니다. 정확한 종목명을 확인해주세요."}), 404

    # JSON 변환을 위해 필요한 컬럼만 선택 (예시)
    json_data = filtered_df[[
        '날짜', '종가', '전일비', '거래량', '제목', '링크', '본문'
    ]].sort_values('날짜', ascending=False).to_dict(orient='records')

    return jsonify({'company_name': company_name, 'data': json_data}), 200