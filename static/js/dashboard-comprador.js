// Dashboard JavaScript - Campo Directo (Compradores)

document.addEventListener('DOMContentLoaded', async function () {
    console.log('[Dashboard Comprador] === INICIANDO DASHBOARD COMPRADOR ===');
    console.log('[Dashboard Comprador] URL actual:', window.location.href);
    console.log('[Dashboard Comprador] Token presente:', !!localStorage.getItem('authToken'));

    // Verificar autenticación JWT
    if (!isAuthenticated()) {
        console.log('[Dashboard Comprador] ❌ No hay token de autenticación, redirigiendo al login');
        window.location.href = '/login/';
        return;
    }

    console.log('[Dashboard Comprador] ✅ Token válido, verificando perfil...');

    // Verificar que el usuario sea un comprador
    try {
        console.log('[Dashboard Comprador] Obteniendo perfil del usuario...');
        const profile = await authApi.getProfile();
        console.log('[Dashboard Comprador] Perfil obtenido:', profile);

        if (!profile || (profile.tipo_usuario !== 'comprador' && profile.tipo_usuario !== 'campesino')) {
            console.log('[Dashboard Comprador] ❌ Usuario no tiene permisos de compra, tipo:', profile?.tipo_usuario);
            window.location.href = '/login/';
            return;
        }

        console.log(`[Dashboard Comprador] ✅ Usuario autenticado (${profile.tipo_usuario}): ${profile.nombre} ${profile.apellido}`);

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
            window.location.href = '/login/';
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
    loadMarketplace();
    setupQuantityModal();
    setupRatingModal();
    setupOrderTabs();
    
    // Inicializar contador real de favoritos almacenados
    if (typeof updateFavoriteProductsCount === 'function') {
        updateFavoriteProductsCount();
    }

    console.log('[Dashboard Comprador] ✅ Dashboard comprador cargado correctamente');
    console.log('[Dashboard Comprador] === FIN DE INICIALIZACIÓN ===');
});

// La variable compradorData simulada fue eliminada permanentemente.
// Ahora los datos provienen en tiempo real del backend usando productApi.

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', function (e) {
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
                switch (targetSection) {
                    case 'marketplace':
                        loadMarketplace();
                        break;
                    case 'favorites':
                        loadFavorites();
                        break;
                    case 'my-orders':
                        loadOrders();
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
        userMenuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });

        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', function () {
            userDropdown.classList.remove('show');
        });

        // Manejar enlaces de perfil y configuración
        const showSection = (sectionId, e) => {
            e.preventDefault();
            userDropdown.classList.remove('show');
            
            // Remover 'active' de navegación lateral y todas las secciones
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
            
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
                if (sectionId === 'profile') {
                    loadProfileData();
                    document.getElementById('changePasswordForm')?.reset();
                }
            }
        };

        const profileLink = document.getElementById('profileLink');
        if (profileLink) profileLink.addEventListener('click', (e) => showSection('profile', e));
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function (e) {
            e.preventDefault();
            handleLogout();
        });
    }
}

async function handleLogout() {
    console.log('[Dashboard Comprador] Iniciando proceso de logout...');
    try {
        await authApi.logout();

        // Usar endpoint Django para logout de sesión
        console.log('[Dashboard Comprador] Redirigiendo a /logout/ para cerrar sesión Django');
        window.location.href = '/logout/';
    } catch (error) {
        console.warn('[Dashboard Comprador] Error al redirigir a logout:', error);
        window.location.href = '/logout/';
    }
}

// Variable global para almacenar productos en memoria y poder filtrarlos
let allMarketplaceProducts = [];

async function loadMarketplace() {
    const grid = document.getElementById('marketplaceGrid');
    if (!grid) return;

    try {
        console.log('[Dashboard Comprador] Cargando productos reales desde el backend...');
        grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 2rem;">Cargando productos del marketplace...</div>';

        // Petición al backend
        const data = await productApi.getProducts({ estado: 'disponible' });
        // DRF con paginación usualmente devuelve la lista en results
        allMarketplaceProducts = data.results || data;

        if (!allMarketplaceProducts || allMarketplaceProducts.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 2rem;">No hay productos disponibles por el momento.</div>';
            return;
        }

        // Configurar Event Listeners para los filtros si no están configurados
        setupMarketplaceFilters();

        // Renderizar todos los productos inicialmente
        renderMarketplaceProducts(allMarketplaceProducts);

    } catch (error) {
        console.error('[Dashboard Comprador] Error al cargar marketplace:', error);
        grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: red; padding: 2rem;">Hubo un error cargando los productos. Por favor intenta de nuevo más tarde.</div>';
    }
}

