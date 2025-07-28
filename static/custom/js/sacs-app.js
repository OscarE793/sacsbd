/**
 * SACS_BD - Aplicación JavaScript
 * Funcionalidades personalizadas sobre Metronic
 */

class SACSApp {
    constructor() {
        this.version = '1.0.0';
        this.init();
    }
    
    init() {
        console.log(`🚀 SACS_BD App v${this.version} iniciada`);
        this.setupEventListeners();
        this.initComponents();
        this.logSystemInfo();
    }
    
    setupEventListeners() {
        // Manejo de sidebar toggle en móvil
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-sacs-sidebar-toggle]')) {
                this.toggleSidebar();
            }
        });
        
        // Confirmación para acciones destructivas
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-confirm]')) {
                e.preventDefault();
                this.confirmAction(e.target);
            }
        });
        
        // Auto-refresh para KPIs del dashboard
        if (document.body.classList.contains('dashboard-page')) {
            this.setupAutoRefresh();
        }
    }
    
    initComponents() {
        this.initTooltips();
        this.initAnimations();
        this.initModals();
        this.initNotifications();
    }
    
    logSystemInfo() {
        const info = {
            userAgent: navigator.userAgent,
            viewport: `${window.innerWidth}x${window.innerHeight}`,
            timestamp: new Date().toISOString(),
            page: window.location.pathname
        };
        console.log('📊 SACS_BD System Info:', info);
    }
    
    toggleSidebar() {
        const sidebar = document.querySelector('[data-kt-drawer="app-sidebar"]');
        if (sidebar) {
            // Usar API de Metronic si está disponible
            if (typeof KTDrawer !== 'undefined') {
                const drawer = KTDrawer.getInstance(sidebar);
                if (drawer) {
                    drawer.toggle();
                }
            } else {
                // Fallback manual
                sidebar.classList.toggle('drawer-on');
            }
        }
    }
    
    confirmAction(element) {
        const message = element.getAttribute('data-confirm') || '¿Está seguro de realizar esta acción?';
        const type = element.getAttribute('data-confirm-type') || 'warning';
        
        if (typeof Swal !== 'undefined') {
            // Usar SweetAlert2 si está disponible
            Swal.fire({
                title: '¿Confirmar acción?',
                text: message,
                icon: type,
                showCancelButton: true,
                confirmButtonText: 'Sí, continuar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#1b84ff',
                cancelButtonColor: '#f1416c'
            }).then((result) => {
                if (result.isConfirmed) {
                    if (element.href) {
                        window.location.href = element.href;
                    } else if (element.onclick) {
                        element.onclick();
                    }
                }
            });
        } else {
            // Fallback nativo
            if (confirm(message)) {
                if (element.href) {
                    window.location.href = element.href;
                } else if (element.onclick) {
                    element.onclick();
                }
            }
        }
    }
    
    initTooltips() {
        // Inicializar tooltips de Bootstrap
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        console.log(`✅ ${tooltipTriggerList.length} tooltips inicializados`);
    }
    
    initAnimations() {
        // Observador para animaciones al hacer scroll
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.animationPlayState = 'running';
                        observer.unobserve(entry.target); // Solo animar una vez
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '50px'
            });
            
            // Observar elementos con animaciones
            document.querySelectorAll('.sacs-animate-up, .sacs-animate-scale').forEach(el => {
                el.style.animationPlayState = 'paused';
                observer.observe(el);
            });
        }
    }
    
    initModals() {
        // Configurar modales para cargar contenido dinámico
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-modal-url]')) {
                e.preventDefault();
                const url = e.target.getAttribute('data-modal-url');
                this.loadModalContent(url);
            }
        });
    }
    
    async loadModalContent(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const html = await response.text();
            
            // Buscar modal dinámico o crear uno
            let modal = document.getElementById('dynamicModal');
            if (!modal) {
                modal = this.createDynamicModal();
                document.body.appendChild(modal);
            }
            
            modal.querySelector('.modal-body').innerHTML = html;
            
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
            
        } catch (error) {
            console.error('Error cargando contenido del modal:', error);
            this.showNotification('Error cargando contenido', 'error');
        }
    }
    
    createDynamicModal() {
        const modalHTML = `
            <div class="modal fade" id="dynamicModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">SACS_BD</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="d-flex justify-content-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Cargando...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const temp = document.createElement('div');
        temp.innerHTML = modalHTML;
        return temp.firstElementChild;
    }
    
    initNotifications() {
        // Crear contenedor para notificaciones si no existe
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1070';
            document.body.appendChild(container);
        }
    }
    
    setupAutoRefresh() {
        // Auto-refresh para dashboard cada 30 segundos
        const refreshInterval = 30000; // 30 segundos
        
        let intervalId = setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.refreshKPIs();
            }
        }, refreshInterval);
        
        // Pausar auto-refresh cuando la pestaña no es visible
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                clearInterval(intervalId);
            } else {
                intervalId = setInterval(() => {
                    this.refreshKPIs();
                }, refreshInterval);
            }
        });
    }
    
    async refreshKPIs() {
        try {
            const response = await this.request('/dashboard/kpis-api/');
            this.updateKPIValues(response);
            console.log('🔄 KPIs actualizados', new Date().toLocaleTimeString());
        } catch (error) {
            console.error('Error actualizando KPIs:', error);
        }
    }
    
    updateKPIValues(data) {
        // Actualizar valores de KPIs con animación
        Object.keys(data).forEach(key => {
            const element = document.getElementById(`kpi-${key}`);
            if (element && data[key].total !== undefined) {
                this.animateCounter(element, data[key].total);
            }
        });
    }
    
    animateCounter(element, target, duration = 1000) {
        const current = parseInt(element.textContent) || 0;
        const increment = (target - current) / (duration / 50);
        let counter = current;
        
        const timer = setInterval(() => {
            counter += increment;
            if ((increment > 0 && counter >= target) || (increment < 0 && counter <= target)) {
                counter = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(counter);
        }, 50);
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="ki-outline ki-information fs-6 me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        const container = document.getElementById('toast-container');
        container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });
        bsToast.show();
        
        // Remover del DOM después de que se oculte
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    // Utilidad para requests AJAX con CSRF
    async request(url, options = {}) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.querySelector('meta[name="csrf-token"]')?.content;
        
        const defaultOptions = {
            headers: {
                'X-CSRFToken': csrfToken || '',
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('Request error:', error);
            throw error;
        }
    }
    
    // Método para mostrar loading state
    showLoading(element, text = 'Cargando...') {
        if (element) {
            element.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                ${text}
            `;
            element.disabled = true;
        }
    }
    
    hideLoading(element, originalText = 'Enviar') {
        if (element) {
            element.innerHTML = originalText;
            element.disabled = false;
        }
    }
}

