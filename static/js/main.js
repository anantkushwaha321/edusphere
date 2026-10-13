/**
 * IIMTMANIA — Core Main UI Interactions & Accessibility Handlers
 */

(function () {
    'use strict';

    // Helper: Obtain Django CSRF Cookie
    window.getCsrfToken = function() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    };

    // Helper: Show animated dynamic Toast / Alert banner
    window.showLiquidAlert = function(message, type = 'info', containerId = 'globalAlertBox') {
        const box = document.getElementById(containerId);
        if (!box) return;

        const textEl = box.querySelector('.alert-message') || box;
        const iconEl = box.querySelector('.alert-icon');

        box.className = 'glass-card p-4 text-xs font-semibold border transition-all duration-200 mb-4 block animate-fade-in';

        if (type === 'success') {
            box.style.borderColor = 'rgba(16, 185, 129, 0.4)';
            box.style.backgroundColor = 'rgba(16, 185, 129, 0.12)';
            box.style.color = '#A7F3D0';
            if (iconEl) iconEl.textContent = '✅';
        } else if (type === 'error') {
            box.style.borderColor = 'rgba(239, 68, 68, 0.4)';
            box.style.backgroundColor = 'rgba(239, 68, 68, 0.12)';
            box.style.color = '#FECACA';
            if (iconEl) iconEl.textContent = '⚠️';
        } else if (type === 'warning') {
            box.style.borderColor = 'rgba(245, 158, 11, 0.4)';
            box.style.backgroundColor = 'rgba(245, 158, 11, 0.12)';
            box.style.color = '#FDE68A';
            if (iconEl) iconEl.textContent = '🔔';
        } else {
            box.style.borderColor = 'rgba(59, 130, 246, 0.4)';
            box.style.backgroundColor = 'rgba(59, 130, 246, 0.12)';
            box.style.color = '#BFDBFE';
            if (iconEl) iconEl.textContent = 'ℹ️';
        }

        if (textEl) textEl.textContent = message;
        box.classList.remove('hidden');

        // Optional auto-dismiss after 6s
        setTimeout(() => {
            box.classList.add('hidden');
        }, 6000);
    };

    document.addEventListener('DOMContentLoaded', () => {
        // Mobile Sidebar Drawer
        const sidebar = document.getElementById('sidebar');
        const openBtn = document.getElementById('openSidebarBtn');
        const closeBtn = document.getElementById('closeSidebarBtn');

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

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (sidebar && !sidebar.classList.contains('-translate-x-full') && window.innerWidth < 768) {
                    sidebar.classList.add('-translate-x-full');
                }
                const openModals = document.querySelectorAll('.glass-modal:not(.hidden)');
                openModals.forEach(m => m.classList.add('hidden'));
            }
        });

        // Form Submit Buttons Tactile Feedback & Double-click Prevention
        const submitForms = document.querySelectorAll('form:not([data-no-loading])');
        submitForms.forEach(form => {
            form.addEventListener('submit', () => {
                const btn = form.querySelector('button[type="submit"]');
                if (btn && !btn.dataset.keepActive) {
                    const originalText = btn.innerHTML;
                    btn.setAttribute('data-original-text', originalText);
                    // Add subtle loading state without breaking layout
                    btn.classList.add('opacity-80', 'pointer-events-none');
                }
            });
        });
    });

})();