function renderMarketplaceProducts(productos) {
    const grid = document.getElementById('marketplaceGrid');
    if (!grid) return;

    if (productos.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 2rem; background: white; border-radius: 8px;">No se encontraron productos que coincidan con tu búsqueda. 🌾</div>';
        return;
    }

    // Cargar favoritos guardados
    const favorites = JSON.parse(localStorage.getItem('comprador_favorites') || '[]');

    grid.innerHTML = productos.map(product => {
        const defaultImage = '/static/images/logo.png';
        const imageUrl = product.imagen_principal || defaultImage;
        const priceVal = product.precio_por_kg || product.precio_base || 0;
        const price = parseFloat(priceVal).toLocaleString();
        const heartIcon = favorites.some(f => f.id === product.id) ? '❤️' : '🤍';

        const campesinoNombre = product.campesino_nombre || `Campesino N.º ${product.campesino || 'Desconocido'}`;
        const fincaNombre = product.finca_nombre || 'Finca Local';
        const ubicacion = product.ubicacion || 'Colombia';
        const categoria = product.categoria_nombre || 'Producto';

        // Escapamos strings para evitar problemas en el HTML
        const safeName = product.nombre.replace(/'/g, "\\'");
        const safeImg = imageUrl.replace(/'/g, "\\'");

        return `
        <div class="product-card" data-id="${product.id}">
            <a href="${imageUrl}" onclick="event.preventDefault(); openLightbox('${safeImg}')" title="Haz clic para ver la imagen completa" style="display:block; text-decoration:none; color:inherit;">
            <div class="product-image" style="background-image: url('${imageUrl}'); background-size: cover; background-position: center; min-height: 180px; position:relative; cursor:zoom-in;">
                <span class="product-status status-disponible" style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.9); padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; color: #333;">${categoria}</span>
            </div>
            </a>
            <div class="product-info" style="padding: 15px;">
                <h3 class="product-name" style="margin-bottom: 5px; font-size: 1.2rem;">${product.nombre}</h3>
                <p class="product-farmer" style="margin-bottom: 3px; color: #555;">
                    🧑‍🌾 ${campesinoNombre} 
                    <button onclick="showReviewsModal(${product.campesino || 0}, '${safeName.replace(/'/g, '')}')" 
                        title="Ver reseñas y comentarios de este productor"
                        style="font-size: 0.82rem; color: #f39c12; margin-left: 6px; background: #fffbea; border: 1px solid #f7dc6f; border-radius: 20px; padding: 2px 9px; cursor: pointer; font-weight: 600; transition: background 0.2s;">
                        ⭐ ${product.campesino_calificacion > 0 ? parseFloat(product.campesino_calificacion).toFixed(1) : 'Nuevo'} <span style="font-size:0.75rem; color:#aaa;">ver reseñas</span>
                    </button>
                </p>
                <p class="product-location" style="margin-bottom: 8px; font-size: 0.85rem; color: #777;">📍 ${fincaNombre}, ${ubicacion}</p>
                <p class="product-description" style="font-size: 0.85rem; color: #666; margin-bottom: 8px; font-style: italic; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${(product.descripcion || '').replace(/"/g, '&quot;')}">${product.descripcion || 'Sin descripción adicional'}</p>
                <p class="product-price" style="font-size: 1.1rem; color: #2d5016; font-weight: bold; margin-bottom: 5px;">$${price} / ${product.unidad_medida}</p>
                <p class="product-stock" style="font-size: 0.9rem; color: #444;">Disponibles: ${product.stock_disponible || product.cantidad_disponible || 0}</p>
            </div>
            <div class="product-actions" style="margin-top: auto; padding: 15px; border-top: 1px solid #eee; display: flex; gap: 5px;">
                <button class="btn btn-favorite" onclick="toggleFavorite(this, ${product.id}, '${safeName}', '${safeImg}', ${product.campesino || 0})" style="padding: 8px 12px; font-size: 1.2rem; background: #f8f9fa; border: 1px solid #ddd;">${heartIcon}</button>
                <button class="btn btn-primary" onclick="openQuantityModal(${product.id})" style="padding: 8px 12px; flex: 1;">🛒 Agregar</button>
            </div>
        </div>
        `;
    }).join('');
}

function setupMarketplaceFilters() {
    const searchInput = document.getElementById('productSearch');
    const categoryFilter = document.getElementById('categoryFilter');
    const locationFilter = document.getElementById('locationFilter');

    // Poblar el filtro de ubicación dinámicamente si existe colombiaData
    populateLocationFilter();

    // Función que aplica todos los filtros activos a la vez
    const applyFilters = () => {
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const categoryTerm = categoryFilter ? categoryFilter.value.toLowerCase().trim() : '';
        const locationTerm = locationFilter ? locationFilter.value.toLowerCase().trim() : '';

        const filteredProducts = allMarketplaceProducts.filter(product => {
            // Preparar las variables en minúsculas para comparar
            const name = (product.nombre || '').toLowerCase();
            const category = (product.categoria_nombre || '').toLowerCase();
            const location = (product.ubicacion || '').toLowerCase();
            const tags = product.tags_list ? product.tags_list.join(' ').toLowerCase() : '';

            // Match de búsqueda por texto (nombre o etiquetas)
            const matchSearch = searchTerm === '' || name.includes(searchTerm) || tags.includes(searchTerm);

            // Match de categoría
            const matchCategory = categoryTerm === '' || category.includes(categoryTerm);

            // Match de ubicación
            const matchLocation = locationTerm === '' || location.includes(locationTerm);

            return matchSearch && matchCategory && matchLocation;
        });

        renderMarketplaceProducts(filteredProducts);
    };

    // Asignar listeners y evitar asignarlos múltiples veces
    if (searchInput && !searchInput.hasAttribute('data-listening')) {
        searchInput.addEventListener('input', applyFilters);
        searchInput.setAttribute('data-listening', 'true');
    }

    if (categoryFilter && !categoryFilter.hasAttribute('data-listening')) {
        categoryFilter.addEventListener('change', applyFilters);
        categoryFilter.setAttribute('data-listening', 'true');
    }

    if (locationFilter && !locationFilter.hasAttribute('data-listening')) {
        locationFilter.addEventListener('change', applyFilters);
        locationFilter.setAttribute('data-listening', 'true');
    }
}

window.updateFavoriteProductsCount = function() {
    let favorites = JSON.parse(localStorage.getItem('comprador_favorites') || '[]');
    const countElement = document.getElementById('favoriteProducts');
    if (countElement) {
        countElement.textContent = favorites.length;
    }
};

window.toggleFavorite = function(btn, productId, productName, imageUrl, campesinoId) {
    let favorites = JSON.parse(localStorage.getItem('comprador_favorites') || '[]');
    const isFavorite = favorites.some(f => f.id === productId);

    if (isFavorite) {
        // Remover de favoritos
        favorites = favorites.filter(f => f.id !== productId);
        btn.textContent = '🤍';
        showNotification(`${productName} eliminado de favoritos`, 'info');
    } else {
        // Agregar a favoritos
        favorites.push({ id: productId, name: productName, image: imageUrl, campesino: campesinoId });
        btn.textContent = '❤️';
        showNotification(`${productName} guardado en favoritos`, 'success');
    }

    localStorage.setItem('comprador_favorites', JSON.stringify(favorites));
    updateFavoriteProductsCount();

    // Si estamos en la pestaña de favoritos, recargarla
    if (document.getElementById('favorites').classList.contains('active')) {
        loadFavorites();
    }
}

function openQuantityModal(productId) {
    const product = allMarketplaceProducts.find(p => p.id === productId);
    if (!product) return;

    const modal = document.getElementById('quantityModal');
    if (!modal) return;

    // 1. Inyectar datos base
    document.getElementById('quantityProductName').textContent = product.nombre;
    const maxStock = product.stock_disponible || product.cantidad_disponible || 0;
    const stockSpan = document.getElementById('quantityMaxStock');
    if (stockSpan) stockSpan.textContent = maxStock;
    const unitSpan = document.getElementById('quantityUnit');
    if (unitSpan) unitSpan.textContent = product.unidad_medida || 'unidades';

    // 2. Extraer precio base
    const priceVal = product.precio_por_kg || product.precio_base || 0;
    document.getElementById('quantityUnitPrice').textContent = priceVal.toLocaleString();
    document.getElementById('quantityUnitType').textContent = product.unidad_medida || 'unidad';

    // 3. Resetear inputs
    const input = document.getElementById('quantityInput');
    const typeSelect = document.getElementById('purchaseType');
    const priceDisplay = document.getElementById('quantityTotalPrice');
    
    if (input) {
        input.value = 1;
        input.max = maxStock;
    }
    if (typeSelect) typeSelect.value = 'unidad';

    const idInput = document.getElementById('quantityProductId');
    if (idInput) idInput.value = productId;

    // 4. Lógica de cálculo reactivo abstracto
    const calculateTotal = () => {
        let qty = parseFloat(input.value) || 0;
        // Si eligió por peso pero el precio es por Kg, se asume 1:1, etc.
        let total = qty * priceVal;
        priceDisplay.textContent = total.toLocaleString();
    };

    // Escuchar tipeo vivo
    input.removeEventListener('input', calculateTotal);
    typeSelect.removeEventListener('change', calculateTotal);
    input.addEventListener('input', calculateTotal);
    typeSelect.addEventListener('change', calculateTotal);

    // Calcular render inicial
    calculateTotal();
    modal.style.display = 'flex';
}

function closeQuantityModal() {
    const modal = document.getElementById('quantityModal');
    if (modal) modal.style.display = 'none';
}

function confirmQuantitySelection() {
    const productId = parseInt(document.getElementById('quantityProductId').value);
    const quantity = parseFloat(document.getElementById('quantityInput').value);
    const method = document.getElementById('purchaseType').value;
    const product = allMarketplaceProducts.find(p => p.id === productId);

    if (!product) return;

    const maxStock = product.stock_disponible || product.cantidad_disponible || 0;
    if (quantity <= 0 || quantity > maxStock) {
        showNotification('Cantidad inválida o superior al stock disponible', 'error');
        return;
    }

    let cart = JSON.parse(localStorage.getItem('comprador_cart') || '[]');

    const defaultImage = '/static/images/logo.png';
    const imageUrl = product.imagen_principal || defaultImage;
    const priceVal = product.precio_por_kg || product.precio_base || 0;


    // Verificar si el item ya esta en el carrito
    const existingIndex = cart.findIndex(item => item.id === productId);
    if (existingIndex >= 0) {
        cart[existingIndex].quantity += quantity;
        if (cart[existingIndex].quantity > maxStock) cart[existingIndex].quantity = maxStock;
    } else {
        cart.push({
            cartItemId: Date.now(),
            id: productId,
            name: product.nombre,
            price: priceVal,
            quantity: quantity,
            image: imageUrl,
            campesino_id: product.campesino,
            campesino_nombre: product.campesino_nombre || 'Campesino',
            date: new Date().toLocaleDateString()
        });
    }

    localStorage.setItem('comprador_cart', JSON.stringify(cart));

    closeQuantityModal();
    showNotification(`${quantity}x ${product.nombre} agregado al carrito 🛒`, 'success');

    if (document.getElementById('my-orders').classList.contains('active')) {
        loadOrders();
    }
    updateCartBadge();
}

function setupQuantityModal() {
    const closeBtn = document.getElementById('closeQuantityModal');
    const cancelBtn = document.getElementById('cancelQuantityBtn');
    const confirmBtn = document.getElementById('confirmQuantityBtn');

    if (closeBtn) closeBtn.addEventListener('click', closeQuantityModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeQuantityModal);
    if (confirmBtn) confirmBtn.addEventListener('click', confirmQuantitySelection);
}

// ----------------------------------------------------
// SISTEMA DE CALIFICACIONES (COMPRADOR A CAMPESINO)
// ----------------------------------------------------
function setupRatingModal() {
    const closeBtn = document.getElementById('closeRatingModal');
    const cancelBtn = document.getElementById('cancelRatingBtn');
    const submitBtn = document.getElementById('submitRatingBtn');
    const stars = document.querySelectorAll('#ratingStars .star');

    if (closeBtn) closeBtn.addEventListener('click', closeRatingModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeRatingModal);
    
    if (submitBtn) {
        submitBtn.addEventListener('click', async function() {
            const orderId = document.getElementById('ratingOrderId').value;
            const score = document.getElementById('ratingScore').value;
            const comment = document.getElementById('ratingComment').value;
            
            if (!score || score === '0') return;
            
            this.disabled = true;
            this.textContent = 'Enviando...';
            
            try {
                await orderApi.calificar(orderId, { calificacion: parseInt(score), comentario: comment });
                showNotification('¡Gracias! Calificación enviada existosamente', 'success');
                closeRatingModal();
                loadOrders(); // Recarga la pestaña actual
            } catch (error) {
                console.error("Error al enviar calificación:", error);
                showNotification(error.message || 'Error al enviar calificación', 'error');
            } finally {
                this.disabled = false;
                this.textContent = 'Enviar Calificación';
            }
        });
    }

    // Efectos de Hover y Click para estrellas
    stars.forEach(star => {
        star.addEventListener('mouseover', function() {
            const value = this.getAttribute('data-value');
            highlightStars(value);
        });
        
        star.addEventListener('mouseout', function() {
            const currentScore = document.getElementById('ratingScore').value;
            highlightStars(currentScore);
        });
        
        star.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            document.getElementById('ratingScore').value = value;
            highlightStars(value);
            
            // Habilitar botón de enviar
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        });
    });
}

