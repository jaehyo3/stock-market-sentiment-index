# app/services/stock/chart_utils.py

from db import get_connection

# 각 종목별 최근 N일치 종가 데이터를 가져오는 공통 헬퍼 함수
def get_recent_stock_prices(stock_code, n=7):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # live_data 테이블에서 execution_price를 가져오도록 수정
            cursor.execute("""
                SELECT execution_price  -- close_price 대신 execution_price 사용
                FROM live_data          -- stock_data 대신 live_data 사용
                WHERE stock_code = %s
                ORDER BY date DESC, time DESC LIMIT %s
            """, (stock_code, n))
            rows = cursor.fetchall()
            # row['execution_price']로 접근하도록 변경
            return [row['execution_price'] for row in rows][::-1]
    finally:
        conn.close()

# 주가 데이터 리스트를 바탕으로 SVG 미니 차트 문자열을 생성하는 공통 함수
def generate_mini_chart_svg(prices, width=100, height=30):
    if not prices or len(prices) < 2:
        return f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}'><text x='50' y='15' font-size='10' fill='#aaa' text-anchor='middle' alignment-baseline='middle'>데이터 부족</text></svg>"

    padding_y = 5 # 상하 패딩을 주어 그래프가 너무 끝에 붙지 않게 함

    min_price = min(prices)
    max_price = max(prices)

    normalized_prices = []
    if min_price == max_price: # 모든 가격이 동일하면 중간에 일직선
        normalized_prices = [height / 2 for _ in prices]
    else:
        # 가격 데이터를 0에서 1 사이로 정규화한 후 SVG의 Y 좌표로 매핑 (SVG Y축은 상단이 0)
        # 높이 계산 시 패딩을 고려. min_price가 0이 아닌 경우 max_price - min_price가 0이 될 수 있으므로 0.01 더함 (나눗셈 오류 방지)
        range_price = (max_price - min_price) if (max_price - min_price) != 0 else 0.01
        for p in prices:
            normalized_y = height - padding_y - ((p - min_price) / range_price) * (height - 2 * padding_y)
            normalized_prices.append(normalized_y)

    # SVG Path 데이터 생성
    path_data = []
    num_points = len(prices)
    for i, y in enumerate(normalized_prices):
        # X 좌표 계산 (width를 num_points-1로 나누어 각 점 사이의 간격을 균등하게 배분)
        x = (i / (num_points - 1)) * width if num_points > 1 else width / 2 # num_points가 1개일 경우 방지
        if i == 0:
            path_data.append(f"M{x},{y}") # M은 'Move to' (시작점)
        else:
            path_data.append(f"L{x},{y}") # L은 'Line to' (이전 점에서 현재 점까지 선 그리기)

    # 그래프 색상 결정 (마지막 가격이 시작 가격보다 높으면 빨간색, 낮으면 파란색)
    stroke_color = '#888888' # 기본 회색 (데이터 부족 또는 변화 없을 때)
    if prices[-1] > prices[0]: # 마지막 가격이 첫 가격보다 높으면 상승 (빨간색)
        stroke_color = '#e53a3a'
    elif prices[-1] < prices[0]: # 마지막 가격이 첫 가격보다 낮으면 하락 (파란색)
        stroke_color = '#1976d2'

    # 최종 SVG 문자열 반환
    return f"<svg width='100%' height='{height}' viewBox='0 0 {width} {height}' preserveAspectRatio='none'><path d='{' '.join(path_data)}' fill='none' stroke='{stroke_color}' stroke-width='1.5'></path></svg>"