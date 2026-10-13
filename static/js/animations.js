/**
 * IIMTMANIA — Animation Engine & Background Orchestrator
 */

(function () {
    'use strict';

    // 1. Page Entrance Transition Trigger
    document.addEventListener('DOMContentLoaded', () => {
        const transitionWrappers = document.querySelectorAll('.page-transition');
        transitionWrappers.forEach(el => {
            requestAnimationFrame(() => {
                el.classList.add('page-active');
            });
        });

        // 2. Setup Scroll Reveals using single shared IntersectionObserver
        setupScrollObserver();

        // 3. Setup Spotlight Cards (Pointer-reactive glass reflection)
        setupSpotlightCards();

        // 4. Setup Animated Particle Canvas Background
        setupParticleCanvas();
    });

    // IntersectionObserver for Scroll Reveals
    function setupScrollObserver() {
        const revealElements = document.querySelectorAll('.reveal-on-scroll');
        if (!revealElements.length) return;

        if (!('IntersectionObserver' in window)) {
            revealElements.forEach(el => el.classList.add('is-revealed'));
            return;
        }

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-revealed');
                    obs.unobserve(entry.target); // One-time reveal by default
                }
            });
        }, {
            threshold: 0.12,
            rootMargin: '0px 0px -40px 0px'
        });

        revealElements.forEach(el => observer.observe(el));
    }

    // Pointer-reactive lighting on cards
    function setupSpotlightCards() {
        if (window.matchMedia('(hover: hover)').matches) {
            document.addEventListener('mousemove', (e) => {
                const target = e.target.closest('.spotlight-card, .glass-card');
                if (target) {
                    const rect = target.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    target.style.setProperty('--mouse-x', `${x}px`);
                    target.style.setProperty('--mouse-y', `${y}px`);
                }
            }, { passive: true });
        }
    }

    // Particle Canvas Background
    function setupParticleCanvas() {
        const canvas = document.getElementById('ambientCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;
        let animationFrameId = null;
        let isTabActive = true;

        // Create light ambient particle nodes
        const particleCount = window.innerWidth < 768 ? 20 : 45;
        const particles = [];
        const colors = [
            'rgba(59, 130, 246, 0.45)', // Electric Blue
            'rgba(139, 92, 246, 0.40)', // Violet
            'rgba(34, 211, 238, 0.35)',  // Cyan
            'rgba(255, 255, 255, 0.25)'  // White
        ];

        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                radius: Math.random() * 2.2 + 0.8,
                color: colors[Math.floor(Math.random() * colors.length)],
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                pulse: Math.random() * Math.PI,
                pulseSpeed: 0.02 + Math.random() * 0.02
            });
        }

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize, { passive: true });

        function draw() {
            if (!isTabActive) return;

            ctx.clearRect(0, 0, width, height);

            // Draw glowing soft particles
            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;
                p.pulse += p.pulseSpeed;

                // Screen boundaries bounce
                if (p.x < 0 || p.x > width) p.vx *= -1;
                if (p.y < 0 || p.y > height) p.vy *= -1;

                const currentRadius = p.radius + Math.sin(p.pulse) * 0.5;

                ctx.beginPath();
                ctx.arc(p.x, p.y, Math.max(0.5, currentRadius), 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.shadowBlur = 10;
                ctx.shadowColor = p.color;
                ctx.fill();
            }

            animationFrameId = requestAnimationFrame(draw);
        }

        // Pause animation when tab is in background to save CPU/GPU resources
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                isTabActive = false;
                if (animationFrameId) cancelAnimationFrame(animationFrameId);
            } else {
                isTabActive = true;
                animationFrameId = requestAnimationFrame(draw);
            }
        });

        // Respect reduced motion
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        if (!prefersReducedMotion.matches) {
            draw();
        }
    }

})();
