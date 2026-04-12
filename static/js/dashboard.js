// Dashboard JavaScript - Campo Directo (Campesinos)

document.addEventListener('DOMContentLoaded', async function () {
    console.log('[Dashboard] Iniciando dashboard campesino con autenticación JWT');

    // Verificar autenticación JWT (solo si no estamos ya en dashboard cargado por Django)
    console.log('[Dashboard] Verificando estado de autenticación...');

    // Si estamos aquí, es porque Django ya verificó la autenticación en el servidor
    // No necesitamos redirigir, pero podemos intentar usar JWT si está disponible
    const hasJwtToken = isAuthenticated();
    console.log('[Dashboard] JWT Token disponible:', hasJwtToken);

    // Intentar obtener perfil usando API (funciona con JWT O con Cookie de Sesión de Django gracias a credentials: 'include')
    try {
        console.log('[Dashboard] Intentando obtener perfil de forma asíncrona...');
        const profile = await authApi.getProfile();

        if (profile && profile.tipo_usuario === 'campesino') {
            console.log(`[Dashboard] Perfil cargado: ${profile.nombre} ${profile.apellido}`);
            
            // Guardar ID para el sistema de chat y otros componentes
            window.currentUserId = profile.id;

            // Actualizar nombre en la UI
            const userNameElement = document.getElementById('userName');
            if (userNameElement && userNameElement.textContent.includes('Usuario')) {
                userNameElement.textContent = `${profile.nombre} ${profile.apellido}`;
            }

            // Cargar datos reales del dashboard
            console.log('[Dashboard] Iniciando carga de datos reales...');
            await loadRealDashboardData();
            console.log('[Dashboard] Carga de datos reales completada.');
        } else if (profile && profile.tipo_usuario !== 'campesino') {
            console.log('[Dashboard] Usuario no es campesino, ignorando datos de dashboard');
        }

    } catch (error) {
        console.warn('[Dashboard] Error obteniendo perfil de la API, puede ser sesión no válida o sin permisos:', error);
        
        // Aún así, intentamos cargar los datos del dashboard en caso de que sea sólo el perfil lo que falló
        try {
            console.log('[Dashboard] Fallback: Intentando cargar datos reales del dashboard directamente...');
            await loadRealDashboardData();
        } catch (e) {
            console.error('[Dashboard] Error definitivo al cargar datos.', e);
        }
    }

    // Mostrar la aplicación
    const app = document.getElementById('appContainer');
    if (app) {
        app.style.display = 'block';
    }

    setupNavigation();
    setupLogout();
    setupProductModal();
    setupRatingModal();
    setupOrderTabsCampesino();
    
    // Escuchar el cambio en el selector de periodo para estadísticas
    const salesPeriodSelect = document.getElementById('salesPeriod');
    if (salesPeriodSelect) {
        salesPeriodSelect.addEventListener('change', async function(e) {
            console.log('[Dashboard] Cambiando periodo de ventas a:', e.target.value);
            await loadRealDashboardData(e.target.value);
            
            // Si la vista está en "ventas", necesitamos volver a renderizar con la nueva información
            const salesSection = document.getElementById('sales');
            if (salesSection && salesSection.classList.contains('active')) {
                if (dashboardData.stats.ventas_grafico && dashboardData.stats.ventas_grafico.labels.length > 0) {
                    renderSalesChart(dashboardData.stats.ventas_grafico);
                }
            }
        });
    }

    // updateStats() se llama desde loadRealDashboardData()

    // Cargar productos del usuario
    await loadUserProducts();

    console.log('[Dashboard] Dashboard campesino cargado');
});

let salesChart = null;
let dashboardData = {
    stats: {
        activeProducts: 0,
        pendingOrders: 0,
        monthSales: 0,
        rating: 0.0,
        productsSold: 0,
        uniqueCustomers: 0,
        ventas_grafico: { labels: [], data: [] }
    },
    recentActivity: []
};

// Cargar datos reales del dashboard desde la API
async function loadRealDashboardData(period = 'month') {
    try {
        console.log(`[Dashboard] Cargando datos reales del usuario (periodo: ${period})...`);
        console.log('[Dashboard] URL del endpoint:', '/api/users/dashboard/');

        // Obtener datos del dashboard del usuario
        console.log('[Dashboard] Haciendo petición a la API con authApi.getDashboard()...');
        const data = await authApi.getDashboard(period);
        console.log('[Dashboard] Datos obtenidos:', data);

        if (data) {
            // Actualizar datos del dashboard
            dashboardData.stats = {
                activeProducts: data.productos_activos || 0,
                pendingOrders: data.pedidos_pendientes || 0,
                monthSales: data.ventas_mes || 0,
                rating: data.calificacion || 0.0,
                productsSold: (data.estadisticas && data.estadisticas.productos_vendidos) || data.productos_vendidos || 0,
                uniqueCustomers: (data.estadisticas && data.estadisticas.clientes_unicos) || data.clientes_unicos || 0,
                ventas_grafico: (data.estadisticas && data.estadisticas.ventas_grafico) || data.ventas_grafico || { labels: [], data: [] }
            };

            dashboardData.recentActivity = data.actividad_reciente || [];

            // Actualizar UI con datos reales
            updateStats(period);
            updateRecentActivity();
            
            // Renderizar gráfico si hay datos
            console.log('[Dashboard] Datos para grafico:', dashboardData.stats.ventas_grafico);
            if (dashboardData.stats.ventas_grafico && dashboardData.stats.ventas_grafico.labels.length > 0) {
                console.log('[Dashboard] Intentando renderizado inicial del grafico...');
                renderSalesChart(dashboardData.stats.ventas_grafico);
            }

            console.log('[Dashboard] Datos actualizados en la UI');
        } else {
            console.warn('[Dashboard] No se pudieron cargar datos del dashboard, respuesta:', response.status);
            console.log('[Dashboard] Usuario probablemente autenticado por sesión Django, usando datos del template');
            // No llamar updateStats() para no sobrescribir datos del template Django
        }
    } catch (error) {
        console.error('[Dashboard] Error cargando datos del dashboard:', error);
        console.error('[Dashboard] Detalles del error:', error.message, error.stack);
        console.log('[Dashboard] No se pueden cargar datos vía API, usando datos del template Django');
        // No llamar updateStats() para preservar datos del template Django
    }
}

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
                if (targetSection === 'orders') {
                    loadCampesinoOrders();
                } else if (targetSection === 'products') {
                    loadUserProducts();
                } else if (targetSection === 'sales') {
                    // Renderizar el gráfico cuando se muestra la sección de ventas
                    if (dashboardData.stats.ventas_grafico && dashboardData.stats.ventas_grafico.labels.length > 0) {
                        setTimeout(() => renderSalesChart(dashboardData.stats.ventas_grafico), 100);
                    }
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
    console.log('[Dashboard] Iniciando proceso de logout...');

    // Limpiar tokens JWT inmediatamente
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    console.log('[Dashboard] Tokens JWT eliminados');

    try {
        // Usar endpoint Django para logout de sesión
        console.log('[Dashboard] Redirigiendo a /logout/ para cerrar sesión Django');
        window.location.href = '/logout/';
    } catch (error) {
        console.warn('[Dashboard] Error al redirigir a logout:', error);
        // Fallback: redirigir directamente al home
        window.location.href = '/';
    }
}

function updateStats(period = 'month') {
    const activeProductsEl = document.getElementById('activeProducts');
    const pendingOrdersEl = document.getElementById('pendingOrders');
    const monthSalesEl = document.getElementById('monthSales');
    const totalRevenueEl = document.getElementById('totalRevenue');
    const productsSoldEl = document.getElementById('productsSold');
    const uniqueCustomersEl = document.getElementById('uniqueCustomers');
    const ratingEl = document.getElementById('rating');
    const userRatingEl = document.getElementById('userRating');

    // Cambiar leyendas según el periodo
    const revenuePeriodEl = document.getElementById('revenuePeriodLabel');
    const productsPeriodEl = document.getElementById('productsPeriodLabel');
    const customersPeriodEl = document.getElementById('customersPeriodLabel');
    const chartPeriodEl = document.getElementById('chartPeriodLabel');

    let periodText = 'Este mes';
    let revenuePeriodText = 'Mes actual';
    let chartText = 'Ventas por Día';

    if (period === 'week') {
        periodText = 'Esta semana';
        revenuePeriodText = 'Semana actual';
        chartText = 'Ventas por Día';
    } else if (period === 'year') {
        periodText = 'Este año';
        revenuePeriodText = 'Año actual';
        chartText = 'Ventas por Mes';
    }

    if (revenuePeriodEl) revenuePeriodEl.textContent = revenuePeriodText;
    if (productsPeriodEl) productsPeriodEl.textContent = periodText;
    if (customersPeriodEl) customersPeriodEl.textContent = periodText;
    if (chartPeriodEl) chartPeriodEl.textContent = chartText;

    if (activeProductsEl) activeProductsEl.textContent = dashboardData.stats.activeProducts;
    if (pendingOrdersEl) pendingOrdersEl.textContent = dashboardData.stats.pendingOrders;
    
    // El dashboard campesino tiene IDs diferentes para las tarjetas de resumen
    if (monthSalesEl) monthSalesEl.textContent = formatCurrency(dashboardData.stats.monthSales);
    if (totalRevenueEl) totalRevenueEl.textContent = formatCurrency(dashboardData.stats.monthSales);
    
    if (productsSoldEl) productsSoldEl.textContent = `${dashboardData.stats.productsSold} unidades`;
    if (uniqueCustomersEl) uniqueCustomersEl.textContent = dashboardData.stats.uniqueCustomers;
    
    if (ratingEl) ratingEl.textContent = dashboardData.stats.rating.toFixed(1);
}

