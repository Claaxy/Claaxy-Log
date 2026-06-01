(function () {
    const list = document.querySelector('.dashboard-project-list');
    if (!list) return;

    const mobileQuery = window.matchMedia('(max-width: 991.98px)');
    const projectInput = document.getElementById('dashboard-selected-project');

    function isMobile() {
        return mobileQuery.matches;
    }

    function collapseAll(updateUrl) {
        list.querySelectorAll('.dashboard-project-entry').forEach((item) => {
            item.classList.remove('is-selected');
            item.querySelector('.dashboard-project-item')?.classList.remove('active');
            item.querySelector('.dashboard-project-expand')?.classList.add('d-none');
        });

        if (projectInput) {
            projectInput.value = '';
        }

        if (updateUrl) {
            const url = new URL(window.location.href);
            url.searchParams.delete('project');
            const query = url.searchParams.toString();
            window.history.replaceState(null, '', query ? `${url.pathname}?${query}` : url.pathname);
        }
    }

    function selectProject(entry, updateUrl) {
        if (!entry) return;

        list.querySelectorAll('.dashboard-project-entry').forEach((item) => {
            item.classList.remove('is-selected');
            item.querySelector('.dashboard-project-item')?.classList.remove('active');
            item.querySelector('.dashboard-project-expand')?.classList.add('d-none');
        });

        entry.classList.add('is-selected');
        entry.querySelector('.dashboard-project-item')?.classList.add('active');
        entry.querySelector('.dashboard-project-expand')?.classList.remove('d-none');

        const projectId = entry.dataset.projectId;
        if (projectInput && projectId) {
            projectInput.value = projectId;
        }

        if (updateUrl) {
            const link = entry.querySelector('.dashboard-project-item');
            if (link) {
                const url = new URL(link.href, window.location.origin);
                window.history.replaceState(null, '', url.pathname + url.search);
            }
        }
    }

    list.addEventListener('click', (event) => {
        if (!isMobile()) return;

        const link = event.target.closest('a.dashboard-project-item');
        if (!link || !list.contains(link)) return;

        event.preventDefault();

        const entry = link.closest('.dashboard-project-entry');
        if (entry.classList.contains('is-selected')) {
            collapseAll(true);
            return;
        }

        selectProject(entry, true);
    });

    mobileQuery.addEventListener('change', () => {
        if (!isMobile()) return;
        const selected = list.querySelector('.dashboard-project-entry.is-selected');
        if (selected) {
            selectProject(selected, false);
        }
    });

    if (isMobile() && window.location.search.includes('project=')) {
        const selected = list.querySelector('.dashboard-project-entry.is-selected');
        if (selected) {
            requestAnimationFrame(() => {
                selected.scrollIntoView({ block: 'nearest' });
            });
        }
    }
})();