function highlightStars(count) {
    const stars = document.querySelectorAll('#ratingStars .star');
    stars.forEach(star => {
        const val = parseInt(star.getAttribute('data-value'));
        if (val <= count) {
            star.style.color = '#ffc107'; // Amarillo
        } else {
            star.style.color = '#ccc'; // Gris
        }
    });
}

window.openRatingModal = function(orderId, targetName) {
    const modal = document.getElementById('ratingModal');
    if (!modal) return;

    document.getElementById('ratingTargetName').textContent = targetName;
    document.getElementById('ratingOrderId').value = orderId;
    
    // Reset modal
    document.getElementById('ratingScore').value = "0";
    document.getElementById('ratingComment').value = "";
    highlightStars(0);
    
    const submitBtn = document.getElementById('submitRatingBtn');
    if (submitBtn) submitBtn.disabled = true;

    modal.style.display = 'block';
};

window.closeRatingModal = function() {
    const modal = document.getElementById('ratingModal');
    if (modal) modal.style.display = 'none';
};

// Cargar pestaña de Favoritos
function loadFavorites() {
    const grid = document.getElementById('favoritesGrid');
    if (!grid) return;

    const favorites = JSON.parse(localStorage.getItem('comprador_favorites') || '[]');

    if (favorites.length === 0) {
        grid.innerHTML = `
        <div class="activity-item" style="grid-column: 1 / -1; text-align:center; padding: 20px;">
            <span class="activity-icon">📉</span>
            <div class="activity-content">
                <p><strong>No tienes favoritos agregados actualmente.</strong></p>
                <small>Explora el Marketplace y pulsa el corazón ❤️ para guardarlos aquí.</small>
            </div>
        </div>`;
        return;
    }

    grid.innerHTML = favorites.map(fav => `
        <div class="activity-item" style="display: flex; align-items: center; gap: 15px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="width: 50px; height: 50px; background-image: url('${fav.image}'); background-size: cover; border-radius: 8px;"></div>
            <div class="activity-content" style="flex: 1;">
                <p><strong>${fav.name}</strong></p>
                <small>Producto favorito</small>
            </div>
            <button class="btn btn-secondary" onclick="toggleFavorite(this, ${fav.id}, '${fav.name.replace(/'/g, "\\'")}', '${fav.image}')" style="padding: 5px 10px;">Quitar 🤍</button>
        </div>
    `).join('');
}