// ============================================================
// FUNCIONALIDAD: MIS RESEÑAS (CAMPESINO)
// ============================================================
async function abrirModalMisResenas() {
    console.log('[Dashboard] Abriendo modal de Mis Reseñas...');
    const modal = document.getElementById('misResenasModal');
    const closeBtn = document.getElementById('closeMisResenasModal');
    const container = document.getElementById('misResenasContainer');
    
    if (!modal) return;
    
    // Configurar cierre
    if (closeBtn) {
        closeBtn.onclick = () => modal.style.display = 'none';
    }
    
    // Cerrar si hace clic fuera
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
    
    // Mostrar modal con loader
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    container.innerHTML = `
        <div style="text-align: center; padding: 30px;">
            <span class="loader" style="width: 30px; height: 30px; border: 3px solid #f3f3f3; border-top: 3px solid #2d5016; border-radius: 50%; display: inline-block; animation: spin 1s linear infinite;"></span>
            <p style="margin-top: 15px; color: #666;">Cargando tus reseñas...</p>
        </div>
    `;
    
    try {
        // Cargar reseñas utilizando el authApi genérico (o userApi)
        let data;
        let esAutor = false;
        
        try {
            // Intentamos usar el endpoint del usuario campesino
            const campesinoId = window.currentUserId;
            if (campesinoId && window.userApi && window.userApi.getResenasCampesino) {
                console.log(`[Dashboard] Obteniendo reseñas para campesino ID: ${campesinoId}`);
                data = await window.userApi.getResenasCampesino(campesinoId);
            } else if (window.userApi && window.userApi.getMisResenas) {
                console.log(`[Dashboard] Obteniendo mis reseñas directamente`);
                data = await window.userApi.getMisResenas();
                esAutor = true;
            } else {
                throw new Error("No hay método disponible para cargar reseñas");
            }
        } catch (apiError) {
            console.warn('[Dashboard] Falló getResenasCampesino, probando getMisResenas...', apiError);
            if (window.userApi && window.userApi.getMisResenas) {
                data = await window.userApi.getMisResenas();
                esAutor = true;
            } else {
                throw apiError;
            }
        }
        
        const resenas = data.resenas || data.results || data;
        
        if (!resenas || !Array.isArray(resenas) || resenas.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 30px; color: #666;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">⭐</div>
                    <h3>Aún no tienes calificaciones</h3>
                    <p>Cuando un comprador califique tus productos, aparecerán aquí.</p>
                </div>
            `;
            return;
        }
        
        // Estructura General:
        let html = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid #eee;">
                <div>
                    <div style="font-size: 3rem; font-weight: bold; color: #2d5016;">${dashboardData.stats.rating.toFixed(1)}</div>
                </div>
                <div>
                    <div style="color: #ffc107; font-size: 1.5rem;">${'★'.repeat(Math.round(dashboardData.stats.rating))}${'☆'.repeat(5 - Math.round(dashboardData.stats.rating))}</div>
                    <div style="color: #666; font-size: 0.9rem;">Basado en ${resenas.length} calificación(es)</div>
                </div>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 15px;">
        `;
        
        resenas.forEach(resena => {
            // Manejar diferencias entre formatos de API
            const stars = resena.calificacion || resena.estrellas || resena.calificacion_campesino || 5;
            const text = resena.comentario || resena.comentario_calificacion || "Sin comentario adicional.";
            // Si tiene pedido, podemos mostrar quién lo generó
            let name = "Usuario Anónimo";
            if (resena.comprador_nombre) name = resena.comprador_nombre;
            else if (resena.autor) name = resena.autor;
            
            let date = resena.fecha ? new Date(resena.fecha).toLocaleDateString() : "";
            
            html += `
                <div style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <strong style="color: #333;">${name}</strong>
                        <span style="color: #888; font-size: 0.85rem;">${date}</span>
                    </div>
                    <div style="color: #ffc107; margin-bottom: 8px;">
                        ${'★'.repeat(stars)}${'☆'.repeat(5 - stars)}
                    </div>
                    <p style="color: #555; margin: 0; font-size: 0.95rem; line-height: 1.4;">"${text}"</p>
                </div>
            `;
        });
        
        html += `</div>`;
        container.innerHTML = html;
        
    } catch (e) {
        console.error('[Dashboard] Error cargando reseñas:', e);
        container.innerHTML = `
            <div style="text-align: center; padding: 30px; color: #e74c3c;">
                <p>Ocurrió un error al cargar tus reseñas.</p>
                <small>${e.message}</small>
            </div>
        `;
    }
}

/**
 * Renderiza el gráfico de ventas usando Chart.js
 */
function renderSalesChart(data) {
    console.log('[Chart] Iniciando renderizado con:', data);
    
    if (typeof Chart === 'undefined') {
        console.error('[Chart] ERROR: La librería Chart.js no está cargada.');
        return;
    }

    const ctx = document.getElementById('salesChart');
    if (!ctx) {
        console.error('[Chart] ERROR: No se encontró el elemento canvas #salesChart');
        return;
    }
    
    console.log('[Chart] Canvas encontrado, dimensiones:', ctx.offsetWidth, 'x', ctx.offsetHeight);

    if (salesChart) {
        console.log('[Chart] Destruyendo gráfico previo');
        salesChart.destroy();
    }

    try {
        salesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Ventas Diarias ($)',
                data: data.data,
                borderColor: '#2d5016',
                backgroundColor: 'rgba(45, 80, 22, 0.1)',
                borderWidth: 3,
                pointBackgroundColor: '#2d5016',
                pointBorderColor: '#fff',
                pointHoverRadius: 6,
                pointRadius: 4,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000) {
                                return '$' + (value / 1000) + 'k';
                            }
                            return '$' + value;
                        },
                        font: {
                            family: "'Segoe UI', sans-serif",
                            size: 11
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: "'Segoe UI', sans-serif",
                            size: 11
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#2d5016',
                    bodyColor: '#333',
                    borderColor: '#2d5016',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return 'Ventas: ' + formatCurrency(context.parsed.y);
                        }
                    }
                }
            }
        }
    });
        console.log('[Chart] Gráfico renderizado exitosamente');
    } catch (error) {
        console.error('[Chart] ERROR fatal renderizando gráfico:', error);
    }
}

function updateRecentActivity() {
    const activityList = document.getElementById('recentActivityList');
    if (!activityList) return;

    if (dashboardData.recentActivity.length === 0) {
        activityList.innerHTML = `
            <div class="activity-item">
                <span class="activity-icon">📈</span>
                <div class="activity-content">
                    <p><strong>No hay actividad reciente</strong></p>
                    <small>Comienza agregando productos a tu finca</small>
                </div>
            </div>
        `;
        return;
    }

    activityList.innerHTML = dashboardData.recentActivity.map(activity => `
        <div class="activity-item">
            <span class="activity-icon">${getActivityIcon(activity.estado)}</span>
            <div class="activity-content">
                <p><strong>${activity.descripcion}</strong></p>
                <small>${activity.tiempo}</small>
            </div>
        </div>
    `).join('');
}

function getActivityIcon(estado) {
    const iconMap = {
        'completed': '✅',
        'pending': '🕰️',
        'confirmed': '📝',
        'preparing': '🚚',
        'ready': '🎁',
        'cancelled': '❌'
    };
    return iconMap[estado] || '📦';
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0
    }).format(amount);
}


// ============================================================
// FUNCIONALIDAD DEL MODAL DE PRODUCTOS
// ============================================================

function setupProductModal() {
    console.log('[Dashboard] Configurando modal de productos...');

    // Elementos del modal
    const addProductBtn = document.getElementById('addProductBtn');
    const modal = document.getElementById('addProductModal');
    const closeModal = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelProduct');
    const productForm = document.getElementById('addProductForm');
    const categorySelect = document.getElementById('productCategory');

    // Abrir modal
    if (addProductBtn) {
        addProductBtn.addEventListener('click', function (e) {
            e.preventDefault();
            openProductModal();
        });
    }

    // Cerrar modal
    if (closeModal) {
        closeModal.addEventListener('click', closeProductModal);
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeProductModal);
    }

    // Cerrar al hacer click fuera del modal (en el backdrop)
    if (modal) {
        modal.addEventListener('click', function (e) {
            const modalContent = modal.querySelector('.modal-content');
            if (modalContent && !modalContent.contains(e.target)) {
                closeProductModal();
            }
        });
    }

    // Enviar formulario
    if (productForm) {
        productForm.addEventListener('submit', handleProductSubmit);
    }

    console.log('[Dashboard] Modal de productos configurado');

    // Configurar otros modales
    setupEditModal();
    setupDeleteModal();

    console.log('[Dashboard] Todos los modales configurados');

    // Inicializar sistema de notificaciones
    initNotificationSystem();
}

async function openProductModal() {
    console.log('[Dashboard] Abriendo modal de productos...');

    const modal = document.getElementById('addProductModal');
    if (!modal) return;

    // Cargar categorías
    await loadProductCategories();

    // Resetear formulario
    const form = document.getElementById('addProductForm');
    if (form) {
        form.reset();
        clearFormErrors();
    }

    // Mostrar modal
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevenir scroll del body

    // Focus en el primer input
    const firstInput = modal.querySelector('input[type="text"]');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
}

function closeProductModal() {
    console.log('[Dashboard] Cerrando modal de productos...');

    const modal = document.getElementById('addProductModal');
    if (!modal) return;

    modal.style.display = 'none';
    document.body.style.overflow = ''; // Restaurar scroll del body

    // Limpiar formulario
    const form = document.getElementById('addProductForm');
    if (form) {
        form.reset();
        clearFormErrors();
    }
}

async function loadProductCategories() {
    console.log('[Dashboard] Cargando categorías de productos...');

    const categorySelect = document.getElementById('productCategory');
    if (!categorySelect) return;

    try {
        console.log('[Dashboard] Intentando cargar categorías desde la API...');

        // Intentar cargar directamente sin usar authApi para evitar problemas con JWT
        let response;
        try {
            response = await fetch('/api/products/categorias/', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            console.log('[Dashboard] Respuesta de categorías:', response.status, response.statusText);
        } catch (fetchError) {
            console.error('[Dashboard] Error en fetch de categorías:', fetchError);
            throw fetchError;
        }

        if (response.ok) {
            const categories = await response.json();
            console.log('[Dashboard] Categorías cargadas desde API:', categories);

            // La respuesta puede ser un array directo o tener results
            const categoryList = Array.isArray(categories) ? categories : (categories.results || []);
            console.log('[Dashboard] Lista de categorías procesada:', categoryList);

            if (categoryList.length > 0) {
                // Limpiar opciones existentes
                categorySelect.innerHTML = '<option value="">Seleccionar categoría</option>';

                // Agregar categorías
                categoryList.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.nombre;
                    categorySelect.appendChild(option);
                    console.log(`[Dashboard] Añadida categoría: ${category.nombre} (ID: ${category.id})`);
                });

                console.log('[Dashboard] Categorías cargadas exitosamente desde la API');
                return;
            } else {
                console.warn('[Dashboard] No se encontraron categorías en la API, usando fallback');
            }
        } else {
            console.warn(`[Dashboard] Error ${response.status} cargando categorías, usando fallback`);
        }

        // Fallback: categorías hardcodeadas con IDs reales de la DB
        console.log('[Dashboard] Usando categorías por defecto con IDs de la DB...');
        categorySelect.innerHTML = `
            <option value="">Seleccionar categoría</option>
            <option value="13">Vegetales y Hortalizas</option>
            <option value="10">Frutas</option>
            <option value="14">Granos y Cereales</option>
            <option value="15">Hierbas Aromáticas</option>
            <option value="16">Tubérculos</option>
            <option value="17">Legumbres</option>
            <option value="18">Productos Avícolas</option>
            <option value="19">Carnes y Pescados</option>
            <option value="20">Lácteos y Derivados</option>
            <option value="21">Plantas y Flores</option>
            <option value="22">Insumos Agrícolas</option>
            <option value="23">Miel y Procesados</option>
        `;

    } catch (error) {
        console.error('[Dashboard] Error cargando categorías:', error);

        // Usar categorías por defecto en caso de error con IDs reales de la DB
        console.log('[Dashboard] Usando categorías de fallback con IDs reales');
        categorySelect.innerHTML = `
            <option value="">Seleccionar categoría</option>
            <option value="13">Vegetales y Hortalizas</option>
            <option value="10">Frutas</option>
            <option value="14">Granos y Cereales</option>
            <option value="15">Hierbas Aromáticas</option>
            <option value="16">Tubérculos</option>
            <option value="17">Legumbres</option>
            <option value="18">Productos Avícolas</option>
            <option value="19">Carnes y Pescados</option>
            <option value="20">Lácteos y Derivados</option>
            <option value="21">Plantas y Flores</option>
            <option value="22">Insumos Agrícolas</option>
            <option value="23">Miel y Procesados</option>
        `;
    }
}

