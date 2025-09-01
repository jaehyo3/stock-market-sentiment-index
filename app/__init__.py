import os
import pandas as pd
from flask import Flask, json

from app.services.stock.data_loader import stock_data_db, searching_stock_db

def create_app():
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    app.config.from_pyfile('config.py')
    app.config['SECRET_KEY'] = 'your_super_secret_key_12c345'
    APP_ROOT = app.root_path
    app.config['FAVORITES_FILE'] = os.path.join(APP_ROOT, 'favorites.csv')

    with app.app_context():
        print("데이터 로딩 시작")
        *_, stock_volume_df = stock_data_db()
        stock_list = searching_stock_db()
        print(f"로드된 종목 수: {len(stock_list)}")
        if not stock_volume_df.empty and '종목명' in stock_volume_df.columns and '거래량' in stock_volume_df.columns:
            max_volume_df = stock_volume_df.groupby('종목명', as_index=False)['거래량'].max()
            sorted_df = max_volume_df.sort_values(by='거래량', ascending=False)
            app.config['TOP_VOLUME_DF'] = sorted_df
        else:
            app.config['TOP_VOLUME_DF'] = pd.DataFrame(columns=['종목명', '거래량'])

    def json_load_filter(json_string):
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return []
    app.jinja_env.filters['from_json'] = json_load_filter

    # ==============================================================================
    # ⭐ [핵심 수정] 라우트 블루프린트 등록
    # ==============================================================================
    # 불필요한 'index_' import 구문을 완전히 삭제합니다.
    from .routes.web import ai_report, index, search, autocomplete
    from .routes.users import admin, login, logout, modify, prefer_stock, profile, signup, signout
    from .routes.web.stocks_bp import stocks_bp
    #from .routes.volume import top_chart
    from .routes.api import search_api, stock_analysis
    from .routes.users import email_verification

    # 블루프린트들을 등록합니다.
    # 불필요한 main_page_router 등록 코드를 삭제하고, index.bp 등록 코드만 남깁니다.
    app.register_blueprint(ai_report.bp)
    app.register_blueprint(index.bp) # <-- 'index.py'의 블루프린트를 정상적으로 등록합니다.
    app.register_blueprint(search.bp)
    app.register_blueprint(autocomplete.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(login.bp)
    app.register_blueprint(logout.bp)
    app.register_blueprint(modify.bp)
    app.register_blueprint(prefer_stock.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(signup.bp)
    app.register_blueprint(signout.bp)
    app.register_blueprint(stocks_bp)
    #app.register_blueprint(top_chart.bp)
    app.register_blueprint(search_api.bp, url_prefix='/api')
    app.register_blueprint(stock_analysis.bp, url_prefix='/api')
    app.register_blueprint(email_verification.bp)

    return app