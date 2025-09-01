document.addEventListener('DOMContentLoaded', function () {
    const priceChartDataContainer = document.getElementById('priceChartDataContainer');
    const chartContainer = document.getElementById('chart-container');

    if (!priceChartDataContainer) {
        console.warn("priceChartDataContainer div를 찾을 수 없습니다. 차트 데이터를 로드할 수 없습니다.");
        return;
    }

    const priceChartDataJson = priceChartDataContainer.dataset.chartData;
    const stockNameForChart = priceChartDataContainer.dataset.stockName;

    if (!priceChartDataJson) {
        console.log("No price chart data available.");
        if (chartContainer) {
            chartContainer.innerHTML = '<p>해당 종목의 유효한 주가 데이터를 찾을 수 없습니다.</p>';
        }
        return;
    }

    let data = [];
    try {
        data = JSON.parse(priceChartDataJson);
    } catch (e) {
        console.error("차트 데이터 파싱 오류:", e);
        if (chartContainer) {
            chartContainer.innerHTML = '<p>주가 데이터 형식이 올바르지 않습니다.</p>';
        }
        return;
    }

    // 날짜 정렬 (오름차순: 오래된 날짜부터)
    data.sort((a, b) => new Date(a['날짜']) - new Date(b['날짜']));

    // 최근 30일 데이터 필터링
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);

    const filteredData = data.filter(item => {
        const date = new Date(item['날짜']);
        return date >= thirtyDaysAgo && date <= today;
    });

    if (!Array.isArray(filteredData) || filteredData.length < 2) {
        console.log("Too few price data points to render chart.");
        if (chartContainer) {
            chartContainer.innerHTML = '<p>해당 종목의 주가 데이터가 너무 적습니다.</p>';
        }
        return;
    }

    // 📌 빠진 날짜 보간 (forward fill)
    const filledData = forwardFillMissingDates(filteredData);

    // 차트용 데이터 추출
    const labels = filledData.map(item => item['날짜']);
    const prices = filledData.map(item => item['종가']);

    const ctx = document.getElementById('stockChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${stockNameForChart} 주가`,
                data: prices,
                borderColor: 'rgb(75, 192, 192)',
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        tooltipFormat: 'yyyy-MM-dd',
                        displayFormats: {
                            month: 'yyyy년 MM월'
                        }
                    },
                    title: {
                        display: true,
                        text: '날짜'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '종가 (원)'
                    },
                    ticks: {
                        callback: function (value) {
                            return value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function (context) {
                            return context[0].label;
                        },
                        label: function (context) {
                            return `종가: ${context.raw.toLocaleString()}원`;
                        }
                    }
                }
            }
        }
    });
});

/**
 * 📌 누락된 날짜를 이전 값으로 보간해주는 함수
 */
function forwardFillMissingDates(data) {
    const filledData = [];
    let lastValue = null;

    // 날짜 정렬
    data.sort((a, b) => new Date(a['날짜']) - new Date(b['날짜']));

    // 날짜 => 종가 맵핑
    const dateMap = {};
    data.forEach(item => {
        dateMap[item['날짜']] = item['종가'];
    });

    const startDate = new Date(data[0]['날짜']);
    const endDate = new Date(data[data.length - 1]['날짜']);

    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        if (dateMap.hasOwnProperty(dateStr)) {
            lastValue = dateMap[dateStr];
        }
        if (lastValue !== null) {
            filledData.push({ 날짜: dateStr, 종가: lastValue });
        }
    }

    return filledData;
}