// Crear categorías por defecto si no existen
async function createDefaultCategories() {
    console.log('[Dashboard] Verificando/creando categorías por defecto...');
    // Esta función podría hacer una llamada a la API para crear categorías si no existen
    // Por ahora es solo un placeholder
}

// Obtener la finca principal del usuario campesino
async function getUserFinca() {
    console.log('[Dashboard] Obteniendo finca del usuario...');

    try {
        // Intentar obtener la finca del endpoint de fincas
        const headers = { 'X-CSRFToken': getCsrfToken() };
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }

        const response = await fetch('/api/farms/fincas/mis_fincas/', {
            method: 'GET',
            headers: headers,
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            console.log('[Dashboard] Respuesta de mis_fincas:', data);
            const fincas = Array.isArray(data) ? data : (data.results || data);

            console.log('[Dashboard] Mis fincas procesadas:', fincas);

            if (fincas.length > 0) {
                const miFinca = fincas[0];
                console.log('[Dashboard] Mi finca encontrada:', miFinca);
                console.log('[Dashboard] ID de mi finca:', miFinca.id);
                return miFinca.id;
            } else {
                console.warn('[Dashboard] Usuario no tiene fincas registradas');
                return null;
            }
        } else {
            const responseText = await response.text();
            console.error('[Dashboard] Error obteniendo mis fincas:', response.status, response.statusText, responseText);

            // Fallback: intentar con el endpoint general si el específico falla
            console.log('[Dashboard] Intentando fallback con endpoint general...');
            try {
                const fallbackResponse = await fetch('/api/farms/fincas/', {
                    method: 'GET',
                    headers: headers,
                    credentials: 'include'
                });

                if (fallbackResponse.ok) {
                    const fallbackData = await fallbackResponse.json();
                    const todasLasFincas = Array.isArray(fallbackData) ? fallbackData : (fallbackData.results || []);

                    // Filtrar solo las fincas que pertenecen al usuario actual
                    const misFincas = todasLasFincas.filter(finca =>
                        finca.campesino_nombre && finca.campesino_nombre.includes('Juan Carlos')
                    );

                    console.log('[Dashboard] Fallback - Mis fincas filtradas:', misFincas);

                    if (misFincas.length > 0) {
                        console.log('[Dashboard] Fallback - Finca encontrada:', misFincas[0]);
                        return misFincas[0].id;
                    }
                }
            } catch (fallbackError) {
                console.error('[Dashboard] Error en fallback:', fallbackError);
            }

            return null;
        }
    } catch (error) {
        console.error('[Dashboard] Error en getUserFinca:', error);
        return null;
    }
}

async function handleProductSubmit(e) {
    e.preventDefault();
    console.log('[Dashboard] Enviando formulario de producto...');

    // Limpiar errores anteriores
    clearFormErrors();

    // Obtener datos del formulario
    const formData = new FormData(e.target);

    // Obtener ID de categoría desde el select
    const categorySelect = document.getElementById('productCategory');
    const selectedOption = categorySelect.options[categorySelect.selectedIndex];
    const categoryId = selectedOption ? selectedOption.value : null;

    console.log('[Dashboard] Categoría seleccionada:', categoryId, selectedOption?.text);

    const productData = {
        nombre: formData.get('productName'),
        categoria: parseInt(categoryId), // Debe ser un ID numérico
        precio_por_kg: parseFloat(formData.get('productPrice')), // Nombre correcto del campo
        stock_disponible: parseInt(formData.get('productStock')),
        descripcion: formData.get('productDescription') || '',
        unidad_medida: formData.get('productUnit') || 'kg',
        estado: 'disponible'
    };

    console.log('[Dashboard] Datos del producto preparados (sin finca):', productData);

    // Obtener ID de finca del usuario
    console.log('[Dashboard] Obteniendo finca del usuario...');
    const fincaId = await getUserFinca();

    if (!fincaId) {
        showNotification('No tienes una finca registrada. Debes registrar una finca antes de agregar productos.', 'error');
        return;
    }

    // Agregar la finca a los datos del producto
    productData.finca = fincaId;
    console.log('[Dashboard] ID de finca obtenido y agregado:', fincaId);
    console.log('[Dashboard] Datos completos del producto:', productData);

    // Validación básica
    const validation = validateProductData(productData);
    if (!validation.isValid) {
        showFormErrors(validation.errors);
        return;
    }

    // Mostrar loading después de todas las validaciones
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Agregando...';
    submitBtn.disabled = true;

    try {
        // Preparar FormData para el envío (incluyendo imagen)
        const submitData = new FormData();

        // Agregar campos de datos del producto, evitando null values
        Object.keys(productData).forEach(key => {
            const value = productData[key];
            if (value !== null && value !== undefined) {
                submitData.append(key, value);
                console.log(`[Dashboard] Agregando campo ${key}:`, value, typeof value);
            } else {
                console.warn(`[Dashboard] Campo ${key} es null/undefined:`, value);
            }
        });

        // Agregar imagen si existe (usar el nombre correcto del campo)
        const imageFile = formData.get('productImage');
        if (imageFile && imageFile.size > 0) {
            submitData.append('imagen_principal', imageFile); // Usar el nombre correcto del campo
            console.log('[Dashboard] Imagen agregada:', imageFile.name, imageFile.size, 'bytes');
        }

        // Obtener CSRF token
        const csrfToken = getCsrfToken();
        console.log('[Dashboard] CSRF Token:', csrfToken ? 'Encontrado' : 'No encontrado');

        // Configurar headers base
        const headers = {
            'X-CSRFToken': csrfToken
        };

        // Añadir autenticación JWT si está disponible
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
            console.log('[Dashboard] Usando autenticación JWT');
        } else {
            console.log('[Dashboard] Usando autenticación de sesión Django');
        }

        console.log('[Dashboard] Enviando request a /api/products/productos/');
        console.log('[Dashboard] Headers que se enviarán:', headers);

        // Verificar estado de autenticación adicional
        const sessionInfo = document.querySelector('[data-user-authenticated]');
        if (sessionInfo) {
            console.log('[Dashboard] Usuario autenticado por sesión Django:', sessionInfo.dataset.userAuthenticated);
        }

        // Verificar información del usuario desde el DOM
        const userNameElement = document.getElementById('userName');
        if (userNameElement) {
            console.log('[Dashboard] Nombre de usuario desde DOM:', userNameElement.textContent);
        }

        // Verificar datos del usuario desde el contexto Django
        if (window.dashboardData) {
            console.log('[Dashboard] Datos completos del usuario:', window.dashboardData.usuario);
            console.log('[Dashboard] Tipo de usuario:', window.dashboardData.usuario.tipo_usuario);
            console.log('[Dashboard] Es campesino:', window.dashboardData.usuario.tipo_usuario === 'campesino');
            console.log('[Dashboard] Tiene finca:', window.dashboardData.finca.tiene_finca);
            console.log('[Dashboard] Autenticado:', window.dashboardData.usuario.is_authenticated);
        }

        // Enviar a la API
        const response = await fetch('/api/products/productos/', {
            method: 'POST',
            headers: headers,
            credentials: 'include', // Importante para cookies de sesión
            body: submitData
        });

        console.log('[Dashboard] Respuesta del servidor:', response.status, response.statusText);
        console.log('[Dashboard] Headers de respuesta:', Object.fromEntries(response.headers.entries()));

        if (response.ok) {
            const result = await response.json();
            console.log('[Dashboard] Producto creado exitosamente:', result);

            showNotification('¡Producto agregado exitosamente!', 'success');
            closeProductModal();

            // Recargar la lista de productos
            await loadUserProducts();

            // Navegar a la sección de productos para mostrar el nuevo producto
            const productsTab = document.querySelector('[data-section="products"]');
            if (productsTab) {
                productsTab.click();
            }

        } else {
            console.error('[Dashboard] Error - Status:', response.status, 'StatusText:', response.statusText);

            let errorData;
            try {
                const responseText = await response.text();
                console.log('[Dashboard] Respuesta completa del servidor:', responseText);

                // Intentar parsear como JSON
                if (responseText) {
                    try {
                        errorData = JSON.parse(responseText);
                    } catch (parseError) {
                        console.error('[Dashboard] Error parseando JSON:', parseError);
                        errorData = { detail: responseText };
                    }
                } else {
                    errorData = { detail: `Error ${response.status}: ${response.statusText}` };
                }
            } catch (readError) {
                console.error('[Dashboard] Error leyendo respuesta:', readError);
                errorData = { detail: `Error de conexión (${response.status})` };
            }

            console.error('[Dashboard] Error procesado:', errorData);

            if (response.status === 400 && errorData) {
                // Errores de validación del servidor
                showFormErrors(errorData);
            } else if (response.status === 401) {
                showNotification('Error de autenticación. Por favor, inicia sesión nuevamente.', 'error');
            } else if (response.status === 403) {
                showNotification('No tienes permisos para agregar productos. Asegúrate de ser un usuario campesino.', 'error');
            } else {
                const message = errorData?.detail || errorData?.message || 'Error al agregar el producto. Inténtalo de nuevo.';
                showNotification(message, 'error');
            }
        }

    } catch (error) {
        console.error('[Dashboard] Error al enviar producto:', error);
        showNotification('Error de conexión. Verifica tu internet e inténtalo de nuevo.', 'error');
    } finally {
        // Restaurar botón
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

function validateProductData(data) {
    const errors = [];

    if (!data.nombre || data.nombre.trim().length < 2) {
        errors.push({ field: 'productName', message: 'El nombre debe tener al menos 2 caracteres' });
    }

    if (!data.categoria || isNaN(data.categoria)) {
        errors.push({ field: 'productCategory', message: 'Selecciona una categoría válida' });
    }

    if (!data.precio_por_kg || data.precio_por_kg <= 0) {
        errors.push({ field: 'productPrice', message: 'El precio debe ser mayor a 0' });
    }

    if (!data.stock_disponible || data.stock_disponible <= 0) {
        errors.push({ field: 'productStock', message: 'La cantidad debe ser mayor a 0' });
    }

    if (!data.finca) {
        errors.push({ field: 'general', message: 'No se pudo obtener la información de tu finca' });
    }

    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

function showFormErrors(errors) {
    // Si errors es un objeto (errores del servidor)
    if (typeof errors === 'object' && !Array.isArray(errors)) {
        Object.keys(errors).forEach(fieldName => {
            const messages = Array.isArray(errors[fieldName]) ? errors[fieldName] : [errors[fieldName]];
            messages.forEach(message => {
                showFieldError(fieldName, message);
            });
        });
    } else if (Array.isArray(errors)) {
        // Si es un array (errores de validación local)
        errors.forEach(error => {
            showFieldError(error.field, error.message);
        });
    }
}

function showFieldError(fieldName, message) {
    // Mapeo especial para cuando DRF devuelve los keys del modelo Python
    const fieldMap = {
        'precio_por_kg': 'productPrice',
        'nombre': 'productName',
        'categoria': 'productCategory',
        'stock_disponible': 'productStock',
        'descripcion': 'productDescription'
    };
    
    // Si el nombre viene del Python, intentar pasarlo a ID del HTML
    const finalId = fieldMap[fieldName] || fieldName;
    const field = document.getElementById(finalId);
    
    if (!field) {
        // En caso de que sea un error general y no encaje en un ID, mostramos una alerta flotante obligatoria
        showNotification(message, 'error');
        return;
    }

    // Añadir clase de error
    field.classList.add('error');

    // Buscar o crear elemento de error
    let errorElement = field.parentNode.querySelector('.field-error');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        field.parentNode.appendChild(errorElement);
    }

    errorElement.textContent = message;
}

function clearFormErrors() {
    // Limpiar clases de error
    const errorFields = document.querySelectorAll('#addProductForm .error');
    errorFields.forEach(field => {
        field.classList.remove('error');
    });

    // Limpiar mensajes de error
    const errorMessages = document.querySelectorAll('#addProductForm .field-error');
    errorMessages.forEach(msg => {
        msg.remove();
    });
}

// Función para cargar productos del usuario
async function loadUserProducts() {
    console.log('[Dashboard] Cargando productos del usuario...');

    try {
        const headers = { 'X-CSRFToken': getCsrfToken() };
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }

        const response = await fetch('/api/products/productos/mis_productos/', {
            method: 'GET',
            headers: headers,
            credentials: 'include'
        });

        if (response.ok) {
            const productos = await response.json();
            console.log('[Dashboard] Productos cargados:', productos);
            displayProducts(productos);
            updateProductStats(productos.length);
        } else {
            console.error('[Dashboard] Error cargando productos:', response.status, response.statusText);
            displayNoProducts();
        }
    } catch (error) {
        console.error('[Dashboard] Error en loadUserProducts:', error);
        displayNoProducts();
    }
}