// Cargar pestaña de Pedidos
function loadOrders() {
    const activeTabObj = document.querySelector('.order-tabs .tab-btn.active');
    const activeTab = activeTabObj ? activeTabObj.dataset.tab : 'cart';
    const list = document.getElementById('buyerOrdersList');
    const cartActions = document.getElementById('cartActionsContainer');
    if (!list) return;

    updateCartBadge();

    list.innerHTML = '<div style="text-align:center; padding: 2rem;">Cargando...</div>';

    if (activeTab === 'cart') {
        renderCart();
    } else if (activeTab === 'active') {
        if (cartActions) cartActions.style.display = 'none';
        fetchRealOrders('active');
    } else if (activeTab === 'completed') {
        if (cartActions) cartActions.style.display = 'none';
        fetchRealOrders('completed');
    }
}

function updateCartBadge() {
    const cart = JSON.parse(localStorage.getItem('comprador_cart') || '[]');
    const badge = document.getElementById('cartCountBadge');
    if (badge) badge.textContent = cart.length;
}

function renderCart() {
    const list = document.getElementById('buyerOrdersList');
    const cartActions = document.getElementById('cartActionsContainer');
    const cart = JSON.parse(localStorage.getItem('comprador_cart') || '[]');

    if (cart.length === 0) {
        if (cartActions) cartActions.style.display = 'none';
        list.innerHTML = `
        <div class="activity-item" style="text-align:center; padding: 20px;">
            <span class="activity-icon">🛒</span>
            <div class="activity-content">
                <p><strong>Tu carrito de compras está vacío.</strong></p>
                <small>Ve al Marketplace para agregar productos a tus pedidos.</small>
            </div>
        </div>`;
        return;
    }

    let total = 0;

    list.innerHTML = cart.map((item) => {
        const subtotal = item.price * (item.quantity || 1);
        total += subtotal;
        return `
        <div class="order-card" style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px; padding: 10px; border: 1px solid #eee; border-radius: 8px;">
            <div style="width: 60px; height: 60px; background-image: url('${item.image}'); background-size: cover; border-radius: 8px;"></div>
            <div class="order-info" style="flex: 1;">
                <h4 style="margin:0 0 5px 0;">${item.name}</h4>
                <p style="margin:0; color:#666;">🧑‍🌾 ${item.campesino_nombre}</p>
                <p style="margin:0; color:#444;">$${parseFloat(item.price).toLocaleString()} x ${item.quantity || 1} = <strong style="color:#2d5016;">$${subtotal.toLocaleString()}</strong></p>
            </div>
            <div style="display:flex; flex-direction:column; gap:5px; align-items:flex-end;">
                <button class="btn" style="background-color: #dc3545; color: white; padding: 6px 12px; font-size: 0.9rem; border: none; border-radius: 4px; cursor: pointer;" onclick="removeFromCart(${item.cartItemId})">Eliminar</button>
            </div>
        </div>`;
    }).join('');

    if (cartActions) {
        cartActions.style.display = 'block';
        const totalElem = document.getElementById('cartTotalAmount');
        if (totalElem) totalElem.textContent = '$' + total.toLocaleString();
    }
}

async function fetchRealOrders(type) {
    const list = document.getElementById('buyerOrdersList');
    try {
        const response = await orderApi.getMisCompras();
        const pedidos = response.results || response || [];

        let filtered = [];
        if (type === 'active') {
            filtered = pedidos.filter(p => ['pending', 'confirmed', 'preparing', 'ready'].includes(p.estado));
            const counter = document.getElementById('activeOrdersCount');
            if (counter) counter.textContent = filtered.length;
        } else {
            filtered = pedidos.filter(p => ['completed', 'cancelled'].includes(p.estado));
        }

        if (filtered.length === 0) {
            list.innerHTML = `<div style="text-align:center; padding: 2rem; color: #666;">No tienes pedidos ${type === 'active' ? 'en curso' : 'en tu historial'}.</div>`;
            return;
        }

        const statusColors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'preparing': '#fd7e14',
            'ready': '#28a745',
            'completed': '#2d5016',
            'cancelled': '#dc3545'
        };
        const statusLabels = {
            'pending': 'Pendiente',
            'confirmed': 'Confirmado',
            'preparing': 'En Preparación',
            'ready': 'Listo para Entrega',
            'completed': 'Completado',
            'cancelled': 'Cancelado'
        };

        list.innerHTML = filtered.map(pedido => {
            const dateObj = new Date(pedido.fecha_pedido);
            const date = dateObj.toLocaleDateString('es-CO');
            const time = dateObj.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
            const statusColor = statusColors[pedido.estado] || '#666';
            const statusLabel = statusLabels[pedido.estado] || pedido.estado;

            let detailsHtml = '';
            if (pedido.detalles && pedido.detalles.length > 0) {
                detailsHtml = '<ul style="margin: 5px 0 0 0; padding-left: 20px; font-size: 0.9rem; color: #555;">';
                pedido.detalles.forEach(d => {
                    detailsHtml += `<li>${d.cantidad}x ${d.nombre_producto_snapshot} ($${parseFloat(d.precio_unitario).toLocaleString()})</li>`;
                });
                detailsHtml += '</ul>';
            }

            let ratingBtnHtml = '';
            let cancelBtnHtml = '';

            if (pedido.estado === 'completed') {
                if (pedido.calificacion_comprador == null) {
                    // Limpieza del nombre de campesino para html
                    const safeName = (pedido.campesino_nombre || 'Campesino').replace(/'/g, "\\'");
                    ratingBtnHtml = `<button class="btn" style="margin-top: 10px; background-color: #ffc107; color: #000; padding: 6px 12px; font-size: 0.9rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;" onclick="openRatingModal('${pedido.id}', '${safeName}')">🌟 Calificar Campesino</button>`;
                } else {
                    const stars = '★'.repeat(pedido.calificacion_comprador) + '☆'.repeat(5 - pedido.calificacion_comprador);
                    ratingBtnHtml = `<p style="margin: 10px 0 0 0; font-size: 0.9rem; color: #ffab00;">Tu calificación: <span style="font-size: 1.1rem;">${stars}</span></p>`;
                }
            } else if (pedido.estado === 'pending' || pedido.estado === 'confirmed') {
                cancelBtnHtml = `<button class="btn" style="margin-top: 10px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 6px 12px; font-size: 0.9rem; border-radius: 4px; cursor: pointer;" onclick="openCancelOrderModal('${pedido.id}')">🚫 Cancelar Pedido</button>`;
            }

            return `
             <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                 <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 10px;">
                     <div><strong style="font-size: 1.1em;">Pedido #${pedido.id}</strong> <span style="color:#777; font-size: 0.85rem; margin-left:10px;">🕒 ${date} ${time}</span></div>
                     <div style="background-color: ${statusColor}; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold;">
                         ${statusLabel}
                     </div>
                 </div>
                 <div style="display: flex; justify-content: space-between;">
                     <div style="flex: 1;">
                         <p style="margin: 0 0 5px 0;"><strong>Productos:</strong></p>
                         ${detailsHtml}
                     </div>
                     <div style="text-align: right; min-width: 120px; display: flex; flex-direction: column; justify-content: flex-end;">
                         <p style="margin: 0 0 5px 0; font-size: 1.1rem; color: #2d5016;"><strong>Total: $${parseFloat(pedido.total || 0).toLocaleString()}</strong></p>
                         ${ratingBtnHtml}
                         ${cancelBtnHtml}
                     </div>
                 </div>
             </div>`;
        }).join('');

    } catch (error) {
        console.error("Error fetching orders:", error);
        list.innerHTML = '<div style="color:red; text-align:center;">Error al cargar los pedidos desde el servidor.</div>';
    }
}

