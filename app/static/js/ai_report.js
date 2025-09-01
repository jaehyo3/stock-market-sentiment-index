let currentStockCode = null; // 현재 로드된 리포트의 종목 코드를 추적

/**
 * 특정 종목 코드를 받아 AI 리포트를 불러와 화면에 표시하는 함수
 * @param {string} stockCode - 조회할 종목의 코드 (예: '005930')
 */
async function fetchAiReportForStock(stockCode) {
    const aiReportContentDiv = document.getElementById('aiReportContent');

    if (!aiReportContentDiv) {
        console.warn("AI Report Content div (#aiReportContent)를 찾을 수 없습니다. AI 리포트를 로드할 수 없습니다.");
        return;
    }

    // ⭐⭐ 중복 생성 방지 및 새 종목 검색 시 초기화 로직 ⭐⭐
    if (currentStockCode === stockCode && aiReportContentDiv.dataset.reportLoaded === 'true') {
        console.log(`AI Report for ${stockCode} already loaded or loading.`);
        return;
    }
    currentStockCode = stockCode; // 현재 요청할 종목 코드를 저장
    aiReportContentDiv.dataset.reportLoaded = 'true'; // 로딩 시작 플래그

    // ⭐⭐⭐ 스크롤바 관리를 위한 초기 스타일 설정 ⭐⭐⭐
    // 로딩 시작과 동시에 스크롤바를 'auto'로 설정하여 내용이 넘치면 바로 스크롤 가능하게 함
    aiReportContentDiv.style.overflowY = 'auto'; // 'hidden' -> 'auto'로 수정
    aiReportContentDiv.style.maxHeight = '600px'; // 예시: 최대 높이 (원하는 높이로 조절)
    aiReportContentDiv.style.height = 'auto'; // 내용에 따라 자동으로 늘어나도록 (초기 높이 제한 없음)

    // 기존 내용 및 로딩 메시지/스피너 표시
    aiReportContentDiv.innerHTML = '<p style="text-align: center; color: #888;">AI 리포트를 불러오는 중입니다... <i class="fas fa-spinner fa-spin"></i></p>';

    // 이전에 추가된 해당 종목의 스타일 태그 제거 (중복 방지)
    const existingStyleTag = document.head.querySelector(`style[data-report-style="${stockCode}"]`);
    if (existingStyleTag) {
        existingStyleTag.remove();
    }

    try {
        const response = await fetch(`/api/ai_report?stock_code=${encodeURIComponent(stockCode)}`);
        const data = await response.json();

        if (data.success) {
            if (data.ai_report) {
                // 이 시점에는 로딩 스피너를 제거하지만, 내용을 바로 채우지 않습니다.
                aiReportContentDiv.innerHTML = '';

                // HTML 문자열을 파싱하여 DOM 요소로 변환
                const parser = new DOMParser();
                const doc = parser.parseFromString(data.ai_report, 'text/html');
                const reportContainer = doc.querySelector('.ai-report-container'); // 백엔드 템플릿의 최상위 div 선택

                if (reportContainer) {
                    // ⭐⭐⭐ <style> 태그 처리 ⭐⭐⭐
                    const styleTag = reportContainer.querySelector('style');
                    if (styleTag) {
                        const clonedStyle = styleTag.cloneNode(true);
                        clonedStyle.setAttribute('data-report-style', stockCode);
                        document.head.appendChild(clonedStyle);
                        styleTag.remove(); // 원본 reportContainer에서는 제거
                    }

                    // ⭐⭐⭐ 핵심 변경: 글자 단위 타이핑 효과 + 구조적 구분 유지 ⭐⭐⭐
                    const typingQueue = []; // 텍스트 덩어리들을 담을 배열

                    // HTML 요소를 텍스트 덩어리로 변환하여 큐에 추가하는 헬퍼 함수
                    const addElementContentToQueue = (element) => {
                        if (element && element.innerText.trim()) {
                            typingQueue.push(element.innerText.trim());
                            typingQueue.push('[BLANK_LINE_AFTER_BLOCK]'); // 블록 끝 구분자
                        }
                    };

                    // 1. 메인 제목과 부제목
                    const mainTitle = reportContainer.querySelector('.report-main-title');
                    const subTitle = reportContainer.querySelector('.report-sub-title');

                    addElementContentToQueue(mainTitle);
                    addElementContentToQueue(subTitle);

                    // 2. report-content-body 내부의 실제 컨텐츠 요소들을 처리
                    const reportContentBody = reportContainer.querySelector('.report-content-body');
                    if (reportContentBody) {
                        const contentChildren = Array.from(reportContentBody.children); // p, h3, h4, ul, ol 등
                        contentChildren.forEach((child) => {
                            addElementContentToQueue(child);
                        });
                    }

                    // 3. 푸터
                    const reportFooter = reportContainer.querySelector('.report-footer');
                    // 푸터는 마지막 요소이므로, 그 뒤에 추가적인 빈 줄 구분자를 넣지 않습니다.
                    if (reportFooter && reportFooter.innerText.trim()) {
                        typingQueue.push(reportFooter.innerText.trim());
                    }


                    let currentChunkIndex = 0;
                    let charIndexInChunk = 0;
                    const charDelay = 5; // 글자 간격 (밀리초)
                    const blockDelay = 600; // ⭐⭐ 블록/문단 사이의 추가 지연 (더 길게) ⭐⭐

                    // 타이핑 효과가 시작되기 전에 기본 텍스트 스타일을 설정
                    aiReportContentDiv.style.whiteSpace = 'pre-wrap'; // 원본 줄바꿈과 공백 유지
                    aiReportContentDiv.style.fontFamily = "'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif";
                    aiReportContentDiv.style.lineHeight = '1.6';
                    aiReportContentDiv.style.color = '#444'; // 기본 텍스트 색상
                    aiReportContentDiv.style.fontSize = '1.05em'; // 기본 폰트 크기
                    aiReportContentDiv.style.padding = '15px'; // aiReportContentDiv의 원래 패딩 유지


                    function typeEffect() {
                        if (currentChunkIndex < typingQueue.length) {
                            let currentChunk = typingQueue[currentChunkIndex];

                            if (currentChunk === '[BLANK_LINE_AFTER_BLOCK]') {
                                // ⭐⭐ 빈 줄 구분자 발견 시 <br><br> 삽입 후 다음 블록으로 이동 ⭐⭐
                                aiReportContentDiv.innerHTML += '<br><br>';
                                currentChunkIndex++;
                                charIndexInChunk = 0; // 다음 덩어리는 처음부터
                                setTimeout(typeEffect, blockDelay); // 블록 간 긴 지연
                                return; // 현재 함수 호출 종료
                            }

                            // 일반 텍스트 덩어리 타이핑
                            if (charIndexInChunk < currentChunk.length) {
                                const char = currentChunk.charAt(charIndexInChunk);
                                aiReportContentDiv.innerHTML += char;
                                charIndexInChunk++;
                                setTimeout(typeEffect, charDelay); // 글자 간 짧은 지연
                            } else {
                                // 현재 덩어리 타이핑 완료, 다음 덩어리로 이동
                                currentChunkIndex++;
                                charIndexInChunk = 0; // 다음 덩어리는 처음부터
                                // 덩어리 내 타이핑 완료 후 다음 덩어리 시작 전 약간의 지연 (필요시 조절)
                                setTimeout(typeEffect, charDelay * 5);
                            }
                        } else {
                            // 모든 덩어리 타이핑 완료
                            // ⭐⭐ 맨 마지막에 추가적인 빈 줄을 원하시면 여기에 <br><br> 추가 ⭐⭐
                            // aiReportContentDiv.innerHTML += '<br><br>'; // 이미 문단마다 <br><br> 들어가므로, 추가 필요하면 주석 해제

                        }
                    }

                    typeEffect(); // 타이핑 효과 시작

                } else {
                    // reportContainer를 찾지 못하면 (예: 백엔드에서 에러 메시지 HTML만 보낸 경우)
                    // 통째로 삽입하고 스크롤바 활성화
                    aiReportContentDiv.innerHTML = data.ai_report;
                    aiReportContentDiv.style.overflowY = 'auto';
                }

                // 리포트 제목이 있다면 섹션 제목도 업데이트
                const sectionTitle = document.querySelector('.ai-report-section .section-title');
                if (sectionTitle && data.report_title) {
                    sectionTitle.textContent = data.report_title;
                }
            } else {
                // data.ai_report가 비어있을 때 (백엔드에서 없는 리포트 메시지 HTML을 보냄)
                aiReportContentDiv.innerHTML = data.ai_report;
                aiReportContentDiv.style.overflowY = 'hidden'; // 내용이 없으면 스크롤 숨김
                const sectionTitle = document.querySelector('.ai-report-section .section-title');
                if (sectionTitle) {
                    sectionTitle.textContent = "AI 리포트"; // 제목 초기화
                }
            }
        } else {
            // API 호출은 성공했지만, 백엔드에서 success: false를 보냈을 때
            console.error("AI 리포트 API 오류:", data.error);
            aiReportContentDiv.innerHTML = `<p class="error-message">AI 리포트를 불러오는 데 실패했습니다: ${data.error}</p>`;
            aiReportContentDiv.style.overflowY = 'hidden';
        }

    } catch (error) {
        // 네트워크 오류 등 API 호출 자체가 실패했을 때
        console.error("AI 리포트 로딩 오류:", error);
        aiReportContentDiv.innerHTML = `<p class="error-message">AI 리포트를 불러오는 데 실패했습니다: ${error.message}</p>`;
        aiReportContentDiv.style.overflowY = 'hidden';
    } finally {
        // 이 finally 블록은 요청 시작 플래그를 관리하며, 요청 완료 후 추가적인 초기화는 search.html에서 담당
    }
}

// 이 함수는 window 객체에 등록하여 search.html 스크립트에서 접근할 수 있도록 합니다.
window.fetchAiReportForStock = fetchAiReportForStock;