// ----------------------------------------------------------------------
// Global Functions (setupAutocomplete 외부에 정의하여 전역적으로 사용 가능)
// ----------------------------------------------------------------------

// 관심주 목록 갱신 함수 (초기 렌더링 및 AJAX 업데이트 시 사용)
function renderStockList(stockArr) {
    const tableBody = document.querySelector(".fav-table tbody");
    if (!tableBody) {
        console.warn("renderStockList: 테이블 body 요소를 찾을 수 없습니다.");
        return;
    }
    tableBody.innerHTML = '';

    if (!stockArr || stockArr.length === 0) {
        const noStockRow = document.createElement("tr");
        noStockRow.innerHTML = `<td colspan="6" style="color:#aaa;">관심주가 없습니다.</td>`; // colspan 6으로 변경
        tableBody.appendChild(noStockRow);
        return;
    }

    stockArr.forEach(stock => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><b>${stock.name}</b><br><span style="font-size:0.96em;color:#bbb;">(${stock.code})</span></td>
            <td class="mini-chart-cell">
                <div class="mini-chart-svg-container"></div> <!-- SVG를 삽입할 컨테이너 -->
            </td>
            <td>${stock.price}원</td>
            <td>
              <span class="${stock.change_color_class}">
                ${stock.price_change_amount}
              </span>
            </td>
            <td>${stock.volume}</td>
            <td>
                <button onclick="showStockDetail('${stock.code}', '${stock.name}')" style="padding:4px 13px; background:#1673e9; color:#fff; border:none; border-radius:7px; font-size:0.98em; cursor:pointer; margin-right: 5px;">상세보기</button>
                <button onclick="deleteStock('${stock.code}')" style="padding:4px 13px; background:#e13c3c; color:#fff; border:none; border-radius:7px; font-size:0.98em; cursor:pointer;">삭제</button>
            </td>

        `;
        tableBody.appendChild(row);

        // 💡 미니차트 SVG 삽입 로직
        const miniChartSvgContainer = row.querySelector('.mini-chart-svg-container');
        if (miniChartSvgContainer && stock.mini_chart_svg) {
            miniChartSvgContainer.innerHTML = stock.mini_chart_svg;
        } else if (miniChartSvgContainer) {
            miniChartSvgContainer.innerHTML = '<span style="color:#aaa; font-size:0.8em;">데이터 부족</span>';
        }
    });
}

// 관심주 삭제 처리 함수 (HTML onclick 및 renderStockList 내부에서 사용)
function deleteStock(stockCode) {
    if (!confirm("정말로 이 종목을 관심주에서 삭제하시겠습니까?")) {
        return;
    }
    fetch(`/prefer_stock/delete/${stockCode}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("선호 주식이 삭제되었습니다.");
            renderStockList(data.stock_display);
            // 삭제 후 상세 패널이 해당 종목을 보여주고 있었다면 숨김
            const detailPanel = document.getElementById('stockDetailPanel');
            // detailStockName이 존재하고, 그 안에 삭제된 종목 코드가 포함되어 있다면 숨김
            if (detailPanel.style.display === 'block' && detailPanel.querySelector('#detailStockName')?.innerText.includes(`(${stockCode})`)) {
                 hideStockDetail(); // 상세 패널 숨기기 함수 호출
            }
        } else {
            console.error("삭제 오류:", data.error);
            alert("삭제에 실패했습니다: " + (data.error || "알 수 없는 오류"));
        }
    })
    .catch(err => {
        console.error("삭제 중 네트워크 오류:", err);
        alert("삭제 중 네트워크 오류가 발생했습니다.");
    });
}


// ----------------------------------------------------------------------
// Autocomplete Setup Function
// ----------------------------------------------------------------------