// ----------------------------------------------------
// CANCELACIÓN DE PEDIDOS (COMPRADOR)
// ----------------------------------------------------
window.openCancelOrderModal = function(orderId) {
    const modal = document.getElementById('cancelOrderModal');
    if (!modal) return;
    
    document.getElementById('cancelOrderIdDisplay').textContent = `#${orderId}`;
    document.getElementById('cancelOrderIdHidden').value = orderId;
    
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
};

window.closeCancelOrderModal = function() {
    const modal = document.getElementById('cancelOrderModal');
    if (modal) modal.style.display = 'none';
};

// Configurar eventos del modal de cancelación
document.addEventListener('DOMContentLoaded', function() {
    const closeBtn = document.getElementById('closeCancelOrderModal');
    const declineBtn = document.getElementById('declineCancelBtn');
    const confirmBtn = document.getElementById('confirmCancelBtn');

    if (closeBtn) closeBtn.addEventListener('click', closeCancelOrderModal);
    if (declineBtn) declineBtn.addEventListener('click', closeCancelOrderModal);
    
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function() {
            const orderId = document.getElementById('cancelOrderIdHidden').value;
            if (!orderId) return;

            this.disabled = true;
            this.textContent = 'Cancelando...';

            try {
                // Llamada a la API para cancelar
                await orderApi.cancelar(orderId);
                
                showNotification(`Pedido ${orderId} cancelado correctamente`, 'success');
                closeCancelOrderModal();
                loadOrders(); // Recarga la pestaña actual de pedidos
            } catch (error) {
                console.error("Error al cancelar pedido:", error);
                showNotification(error.message || 'No se pudo cancelar el pedido', 'error');
            } finally {
                this.disabled = false;
                this.textContent = 'Sí, cancelar';
            }
        });
    }
});

function setupOrderTabs() {
    const tabBtns = document.querySelectorAll('.order-tabs .tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            loadOrders();
        });
    });

    const processBtn = document.getElementById('processPurchaseBtn');
    if (processBtn) processBtn.addEventListener('click', processPurchase);
}

