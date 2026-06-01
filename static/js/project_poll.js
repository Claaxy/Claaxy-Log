(function () {
    const root = document.getElementById('project-root');
    if (!root) return;

    const statusUrl = root.dataset.statusUrl;
    const needsPoll = root.dataset.needsPoll === 'true';

    function isStillProcessing(data) {
        return (data.voice_notes || []).some(
            (note) => note.processing_status === 'pending' || note.processing_status === 'processing'
        );
    }

    function poll() {
        fetch(statusUrl, { headers: { Accept: 'application/json' } })
            .then((response) => response.json())
            .then((data) => {
                if (!isStillProcessing(data)) {
                    window.location.reload();
                }
            })
            .catch((err) => console.error('Poll failed', err));
    }

    if (needsPoll) {
        setInterval(poll, 5000);
    }
})();
