document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("stock_input");
    const codeInput = document.getElementById("stock_code");
    const suggestionsDiv = document.getElementById("suggestions");
    const form = document.getElementById("add-stock-form");
    const listUL = document.getElementById("prefer-stock-list");

    let selectedIndex = -1;

    // 자동완성 기능
    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        suggestionsDiv.innerHTML = '';
        if (!query) {
            suggestionsDiv.style.display = 'none';
            return;
        }
        const filtered = stockList.filter(obj =>
            obj.stock_name.toLowerCase().includes(query.toLowerCase()) ||
            obj.stock_code.toLowerCase().includes(query.toLowerCase())
        );
        if (filtered.length === 0) {
            suggestionsDiv.style.display = 'none';
            return;
        }
        filtered.forEach(obj => {
            const name = obj.stock_name;
            const code = obj.stock_code;
            const div = document.createElement('div');
            div.textContent = `${name}(${code})`;
            div.classList.add('autocomplete-item');
            div.style.cursor = "pointer";
            div.addEventListener('click', () => {
                input.value = name;
                codeInput.value = code;
                suggestionsDiv.innerHTML = '';
                suggestionsDiv.style.display = 'none';
            });
            suggestionsDiv.appendChild(div);
        });
        suggestionsDiv.style.display = 'block';
    });


    // 블러시 자동완성목록 닫기
    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.innerHTML = "";
            suggestionsDiv.style.display = "none";
            selectedIndex = -1;
        }
    });

    // 선호주식 추가 AJAX
    form.addEventListener("submit", function(e){
        e.preventDefault();
        const stockName = input.value.trim();
        const stockCode = codeInput.value.trim();
        if (!stockName || !stockCode) {
          alert("정확한 종목을 선택해 주세요.");
            return;
        }
        fetch(form.action, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            },
            body: "stock_input=" + encodeURIComponent(stockName) +
                  "&stock_code=" + encodeURIComponent(stockCode)
        })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                input.value = "";
                codeInput.value = "";
                renderStockList(data.stock_display);
            } else {
                alert(data.error || "등록에 실패했습니다.");
            }
        });
    });

    // 선호주식 삭제 AJAX
    listUL.addEventListener("click", function(e){
        if(e.target.classList.contains('delete-btn')){
            const li = e.target.closest('li');
            const stockcode = li.getAttribute('data-stock-code');
            fetch(`/prefer_stock/delete/${encodeURIComponent(stockcode)}`, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
            .then(res => res.json())
            .then(data => {
                if(data.success){
                    renderStockList(data.stock_display);
                } else {
                    alert("삭제에 실패했습니다.");
                }
            });
        }
    });

    // 선호주식 리스트 화면 갱신 함수
    function renderStockList(stockArr){
        listUL.innerHTML = "";
        if(!stockArr || stockArr.length === 0){
            listUL.innerHTML = "<li>등록된 선호 주식이 없습니다.</li>";
            return;
        }
        stockArr.forEach(stock => {
            const li = document.createElement('li');
            li.setAttribute("data-stock-name", stock.name);
            li.setAttribute("data-stock-code", stock.code);
            li.style = "display: flex; align-items: center; gap: 10px; margin-bottom: 10px;";

            const a = document.createElement('a');
            a.href = `/search?search=${encodeURIComponent(stock.name)}`;
            a.textContent = stock.name;
            a.style = "color: #007bff; text-decoration: none;";
            li.appendChild(a);

            const btn = document.createElement('button');
            btn.textContent = "삭제";
            btn.className = "delete-btn";
            btn.style = "background-color:#dc3545; color:white; border:none; border-radius:30px; padding:5px 10px; cursor:pointer;";
            li.appendChild(btn);

            listUL.appendChild(li);
        });
    }

    // 키보드 ↑↓ 선택 및 Enter 처리
    input.addEventListener("keydown", (e) => {
        const items = suggestionsDiv.querySelectorAll(".autocomplete-item");
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
            if (selectedIndex >= 0 && selectedIndex < items.length) {
                e.preventDefault();
                const selected = items[selectedIndex];
                const text = selected.textContent;
                const match = text.match(/(.*)\((\d+)\)/);
                if (match) {
                    input.value = match[1];
                    codeInput.value = match[2];
                }
                suggestionsDiv.innerHTML = "";
                suggestionsDiv.style.display = "none";
            }
        }
    });

    // focus 벗어나면 추천 닫기
    function updateSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.style.backgroundColor = "#e0e0e0";
            } else {
                item.style.backgroundColor = "";
            }
        });
    }


});