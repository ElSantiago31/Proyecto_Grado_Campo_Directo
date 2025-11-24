// Dashboard JavaScript - Campo Directo (Compradores)

document.addEventListener('DOMContentLoaded', async function() {
    console.log('[Dashboard Comprador] === INICIANDO DASHBOARD COMPRADOR ===');
    console.log('[Dashboard Comprador] URL actual:', window.location.href);
    console.log('[Dashboard Comprador] Token presente:', !!localStorage.getItem('authToken'));
    
    // Verificar autenticación JWT
    if (!isAuthenticated()) {
        console.log('[Dashboard Comprador] ❌ No hay token de autenticación, redirigiendo al login');
        window.location.href = '/login-comprador/';
        return;
    }
    
    console.log('[Dashboard Comprador] ✅ Token válido, verificando perfil...');
    
    // Verificar que el usuario sea un comprador
    try {
        console.log('[Dashboard Comprador] Obteniendo perfil del usuario...');
        const profile = await authApi.getProfile();
        console.log('[Dashboard Comprador] Perfil obtenido:', profile);
        
        if (!profile || profile.tipo_usuario !== 'comprador') {
            console.log('[Dashboard Comprador] ❌ Usuario no es comprador, tipo:', profile?.tipo_usuario);
            window.location.href = '/login-comprador/';
            return;
        }
        
        console.log(`[Dashboard Comprador] ✅ Usuario comprador autenticado: ${profile.nombre} ${profile.apellido}`);
        
        // Actualizar nombre en la UI
        const userNameElement = document.getElementById('userName');
        if (userNameElement) {
            userNameElement.textContent = `${profile.nombre} ${profile.apellido}`;
        }
        
    } catch (error) {
        console.error('[Dashboard Comprador] ❌ Error verificando perfil:', error);
        
        // Si es error de autenticación (401), redirigir al login
        if (error instanceof ApiError && error.isAuthError()) {
            console.log('[Dashboard Comprador] Error de autenticación, redirigiendo...');
            window.location.href = '/login-comprador/';
            return;
        }
        
        // Para otros errores, continuar con datos por defecto
        console.warn('[Dashboard Comprador] Continuando con datos por defecto debido a error:', error.message);
    }
    
    // Mostrar la aplicación
    const app = document.getElementById('appContainer');
    if (app) {
        app.style.display = 'block';
    }
    
    // Inicializar funciones básicas
    console.log('[Dashboard Comprador] Inicializando navegación y logout...');
    setupNavigation();
    setupLogout();
    loadMarketplaceDemo();
    
    console.log('[Dashboard Comprador] ✅ Dashboard comprador cargado correctamente');
    console.log('[Dashboard Comprador] === FIN DE INICIALIZACIÓN ===');
});

// Datos por defecto del dashboard comprador
let compradorData = {
    user: {
        name: 'María González',
        email: 'comprador@example.com'
    },
    marketplace: [
        {
            id: 1,
            name: 'Tomates Cherry Orgánicos',
            farmer: 'Juan Pérez',
            location: 'Cundinamarca',
            price: 8000,
            unit: 'kg',
            stock: 25,
            category: 'vegetales',
            image: '🍅',
            rating: 4.8,
            description: 'Tomates cherry orgánicos, cultivados sin químicos'
        },
        {
            id: 2,
            name: 'Lechugas Hidropónicas',
            farmer: 'María Rodríguez',
            location: 'Bogotá',
            price: 3500,
            unit: 'unidad',
            stock: 40,
            category: 'vegetales',
            image: '🥬',
            rating: 4.5,
            description: 'Lechugas frescas cultivadas en sistema hidropónico'
        },
        {
            id: 3,
            name: 'Fresas de Invernadero',
            farmer: 'Carlos García',
            location: 'Boyacá',
            price: 15000,
            unit: 'kg',
            stock: 10,
            category: 'frutas',
            image: '🍓',
            rating: 4.9,
            description: 'Fresas dulces y jugosas de invernadero tecnificado'
        }
    ]
};

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remover clase active de todos los items
            navItems.forEach(nav => nav.classList.remove('active'));
            sections.forEach(section => section.classList.remove('active'));
            
            // Agregar clase active al item clickeado
            this.classList.add('active');
            
            // Mostrar la sección correspondiente
            const targetSection = this.getAttribute('data-section');
            const section = document.getElementById(targetSection);
            if (section) {
                section.classList.add('active');
                
                // Cargar datos específicos de la sección
                switch(targetSection) {
                    case 'marketplace':
                        loadMarketplaceDemo();
                        break;
                }
            }
        });
    });
}

function setupLogout() {
    // Menú de usuario
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    const logoutBtn = document.getElementById('logoutBtn');

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });

        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', function() {
            userDropdown.classList.remove('show');
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }
}

async function handleLogout() {
    try {
        await authApi.logout();
    } catch (error) {
        console.warn('Error al hacer logout:', error);
    } finally {
        // Limpiar tokens y redirigir
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        showNotification('Sesión cerrada correctamente', 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    }
}

function loadMarketplaceDemo() {
    const grid = document.getElementById('marketplaceGrid');
    if (!grid) return;

    grid.innerHTML = compradorData.marketplace.map(product => `
        <div class="product-card" data-id="${product.id}">
            <div class="product-image">
                <span class="product-emoji">${product.image}</span>
            </div>
            <div class="product-info">
                <h3 class="product-name">${product.name}</h3>
                <p class="product-farmer">Por: ${product.farmer}</p>
                <p class="product-location">📍 ${product.location}</p>
                <p class="product-price">$${product.price.toLocaleString()} / ${product.unit}</p>
                <div class="product-rating">
                    <span class="stars">⭐</span>
                    <span class="rating-number">${product.rating}</span>
                </div>
                <p class="product-stock">Stock: ${product.stock} ${product.unit}s</p>
            </div>
            <div class="product-actions">
                <button class="btn btn-favorite" onclick="toggleFavorite(${product.id})">
                    🤍
                </button>
                <button class="btn btn-primary" onclick="addToCart(${product.id})">
                    🛒 Agregar
                </button>
            </div>
        </div>
    `).join('');
}

function toggleFavorite(productId) {
    console.log(`Producto ${productId} agregado a favoritos`);
    showNotification('Producto agregado a favoritos', 'success');
}

function addToCart(productId) {
    const product = compradorData.marketplace.find(p => p.id === productId);
    if (product) {
        console.log(`Agregado al carrito: ${product.name}`);
        showNotification(`${product.name} agregado al carrito`, 'success');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        borderRadius: '6px',
        color: 'white',
        fontWeight: '600',
        zIndex: '9999',
        maxWidth: '400px',
        backgroundColor: type === 'error' ? '#dc3545' : 
                       type === 'success' ? '#28a745' : 
                       type === 'warning' ? '#ffc107' : '#2d5016',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease'
    });

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);

    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}