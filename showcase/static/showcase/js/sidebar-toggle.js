// Sidebar Toggle Functionality

document.addEventListener('DOMContentLoaded', function() {
    initSidebarToggle();
});

function initSidebarToggle() {
    const toggleButton = document.getElementById('sidebar-toggle');
    const body = document.body;

    if (!toggleButton) return;

    // Add click handler for sidebar toggle
    toggleButton.addEventListener('click', function(e) {
        e.preventDefault();
        toggleSidebar();
    });

    // Load saved state from localStorage
    loadSidebarState();

    // Add keyboard shortcut (Ctrl/Cmd + B)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            toggleSidebar();
        }
    });
}

function toggleSidebar() {
    const body = document.body;
    const isHidden = body.classList.contains('sidebar-hidden');

    if (isHidden) {
        // Show sidebar
        body.classList.remove('sidebar-hidden');
        saveSidebarState(false);
    } else {
        // Hide sidebar
        body.classList.add('sidebar-hidden');
        saveSidebarState(true);
    }
}

function saveSidebarState(isHidden) {
    try {
        localStorage.setItem('sidebarHidden', JSON.stringify(isHidden));
    } catch (e) {
        // localStorage not available
    }
}

function loadSidebarState() {
    try {
        const isHidden = JSON.parse(localStorage.getItem('sidebarHidden'));
        if (isHidden === true) {
            document.body.classList.add('sidebar-hidden');
        }
    } catch (e) {
        // localStorage not available or invalid data
    }
}