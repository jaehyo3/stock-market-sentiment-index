from flask import Blueprint, request, jsonify
from app.services.stock.data_loader import searching_stock_db

stock_list = searching_stock_db()   # DataFrame 혹은 리스트
bp = Blueprint('autocomplete_bp', __name__)

@bp.route('/autocomplete')
def autocomplete():
    query = request.args.get('query', '').strip()
    if stock_list is None or not query:
        return jsonify([])
    # DataFrame일 때
    filtered = stock_list[
        stock_list['종목명'].str.contains(query, case=False, na=False) |
        stock_list['주식코드'].str.contains(query, case=False, na=False)
    ]
    suggestions = filtered[['종목명', '주식코드']].drop_duplicates()
    result = suggestions.to_dict(orient='records')
    print("DEBUG autocomplete result:", result)
    return jsonify(result[:10])
