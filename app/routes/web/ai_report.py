from flask import Blueprint, request, jsonify, current_app, render_template # ⭐ render_template_string 대신 render_template import
import time
from app.services.stock.data_loader import searching_stock_db # 이 부분은 경로가 정확한지 다시 한번 확인해주세요
from db import get_connection
import pymysql
import markdown

# searching_stock_db() 호출은 애플리케이션 컨텍스트 밖에서 일어나면 오류가 발생할 수 있습니다.
# Flask 앱이 시작될 때 데이터를 로드하여 app.config에 저장하는 것이 일반적입니다.
# 여기서는 편의상 전역 변수로 두지만, 실제 프로덕션 환경에서는 앱 컨텍스트를 활용하세요.
try:
    # app/__init__.py에서 로드된 stock_list를 가져오는 것이 이상적이지만,
    # 여기서는 임시로 직접 로드 시도
    stock_list = searching_stock_db()
except Exception as e:
    # print 대신 current_app.logger 사용 (앱 컨텍스트 밖에서는 print로 fallback)
    try:
        if current_app:
            current_app.logger.error(f"Error loading stock_list at blueprint init: {e}")
        else:
            print(f"Error loading stock_list at blueprint init: {e}")
    except RuntimeError: # current_app 접근 시 발생
        print(f"Error loading stock_list at blueprint init: {e}")
    stock_list = None # 로드 실패 시 None으로 설정

bp = Blueprint('report_ai_report_bp', __name__)

@bp.route('/api/ai_report', methods=['GET'])
def get_ai_report():
    try:
        current_app.logger.debug("Called :: get_ai_report API endpoint")
        stock_code = request.args.get('stock_code', '').strip()

        if not stock_code:
            return jsonify({"success": False, "error": "종목코드가 비어있습니다."}), 400

        global stock_list
        if stock_list is None:
            stock_list = searching_stock_db()
            if stock_list is None:
                return jsonify({"success": False, "error": "종목 목록을 불러올 수 없습니다."}), 500

        # stock_code로 종목명 찾기
        Inputstock_df = stock_list[stock_list['주식코드'].str.upper() == stock_code.upper()]
        stock_name = Inputstock_df.iloc[0]['종목명'] if not Inputstock_df.empty else stock_code

        # ⭐⭐⭐ AI 리포트 생성 시간 시뮬레이션 (3초 대기) ⭐⭐⭐
        # 이 시간 동안 프론트엔드에서는 "리포트 생성 중..." 메시지를 보여주면 됩니다.
        time.sleep(3)

        # ✅ 분석된 리포트 DB에서 불러오기 (원시 마크다운과 position을 반환)
        report_data = get_latest_ai_report(stock_code)

        if not report_data or not report_data.get('report_markdown'):
            # 리포트가 없을 때도 예쁘게 메시지를 보여주도록 HTML을 반환합니다.
            # 이 부분은 여전히 HTML 문자열로 직접 반환합니다.
            no_report_html = f"""
            <div style="font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; text-align: center; padding: 40px; color: #666; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); max-width: 600px; margin: 20px auto;">
                <p style="font-size: 1.1em; margin-bottom: 15px;">🔍 {stock_name}에 대한 AI 리포트가 아직 존재하지 않습니다.</p>
                <p style="font-size: 0.9em; color: #999;">새로운 분석이 곧 업데이트 될 수 있습니다.</p>
            </div>
            """
            return jsonify({
                "success": True,
                "ai_report": no_report_html, # 리포트 없을 때의 HTML 반환
                "report_title": "AI 리포트 없음",
                "sentiment_position": "없음" # 리포트 없을 때 기본값
            }), 200

        raw_report_markdown = report_data['report_markdown']
        sentiment_position = report_data.get('position', 'unknown')

        # 이미지의 제목 "삼성전자 2025년 3분기 AI 전망 리포트"처럼 구성
        main_report_title = f"{stock_name} 2025년 3분기 AI 전망 리포트"
        sub_report_title = f"{stock_name} AI 리포트" # 이미지의 작은 부제목

        # ⭐⭐⭐ 마크다운을 HTML로 변환합니다 ⭐⭐⭐
        report_content_html = markdown.markdown(raw_report_markdown)

        # ⭐⭐⭐ render_template()을 사용하여 HTML 파일 연결 ⭐⭐⭐
        # templates 폴더 안에 'ai_report_template.html' 파일이 있어야 합니다.
        final_html_report = render_template(
            'ai_report_template.html', # ⭐ 파일 경로를 지정합니다.
            main_report_title=main_report_title,
            sub_report_title=sub_report_title,
            report_content_html=report_content_html
        )

        return jsonify({
            "success": True,
            "ai_report": final_html_report, # ⭐ 구조화된 HTML 반환
            "report_title": main_report_title, # 이 값은 프론트엔드에서 참조용으로 사용 (전체 제목)
            "sentiment_position": sentiment_position # ⭐ 감성 데이터는 별도로 반환 (프론트엔드에서 활용)
        }), 200

    except Exception as e:
        error_message = f"서버 내부 오류가 발생했습니다: {str(e)}"
        current_app.logger.error(f"Unexpected server error in get_ai_report: {error_message}")
        return jsonify({"success": False, "error": error_message}), 500


def get_latest_ai_report(stock_code):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        stock_code = str(stock_code).zfill(6)

        cursor.execute("""
            SELECT report, position -- report는 마크다운 텍스트, position은 감성
            FROM stock_keywords
            WHERE stock_code = %s
            ORDER BY date DESC
            LIMIT 1
        """, (stock_code,))
        row = cursor.fetchone()

        if row and row.get('report'):
            # ⭐⭐⭐ 여기서는 더 이상 마크다운을 HTML로 변환하지 않고 원시 텍스트 반환 ⭐⭐⭐
            return {"report_markdown": row['report'], "position": row.get('position')} # ⭐ 마크다운과 position 함께 반환
        else:
            return None

    except Exception as e:
        # print 대신 current_app.logger 사용 (앱 컨텍스트 밖에서는 print로 fallback)
        try:
            if current_app:
                current_app.logger.error(f"DB 오류 발생 in get_latest_ai_report: {e}")
            else:
                print(f"DB 오류 발생: {e}")
        except RuntimeError:
            print(f"DB 오류 발생: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()