function setupAutocomplete(inputId, listId, apiUrl) {
    const searchInput = document.getElementById(inputId);
    const codeInput = document.getElementById("stock_code");
    const list = document.getElementById(listId);
    const form = document.getElementById('add-stock-form');
    const addStockButton = document.getElementById("addStockButton");

    if (!searchInput || !codeInput || !list || !form || !addStockButton) {
        console.error("Critical: 자동완성 설정에 필요한 요소가 하나 이상 누락되었습니다.");
        return;
    }
    console.log("[DEBUG] setupAutocomplete 정상 실행 완료."); // 디버깅용 메시지는 유지

    let selectedIndex = -1;
    let suggestions = [];

    // --- 관심주 추가를 위한 공통 제출 함수 ---
    async function submitStockForm() {
        const stockCode = codeInput.value.trim();
        // console.log("[DEBUG] submitStockForm 호출됨. current stock_code:", stockCode); // 운영에서는 필요 없으므로 제거

        if (!stockCode) {
            alert("유효한 종목을 선택하거나 입력해 주세요.");
            return;
        }

        try {
            const res = await fetch(form.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: `stock_code=${encodeURIComponent(stockCode)}`
            });
            const data = await res.json();

            if (data.success) {
                alert("관심주가 성공적으로 추가되었습니다.");
                renderStockList(data.stock_display);
                searchInput.value = "";
                codeInput.value = "";
            } else {
                console.error("관심주 등록 오류:", data.error);
                alert(data.error || "관심주 등록에 실패했습니다.");
            }
        } catch (err) {
            console.error("관심주 등록 중 네트워크 오류:", err);
            alert("관심주 등록 중 오류가 발생했습니다. 콘솔을 확인하세요.");
        }
    }

    // --- 이벤트 핸들러 바인딩 ---

    // '추가' 버튼 클릭 시 submitStockForm 호출
    // addEventListener를 사용하고, 이전 리스너를 명시적으로 제거하여 중복 문제를 확실히 방지
    // (setupAutocomplete 함수가 여러 번 호출될 수 있는 경우를 대비)
    addStockButton.removeEventListener('click', addStockButton._clickHandler);
    addStockButton._clickHandler = function(event) {
        // console.log("[DEBUG] '추가' button clicked. Calling submitStockForm."); // 운영에서는 필요 없으므로 제거
        submitStockForm();
    };
    addStockButton.addEventListener('click', addStockButton._clickHandler);


    // 자동완성 입력 이벤트: Debounce 적용
    // 실제 검색 요청을 보낼 함수를 정의
    const fetchSuggestions = async () => {
        const query = searchInput.value.trim();
        list.innerHTML = "";
        selectedIndex = -1;
        codeInput.value = "";

        if (!query) return;

        try {
            const res = await fetch(`${apiUrl}?query=${encodeURIComponent(query)}`);
            suggestions = await res.json();

            if (suggestions.length === 0) {
                const noResultDiv = document.createElement("div");
                noResultDiv.className = "autocomplete-item";
                noResultDiv.textContent = "검색 결과가 없습니다.";
                list.appendChild(noResultDiv);
            } else {
                suggestions.forEach((item, index) => {
                    const div = document.createElement("div");
                    div.className = "autocomplete-item";
                    div.dataset.index = index;
                    div.textContent = `${item.종목명} (${String(item.주식코드).padStart(6, '0')})`;
                    list.appendChild(div);
                });
            }
        } catch (err) {
            console.error("자동완성 요청 오류:", err);
        }
    };

    // Debounce된 함수를 생성하여 이벤트 리스너에 할당 (layout.html에 정의된 debounce 함수를 사용)
    searchInput._oninputHandler = debounce(fetchSuggestions, 300); // 300ms 지연 시간
    searchInput.removeEventListener('input', searchInput._oninputHandler);
    searchInput.addEventListener('input', searchInput._oninputHandler);


    // 클릭 이벤트 처리 - 추천 항목 클릭 시
    list.removeEventListener('click', list._onclickHandler);
    list._onclickHandler = (e) => {
        const target = e.target;
        if (target.classList.contains("autocomplete-item")) {
            const idx = Number(target.dataset.index);
            if (isNaN(idx) || !suggestions[idx]) {
                console.warn("[DEBUG] 클릭된 idx가 잘못됨 또는 item이 없음:", idx, suggestions);
                return;
            }
            const item = suggestions[idx];
            searchInput.value = item.종목명 ?? "";
            codeInput.value = (item.주식코드 ?? "").padStart(6, '0');
            // console.log("[DEBUG] 클릭 선택: 종목명:", item.종목명, " 종목코드:", codeInput.value); // 운영에서는 필요 없으므로 제거
            list.innerHTML = "";
            submitStockForm();
        }
    };
    list.addEventListener('click', list._onclickHandler);


    // 키보드 방향키 및 Enter 처리
    searchInput.removeEventListener('keydown', searchInput._onkeydownHandler);
    searchInput._onkeydownHandler = (e) => {
        const items = list.querySelectorAll(".autocomplete-item");
        if (items.length === 0) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            selectedIndex = (selectedIndex + 1) % items.length;
            updateSelection(items);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            selectedIndex = (selectedIndex - 1 + items.length) % items.length;
            updateSelection(items);
        } else if (e.key === "Enter") {
            if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
                e.preventDefault();
                const selected = suggestions[selectedIndex];
                if (!selected) {
                    console.warn("[DEBUG] 엔터: 선택된 suggestion 없음");
                    return;
                }
                searchInput.value = selected.종목명 ?? "";
                codeInput.value = (selected.주식코드 ?? "").padStart(6, '0');
                // console.log("[DEBUG] 엔터 선택: 종목명:", selected.종목명, " 종목코드:", codeInput.value); // 운영에서는 필요 없으므로 제거
                list.innerHTML = "";
                submitStockForm();
            } else if (searchInput.value.trim() !== "" && codeInput.value.trim() !== "") {
                e.preventDefault();
                submitStockForm();
            }
        }
    };
    searchInput.addEventListener('keydown', searchInput._onkeydownHandler);


    // 선택된 항목 강조 처리
    function updateSelection(items) {
        items.forEach((item, index) => {
            item.style.backgroundColor = (index === selectedIndex) ? "#eee" : "";
        });
    }

    // 클릭 영역 밖 클릭 시 자동완성 목록 닫기
    document.removeEventListener("mousedown", document._autocompleteMousedownHandler);
    document._autocompleteMousedownHandler = (e) => {
        if (!searchInput.contains(e.target) && !list.contains(e.target)) {
            list.innerHTML = "";
            selectedIndex = -1;
        }
    };
    document.addEventListener("mousedown", document._autocompleteMousedownHandler);
}