// Función para mostrar productos en la interfaz
function displayProducts(productos) {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;

    if (productos.length === 0) {
        displayNoProducts();
        return;
    }

    let html = '';
    productos.forEach(producto => {
        html += `
            <div class="product-card">
                <div class="product-image">
                    ${producto.imagen_principal ?
                `<a href="${producto.imagen_principal}" onclick="event.preventDefault(); openLightbox('${producto.imagen_principal}')" title="Haz clic para ver la imagen completa" style="display:block; height:100%;"><img src="${producto.imagen_principal}" alt="${producto.nombre}" style="cursor:zoom-in;" /></a>` :
                '<div class="no-image">📦</div>'
            }
                </div>
                <div class="product-info">
                    <h4 class="product-name">${producto.nombre}</h4>
                    <p class="product-category">${producto.categoria_nombre || 'Sin categoría'}</p>
                    <p class="product-price">$${producto.precio_por_kg} / ${producto.unidad_medida}</p>
                    <p class="product-stock">Stock: ${producto.stock_disponible}</p>
                    <div class="product-status status-${producto.estado}">
                        ${producto.estado.charAt(0).toUpperCase() + producto.estado.slice(1)}
                    </div>
                </div>
                <div class="product-actions">
                    <button class="btn btn-sm btn-primary" onclick="editProduct(${producto.id})" title="Editar producto">
                        ✏️ Editar
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProduct(${producto.id})" title="Eliminar producto">
                        🗑️ Eliminar
                    </button>
                </div>
            </div>
        `;
    });

    productsGrid.innerHTML = html;
}

// Función para mostrar mensaje cuando no hay productos
function displayNoProducts() {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;

    productsGrid.innerHTML = `
        <div class="no-products">
            <div class="no-products-icon">📦</div>
            <h3>No tienes productos registrados</h3>
            <p>Comienza agregando tu primer producto para vender</p>
            <button class="btn btn-primary" onclick="openProductModal()">
                + Agregar Primer Producto
            </button>
        </div>
    `;
}

// Función para actualizar estadísticas de productos
function updateProductStats(count) {
    const activeProductsElement = document.getElementById('activeProducts');
    if (activeProductsElement) {
        activeProductsElement.textContent = count;
    }
}

// Funciones placeholder para acciones de productos
async function editProduct(productId) {
    console.log('[Dashboard] Abriendo modal de edición para producto:', productId);

    try {
        // Obtener datos del producto
        const headers = { 'X-CSRFToken': getCsrfToken() };
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }

        const response = await fetch(`/api/products/productos/${productId}/`, {
            method: 'GET',
            headers: headers,
            credentials: 'include'
        });

        if (response.ok) {
            const producto = await response.json();
            console.log('[Dashboard] Datos del producto obtenidos:', producto);

            // Cargar categorías en el modal de edición
            await loadCategoriesForEdit();

            // Llenar el formulario con los datos actuales
            fillEditForm(producto);

            // Mostrar el modal
            showEditModal();
        } else {
            console.error('[Dashboard] Error obteniendo producto:', response.status);
            showNotification('Error al cargar los datos del producto', 'error');
        }
    } catch (error) {
        console.error('[Dashboard] Error en editProduct:', error);
        showNotification('Error de conexión al cargar el producto', 'error');
    }
}

// Llenar formulario de edición con datos del producto
function fillEditForm(producto) {
    document.getElementById('editProductId').value = producto.id;
    document.getElementById('editProductName').value = producto.nombre;
    document.getElementById('editProductCategory').value = producto.categoria || '';
    document.getElementById('editProductPrice').value = producto.precio_por_kg;
    document.getElementById('editProductUnit').value = producto.unidad_medida || 'kg';
    document.getElementById('editProductStock').value = producto.stock_disponible;
    document.getElementById('editProductDescription').value = producto.descripcion || '';
    document.getElementById('editProductStatus').value = producto.estado;
}

// Cargar categorías para el modal de edición
async function loadCategoriesForEdit() {
    const categorySelect = document.getElementById('editProductCategory');
    if (!categorySelect) return;

    try {
        const response = await fetch('/api/products/categorias/', {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const categories = Array.isArray(data) ? data : (data.results || []);

            categorySelect.innerHTML = '<option value="">Seleccionar categoría</option>';

            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.nombre;
                categorySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('[Dashboard] Error cargando categorías para edición:', error);
        // Usar categorías de fallback
        categorySelect.innerHTML = `
            <option value="">Seleccionar categoría</option>
            <option value="13">Vegetales y Hortalizas</option>
            <option value="10">Frutas</option>
            <option value="14">Granos y Cereales</option>
            <option value="15">Hierbas Aromáticas</option>
            <option value="16">Tubérculos</option>
            <option value="17">Legumbres</option>
            <option value="18">Productos Avícolas</option>
            <option value="19">Carnes y Pescados</option>
            <option value="20">Lácteos y Derivados</option>
            <option value="21">Plantas y Flores</option>
            <option value="22">Insumos Agrícolas</option>
            <option value="23">Miel y Procesados</option>
        `;
    }
}

// === FUNCIONES DE MODALES ===
function showEditModal() {
    const modal = document.getElementById('editProductModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // Focus en el primer input
        const firstInput = modal.querySelector('input[type="text"]');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

function hideEditModal() {
    const modal = document.getElementById('editProductModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';

        // Limpiar formulario
        const form = document.getElementById('editProductForm');
        if (form) {
            form.reset();
        }
    }
}

// Configurar eventos de modales
function setupEditModal() {
    const modal = document.getElementById('editProductModal');
    const closeBtn = document.getElementById('closeEditModal');
    const cancelBtn = document.getElementById('cancelEditProduct');
    const form = document.getElementById('editProductForm');

    if (closeBtn) {
        closeBtn.addEventListener('click', hideEditModal);
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', hideEditModal);
    }

    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                hideEditModal();
            }
        });
    }

    if (form) {
        form.addEventListener('submit', handleEditSubmit);
    }
}