async function processPurchase() {
    let cart = JSON.parse(localStorage.getItem('comprador_cart') || '[]');
    if (cart.length === 0) return;

    // Filtrar posibles items del carrito antiguos (sin campesino_id)
    const validCart = cart.filter(item => item.campesino_id);
    if (validCart.length < cart.length) {
        cart = validCart;
        localStorage.setItem('comprador_cart', JSON.stringify(cart));
        updateCartBadge();

        if (cart.length === 0) {
            showNotification("Tus productos guardados caducaron o eran inválidos. Por favor, agrégalos de nuevo desde el Marketplace.", "warning");
            loadOrders();
            return;
        } else {
            showNotification("Algunos productos del carrito ya no están disponibles y fueron removidos.", "info");
        }
    }

        const profileData = await authApi.getProfile();
        // Agrupar por campesino porque el backend exige que 1 pedido = 1 campesino
        const ordersByCampesino = {};
        cart.forEach(item => {
            const campId = item.campesino_id;
            if (!campId) return; // ignore invalid items
            if (!ordersByCampesino[campId]) {
                ordersByCampesino[campId] = {
                    campesino: parseInt(campId),
                    notas_comprador: "Pedido generado desde la web",
                    metodo_pago: "efectivo",
                    metodo_entrega: "recogida",
                    direccion_entrega: profileData?.direccion || "Dirección no registrada",
                    telefono_contacto: profileData?.telefono || "Teléfono no registrado",
                    detalles: []
                };
            }
            ordersByCampesino[campId].detalles.push({
                producto: item.id,
                cantidad: item.quantity,
                precio_unitario: item.price
            });
        });

    const validOrders = Object.values(ordersByCampesino);
    if (validOrders.length === 0) {
        showNotification("No hay productos válidos en el carrito.", "error");
        return;
    }

    const btn = document.getElementById('processPurchaseBtn');
    const originalText = btn.textContent;
    btn.textContent = "Procesando...";
    btn.disabled = true;

    try {
        const promises = validOrders.map(orderPayload => {
            return orderApi.createOrder(orderPayload);
        });

        await Promise.all(promises);

        showNotification("¡Pedido(s) creado(s) exitosamente!", "success");
        localStorage.removeItem('comprador_cart');
        updateCartBadge();

        // Ir a la pestaña de Activos
        const activeTabBtn = document.querySelector('.order-tabs .tab-btn[data-tab="active"]');
        if (activeTabBtn) activeTabBtn.click();
        else loadOrders();

    } catch (error) {
        console.error("Error procesando compra:", error);
        let errMsg = "Hubo un error al procesar el pedido. Verifica el stock.";
        if (error.message) {
            errMsg = error.message;
        }
        if (error.details) {
             try {
                 const detailStr = JSON.stringify(error.details);
                 if (detailStr.length < 150) errMsg += `\n${detailStr}`;
             } catch(e) {}
        }
        showNotification(errMsg, "error");
    } finally {
        if (btn) {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }
}

// Función para eliminar item del carrito
window.removeFromCart = function (cartItemId) {
    let cart = JSON.parse(localStorage.getItem('comprador_cart') || '[]');
    cart = cart.filter(item => item.cartItemId !== cartItemId);
    localStorage.setItem('comprador_cart', JSON.stringify(cart));
    showNotification('Producto eliminado del pedido', 'info');
    loadOrders();
};

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

// ----------------------------------------------------
// MI PERFIL Y CONFIGURACIÓN
// ----------------------------------------------------
async function loadProfileData() {
    try {
        const profile = await authApi.getProfile();
        if (profile) {
            document.getElementById('profileNombre').value = profile.nombre || '';
            document.getElementById('profileApellido').value = profile.apellido || '';
            document.getElementById('profileTelefono').value = profile.telefono || '';
            document.getElementById('profileEmail').value = profile.email || '';
            document.getElementById('profileFechaNacimiento').value = profile.fecha_nacimiento || '';
            document.getElementById('profileDireccion').value = profile.direccion || '';

            // Cargar imagen de perfil si existe
            if (profile.avatar) {
                const avatarImg = document.getElementById('profileAvatarImg');
                const headerAvatarImg = document.getElementById('headerAvatarImg');
                const placeholder = document.getElementById('profileAvatarPlaceholder');
                const headerPlaceholder = document.getElementById('headerAvatarContainer');
                
                if (avatarImg) avatarImg.src = profile.avatar;
                else if (placeholder) {
                    const container = document.getElementById('profileAvatarLarge');
                    if (container) {
                        container.innerHTML = `<img src="${profile.avatar}" alt="Foto de Perfil" id="profileAvatarImg" style="width: 100%; height: 100%; object-fit: cover;">`;
                    }
                }
                
                if (headerAvatarImg) headerAvatarImg.src = profile.avatar;
                else if (headerPlaceholder) {
                    headerPlaceholder.innerHTML = `<img src="${profile.avatar}" alt="Perfil" id="headerAvatarImg" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
                }
            }

            // Actualizar visibilidad del botón de eliminar foto
            const deleteBtn = document.getElementById('deleteProfilePhotoBtn');
            if (deleteBtn) {
                deleteBtn.style.display = profile.avatar ? 'inline-block' : 'none';
            }
        }
        
        // Configurar listener para la foto de perfil (solo una vez)
        setupProfilePhotoUpload();
    } catch (error) {
        console.error("Error al cargar perfil:", error);
    }
}

function setupProfilePhotoUpload() {
    const photoInput = document.getElementById('profilePhotoInput');
    const deleteBtn = document.getElementById('deleteProfilePhotoBtn');
    
    if (!photoInput || photoInput.dataset.initialized) return;
    photoInput.dataset.initialized = 'true';
    
    photoInput.addEventListener('change', async function() {
        const file = this.files[0];
        if (!file) return;
        
        // Validar tipo (solo fotos, nada de gif o video)
        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!allowedTypes.includes(file.type)) {
            showNotification('Solo se permiten fotos (JPG, PNG). No se admiten GIFs ni videos.', 'error');
            this.value = '';
            return;
        }
        
        // Validar tamaño (máx 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showNotification('La imagen es demasiado grande. Máximo 5MB.', 'error');
            return;
        }
        
        // Mostrar previsualización inmediata y loading
        const avatarLarge = document.getElementById('profileAvatarLarge');
        const originalContent = avatarLarge.innerHTML;
        avatarLarge.style.opacity = '0.5';
        
        const formData = new FormData();
        formData.append('avatar', file);
        
        try {
            console.log('[Dashboard Comprador] Subiendo foto de perfil...');
            const response = await authApi.updateProfile(formData);
            console.log('[Dashboard Comprador] Foto de perfil actualizada:', response);
            
            const userData = response.user || response;
            if (userData && userData.avatar) {
                // Actualizar todas las imágenes en la UI
                const newAvatarUrl = userData.avatar;
                
                // Avatar grande
                avatarLarge.innerHTML = `<img src="${newAvatarUrl}" alt="Foto de Perfil" id="profileAvatarImg" style="width: 100%; height: 100%; object-fit: cover;">`;
                
                // Avatar en el header
                const headerAvatarContainer = document.getElementById('headerAvatarContainer');
                if (headerAvatarContainer) {
                    headerAvatarContainer.innerHTML = `<img src="${newAvatarUrl}" alt="Perfil" id="headerAvatarImg" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
                }
                
                // Mostrar botón eliminar
                if (deleteBtn) deleteBtn.style.display = 'inline-block';
                
                showNotification('¡Foto de perfil actualizada!', 'success');
            }
        } catch (error) {
            console.error('[Dashboard Comprador] Error subiendo foto:', error);
            avatarLarge.innerHTML = originalContent;
            showNotification('Error al subir la foto: ' + error.message, 'error');
        } finally {
            avatarLarge.style.opacity = '1';
            // Resetear input
            photoInput.value = '';
        }
    });

    if (deleteBtn) {
        deleteBtn.addEventListener('click', async function() {
            if (!confirm('¿Estás seguro de que deseas eliminar tu foto de perfil?')) return;
            
            const originalText = this.textContent;
            this.disabled = true;
            this.textContent = 'Eliminando...';
            
            try {
                // Enviar null para eliminar la foto
                const response = await authApi.updateProfile({ avatar: null });
                console.log('[Dashboard Comprador] Foto de perfil eliminada:', response);
                
                // Actualizar UI al estado predeterminado
                const avatarLarge = document.getElementById('profileAvatarLarge');
                if (avatarLarge) {
                    avatarLarge.innerHTML = '<span id="profileAvatarPlaceholder">🛒</span>';
                }
                
                const headerAvatarContainer = document.getElementById('headerAvatarContainer');
                if (headerAvatarContainer) {
                    // Restaurar avatar predeterminado
                    headerAvatarContainer.innerHTML = '🛒';
                }
                
                this.style.display = 'none';
                showNotification('Foto de perfil eliminada', 'success');
            } catch (error) {
                console.error('[Dashboard Comprador] Error eliminando foto:', error);
                showNotification('Error al eliminar la foto', 'error');
                this.textContent = originalText;
                this.disabled = false;
            }
        });
    }
}

