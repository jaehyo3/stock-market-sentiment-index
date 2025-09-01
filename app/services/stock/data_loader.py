from db import get_connection
# stock_news DB 연결함수

import pandas as pd

# 이 파일이 Flask 앱 컨텍스트 내에서 실행될 때는 current_app.logger를 사용하고,
# 단독으로 실행될 때는 기본 print 함수를 사용하도록 합니다.

def get_logger_or_print():
    try:
        from flask import current_app
        # Flask 앱 컨텍스트 내에 있고 logger가 유효하면 로거 객체 반환
        if current_app and current_app.logger:
            return current_app.logger
        else: # 혹시 current_app은 있어도 logger가 없을 경우 대비 (거의 발생 안 함)
            return print
    except RuntimeError: # Flask 컨텍스트 밖에서 current_app 접근 시 발생
        return print # 컨텍스트 밖이면 print 함수 반환
    except ImportError: # Flask가 설치되지 않았을 경우 (매우 드물게 발생)
        return print


# 주식 데이터 로딩 함수
# def load_stock_data_from_db():
def stock_data_db():

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                stock_name AS 종목명,
                stock_code AS 주식코드,
                date AS 날짜,
                open_price AS 시가,
                close_price AS 종가,
                price_change AS 전일비,
                volume AS 거래량
            FROM stock_data
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            # print(f"[DEBUG] rows 개수: {len(rows)}")

            if not rows:
                print("[WARNING]DB에서 로드할 데이터가 없습니다.")
                # return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜', '종가', '전일비', '거래량', '제목', '링크'])
                return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜','시가', '종가', '전일비', '거래량'])

            stock_data_df = pd.DataFrame(rows)
            stock_data_df['날짜'] = pd.to_datetime(stock_data_df['날짜'], errors='coerce')
            stock_data_df.dropna(subset=['날짜'], inplace=True)
            stock_data_df['종목명'] = stock_data_df['종목명'].astype(str).str.strip().str.upper()

            # 종목명, 거래량, 날짜만 담은 별도의 DataFrame 생성
            stock_volume_df = stock_data_df.loc[:, ['종목명', '거래량', '날짜']].copy()

            # Stock_Data_Df = stock_data_df['종목명'].unique().tolist()

            # print(f"[DEBUG] change 개수: {len(Stock_Data_Df)}")  # ✅ 추가
            # _logger.info(f"총 {len(stock_data_df)}개의 데이터 포인트 로드. 고유 종목 수: {len(Stock_Data_Df)}")


            return stock_data_df, stock_volume_df

    except Exception as e:
        print(f"[ERROR] DB 데이터 로드 중 오류: {e}")
        # return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜', '종가', '전일비', '거래량', '제목', '링크'])
        return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜','시가', '종가', '전일비', '거래량'])

    finally:
        print("[INFO] stock_data_db의 데이터 로딩 시작")
        # print(f"stock_data_df : 총 {len(stock_data_df)}개의 데이터 포인트 로드")
        # print(f"stock_volume_df : 총 {len(stock_volume_df)}개의 데이터 포인트 로드")
        conn.close()