// Manejar envío de formulario de edición
async function handleEditSubmit(e) {
    e.preventDefault();
    console.log('[Dashboard] Enviando formulario de edición...');

    const formData = new FormData(e.target);
    const productId = formData.get('productId');

    const productData = {
        nombre: formData.get('productName'),
        categoria: parseInt(formData.get('productCategory')),
        precio_por_kg: parseFloat(formData.get('productPrice')),
        stock_disponible: parseInt(formData.get('productStock')),
        descripcion: formData.get('productDescription') || '',
        unidad_medida: formData.get('productUnit') || 'kg',
        estado: formData.get('productStatus')
    };

    console.log('[Dashboard] Datos de edición preparados:', productData);

    // Mostrar loading en el botón
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Actualizando...';
    submitBtn.disabled = true;

    try {
        const submitFormData = new FormData();
        Object.keys(productData).forEach(key => {
            if (productData[key] !== null && productData[key] !== undefined) {
                submitFormData.append(key, productData[key]);
            }
        });

        // Agregar imagen si se seleccionó una nueva
        const imageFile = formData.get('productImage');
        if (imageFile && imageFile.size > 0) {
            submitFormData.append('imagen_principal', imageFile);
        }

        const headers = { 'X-CSRFToken': getCsrfToken() };
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }

        const response = await fetch(`/api/products/productos/${productId}/`, {
            method: 'PATCH',
            headers: headers,
            credentials: 'include',
            body: submitFormData
        });

        if (response.ok) {
            const result = await response.json();
            console.log('[Dashboard] Producto actualizado exitosamente:', result);

            showNotification('Producto actualizado exitosamente', 'success');
            hideEditModal();

            // Recargar la lista de productos
            await loadUserProducts();
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            console.error('[Dashboard] Error actualizando producto:', errorData);

            if (response.status === 400) {
                // Mostrar errores específicos si los hay
                let errorMessage = 'Error de validación:';
                if (typeof errorData === 'object') {
                    Object.keys(errorData).forEach(field => {
                        const fieldErrors = Array.isArray(errorData[field]) ? errorData[field] : [errorData[field]];
                        fieldErrors.forEach(error => {
                            errorMessage += `\n• ${error}`;
                        });
                    });
                } else {
                    errorMessage = errorData.detail || 'Error de validación';
                }
                showNotification(errorMessage, 'error');
            } else {
                showNotification('Error al actualizar el producto: ' + (errorData.detail || 'Error desconocido'), 'error');
            }
        }
    } catch (error) {
        console.error('[Dashboard] Error en handleEditSubmit:', error);
        showNotification('Error de conexión al actualizar el producto', 'error');
    } finally {
        // Restaurar botón
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

// Mostrar modal de confirmación para eliminar
async function deleteProduct(productId) {
    console.log('[Dashboard] Preparando eliminación de producto:', productId);

    try {
        // Obtener datos del producto para mostrar el nombre
        const headers = { 'X-CSRFToken': getCsrfToken() };
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }

        const response = await fetch(`/api/products/productos/${productId}/`, {
            method: 'GET',
            headers: headers,
            credentials: 'include'
        });

        if (response.ok) {
            const producto = await response.json();
            showDeleteModal(productId, producto.nombre);
        } else {
            showDeleteModal(productId, 'Producto desconocido');
        }
    } catch (error) {
        console.error('[Dashboard] Error obteniendo datos del producto:', error);
        showDeleteModal(productId, 'Producto');
    }
}

// Mostrar modal de confirmación
function showDeleteModal(productId, productName) {
    const modal = document.getElementById('confirmDeleteModal');
    const productNameElement = document.getElementById('deleteProductName');

    if (productNameElement) {
        productNameElement.textContent = productName;
    }

    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // Configurar el botón de confirmar para este producto
        const confirmBtn = document.getElementById('confirmDelete');
        if (confirmBtn) {
            confirmBtn.onclick = () => confirmDeleteProduct(productId);
        }
    }
}

// Ocultar modal de confirmación
function hideDeleteModal() {
    const modal = document.getElementById('confirmDeleteModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Confirmar eliminación del producto
async function confirmDeleteProduct(productId) {
    console.log('[Dashboard] Confirmando eliminación de producto:', productId);

    // Cerrar modal
    hideDeleteModal();

    // Mostrar notificación de proceso
    const processingNotification = showNotification('Eliminando producto...', 'info', null, 10000);

    try {
        const headers = { 'X-CSRFToken': getCsrfToken() };
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }

        const response = await fetch(`/api/products/productos/${productId}/`, {
            method: 'DELETE',
            headers: headers,
            credentials: 'include'
        });

        // Cerrar notificación de proceso
        closeNotification(processingNotification);

        if (response.ok) {
            console.log('[Dashboard] Producto eliminado exitosamente');
            showNotification('Producto eliminado exitosamente', 'success');

            // Recargar la lista de productos
            await loadUserProducts();
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            console.error('[Dashboard] Error eliminando producto:', errorData);
            showNotification('Error al eliminar el producto: ' + (errorData.detail || 'Error desconocido'), 'error');
        }
    } catch (error) {
        console.error('[Dashboard] Error en confirmDeleteProduct:', error);
        closeNotification(processingNotification);
        showNotification('Error de conexión al eliminar el producto', 'error');
    }
}

// Configurar modal de eliminación
function setupDeleteModal() {
    const modal = document.getElementById('confirmDeleteModal');
    const closeBtn = document.getElementById('closeConfirmModal');
    const cancelBtn = document.getElementById('cancelDelete');

    if (closeBtn) {
        closeBtn.addEventListener('click', hideDeleteModal);
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', hideDeleteModal);
    }

    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                hideDeleteModal();
            }
        });
    }
}

// Función para cambiar el estado de un producto
async function changeProductStatus(productId, newStatus) {
    console.log(`[Dashboard] Cambiando estado del producto ${productId} a ${newStatus}`);

    const statusNames = {
        'disponible': 'disponible',
        'agotado': 'agotado',
        'inactivo': 'inactivo'
    };

    const actionNames = {
        'disponible': 'activar',
        'agotado': 'marcar como agotado',
        'inactivo': 'desactivar'
    };

    try {
        const headers = {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json'
        };
        const jwtToken = localStorage.getItem('authToken');
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }

        const response = await fetch(`/api/products/productos/${productId}/`, {
            method: 'PATCH',
            headers: headers,
            credentials: 'include',
            body: JSON.stringify({
                estado: newStatus
            })
        });

        if (response.ok) {
            console.log('[Dashboard] Estado del producto actualizado exitosamente');
            showNotification(`Producto ${actionNames[newStatus]} exitosamente`, 'success');

            // Recargar la lista de productos
            await loadUserProducts();
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            console.error('[Dashboard] Error actualizando estado del producto:', errorData);
            showNotification('Error al actualizar el producto: ' + (errorData.detail || 'Error desconocido'), 'error');
        }
    } catch (error) {
        console.error('[Dashboard] Error en changeProductStatus:', error);
        showNotification('Error de conexión al actualizar el producto', 'error');
    }
}

