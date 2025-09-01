# db.py
import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='12tlswogy',
        db='member_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# def get_news_connection():
#     return pymysql.connect(
#         host='192.168.0.12',
#         user='teamuser',
#         password='team1234!',
#         db='member_db',
#         charset='utf8mb4',
#         cursorclass=pymysql.cursors.DictCursor
#     )


# import pandas as pd
# import mysql.connector
# import re

# # CSV 파일 읽기
# df = pd.read_csv('data/finance/merged_new_stock.csv')

# # 날짜 포맷 변환: '20250625' → datetime
# df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')

# # '전일비' 컬럼 숫자만 추출하고 부호 적용 (하락 → 음수, 상승 → 양수)
# def parse_price_change(value):
#     if pd.isna(value):
#         return 0
#     value = str(value).strip()
#     if '하락' in value:
#         sign = -1
#     elif '상승' in value:
#         sign = 1
#     else:
#         sign = 0  # 보합 등
#     digits = re.sub(r'[^\d]', '', value)
#     try:
#         return sign * int(digits)
#     except:
#         return 0

# df['전일비'] = df['전일비'].apply(parse_price_change)

# # MySQL 연결 정보
# conn = mysql.connector.connect(
#     host='localhost',
#     user='root',
#     password='ezen',
#     database='member_db'
# )
# cursor = conn.cursor()

# # INSERT 실행
# for _, row in df.iterrows():
#     cursor.execute("""
#         INSERT INTO stock_news (
#             company_name, stock_code, date,
#             close_price, price_change, open_price, high_price, low_price, volume,
#             news_title, news_body, url, news_body_clean, news_body_noun
#         )
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """, (
#         row['회사명'],
#         row['주식코드'],
#         row['날짜'].date(),
#         int(row['종가']),
#         row['전일비'],
#         int(row['시가']),
#         int(row['고가']),
#         int(row['저가']),
#         int(row['거래량']),
#         row['뉴스제목'],
#         row['뉴스본문'],
#         row['링크'],
#         row['뉴스본문_전처리'],
#         row['뉴스본문_명사']
#     ))

# # 커밋 및 종료
# conn.commit()
# cursor.close()
# conn.close()

# print("✅ 데이터 삽입 완료!")

# print(f"총 {len(df)}건의 데이터를 삽입했습니다.")