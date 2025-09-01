from flask import Blueprint, request, jsonify, current_app

bp = Blueprint('search_api_bp', __name__)

@bp.route('/search_stocks', methods=['GET'])
def search_stocks():
    query = request.args.get('query', '').strip().upper()

    if not query:
        return jsonify([])

    # 후에 주식코드가 있다면 [('삼성전자', '005930'), ('현대차', '005380'), ...] 이런 형태로
    stock_list = current_app.config.get('STOCK_LIST')

    # query가 이름 또는 코드에 포함되는 항목만 필터
    results = [
        {'name': name, 'code':code}
        for name, code in stock_list
        if query in name.upper() or query in code.upper()
    ]

    return jsonify(results[:50])