// ----------------------------------------------------------------------
// 상세 정보 패널 관련 Global Functions
// ----------------------------------------------------------------------

let currentSelectedRow = null;
let myDetailChart = null; // Chart.js 인스턴스를 저장할 전역 변수

// 상세 패널 보이기 및 데이터 로드 함수
async function showStockDetail(stockCode, stockName) {
    // 1. UI 초기화 및 패널 보이기
    const stockDetailPanel = document.getElementById('stockDetailPanel');
    const noStockSelectedMessage = document.getElementById('noStockSelectedMessage');
    const favTableBody = document.querySelector(".fav-table tbody");

    // 이전 선택된 행의 하이라이트 제거
    if (currentSelectedRow) {
        currentSelectedRow.classList.remove('selected');
    }

    // 현재 클릭된 버튼의 부모 <tr> 찾아서 하이라이트
    const allButtons = favTableBody.querySelectorAll('button[onclick^="showStockDetail("]');
    let targetRow = null;
    for (let i = 0; i < allButtons.length; i++) {
        if (allButtons[i].onclick.toString().includes(`'${stockCode}'`)) {
            targetRow = allButtons[i].closest('tr');
            break;
        }
    }

    if (targetRow) {
        targetRow.classList.add('selected');
        currentSelectedRow = targetRow;
    }

    stockDetailPanel.style.display = 'block';
    noStockSelectedMessage.style.display = 'none';

    // 로딩 상태 표시
    document.getElementById('detailStockName').innerText = `${stockName} (${stockCode})`;
    document.getElementById('detailPrice').innerText = '...';
    document.getElementById('detailPercentageChange').innerText = '...';
    document.getElementById('detailSignal').innerText = '...';
    document.getElementById('detailVolume').innerText = '...';
    document.getElementById('detailNewsList').innerHTML = '<p>뉴스를 불러오는 중...</p>';

    // 차트 초기화 (기존 차트 인스턴스가 있다면 파괴)
    if (myDetailChart) {
        myDetailChart.destroy();
        myDetailChart = null; // 참조 해제
        document.getElementById('detailChartContainer').innerHTML = '<canvas id="detailStockChart"></canvas>';
    }

    try {
        // 2. 백엔드 API 호출
        const response = await fetch(`/api/stock_detail/${stockCode}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '상세 정보를 불러오는데 실패했습니다.');
        }
        const data = await response.json();

        if (data.success && data.detail) {
            const detail = data.detail;

            // 3. 받아온 데이터로 UI 업데이트
            document.getElementById('detailStockName').innerText = `${detail.name} (${detail.code})`;
            document.getElementById('detailPrice').innerText = `${detail.price.toLocaleString()}`;

            const percentageChangeDisplay = (detail.percentage_change !== null && detail.percentage_change !== undefined) ? `${detail.percentage_change.toFixed(2)}%` : 'N/A';
            document.getElementById('detailPercentageChange').innerHTML = `<span class="${detail.change_color_class}">${detail.change_icon}${Math.abs(detail.price_change).toLocaleString()}원 (${percentageChangeDisplay})</span>`;
            document.getElementById('detailSignal').innerText = detail.signal || '데이터 없음';
            document.getElementById('detailVolume').innerText = `${detail.volume.toLocaleString()}`;

            // 뉴스 목록 업데이트 (수정된 부분)
            const newsListElem = document.getElementById('detailNewsList');
            if (detail.news && detail.news.length > 0) {
                newsListElem.innerHTML = '<h4 class="detail-title" style="margin-top:20px;">주요 뉴스</h4><ul class="news-list">' +
                                         detail.news.map(newsItem => `<li><a href="${newsItem.link}" target="_blank" style="text-decoration: none; color: inherit;">${newsItem.title}</a></li>`).join('') +
                                         '</ul>';
            } else {
                newsListElem.innerHTML = '<p>관련 뉴스가 없습니다.</p>';
            }

            // '이 종목 삭제' 버튼의 onclick 속성 업데이트
            document.getElementById('deleteStockFromDetailButton').onclick = () => deleteStockFromDetailPanel(stockCode);

            // 4. 차트 그리기 (Chart.js 사용)
            if (detail.chart_data && detail.chart_data.length > 0) {
                const ctx = document.getElementById('detailStockChart').getContext('2d');
                const labels = Array.from({length: detail.chart_data.length}, (_, i) => `Day ${i + 1}`);
                const borderColor = detail.chart_data[detail.chart_data.length - 1] > detail.chart_data[0] ? '#e53a3a' : '#1976d2';

                myDetailChart = new Chart(ctx, { // 전역 변수에 할당
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: '종가',
                            data: detail.chart_data,
                            borderColor: borderColor,
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false,
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: { enabled: true }
                        },
                        scales: {
                            x: { display: false },
                            y: { display: false }
                        }
                    }
                });
            } else {
                document.getElementById('detailChartContainer').innerHTML = '<p style="text-align:center; color:#aaa; font-size:0.9em; margin-top:20px;">차트 데이터가 부족합니다.</p>';
            }

        } else {
            alert(data.error || '상세 정보를 불러올 수 없습니다.');
            hideStockDetail();
        }

    } catch (error) {
        console.error("상세 정보 로드 오류:", error);
        alert("상세 정보를 불러오는 중 오류가 발생했습니다: " + error.message);
        hideStockDetail();
    }
}

// 상세 패널 숨기기 함수
function hideStockDetail() {
    document.getElementById('stockDetailPanel').style.display = 'none';
    document.getElementById('noStockSelectedMessage').style.display = 'flex';

    if (myDetailChart) {
        myDetailChart.destroy();
        myDetailChart = null;
        document.getElementById('detailChartContainer').innerHTML = '<canvas id="detailStockChart"></canvas>';
    }

    if (currentSelectedRow) {
        currentSelectedRow.classList.remove('selected');
        currentSelectedRow = null;
    }
}

// 상세 패널에서 삭제 버튼 클릭 시 호출될 함수
function deleteStockFromDetailPanel(stockCode) {
    deleteStock(stockCode);
    // deleteStock 함수에서 목록 갱신 후 상세 패널 숨김 로직이 포함되어 있습니다.
}