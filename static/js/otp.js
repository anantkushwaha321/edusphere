/**
 * IIMTMANIA — Reusable OTP Input & Countdown Controller
 */

window.initOtpFieldHandlers = function(options = {}) {
    const selector = options.selector || '.otp-digit';
    const digitInputs = document.querySelectorAll(selector);
    if (!digitInputs.length) return;

    digitInputs.forEach((input, index) => {
        // Input number handling & auto-advance
        input.addEventListener('input', (e) => {
            const val = e.target.value.replace(/\D/g, '');
            e.target.value = val ? val[0] : '';
            if (val && index < digitInputs.length - 1) {
                digitInputs[index + 1].focus();
            }
        });

        // Backspace handling
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                digitInputs[index - 1].focus();
            }
        });

        // Full 6-digit paste handling
        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pasteData = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
            if (pasteData.length >= 6) {
                for (let i = 0; i < 6; i++) {
                    if (digitInputs[i]) {
                        digitInputs[i].value = pasteData[i];
                    }
                }
                digitInputs[Math.min(5, digitInputs.length - 1)].focus();
                if (typeof options.onComplete === 'function') {
                    options.onComplete(pasteData.slice(0, 6));
                }
            }
        });
    });
};

// Helper: Extract entered 6-digit string
window.getEnteredOtpCode = function(selector = '.otp-digit') {
    let code = '';
    document.querySelectorAll(selector).forEach(el => {
        code += el.value.trim();
    });
    return code;
};
