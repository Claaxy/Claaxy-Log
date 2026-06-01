(function () {
    const startBtn = document.getElementById('btn-start');
    const stopBtn = document.getElementById('btn-stop');
    const uploadForm = document.getElementById('upload-form');
    const audioInput = document.getElementById('audio-input');
    const recDot = document.getElementById('rec-dot');
    const recTimer = document.getElementById('rec-timer');

    if (!startBtn || !stopBtn) return;

    let mediaRecorder = null;
    let chunks = [];
    let timerInterval = null;
    let seconds = 0;

    function formatTime(total) {
        const m = String(Math.floor(total / 60)).padStart(2, '0');
        const s = String(total % 60).padStart(2, '0');
        return `${m}:${s}`;
    }

    function resetTimer() {
        clearInterval(timerInterval);
        timerInterval = null;
        seconds = 0;
        recTimer.textContent = '00:00';
        recDot.classList.add('d-none');
    }

    startBtn.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            chunks = [];
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) chunks.push(event.data);
            };
            mediaRecorder.onstop = () => {
                stream.getTracks().forEach((track) => track.stop());
                const blob = new Blob(chunks, { type: 'audio/webm' });
                const file = new File([blob], 'recording.webm', { type: 'audio/webm' });
                const dt = new DataTransfer();
                dt.items.add(file);
                audioInput.files = dt.files;
                uploadForm.submit();
            };
            mediaRecorder.start();
            startBtn.disabled = true;
            stopBtn.disabled = false;
            recDot.classList.remove('d-none');
            timerInterval = setInterval(() => {
                seconds += 1;
                recTimer.textContent = formatTime(seconds);
            }, 1000);
        } catch (err) {
            alert('Microphone access denied or unavailable.');
            console.error(err);
        }
    });

    stopBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            stopBtn.disabled = true;
            stopBtn.textContent = 'Uploading…';
            mediaRecorder.stop();
            resetTimer();
        }
    });
})();