// === SISTEMA DE NOTIFICACIONES MODERNO ===
function initNotificationSystem() {
    // Verificar si el contenedor existe
    let container = document.getElementById('notificationContainer');
    if (container) {
        console.log('[Dashboard] Container de notificaciones encontrado en HTML');
        console.log('[Dashboard] Container classes:', container.className);

        // Asegurarse de que tiene la clase correcta
        if (!container.classList.contains('notification-container')) {
            console.log('[Dashboard] Añadiendo clase notification-container');
            container.classList.add('notification-container');
        }

        // Verificar estilos
        const computedStyle = window.getComputedStyle(container);
        console.log('[Dashboard] Position:', computedStyle.position);
        console.log('[Dashboard] Z-index:', computedStyle.zIndex);
        console.log('[Dashboard] Top:', computedStyle.top);
        console.log('[Dashboard] Right:', computedStyle.right);
    } else {
        console.log('[Dashboard] Container no encontrado, creando...');
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'notification-container';
        document.body.appendChild(container);
        console.log('[Dashboard] Container creado y añadido al body');
    }

    // Forzar estilos CSS críticos si no se están aplicando
    const computedStyle = window.getComputedStyle(container);
    if (computedStyle.position === 'static') {
        console.warn('[Dashboard] Los estilos CSS no se están aplicando. Forzando estilos...');
        container.style.cssText = `
            position: fixed !important;
            top: 20px !important;
            right: 20px !important;
            z-index: 3000 !important;
            max-width: 400px !important;
            pointer-events: none;
        `;

        // Permitir clicks en las notificaciones individuales
        container.addEventListener('click', function (e) {
            e.target.style.pointerEvents = 'auto';
        });
    }

    // Agregar animaciones CSS si no existen
    if (!document.querySelector('#notification-animations')) {
        const animationStyles = document.createElement('style');
        animationStyles.id = 'notification-animations';
        animationStyles.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
            
            @keyframes progressBar {
                from { width: 100%; }
                to { width: 0%; }
            }
        `;
        document.head.appendChild(animationStyles);
    }

    console.log('[Dashboard] Sistema de notificaciones inicializado');
}

function showNotification(message, type = 'info', title = null, duration = 4000) {
    console.log(`[Dashboard] Mostrando notificación: "${message}" (${type})`);

    // Asegurar que el contenedor existe
    let container = document.getElementById('notificationContainer');
    console.log('[Dashboard] Container encontrado:', !!container);

    if (!container) {
        console.warn('[Dashboard] Container de notificaciones no encontrado, creando...');
        initNotificationSystem();
        container = document.getElementById('notificationContainer');
        console.log('[Dashboard] Container después de init:', !!container);
    }

    if (!container) {
        console.error('[Dashboard] Error crítico: No se pudo crear el contenedor de notificaciones');
        // Fallback: usar alert como último recurso
        alert(`${title || type.toUpperCase()}: ${message}`);
        return null;
    }

    console.log('[Dashboard] Container final classes:', container.className);
    console.log('[Dashboard] Container parent:', container.parentElement);
    console.log('[Dashboard] Container computed position:', window.getComputedStyle(container).position);

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    // Forzar estilos críticos para la notificación si es necesario
    notification.style.cssText = `
        background: white;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-left: 4px solid ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#17a2b8'};
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideInRight 0.3s ease-out;
        position: relative;
        overflow: hidden;
        pointer-events: auto;
        min-width: 300px;
    `;

    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠️',
        info: '🛈'
    };

    const titles = {
        success: title || '¡Éxito!',
        error: title || 'Error',
        warning: title || 'Advertencia',
        info: title || 'Información'
    };

    notification.innerHTML = `
        <div class="notification-icon">${icons[type] || icons.info}</div>
        <div class="notification-content">
            <div class="notification-title">${titles[type]}</div>
            <div class="notification-message">${message}</div>
        </div>
        <button class="notification-close" onclick="closeNotification(this.parentElement)">×</button>
        <div class="notification-progress"></div>
    `;

    container.appendChild(notification);

    console.log('[Dashboard] Notificación creada y añadida al container');
    console.log('[Dashboard] Notification classes:', notification.className);
    console.log('[Dashboard] Notification computed styles:', {
        position: window.getComputedStyle(notification).position,
        display: window.getComputedStyle(notification).display,
        background: window.getComputedStyle(notification).backgroundColor
    });

    // Auto-cerrar después del tiempo especificado
    setTimeout(() => {
        closeNotification(notification);
    }, duration);

    return notification;
}

function closeNotification(notification) {
    if (!notification) return;

    notification.style.animation = 'slideOutRight 0.3s ease-out';
    setTimeout(() => {
        if (notification.parentElement) {
            notification.parentElement.removeChild(notification);
        }
    }, 300);
}

// Helper para obtener CSRF token
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return decodeURIComponent(value);
        }
    }
    return '';
}

// ============================================================
// ESTILOS DINÁMICOS PARA EL MODAL
// ============================================================

// Agregar estilos CSS para el modal si no existen
if (!document.querySelector('#modal-styles')) {
    const modalStyles = document.createElement('style');
    modalStyles.id = 'modal-styles';
    modalStyles.textContent = `
        .modal {
            display: none;
            position: fixed;
            z-index: 10000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            animation: fadeIn 0.3s ease;
        }
        
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 0;
            border-radius: 8px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            animation: slideIn 0.3s ease;
        }
        
        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #f8f9fa;
        }
        
        .modal-header h3 {
            margin: 0;
            color: #2d5016;
            font-size: 1.25rem;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #6c757d;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-close:hover {
            color: #dc3545;
        }
        
        .modal-form {
            padding: 1.5rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #333;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e9ecef;
            border-radius: 4px;
            font-size: 1rem;
            transition: border-color 0.2s ease;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #2d5016;
            box-shadow: 0 0 0 3px rgba(45, 80, 22, 0.1);
        }
        
        .form-group input.error,
        .form-group select.error,
        .form-group textarea.error {
            border-color: #dc3545;
            box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1);
        }
        
        .field-error {
            color: #dc3545;
            font-size: 0.875rem;
            margin-top: 0.25rem;
            display: block;
        }
        
        .modal-actions {
            display: flex;
            gap: 0.5rem;
            justify-content: flex-end;
            margin-top: 1.5rem;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .btn-primary {
            background-color: #2d5016;
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            background-color: #1e3610;
        }
        
        .btn-primary:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background-color: #545b62;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        @media (max-width: 768px) {
            .modal-content {
                margin: 2% auto;
                width: 95%;
            }
            
            .modal-actions {
                flex-direction: column;
            }
        }
    `;

    document.head.appendChild(modalStyles);
}

// ============================================================
// INICIALIZACIÓN DEL DASHBOARD
// ============================================================

// Inicializar dashboard cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    console.log('[Dashboard] DOM loaded, inicializando...');

    // Verificar elementos críticos del DOM
    const productsGrid = document.getElementById('productsGrid');
    const notificationContainer = document.getElementById('notificationContainer');
    const sidebar = document.querySelector('.dashboard-sidebar');
    const navItems = document.querySelectorAll('.nav-item');

    console.log('[Dashboard] productsGrid encontrado:', !!productsGrid);
    console.log('[Dashboard] notificationContainer encontrado:', !!notificationContainer);
    console.log('[Dashboard] sidebar encontrado:', !!sidebar);
    console.log('[Dashboard] nav items encontrados:', navItems.length);
    console.log('[Dashboard] Ancho de ventana:', window.innerWidth);

    // Verificar si estamos en móvil
    if (window.innerWidth <= 768) {
        console.log('[Dashboard] Modo móvil detectado');
        if (sidebar) {
            const computedStyles = window.getComputedStyle(sidebar);
            console.log('[Dashboard] Sidebar computed styles:', {
                position: computedStyles.position,
                width: computedStyles.width,
                display: computedStyles.display,
                visibility: computedStyles.visibility
            });

            // Forzar estilos de navegación móvil si no se están aplicando
            if (computedStyles.width !== '100%' || computedStyles.position !== 'sticky') {
                console.warn('[Dashboard] CSS móvil no aplicado, forzando estilos...');

                // Forzar estilos del sidebar
                sidebar.style.cssText = `
                    width: 100% !important;
                    position: sticky !important;
                    top: 0 !important;
                    z-index: 1000 !important;
                    background: white !important;
                    border-right: none !important;
                    border-bottom: 1px solid #e9ecef !important;
                    padding: 0 !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                    margin-bottom: 1rem !important;
                    display: block !important;
                    visibility: visible !important;
                `;

                // Forzar estilos de la lista de navegación
                const navItems = sidebar.querySelector('.nav-items');
                if (navItems) {
                    navItems.style.cssText = `
                        display: flex !important;
                        flex-direction: row !important;
                        overflow-x: auto !important;
                        padding: 0.5rem 0 !important;
                        gap: 0 !important;
                        -webkit-overflow-scrolling: touch !important;
                    `;
                }

                // Forzar estilos de cada item de navegación
                const navItemElements = sidebar.querySelectorAll('.nav-item');
                navItemElements.forEach(item => {
                    item.style.cssText = `
                        flex: 0 0 auto !important;
                        min-width: 120px !important;
                        white-space: nowrap !important;
                        padding: 0.75rem 1rem !important;
                        border-right: none !important;
                        border-bottom: 3px solid transparent !important;
                        text-align: center !important;
                        font-size: 0.85rem !important;
                        gap: 0.5rem !important;
                        flex-direction: column !important;
                        display: flex !important;
                        align-items: center !important;
                        text-decoration: none !important;
                        color: #666 !important;
                        transition: all 0.3s ease !important;
                    `;

                    if (item.classList.contains('active')) {
                        item.style.borderBottomColor = '#2d5016';
                        item.style.background = '#f0f4ed';
                        item.style.color = '#2d5016';
                    }
                });

                console.log('[Dashboard] Estilos móvil forzados aplicados');
            }
        }
    }

    // Configurar autenticación
    setupAuthentication();

    // Configurar navegación
    setupNavigation();

    // Configurar modal de productos
    setupProductModal();

    // Configurar modal de edición
    setupEditModal();

    // Configurar modal de eliminación
    setupDeleteModal();

    // Inicializar sistema de notificaciones
    initNotificationSystem();

    // Probar notificación inicial y estado del sistema después de 3 segundos
    setTimeout(() => {
        console.log('[Dashboard] Probando notificación inicial...');
        showNotification('Sistema inicializado correctamente', 'success', '¡Bienvenido!');

        // Debug adicional sobre el estado del DOM
        setTimeout(() => {
            const container = document.getElementById('notificationContainer');
            const productsGrid = document.getElementById('productsGrid');

            console.log('[Dashboard] === DEBUG DEL ESTADO ===');
            console.log('Container de notificaciones:', container);
            console.log('Productos grid:', productsGrid);
            console.log('Children del container:', container ? container.children.length : 'N/A');
            console.log('Children del products grid:', productsGrid ? productsGrid.children.length : 'N/A');
            console.log('=================================');
        }, 1000);

    }, 3000);

    // Cargar datos iniciales
    loadInitialData();

    // Aplicar navegación móvil después de un breve delay para asegurar que el DOM esté listo
    setTimeout(() => {
        applyMobileNavigation();
    }, 500);

    // Listener para redimensionado de ventana
    window.addEventListener('resize', function () {
        console.log('[Dashboard] Ventana redimensionada:', window.innerWidth);
        setTimeout(() => {
            applyMobileNavigation();
        }, 100);
    });

    console.log('[Dashboard] Inicialización completa');
});

// ============================================================
// FUNCIONES DE CONFIGURACIÓN
// ============================================================

// Configurar autenticación
function setupAuthentication() {
    console.log('[Dashboard] Configurando autenticación...');

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function (e) {
            e.preventDefault();
            // Limpiar tokens
            localStorage.removeItem('authToken');
            // Redirigir al login
            window.location.href = '/accounts/login/';
        });
    }
}

// Configurar navegación
function setupNavigation() {
    console.log('[Dashboard] Configurando navegación...');

    const navItems = document.querySelectorAll('.nav-item[data-section]');
    navItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const section = this.dataset.section;
            showSection(section);
        });
    });

    // Menú de usuario
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function () {
            userDropdown.classList.toggle('show');
        });

        // Cerrar menú al hacer clic fuera
        document.addEventListener('click', function (e) {
            if (!userMenuBtn.contains(e.target)) {
                userDropdown.classList.remove('show');
            }
        });
    }
}

// Mostrar sección
function showSection(sectionName) {
    console.log('[Dashboard] Mostrando sección:', sectionName);

    // Ocultar todas las secciones
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });

    // Mostrar sección seleccionada
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Actualizar navegación activa
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
    });

    const activeNavItem = document.querySelector(`[data-section="${sectionName}"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }

    if (sectionName === 'products') {
        loadUserProducts();
    } else if (sectionName === 'orders') {
        loadCampesinoOrders();
    } else if (sectionName === 'messages') {
        // Asegurar que se carguen las conversaciones al entrar a la sección
        // Esto es crítico para la navegación móvil que usa showSection directamente
        console.log('[Dashboard] Cargando conversaciones para la sección de mensajes');
        loadConversations();
    }
}

// Aplicar navegación móvil
function applyMobileNavigation() {
    if (window.innerWidth <= 768) {
        console.log('[Dashboard] Aplicando navegación móvil...');

        const sidebar = document.querySelector('.dashboard-sidebar');
        if (sidebar) {
            // Forzar estilos del sidebar
            sidebar.style.cssText = `
                width: 100% !important;
                position: sticky !important;
                top: 0 !important;
                z-index: 1000 !important;
                background: white !important;
                border-right: none !important;
                border-bottom: 1px solid #e9ecef !important;
                padding: 0 !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                margin-bottom: 1rem !important;
                display: block !important;
                visibility: visible !important;
            `;

            // Forzar estilos de la lista de navegación
            const navItems = sidebar.querySelector('.nav-items');
            if (navItems) {
                navItems.style.cssText = `
                    display: flex !important;
                    flex-direction: row !important;
                    overflow-x: auto !important;
                    padding: 0.5rem 0 !important;
                    gap: 0 !important;
                    -webkit-overflow-scrolling: touch !important;
                    list-style: none !important;
                    margin: 0 !important;
                `;
            }

            // Forzar estilos de cada item de navegación
            const navItemElements = sidebar.querySelectorAll('.nav-item');
            navItemElements.forEach(item => {
                item.style.cssText = `
                    flex: 0 0 auto !important;
                    min-width: 120px !important;
                    white-space: nowrap !important;
                    padding: 0.75rem 1rem !important;
                    border-right: none !important;
                    border-bottom: 3px solid transparent !important;
                    text-align: center !important;
                    font-size: 0.85rem !important;
                    gap: 0.5rem !important;
                    flex-direction: column !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    text-decoration: none !important;
                    color: #666 !important;
                    transition: all 0.3s ease !important;
                    background: transparent !important;
                `;

                if (item.classList.contains('active')) {
                    item.style.borderBottomColor = '#2d5016 !important';
                    item.style.background = '#f0f4ed !important';
                    item.style.color = '#2d5016 !important';
                }

                // Asegurar que el icono esté visible
                const icon = item.querySelector('.nav-icon');
                if (icon) {
                    icon.style.cssText = `
                        font-size: 1.1rem !important;
                        width: auto !important;
                        text-align: center !important;
                        margin-bottom: 0.25rem !important;
                        display: block !important;
                    `;
                }
            });

            console.log('[Dashboard] Navegación móvil aplicada exitosamente');
        }
    }
}

