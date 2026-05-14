/* ========================================
   PROFESSIONAL INTERACTIONS & ANIMATIONS JS
   ======================================== */

// ========================================
// SCROLL ANIMATIONS
// ========================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-on-scroll');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all elements with animation class
document.querySelectorAll('.animate-fade-in-up, .card, .stat-card, .service-card').forEach(el => {
    observer.observe(el);
});

// ========================================
// NAVBAR EFFECTS
// ========================================

let lastScroll = 0;
const navbar = document.querySelector('.navbar');

if (navbar) {
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 50) {
            navbar.style.boxShadow = 'var(--shadow-md)';
        } else {
            navbar.style.boxShadow = 'var(--shadow-sm)';
        }

        lastScroll = currentScroll;
    });
}

// ========================================
// SMOOTH SCROLL ANCHOR LINKS
// ========================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && document.querySelector(href)) {
            e.preventDefault();
            document.querySelector(href).scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// ========================================
// ACTIVE NAV LINK
// ========================================

function setActiveNavLink() {
    const navLinks = document.querySelectorAll('.navbar-nav a');
    const currentLocation = location.pathname;

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

setActiveNavLink();

// ========================================
// MOBILE MENU TOGGLE
// ========================================

const menuToggle = document.querySelector('.menu-toggle');
const mobileMenu = document.querySelector('.mobile-menu');

if (menuToggle && mobileMenu) {
    menuToggle.addEventListener('click', () => {
        mobileMenu.classList.toggle('active');
        menuToggle.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.navbar')) {
            mobileMenu.classList.remove('active');
            menuToggle.classList.remove('active');
        }
    });
}

// ========================================
// DROPDOWN MENUS
// ========================================

document.querySelectorAll('.dropdown').forEach(dropdown => {
    const toggle = dropdown.querySelector('[data-dropdown-toggle]');
    const menu = dropdown.querySelector('.dropdown-menu');

    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('active');
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target)) {
                menu.classList.remove('active');
            }
        });

        // Close on menu item click
        menu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                menu.classList.remove('active');
            });
        });
    }
});

// ========================================
// FORM VALIDATION
// ========================================

const form = document.querySelector('form');

if (form) {
    form.addEventListener('submit', (e) => {
        const inputs = form.querySelectorAll('input[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('error');
                isValid = false;
            } else {
                input.classList.remove('error');
            }
        });

        if (!isValid) {
            e.preventDefault();
        }
    });

    // Remove error class on input
    form.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('input', () => {
            if (input.value.trim()) {
                input.classList.remove('error');
            }
        });
    });
}

// ========================================
// TOAST NOTIFICATIONS
// ========================================

class Toast {
    static show(message, type = 'info', duration = 3000) {
        const container = document.querySelector('.toast-container') || this.createContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">${message}</div>
            <div class="toast-close">&times;</div>
        `;

        container.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.close(toast);
        });

        // Auto close
        setTimeout(() => {
            this.close(toast);
        }, duration);
    }

    static close(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }

    static createContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
}

// ========================================
// LAZY LOAD IMAGES
// ========================================

if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });

    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// ========================================
// MODAL DIALOGS
// ========================================

class Modal {
    constructor(selector) {
        this.modal = document.querySelector(selector);
        this.closeBtn = this.modal?.querySelector('[data-close]');
        this.init();
    }

    init() {
        if (!this.modal) return;

        this.closeBtn?.addEventListener('click', () => this.close());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        });
    }

    open() {
        if (this.modal) {
            this.modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    close() {
        if (this.modal) {
            this.modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    toggle() {
        this.modal?.classList.contains('show') ? this.close() : this.open();
    }
}

// ========================================
// TABLE SORTING & FILTERING
// ========================================

class DataTable {
    constructor(tableSelector) {
        this.table = document.querySelector(tableSelector);
        this.rows = Array.from(this.table?.querySelectorAll('tbody tr') || []);
        this.init();
    }

    init() {
        // Sort headers
        this.table?.querySelectorAll('th[data-sort]').forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => this.sort(header.dataset.sort));
        });

        // Filter inputs
        this.table?.querySelectorAll('[data-filter]').forEach(filter => {
            filter.addEventListener('input', () => this.filter());
        });
    }

    sort(column) {
        const ascending = !this.table.dataset.sortAsc;
        this.table.dataset.sortAsc = ascending;

        this.rows.sort((a, b) => {
            const aValue = a.querySelector(`[data-column="${column}"]`)?.textContent;
            const bValue = b.querySelector(`[data-column="${column}"]`)?.textContent;

            if (ascending) {
                return aValue.localeCompare(bValue);
            } else {
                return bValue.localeCompare(aValue);
            }
        });

        this.table.querySelector('tbody').innerHTML = '';
        this.rows.forEach(row => {
            this.table.querySelector('tbody').appendChild(row);
        });
    }

    filter() {
        const query = Array.from(this.table?.querySelectorAll('[data-filter]') || [])
            .map(f => f.value.toLowerCase())
            .join('');

        this.rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    }
}

// ========================================
// COPY TO CLIPBOARD
// ========================================

document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', async () => {
        const text = btn.dataset.copy;
        try {
            await navigator.clipboard.writeText(text);
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => {
                btn.textContent = originalText;
            }, 2000);
        } catch (err) {
            Toast.show('Failed to copy', 'error');
        }
    });
});

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Format date
function formatDate(date) {
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

// ========================================
// PAGE LOAD ANIMATIONS
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Add animation to elements
    document.querySelectorAll('.card, .stat-card, .service-card').forEach((el, i) => {
        el.style.animationDelay = `${i * 50}ms`;
    });

    // Fade in page content
    document.body.classList.add('loaded');
});

// ========================================
// DARK MODE TOGGLE (OPTIONAL)
// ========================================

const darkModeToggle = document.querySelector('[data-dark-mode-toggle]');

if (darkModeToggle) {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';

    if (isDarkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        darkModeToggle.classList.add('active');
    }

    darkModeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('darkMode', 'false');
            darkModeToggle.classList.remove('active');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('darkMode', 'true');
            darkModeToggle.classList.add('active');
        }
    });
}

// ========================================
// EXPORT FOR EXTERNAL USE
// ========================================

window.Toast = Toast;
window.Modal = Modal;
window.DataTable = DataTable;
window.debounce = debounce;
window.throttle = throttle;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
