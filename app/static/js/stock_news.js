document.addEventListener('DOMContentLoaded', () => {
    const newsListContainer = document.getElementById('news-list');

    /**
     * 특정 종목에 대한 뉴스 기사를 API에서 가져와 화면에 표시합니다.
     */
    window.fetchNewsForStock = async function(companyName) {
        newsListContainer.innerHTML = '<p>뉴스 기사를 불러오는 중...</p>';

        if (!companyName) {
            newsListContainer.innerHTML = '<p>종목명을 입력해주세요.</p>';
            return;
        }

        try {
            const response = await fetch(`/api/news?company_name=${encodeURIComponent(companyName)}`);
            const data = await response.json();

            if (!response.ok) {
                newsListContainer.innerHTML = `<p class="error-message">뉴스 데이터를 불러오는 데 실패했습니다: ${data.error || '알 수 없는 오류'}</p>`;
                return;
            }

            displayNewsArticles(data.news_articles);

        } catch (error) {
            console.error('Fetch news error:', error);
            newsListContainer.innerHTML = '<p class="error-message">서버 통신 중 뉴스 데이터를 불러오는 데 오류가 발생했습니다.</p>';
        }
    };

    /**
     * 뉴스 기사 목록을 HTML에 표시합니다.
     */
    function displayNewsArticles(newsArticles) {
        newsListContainer.innerHTML = '';

        if (!newsArticles || newsArticles.length === 0) {
            newsListContainer.innerHTML = '<p>해당 종목에 대한 뉴스 기사를 찾을 수 없습니다.</p>';
            return;
        }

        const ul = document.createElement('ul');
        newsArticles.forEach(article => {
            const li = document.createElement('li');
            li.classList.add('news-article');

            // ==============================================================================
            // ⭐ [최종 수정] 날짜 형식 변경, null 처리, 링크 기능 추가
            // ==============================================================================

            // 1. 날짜 형식을 'YYYY-MM-DD'로 변경합니다.
            const date = new Date(article.날짜);
            const formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

            // 2. 제목이 null이거나 비어있으면 "제목 없음"으로 표시합니다.
            const title = article.제목 || "제목 없음";

            // 3. 링크가 있는 경우에만 a 태그로 감싸고, 없으면 그냥 제목만 표시합니다.
            const link = article.링크;
            const titleElement = link ? `<a href="${link}" target="_blank">${title}</a>` : title;

            li.innerHTML = `
                <p><strong>날짜:</strong> ${formattedDate}</p>
                <p><strong>제목:</strong> ${titleElement}</p>
            `;
            ul.appendChild(li);
        });
        newsListContainer.appendChild(ul);
    }
});