// Cargar datos iniciales
function loadInitialData() {
    console.log('[Dashboard] Cargando datos iniciales...');

    // Aplicar navegación móvil
    applyMobileNavigation();

    // Cargar datos del usuario
    if (window.dashboardData && window.dashboardData.usuario.is_authenticated) {
        loadUserProducts();
        // Cargar pedidos automáticamente al entrar al dashboard
        loadCampesinoOrders();
    }

    // Polling: notificar al campesino si llega un pedido nuevo cada 30 segundos
    startOrderPolling();
}

// Estado previo de pedidos para detectar nuevos
let _lastKnownPendingCount = null;

async function startOrderPolling() {
    // Primer check inmediato para establecer baseline
    _lastKnownPendingCount = await getOrderPendingCount();

    setInterval(async () => {
        const currentCount = await getOrderPendingCount();
        if (_lastKnownPendingCount !== null && currentCount > _lastKnownPendingCount) {
            const nuevos = currentCount - _lastKnownPendingCount;
            showNotification(
                `Tienes ${nuevos} pedido${nuevos > 1 ? 's' : ''} nuevo${nuevos > 1 ? 's' : ''} pendiente${nuevos > 1 ? 's' : ''} de confirmar.`,
                'warning',
                '🛒 Nuevo Pedido'
            );
            // Recargar la lista de pedidos si la sección está activa
            const ordersSection = document.getElementById('orders');
            if (ordersSection && ordersSection.classList.contains('active')) {
                loadCampesinoOrders();
            }
            // Actualizar badge de pendientes
            updatePendingCount(currentCount);
        }
        _lastKnownPendingCount = currentCount;
    }, 30000); // cada 30 segundos
}

async function getOrderPendingCount() {
    try {
        const response = await orderApi.getMisVentas();
        const pedidos = response.results || response || [];
        return pedidos.filter(p => ['pending', 'confirmed', 'preparing', 'ready'].includes(p.estado)).length;
    } catch {
        return _lastKnownPendingCount ?? 0;
    }
}

// ============================================================
// GESTIÓN DE PEDIDOS DEL CAMPESINO
// ============================================================

function setupOrderTabsCampesino() {
    const tabBtns = document.querySelectorAll('.order-tabs .tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            loadCampesinoOrders();
        });
    });
}

function updatePendingCount(count) {
    const pc = document.getElementById('pendingCount');
    const pc2 = document.getElementById('pendingOrders'); // in stats dashboard
    if (pc) pc.textContent = count;
    if (pc2) pc2.textContent = count;
}