document.getElementById('profileForm')?.addEventListener('submit', async function (e) {
    e.preventDefault();
    const btn = document.getElementById('saveProfileBtn');
    btn.disabled = true;
    btn.textContent = 'Guardando...';

    const profileData = {
        nombre: document.getElementById('profileNombre').value.trim(),
        apellido: document.getElementById('profileApellido').value.trim(),
        telefono: document.getElementById('profileTelefono').value.trim(),
        email: document.getElementById('profileEmail').value.trim(),
        direccion: document.getElementById('profileDireccion').value.trim()
    };
    
    const fecha = document.getElementById('profileFechaNacimiento').value;
    if (fecha) {
        profileData.fecha_nacimiento = fecha;
    }

    try {
        await authApi.updateProfile(profileData);
        if (typeof showNotification === 'function') {
            showNotification('Perfil actualizado exitosamente', 'success');
        } else {
            alert('Perfil actualizado exitosamente');
        }

        // Actualizar UI
        const userNameElement = document.getElementById('userName');
        if (userNameElement) userNameElement.textContent = profileData.nombre + ' ' + profileData.apellido;

    } catch (error) {
        console.error("Error al guardar perfil:", error);
        if (typeof showNotification === 'function') {
            showNotification('Error al guardar el perfil: ' + error.message, 'error');
        } else {
            alert('Error al guardar el perfil: ' + error.message);
        }
    } finally {
        btn.disabled = false;
        btn.textContent = '💾 Guardar Cambios';
    }
});

// Manejo del Cambio de Contraseña
document.getElementById('changePasswordForm')?.addEventListener('submit', async function (e) {
    e.preventDefault();
    
    const cp = document.getElementById('currentPassword').value;
    const np = document.getElementById('newPassword').value;
    const npc = document.getElementById('newPasswordConfirm').value;
    
    if (np !== npc) {
        if (typeof showNotification === 'function') showNotification('Las nuevas contraseñas no coinciden', 'error');
        else alert('Las nuevas contraseñas no coinciden');
        return;
    }
    
    const btn = document.getElementById('changePasswordBtn');
    btn.disabled = true;
    btn.textContent = 'Guardando...';

    try {
        await authApi.changePassword({
            current_password: cp,
            new_password: np,
            new_password_confirm: npc
        });
        
        if (typeof showNotification === 'function') showNotification('Contraseña actualizada con éxito', 'success');
        else alert('Contraseña actualizada con éxito');
        
        document.getElementById('changePasswordForm').reset();
    } catch (error) {
        console.error("Error cambiando contraseña:", error);
        let msgDetalle = error.message;
        if (error.details) {
            try { msgDetalle += " - " + JSON.stringify(error.details); } catch (ex) { }
        }
        if (typeof showNotification === 'function') showNotification('Error al cambiar contraseña: ' + msgDetalle, 'error');
        else alert('Error al cambiar contraseña:\n' + msgDetalle);
    } finally {
        btn.disabled = false;
        btn.textContent = '🔑 Cambiar Contraseña';
    }
});

// ==========================================================================
// MÓDULO DE CHAT (ANTI-INTERMEDIARIOS)
// ==========================================================================
let activeConversationId = null;
let chatPollingInterval = null;
let myChatUserId = null; // Guardará nuestro ID numérico usando los datos de las conversaciones

async function loadConversations() {
    try {
        const response = await chatApi.getConversations();
        renderConversations(response.results || response);
    } catch (error) {
        console.error("Error cargando conversaciones:", error);
        document.getElementById('chatContactsList').innerHTML = `<li style="padding: 20px; text-align: center; color: red;">Error al cargar chats: <br><small>${error.message}</small><br><small>${error.stack?.substring(0,100)}</small></li>`;
    }
}

function renderConversations(conversations) {
    const listEl = document.getElementById('chatContactsList');
    listEl.innerHTML = '';
    
    if (!conversations || conversations.length === 0) {
        listEl.innerHTML = `<li style="padding: 20px; text-align: center; color: #888;">No hay chats iniciados. Cuando realices compras aparecerán aquí.</li>`;
        return;
    }

    const isCampesino = window.location.pathname.includes('dashboard') && !window.location.pathname.includes('comprador');

    conversations.forEach(conv => {
        // Almacenamos nuestra propia ID para saber qué burbujas pintar verde/blanco luego
        if (!myChatUserId) {
            myChatUserId = isCampesino ? conv.campesino : conv.comprador;
        }

        const li = document.createElement('li');
        li.className = `chat-contact ${activeConversationId === conv.id ? 'active' : ''}`;
        
        // Identificar nombre de la contraparte a renderizar
        let counterPartName = isCampesino ? conv.comprador_nombre : conv.campesino_nombre;
        let lastMsg = conv.ultimo_mensaje ? conv.ultimo_mensaje.contenido : 'Conversación iniciada';
        let unreadBadge = conv.mensajes_no_leidos > 0 ? `<span style="background: #e74c3c; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.75rem; margin-left: auto; font-weight: bold;">${conv.mensajes_no_leidos}</span>` : '';
        
        li.innerHTML = `
            <div class="chat-avatar">${counterPartName.charAt(0).toUpperCase()}</div>
            <div class="chat-contact-info">
                <h4 class="chat-contact-name">${counterPartName}</h4>
                <p class="chat-contact-preview">${lastMsg}</p>
            </div>
            ${unreadBadge}
        `;
        
        li.addEventListener('click', () => {
             // Actualizar UI del chat activo
             document.querySelectorAll('.chat-contact').forEach(el => el.classList.remove('active'));
             li.classList.add('active');
             
             if(conv.mensajes_no_leidos > 0) {
                 li.querySelector('span')?.remove(); // quita el badge al clickear
             }
             
             openChat(conv.id, counterPartName);
        });
        
        listEl.appendChild(li);
    });
}

function openChat(convId, counterPartName) {
    activeConversationId = convId;
    
    // Cambiar vistas
    document.getElementById('chatEmptyState').style.display = 'none';
    document.getElementById('chatMainArea').style.display = 'flex';
    document.getElementById('activeChatName').textContent = counterPartName;
    document.getElementById('activeChatAvatar').textContent = counterPartName.charAt(0).toUpperCase();
    
    // Ajuste móvil
    if(window.innerWidth <= 768) {
        document.querySelector('.chat-sidebar').style.display = 'none';
        document.getElementById('chatMobileBackBtn').style.display = 'block';
    }
    
    // Carga inicial 
    loadMessages(convId);
    
    // Iniciar el Polling por si responden en vivo (cada 4 segundos)
    if(chatPollingInterval) clearInterval(chatPollingInterval);
    chatPollingInterval = setInterval(() => loadMessages(convId, true), 4000);
}

document.getElementById('chatMobileBackBtn')?.addEventListener('click', () => {
    document.querySelector('.chat-sidebar').style.display = 'flex';
    document.getElementById('chatMainArea').style.display = 'none';
    document.getElementById('chatMobileBackBtn').style.display = 'none';
    if(chatPollingInterval) clearInterval(chatPollingInterval);
    activeConversationId = null;
    loadConversations();
});

async function loadMessages(convId, isPolling = false) {
    try {
        const messages = await chatApi.getMessages(convId);
        renderMessages(messages);
        
        if (!isPolling || document.visibilityState === 'visible') {
            await chatApi.markAsRead(convId);
        }
    } catch (error) {
        console.error("Error al cargar mensajes:", error);
    }
}

