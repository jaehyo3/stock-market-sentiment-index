document.addEventListener("DOMContentLoaded", function() {
    // --- 인증번호 발송 버튼 ---
    const emailSendBtn = document.getElementById('email-send-btn');
    if (emailSendBtn) {
        emailSendBtn.onclick = function() {
            const emailInput = document.getElementById('signup-email');
            const email = emailInput ? emailInput.value.trim() : '';
            if (!email) {
                alert('이메일을 입력하세요!');
                return;
            }
            fetch('/send_email_code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.msg);
            });
        };
    }

    // --- 인증번호 확인 버튼 ---
    const verifyBtn = document.getElementById("email-verify-btn");
    if (verifyBtn) {
        verifyBtn.onclick = function() {
            const email = document.getElementById("signup-email").value.trim();
            const codeInput = document.getElementById("email-code");
            const code = codeInput.value.trim();
            const resultSpan = document.getElementById("email-verify-result");

            if (!email || !code) {
                resultSpan.textContent = "이메일과 인증번호를 모두 입력하세요.";
                resultSpan.style.color = "red";
                return;
            }

            fetch("/verify_email_code", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ email: email, code: code })
            })
            .then(res => res.json())
            .then(data => {
                if (data.result === "success") {
                    resultSpan.textContent = "인증 성공!";
                    resultSpan.style.color = "green";
                    verifyBtn.disabled = true;       // 확인 버튼 비활성화
                    codeInput.readOnly = true;       // 입력창 readOnly
                    codeInput.style.background = "#eee";
                    verifyBtn.textContent = "인증 완료";
                } else {
                    resultSpan.textContent = data.message;
                    resultSpan.style.color = "red";
                }
            })
            .catch(err => {
                resultSpan.textContent = "서버 오류가 발생했습니다.";
                resultSpan.style.color = "red";
            });
        };
    }
});