# 주식 검색 데이터 로딩
def searching_stock_db():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    stock_name AS 종목명,
                    stock_code AS 주식코드
                FROM stock_data
                WHERE date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                """
            cursor.execute(sql)
            rows = cursor.fetchall()
            # print(f"[DEBUG] rows 개수: {len(rows)}")

            if not rows:
                print("[WARNING]DB에서 로드할 데이터가 없습니다.")
                return pd.DataFrame(columns=['종목명', '주식코드'])

            stock_list = pd.DataFrame(rows, columns=['종목명', '주식코드']) # 컬럼명 명시적으로 지정
            stock_list['종목명'] = stock_list['종목명'].astype(str).str.strip().str.upper()
            stock_list['주식코드'] = stock_list['주식코드'].astype(str).str.strip().str.upper()
            # 중복제거
            stock_list = stock_list.drop_duplicates(subset=['종목명', '주식코드'])

            # print(f"[DEBUG] stock_list 개수: {len(stock_list)}")  # ✅ 추가
            # print("[INFO] searching_stock_db의 데이터 로딩 시작")

            return stock_list

    except Exception as e:
        print(f"[ERROR] DB 데이터 로드 중 오류: {e}")
        return pd.DataFrame(columns=['종목명', '주식코드']) # 튜플이 아닌 DataFrame만 반환!

    finally:
        print(f"[INFO] stock_list의 데이터 로딩 시작")
        # print(f"stock_list : 총 {len(stock_list)}개의 데이터 포인트 로드")
        conn.close()


# 뉴스 관련 데이터 로딩
def news_data_db():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
           # 상황에 따라서 옵티마이저 힌트가 필요할 수 있음
            sql = """
            SELECT
                sd.stock_name AS 종목명,
                sd.stock_code AS 주식코드,
                sd.date AS 날짜,
                cn.title AS 제목,
                cn.link AS 링크,
                cn.content AS 본문
            FROM stock_data sd
            LEFT JOIN company_news cn
            ON sd.stock_name = cn.stock_name AND sd.date = cn.date
            WHERE sd.date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            # print(f"[DEBUG] rows 개수: {len(rows)}")

            if not rows:
                print("[WARNING]DB에서 로드할 데이터가 없습니다.")
                # return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜', '제목', '링크'])
                return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜', '제목', '링크', '본문'])

            news_data_df = pd.DataFrame(rows)
            news_data_df['날짜'] = pd.to_datetime(news_data_df['날짜'], errors='coerce')
            news_data_df.dropna(subset=['날짜'], inplace=True)
            news_data_df['종목명'] = news_data_df['종목명'].astype(str).str.strip().str.upper()
            return news_data_df

    except Exception as e:
        print(f"[ERROR] DB 데이터 로드 중 오류: {e}")
        # return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜', '제목', '링크'])
        return [], pd.DataFrame(columns=['종목명', '주식코드', '날짜', '제목', '링크', '본문'])

    finally:
        print("[INFO] news_data_db의 데이터 로딩 시작")
        # print(f"news_data_df : 총 {len(news_data_df)}개의 데이터 포인트 로드")
        conn.close()




# company_name를 stock_list를 활용하여 종목명이 아니라 종목코드 문자열이 나오도록 수정해야함
# 주식데이터와 뉴스 기사 추출(주식 분석 함수)
def analyze_stock_data(data_df, company_name):
    print(f"\n[DEBUG] '{company_name}' 종목 정보 추출 중...\n")

    search_company_name = company_name.strip().upper()
    stock_data = data_df[data_df['종목명'].str.upper() == search_company_name].copy()

    if stock_data.empty:
        print(f"[WARNING] '{company_name}'에 대한 데이터를 찾을 수 없습니다.")
        return {}

    stock_data = stock_data.sort_values(by='날짜')
    print(f"[INFO] '{company_name}' 종목의 데이터 ({len(stock_data)}개)를 찾았습니다.")

    # 주가 데이터 추출 (기존과 동일)
    stock_data['종가'] = pd.to_numeric(stock_data['종가'], errors='coerce')
    price_data = stock_data[['날짜', '종가']].dropna().to_dict(orient='records')
    for item in price_data:
        item['날짜'] = item['날짜'].strftime('%Y-%m-%d')

    if not price_data:
        print(f"[WARNING] '{company_name}' 종목의 유효한 주가 데이터가 없습니다.")

    # ⭐⭐⭐ 뉴스 데이터 추출 부분 수정 ⭐⭐⭐
    # 필터링된 stock_data에서 뉴스 관련 컬럼을 선택
    # 주의: LEFT JOIN으로 인해 뉴스가 없는 날짜도 포함될 수 있으므로, 제목이 있는 행만 선택
    filtered_news_articles = stock_data[['날짜', '제목', '링크']].dropna(subset=['제목', '링크']) \
                               .drop_duplicates(subset=['제목', '링크']) \
                               .sort_values(by='날짜', ascending=False)

    news_list = []
    if not filtered_news_articles.empty:
        for _, row in filtered_news_articles.head(10).iterrows(): # 상위 10개 기사만
            news_list.append({
                'date': row['날짜'].strftime('%Y-%m-%d'),
                'title': row['제목'],
                'link': row['링크']
            })
        print(f"[INFO] '{company_name}' 종목에 대한 총 {len(filtered_news_articles)}개의 기사 중 상위 10개 데이터 준비.")
    else:
        print(f"[WARNING] '{company_name}' 종목에 대한 뉴스 기사를 찾을 수 없습니다.")


    return {
        'price_data': price_data,
        'news_articles': news_list
    }