function renderMessages(messages) {
    const area = document.getElementById('chatMessagesArea');
    
    // Optimización muy básica de DOM para evitar flickers en el polling
    const newLength = messages.length;
    let oldLength = area.dataset.msgCount ? parseInt(area.dataset.msgCount) : 0;
    if (newLength === oldLength && newLength > 0) return; 
    
    area.innerHTML = '';
    area.dataset.msgCount = newLength;

    if (!messages || messages.length === 0) {
        area.innerHTML = '<p style="text-align:center; color:#888; margin-top: 2rem;">Inicio de la conversación.</p>';
        return;
    }

    messages.forEach(msg => {
        const div = document.createElement('div');
        
        let msgType = 'received';
        if (msg.tipo_mensaje === 'sistema') {
            // El mensaje sistema o autogenerado por el backend
            msgType = 'system';
        } else if (msg.remitente === myChatUserId) {
            msgType = 'sent';
        }
        
        div.className = `chat-bubble-wrapper ${msgType}`;
        const timeStr = new Date(msg.fecha_envio).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        div.innerHTML = `
            <div class="chat-bubble">
                <span style="white-space: pre-wrap;">${msg.contenido}</span>
                <span class="chat-time">${timeStr}</span>
            </div>
        `;
        area.appendChild(div);
    });
    
    // Auto-scroll the chat
    area.scrollTop = area.scrollHeight;
}

document.getElementById('chatForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!activeConversationId) return;
    
    const input = document.getElementById('chatInputMessage');
    const txt = input.value.trim();
    if(!txt) return;
    
    input.value = '';
    input.disabled = true;
    
    try {
        await chatApi.sendMessage(activeConversationId, {
            tipo_mensaje: 'texto',
            contenido: txt
        });
        
        loadMessages(activeConversationId);
        loadConversations();
    } catch(err) {
        console.error(err);
        alert('Error enviando mensaje.');
        input.value = txt; 
    } finally {
        input.disabled = false;
        input.focus();
    }
});

// Listener extra para refrescar chats a demanda cuando se abre la ventana (al darle a Navegación -> Mensajes)
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        if(e.currentTarget.getAttribute('data-section') === 'messages') {
            updateMsgBadge(0);
            loadConversations();
        } else {
            // Si nos vamos a otra tab, apagamos el polling del chat activo
            if(chatPollingInterval) clearInterval(chatPollingInterval);
        }
    });
});

// ==========================================================================
// POLLER GLOBAL DE NOTIFICACIONES DE MENSAJES
// ==========================================================================
let _lastUnreadCount = 0;
let _globalMsgPoller = null;

function updateMsgBadge(count) {
    const badge = document.getElementById('msgNavBadge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
    document.title = count > 0 ? `(${count}) Campo Directo` : 'Campo Directo';
}

async function pollUnreadMessages() {
    if (document.visibilityState !== 'visible') return;
    const messagesSection = document.getElementById('messages');
    if (messagesSection && messagesSection.classList.contains('active') && activeConversationId) return;

    try {
        const response = await chatApi.getConversations();
        const conversations = response.results || response;
        const totalUnread = conversations.reduce((sum, c) => sum + (c.mensajes_no_leidos || 0), 0);

        updateMsgBadge(totalUnread);

        if (totalUnread > _lastUnreadCount && _lastUnreadCount !== null) {
            triggerBrowserNotification(totalUnread - _lastUnreadCount, conversations);
        }
        _lastUnreadCount = totalUnread;
    } catch (e) {
        console.debug('[ChatPoller] Error silenciado:', e.message);
    }
}

function triggerBrowserNotification(count, conversations) {
    if (!('Notification' in window)) return;
    const convWithUnread = conversations.find(c => c.mensajes_no_leidos > 0);
    const senderName = convWithUnread ? convWithUnread.campesino_nombre : 'Alguien';
    const body = count === 1 ? `${senderName} te envió un mensaje.` : `Tienes ${count} mensajes nuevos.`;

    if (Notification.permission === 'granted') {
        const n = new Notification('💬 Campo Directo', { body, icon: '/static/images/logo.png' });
        setTimeout(() => n.close(), 5000);
        n.onclick = () => {
            window.focus();
            document.querySelector('[data-section="messages"]')?.click();
        };
    } else if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

document.addEventListener('click', function askNotifPermission() {
    if (Notification.permission === 'default') Notification.requestPermission();
    document.removeEventListener('click', askNotifPermission);
}, { once: true });

setTimeout(() => {
    pollUnreadMessages();
    _globalMsgPoller = setInterval(pollUnreadMessages, 10000);
}, 5000);

function populateLocationFilter() {
    const locationFilter = document.getElementById('locationFilter');
    if (!locationFilter || !window.colombiaData) {
        console.warn('[Marketplace] No se pudo cargar colombiaData o no se encontró el selector de ubicación.');
        return;
    }

    // Limpiar opciones previas excepto la primera (id="")
    while (locationFilter.options.length > 1) {
        locationFilter.remove(1);
    }

    // Ordenar departamentos alfabéticamente
    const sortedData = [...window.colombiaData].sort((a, b) => 
        a.departamento.localeCompare(b.departamento)
    );

    sortedData.forEach(item => {
        const option = document.createElement('option');
        // Usamos el nombre del departamento en minúsculas como valor para el filtro JS
        option.value = item.departamento.toLowerCase();
        
        // Asignar emoji temático según la región
        let emoji = '📍';
        const d = item.departamento.toLowerCase();
        if (d.includes('cundinamarca') || d.includes('bogot')) emoji = '🏔️';
        else if (d.includes('antioquia') || d.includes('boyac')) emoji = '⛰️';
        else if (d.includes('atl') || d.includes('bol') || d.includes('magdalena') || d.includes('guajira')) emoji = '🌊';
        else if (d.includes('valle')) emoji = '💃';
        else if (d.includes('meta') || d.includes('casanare') || d.includes('vichada')) emoji = '🐎';
        else if (d.includes('santander')) emoji = '🧗';
        else if (d.includes('huila') || d.includes('tolima')) emoji = '🏜️';
        else if (d.includes('quind') || d.includes('risaralda') || d.includes('caldas')) emoji = '☕';
        else if (d.includes('nar') || d.includes('cauca') || d.includes('putumayo')) emoji = '🌋';
        else if (d.includes('amazonas') || d.includes('guain') || d.includes('vaup')) emoji = '🌳';
        
        option.textContent = `${emoji} ${item.departamento}`;
        locationFilter.appendChild(option);
    });
    console.log(`[Marketplace] Filtro de ubicación poblado con ${sortedData.length} departamentos colombianos.`);
}