async function loadCampesinoOrders() {
    const list = document.getElementById('ordersList');
    if (!list) return;

    const activeTabObj = document.querySelector('.order-tabs .tab-btn.active');
    const activeTab = activeTabObj ? activeTabObj.dataset.tab : 'pending';

    list.innerHTML = '<div style="text-align:center; padding: 2rem;">Cargando pedidos...</div>';

    try {
        const response = await orderApi.getMisVentas();
        const pedidos = response.results || response || [];

        // Count pending for badge
        const pendingOrders = pedidos.filter(p => ['pending', 'confirmed', 'preparing', 'ready'].includes(p.estado));
        updatePendingCount(pendingOrders.length);

        let filtered = [];
        if (activeTab === 'pending') {
            filtered = pendingOrders;
        } else if (activeTab === 'completed') {
            filtered = pedidos.filter(p => p.estado === 'completed');
        } else if (activeTab === 'cancelled') {
            filtered = pedidos.filter(p => p.estado === 'cancelled');
        }

        if (filtered.length === 0) {
            list.innerHTML = `<div style="text-align:center; padding: 2rem; color: #666;">No hay pedidos en esta categoría.</div>`;
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
            'ready': 'Para Entrega',
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
            let pedidoDescriptLabel = 'Varios productos';
            if (pedido.detalles && pedido.detalles.length > 0) {
                pedidoDescriptLabel = pedido.detalles[0].producto_nombre || 'Producto';
                detailsHtml = '<ul style="margin: 5px 0 0 0; padding-left: 20px; font-size: 0.9rem; color: #555;">';
                pedido.detalles.forEach(d => {
                    const nombreProd = d.producto_nombre || d.nombre_producto_snapshot || 'Producto';
                    detailsHtml += `<li>${d.cantidad}x ${nombreProd} ($${parseFloat(d.precio_unitario).toLocaleString()})</li>`;
                });
                detailsHtml += '</ul>';
            }

            // Generar los botones de acción dependiendo del estado del pedido
            let actionButtons = '';
            if (pedido.estado === 'pending') {
                actionButtons = `
                    <button onclick="changeOrderStatus('${pedido.id}', 'confirmed')" class="btn btn-primary" style="padding: 6px 12px; font-size: 0.85rem; background: #28a745; border: none; border-radius: 4px; color: white;">Aceptar Pedido</button>
                    <button onclick="changeOrderStatus('${pedido.id}', 'cancelled')" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.85rem; background: #dc3545; border: none; border-radius: 4px; color: white;">Rechazar</button>
                 `;
            } else if (pedido.estado === 'confirmed') {
                actionButtons = `
                    <button onclick="changeOrderStatus('${pedido.id}', 'preparing')" class="btn btn-primary" style="padding: 6px 12px; font-size: 0.85rem; background: #fd7e14; border: none; border-radius: 4px; color: white;">Marcar En Preparación</button>
                    <button onclick="changeOrderStatus('${pedido.id}', 'cancelled')" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.85rem; background: #dc3545; border: none; border-radius: 4px; color: white; margin-top:5px;">Cancelar Venta</button>
                 `;
            } else if (pedido.estado === 'preparing') {
                actionButtons = `
                    <button onclick="changeOrderStatus('${pedido.id}', 'ready')" class="btn btn-primary" style="padding: 6px 12px; font-size: 0.85rem; background: #17a2b8; border: none; border-radius: 4px; color: white;">Marcar Listo</button>
                 `;
            } else if (pedido.estado === 'ready') {
                actionButtons = `
                    <button onclick="changeOrderStatus('${pedido.id}', 'completed')" class="btn btn-primary" style="padding: 6px 12px; font-size: 0.85rem; background: #2d5016; border: none; border-radius: 4px; color: white;">Entregado / Completado</button>
                 `;
            } else if (pedido.estado === 'completed') {
                if (pedido.calificacion_campesino == null) {
                    const safeName = (pedido.comprador_nombre || 'Comprador').replace(/'/g, "\\'");
                    actionButtons = `
                        <button onclick="openRatingModal('${pedido.id}', '${safeName}')" class="btn btn-primary" style="padding: 6px 12px; font-size: 0.85rem; background: #ffc107; border: none; border-radius: 4px; color: #000; font-weight: bold;">🌟 Calificar Comprador</button>
                    `;
                } else {
                    const stars = '★'.repeat(pedido.calificacion_campesino) + '☆'.repeat(5 - pedido.calificacion_campesino);
                    actionButtons = `<p style="margin: 0; font-size: 0.9rem; color: #ffab00; text-align: right;">Tu calificación: <br><span style="font-size: 1.1rem;">${stars}</span></p>`;
                }
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
                         <p style="margin: 10px 0 0 0; font-size: 0.9rem;"><strong>Cliente:</strong> ${pedido.comprador_nombre || 'No registrado'}</p>
                         <p style="margin: 5px 0 0 0; font-size: 0.9rem;"><strong>Teléfono:</strong> ${pedido.telefono_contacto || 'No especificado'}</p>
                         <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #17a2b8;"><strong>Dirección de Envío:</strong> ${pedido.direccion_entrega || 'No especificada'}</p>
                     </div>
                     <div style="text-align: right; min-width: 150px; display: flex; flex-direction: column; justify-content: space-between;">
                         <p style="margin: 0 0 10px 0; font-size: 1.1rem; color: #2d5016;"><strong>Total: $${parseFloat(pedido.total || 0).toLocaleString()}</strong></p>
                         <div style="display: flex; flex-direction: column; gap: 5px;">
                             ${actionButtons}
                         </div>
                     </div>
                 </div>
             </div>`;
        }).join('');

    } catch (error) {
        console.error("Error fetching campesino orders:", error);
        list.innerHTML = '<div style="color:red; text-align:center;">Error al cargar tus pedidos de la base de datos.</div>';
    }
}

// Hacer la función global para que los onclick puedan invocarla
window.changeOrderStatus = async function (orderId, newStatus) {
    try {
        await orderApi.updateOrderStatus(orderId, newStatus);

        // Recargar la UI
        loadCampesinoOrders();

        // Notificar
        const msgs = {
            'confirmed': 'Pedido aceptado y guardado.',
            'cancelled': 'Pedido rechazado/cancelado.',
            'preparing': 'Pedido marcado en preparación.',
            'ready': 'Pedido marcado como listo para el comprador.',
            'completed': 'Venta completada exitosamente.'
        };

        if (typeof showNotification === 'function') {
            showNotification(msgs[newStatus] || 'Estado actualizado', 'success');
        } else {
            alert(msgs[newStatus] || 'Estado actualizado');
        }

    } catch (error) {
        console.error("Error changing order status:", error);

        // Mejor manejo para mostrar la causa raíz al usuario
        let msgDetalle = error.message;
        if (error.details) {
            try { msgDetalle += " - " + JSON.stringify(error.details); } catch (e) { }
        }

        if (typeof showNotification === 'function') {
            showNotification('Error: ' + msgDetalle, 'error');
        } else {
            alert('Falla al intentar cambiar el estado del pedido:\n\n' + msgDetalle);
        }
    }
}

// ----------------------------------------------------
// SISTEMA DE CALIFICACIONES (CAMPESINO A COMPRADOR)
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
                loadCampesinoOrders(); // Recarga la pestaña actual
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
            
            // Habilitar botón
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
    
    // Reset
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
            
            const fincaField = document.getElementById('profileNombreFinca');
            if (fincaField) {
                fincaField.value = profile.nombre_finca || '';
            }

            if (profile.tipo_usuario === 'campesino') {
                const deptoSelect = document.getElementById('profileDepartamentoFinca');
                const muniSelect = document.getElementById('profileMunicipioFinca');
                
                if (typeof colombiaData !== 'undefined' && deptoSelect && muniSelect) {
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

                    deptoSelect.innerHTML = '<option value="">Selecciona Departamento</option>';
                    colombiaData.forEach(d => {
                        const option = document.createElement('option');
                        option.value = d.departamento;
                        option.textContent = d.departamento;
                        deptoSelect.appendChild(option);
                    });

                    deptoSelect.addEventListener('change', function() {
                        muniSelect.innerHTML = '<option value="">Selecciona Municipio</option>';
                        if (this.value) {
                            const deptoData = colombiaData.find(d => d.departamento === this.value);
                            if (deptoData) {
                                deptoData.ciudades.forEach(c => {
                                    const option = document.createElement('option');
                                    option.value = c;
                                    option.textContent = c;
                                    muniSelect.appendChild(option);
                                });
                                muniSelect.disabled = false;
                            }
                        } else {
                            muniSelect.disabled = true;
                        }
                    });
                }

                document.getElementById('profileNombreFinca').value = profile.nombre_finca || '';
                
                // Set default values after building the options
                if (profile.departamento_finca) {
                    deptoSelect.value = profile.departamento_finca;
                    // Trigger change to load cities
                    deptoSelect.dispatchEvent(new Event('change'));
                    if (profile.municipio_finca) {
                        muniSelect.value = profile.municipio_finca;
                    }
                }
                
                document.getElementById('fincaFieldGroup').style.display = 'block';
            } else {
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
            console.log('[Dashboard] Subiendo foto de perfil...');
            const response = await authApi.updateProfile(formData);
            console.log('[Dashboard] Foto de perfil actualizada:', response);
            
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
            console.error('[Dashboard] Error subiendo foto:', error);
            avatarLarge.innerHTML = originalContent;
            showNotification('Error al subir la foto: ' + error.message, 'error');
        } finally {
            avatarLarge.style.opacity = '1';
            // Resetear input para permitir subir la misma foto si se desea
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
                console.log('[Dashboard] Foto de perfil eliminada:', response);
                
                // Actualizar UI al estado predeterminado
                const avatarLarge = document.getElementById('profileAvatarLarge');
                if (avatarLarge) {
                    avatarLarge.innerHTML = '<span id="profileAvatarPlaceholder">👤</span>';
                }
                
                const headerAvatarContainer = document.getElementById('headerAvatarContainer');
                if (headerAvatarContainer) {
                    // Restaurar avatar predeterminado
                    headerAvatarContainer.innerHTML = '👤';
                }
                
                this.style.display = 'none';
                showNotification('Foto de perfil eliminada', 'success');
            } catch (error) {
                console.error('[Dashboard] Error eliminando foto:', error);
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
        email: document.getElementById('profileEmail').value.trim()
    };
    
    const fecha = document.getElementById('profileFechaNacimiento').value;
    if (fecha) {
        profileData.fecha_nacimiento = fecha;
    }
    
    const fincaName = document.getElementById('profileNombreFinca').value;
    if(fincaName) profileData.nombre_finca = fincaName;
    
    const depto = document.getElementById('profileDepartamentoFinca').value;
    if(depto) profileData.departamento_finca = depto;
    
    const muni = document.getElementById('profileMunicipioFinca').value;
    if(muni) profileData.municipio_finca = muni;

    profileData.direccion = undefined;

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
// myChatUserId se inicializará con window.currentUserId si está disponible, 
// o se autodetectará de la primera conversación como respaldo.
let myChatUserId = window.currentUserId || null; 

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
        listEl.innerHTML = `<li style="padding: 20px; text-align: center; color: #888;">No hay chats iniciados. Cuando realicen compras aparecerán aquí.</li>`;
        return;
    }

    conversations.forEach(conv => {
        // Determinar el rol del usuario en ESTA conversación específica,
        // comparando el ID real del usuario con el campo campesino/comprador.
        // Esto funciona correctamente en ambos dashboards y al cambiar de rol.
        const myId = window.currentUserId || myChatUserId;
        const iAmCampesino = myId ? (conv.campesino === myId || conv.campesino === parseInt(myId)) : true;

        // Almacenamos nuestra propia ID para saber qué burbujas pintar verde/blanco luego
        if (!myChatUserId) {
            myChatUserId = myId || (iAmCampesino ? conv.campesino : conv.comprador);
        }

        const li = document.createElement('li');
        li.className = `chat-contact ${activeConversationId === conv.id ? 'active' : ''}`;
        li.dataset.id = conv.id;
        li.dataset.name = iAmCampesino ? conv.comprador_nombre : conv.campesino_nombre;
        
        // Identificar nombre de la contraparte a renderizar
        let counterPartName = iAmCampesino ? conv.comprador_nombre : conv.campesino_nombre;
        let lastMsg = conv.ultimo_mensaje ? conv.ultimo_mensaje.contenido : 'Conversación iniciada';
        let unreadBadge = conv.mensajes_no_leidos > 0 ? `<span class="unread-badge" style="background: #e74c3c; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.75rem; margin-left: auto; font-weight: bold;">${conv.mensajes_no_leidos}</span>` : '';
        
        li.innerHTML = `
            <div class="chat-avatar">${counterPartName.charAt(0).toUpperCase()}</div>
            <div class="chat-contact-info">
                <h4 class="chat-contact-name">${counterPartName}</h4>
                <p class="chat-contact-preview">${lastMsg}</p>
            </div>
            ${unreadBadge}
        `;
        
        listEl.appendChild(li);
    });

    // Delegación de eventos en el contenedor padre
    listEl.onclick = (e) => {
        const li = e.target.closest('.chat-contact');
        if (!li) return;

        const convId = parseInt(li.dataset.id);
        const name = li.dataset.name;

        console.log(`[Chat] Seleccionando conversación ID: ${convId}, Nombre: ${name}`);

        // Actualizar UI activa
        document.querySelectorAll('.chat-contact').forEach(el => el.classList.remove('active'));
        li.classList.add('active');
        
        // Quitar badge si existe
        const badge = li.querySelector('.unread-badge');
        if (badge) badge.remove();
        
        openChat(convId, name);
    };
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
        
        // Guardia de sincronización: Verificar si el ID de la petición 
        // coincide con la conversación activa actualmente
        if (activeConversationId !== convId) {
            console.debug(`[Chat] Ignorando mensajes de la conv ${convId} (activa: ${activeConversationId})`);
            return;
        }

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
    
    // Optimización de polling: solo evitar re-render si es polling Y el convId Y el conteo son iguales
    // NOTA: No usar solo el conteo, dos chats pueden tener el mismo número de mensajes
    const newLength = messages.length;
    const storedConvId = area.dataset.convId ? parseInt(area.dataset.convId) : -1;
    const oldLength = area.dataset.msgCount ? parseInt(area.dataset.msgCount) : 0;
    
    // Saltar solo durante polling cuando el chat Y el conteo no cambiaron
    if (newLength === oldLength && newLength > 0 && storedConvId === activeConversationId) return;
    
    area.innerHTML = '';
    area.dataset.msgCount = newLength;
    area.dataset.convId = activeConversationId;

    if (!messages || messages.length === 0) {
        area.innerHTML = '<p style="text-align:center; color:#888; margin-top: 2rem;">Inicio de la conversación.</p>';
        return;
    }

    messages.forEach(msg => {
        const div = document.createElement('div');
        
        let msgType = 'received';
        if (msg.tipo_mensaje === 'sistema') {
            // El mensaje sistema o autogenerado por el backend lo tratamos con estilo neutral si quieres, o si decidimos mandarlo como 'texto' (como hicimos en serializers.py) se pintará verde/blanco segun remitente.
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
            // Al abrir la sección, resetear el badge y cargar conversaciones
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
// Corre en segundo plano cada 10 segundos y actualiza el badge del menú
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
    // Actualizar el título de la pestaña del navegador
    if (count > 0) {
        document.title = `(${count}) Campo Directo`;
    } else {
        document.title = 'Campo Directo';
    }
}

async function pollUnreadMessages() {
    // No ejecutar si la pestaña está inactiva para ahorrar recursos
    if (document.visibilityState !== 'visible') return;
    // No ejecutar si estamos en la sección de mensajes con un chat activo
    const messagesSection = document.getElementById('messages');
    if (messagesSection && messagesSection.classList.contains('active') && activeConversationId) return;

    try {
        const response = await chatApi.getConversations();
        const conversations = response.results || response;
        const totalUnread = conversations.reduce((sum, c) => sum + (c.mensajes_no_leidos || 0), 0);

        updateMsgBadge(totalUnread);

        // Si hay mensajes nuevos vs la última vez, lanzar notificación del navegador
        if (totalUnread > _lastUnreadCount && _lastUnreadCount !== null) {
            const newMsgs = totalUnread - _lastUnreadCount;
            triggerBrowserNotification(newMsgs, conversations);
        }
        _lastUnreadCount = totalUnread;

    } catch (e) {
        // Silenciar errores del poller para no distraer con alertas en pantalla
        console.debug('[ChatPoller] Error silenciado:', e.message);
    }
}

function triggerBrowserNotification(count, conversations) {
    if (!('Notification' in window)) return;

    // Buscar la conversación con el mensaje más reciente
    const convWithUnread = conversations.find(c => c.mensajes_no_leidos > 0);
    const senderName = convWithUnread
        ? (window.location.pathname.includes('comprador') ? convWithUnread.campesino_nombre : convWithUnread.comprador_nombre)
        : 'Alguien';

    const body = count === 1
        ? `${senderName} te envió un mensaje.`
        : `Tienes ${count} mensajes nuevos.`;

    if (Notification.permission === 'granted') {
        const n = new Notification('💬 Campo Directo', { body, icon: '/static/images/logo.png' });
        // Cerrar automáticamente después de 5 segundos
        setTimeout(() => n.close(), 5000);
        n.onclick = () => {
            window.focus();
            document.querySelector('[data-section="messages"]')?.click();
        };
    } else if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Solicitar permiso de notificaciones una vez que el usuario interactúe
document.addEventListener('click', function askNotifPermission() {
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
    document.removeEventListener('click', askNotifPermission);
}, { once: true });

// Arrancar el poller global con un delay inicial de 5s para no solaparse con la carga inicial
setTimeout(() => {
    pollUnreadMessages(); // ejecutar una vez de inmediato
    _globalMsgPoller = setInterval(pollUnreadMessages, 10000); // luego cada 10s
}, 5000);
