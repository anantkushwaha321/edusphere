/**
 * EduSphere — UI Interaction Utilities
 * Clean, lightweight, event-driven JavaScript without continuous rendering loops.
 */

(function () {
    'use strict';

    // Mobile sidebar toggle helper
    document.addEventListener('DOMContentLoaded', () => {
        const openBtn = document.getElementById('openSidebarBtn');
        const closeBtn = document.getElementById('closeSidebarBtn');
        const sidebar = document.getElementById('sidebar');

        if (openBtn && sidebar) {
            openBtn.addEventListener('click', () => {
                sidebar.classList.remove('-translate-x-full');
            });
        }

        if (closeBtn && sidebar) {
            closeBtn.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
            });
        }
    });

})();