// Inicializar aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.SACS = new SACSApp();
});

// Utilidades globales
window.SACSUtils = {
    formatBytes: (bytes, decimals = 2) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },
    
    formatDate: (date, locale = 'es-CO') => {
        return new Intl.DateTimeFormat(locale, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },
    
    formatCurrency: (amount, currency = 'COP') => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    },
    
    // Validar email
    isValidEmail: (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Validar teléfono colombiano
    isValidPhone: (phone) => {
        const phoneRegex = /^(\+57|57|0)?[1-9]\d{8,9}$/;
        return phoneRegex.test(phone.replace(/\s/g, ''));
    }
};

// Event listener para manejo global de formularios
document.addEventListener('submit', function(e) {
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (submitBtn && !submitBtn.disabled) {
        const originalText = submitBtn.innerHTML;
        window.SACS.showLoading(submitBtn, 'Procesando...');
        
        // Restaurar botón después de 5 segundos como fallback
        setTimeout(() => {
            window.SACS.hideLoading(submitBtn, originalText);
        }, 5000);
    }
});

// Manejo global de errores JavaScript
window.addEventListener('error', function(e) {
    console.error('Error JavaScript capturado:', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno,
        stack: e.error?.stack
    });
    
    if (window.SACS) {
        window.SACS.showNotification('Se produjo un error inesperado', 'danger');
    }
});
