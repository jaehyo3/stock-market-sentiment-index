document.addEventListener("DOMContentLoaded", () => {
    const chartDataElement = document.getElementById("priceChartData");
    if (!chartDataElement) return;

    const chartData = JSON.parse(chartDataElement.textContent);
    if (chartData.length === 0) return;

    const ctx = document.getElementById("priceChart").getContext("2d");
    const labels = chartData.map(item => item.date);
    const prices = chartData.map(item => item.close);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '종가',
                data: prices,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true },
                title: { display: true, text: '최근 10일 주가 추이' }
            },
            scales: {
                y: { beginAtZero: false }
            }
        }
    });
});
