// ============================================================
// CONFIGURACIÓN DE API - CAMPO DIRECTO FRONTEND
// ============================================================

// Configuración de la API
const API_CONFIG = {
    // Usar la misma URL en la que está montada la página (ej: localhost o pythonanywhere)
    BASE_URL: window.location.origin + '/api',
    TIMEOUT: 10000,
    RETRY_ATTEMPTS: 3
};

// Token de autenticación
let authToken = localStorage.getItem('authToken') || null;

/**
 * Clase para manejar las llamadas a la API
 */
class ApiClient {
    constructor() {
        this.baseURL = API_CONFIG.BASE_URL;
        this.timeout = API_CONFIG.TIMEOUT;
        this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS;
    }

    /**
     * Configurar token de autenticación
     */
    setAuthToken(token) {
        authToken = token;
        if (token) {
            localStorage.setItem('authToken', token);
        } else {
            localStorage.removeItem('authToken');
        }
    }

    /**
     * Obtener token de autenticación
     */
    getAuthToken() {
        return authToken;
    }

    /**
     * Construir headers para las peticiones
     */
    buildHeaders(additionalHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...additionalHeaders
        };

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        // Agregar CSRF token para Django
        const csrfToken = window.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        return headers;
    }

    /**
     * Realizar petición HTTP
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const config = {
            method: options.method || 'GET',
            headers: this.buildHeaders(options.headers),
            credentials: 'include', // Forzar envío/recepción de cookies (sessionid)
            ...options
        };

        // Agregar body si es necesario
        if (options.data && config.method !== 'GET') {
            if (options.data instanceof FormData) {
                config.body = options.data;
                // Importante: al usar FormData, no debemos poner Content-Type manual 
                // para que el navegador ponga el boundary correcto
                delete config.headers['Content-Type'];
            } else {
                config.body = JSON.stringify(options.data);
            }
        }

        try {
            const response = await this.fetchWithTimeout(url, config);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new ApiError(
                    errorData.message || 'Error en la petición',
                    response.status,
                    errorData
                );
            }

            return await response.json();

        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }

            // Error de red o timeout
            throw new ApiError(
                'Error de conexión. Verifica tu conexión a internet.',
                0,
                { originalError: error.message }
            );
        }
    }

    /**
     * Fetch con timeout
     */
    async fetchWithTimeout(url, options) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }

    /**
     * Métodos HTTP convenientes
     */
    get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    post(endpoint, data, options = {}) {
        return this.request(endpoint, { ...options, method: 'POST', data });
    }

    put(endpoint, data, options = {}) {
        return this.request(endpoint, { ...options, method: 'PUT', data });
    }

    patch(endpoint, data, options = {}) {
        return this.request(endpoint, { ...options, method: 'PATCH', data });
    }

    delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }
}

/**
 * Clase para manejar errores de API
 */
class ApiError extends Error {
    constructor(message, status = 0, details = {}) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.details = details;
    }

    isAuthError() {
        return this.status === 401;
    }

    isValidationError() {
        return this.status === 400;
    }

    isNotFoundError() {
        return this.status === 404;
    }

    isServerError() {
        return this.status >= 500;
    }
}

// Instancia global del cliente API
const api = new ApiClient();

// ============================================================
// ENDPOINTS ESPECÍFICOS
// ============================================================

/**
 * APIs de Autenticación
 */
const authApi = {
    async login(credentials) {
        const response = await api.post('/auth/login/', credentials);
        if (response.access && response.refresh) {
            api.setAuthToken(response.access);
            localStorage.setItem('refreshToken', response.refresh);
        }
        return response;
    },

    async register(userData) {
        const response = await api.post('/auth/register/', userData);
        if (response.access && response.refresh) {
            api.setAuthToken(response.access);
            localStorage.setItem('refreshToken', response.refresh);
        }
        return response;
    },

    async logout() {
        api.setAuthToken(null);
        localStorage.removeItem('refreshToken');
        return { success: true };
    },

    async getProfile() {
        return await api.get('/auth/profile/');
    },

    async updateProfile(profileData) {
        return await api.put('/auth/profile/update/', profileData);
    },

    async changePassword(passwordData) {
        return await api.post('/auth/change-password/', passwordData);
    },

    async getDashboard(period = 'month') {
        return await api.get(`/auth/dashboard/?period=${period}`);
    },

    async refreshToken() {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
            throw new ApiError('No refresh token available', 401);
        }

        const response = await api.post('/auth/token/refresh/', {
            refresh: refreshToken
        });

        if (response.access) {
            api.setAuthToken(response.access);
        }

        return response;
    }
};

/**
 * APIs de Usuarios
 */
const userApi = {
    async getProfile() {
        return await api.get('/users/profile');
    },

    async updateProfile(profileData) {
        return await api.put('/users/profile', profileData);
    },

    async getStats() {
        return await api.get('/users/stats');
    },

    async getFarmers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await api.get(`/users/farmers?${queryString}`);
    },

    async getResenasCampesino(campesinoId) {
        return await api.get(`/auth/campesinos/${campesinoId}/resenas/`);
    },

    async getMisResenas() {
        return await api.get('/auth/mis-resenas/');
    }
};


/**
 * APIs de Productos
 */
const productApi = {
    async getProducts(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await api.get(`/products/productos/?${queryString}`);
    },

    async getProduct(id) {
        return await api.get(`/products/productos/${id}/`);
    },

    async createProduct(productData) {
        return await api.post('/products/', productData);
    },

    async updateProduct(id, productData) {
        return await api.put(`/products/${id}/`, productData);
    },

    async deleteProduct(id) {
        return await api.delete(`/products/${id}/`);
    },

    async getCategories() {
        return await api.get('/products/categorias/');
    }
};

/**
 * APIs de Dashboard
 */
const dashboardApi = {
    async getStats() {
        return await api.get('/dashboard/stats');
    },

    async getActivities() {
        return await api.get('/dashboard/activities');
    },

    async addActivity(activityData) {
        return await api.post('/dashboard/activities', activityData);
    }
};

/**
 * APIs de Pedidos
 */
const orderApi = {
    async getOrders(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await api.get(`/orders/pedidos/?${queryString}`);
    },

    async getMisCompras(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await api.get(`/orders/pedidos/mis_compras/?${queryString}`);
    },

    async getMisVentas(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await api.get(`/orders/pedidos/mis_ventas/?${queryString}`);
    },

    async createOrder(orderData) {
        return await api.post('/orders/pedidos/', orderData);
    },

    async updateOrderStatus(orderId, status) {
        return await api.patch(`/orders/pedidos/${orderId}/actualizar_estado/`, { nuevo_estado: status });
    },

    async calificar(orderId, ratingData) {
        return await api.post(`/orders/pedidos/${orderId}/calificar/`, ratingData);
    },

    async cancelar(orderId) {
        return await api.patch(`/orders/pedidos/${orderId}/cancelar/`);
    }
};

/**
 * APIs de Fincas
 */
const farmApi = {
    async getMyFarm() {
        return await api.get('/farms/my-farm');
    },

    async updateMyFarm(farmData) {
        return await api.put('/farms/my-farm', farmData);
    }
};

/**
 * APIs de Chat (Anti-Intermediarios)
 */
const chatApi = {
    async getConversations(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/anti-intermediarios/conversaciones/?${queryString}` : '/anti-intermediarios/conversaciones/';
        return await api.get(endpoint);
    },

    async getConversationDetails(id) {
        return await api.get(`/anti-intermediarios/conversaciones/${id}/`);
    },

    async getMessages(conversacionId) {
        return await api.get(`/anti-intermediarios/conversaciones/${conversacionId}/mensajes/`);
    },

    async sendMessage(conversacionId, messageData) {
        return await api.post(`/anti-intermediarios/conversaciones/${conversacionId}/enviar_mensaje/`, messageData);
    },

    async markAsRead(conversacionId) {
        return await api.patch(`/anti-intermediarios/conversaciones/${conversacionId}/marcar_como_leidos/`);
    }
};

// ============================================================
// UTILIDADES
// ============================================================

/**
 * Verificar si el usuario está autenticado
 */
function isAuthenticated() {
    return !!api.getAuthToken();
}

/**
 * Manejar errores de autenticación
 */
function handleAuthError() {
    api.setAuthToken(null);
    localStorage.removeItem('refreshToken');

    // Redirigir al login unificado si no estamos ya ahí
    const currentPath = window.location.pathname;
    if (!currentPath.includes('login') && !currentPath.includes('registro')) {
        // console.log('Token inválido, redirigiendo al login')log
        window.location.href = '/login/';
    }
}

/**
 * Interceptor global para errores de autenticación (MEJORADO CON FIX PARA COMPRADORES)
 */
let isRefreshingToken = false;
let refreshPromise = null;

const originalRequest = api.request;
api.request = async function (endpoint, options = {}) {
    try {
        return await originalRequest.call(this, endpoint, options);
    } catch (error) {
        if (error instanceof ApiError && error.isAuthError()) {
            // Evitar bucles infinitos para endpoints de auth
            if (endpoint.includes('/auth/') || options._isRetry) {
                // console.log(`[API] Error de auth en ${endpoint}, no interceptando`)log
                throw error;
            }

            // console.log(`[API] Error de autenticación interceptado en ${endpoint}`)log

            // Si ya estamos renovando el token, esperar
            if (isRefreshingToken && refreshPromise) {
                try {
                    await refreshPromise;
                    // Reintentar con el nuevo token
                    options._isRetry = true;
                    return await originalRequest.call(this, endpoint, options);
                } catch (refreshError) {
                    // console.log('[API] Error renovando token, activando handleAuthError')log
                    handleAuthError();
                    throw error;
                }
            }

            // Intentar renovar el token automáticamente
            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken && !isRefreshingToken) {
                // console.log('[API] Intentando renovar token...')log
                isRefreshingToken = true;
                refreshPromise = authApi.refreshToken();

                try {
                    await refreshPromise;
                    isRefreshingToken = false;
                    refreshPromise = null;

                    // console.log('[API] Token renovado exitosamente, reintentando petición')log
                    // Reintentar la petición original con el nuevo token
                    options._isRetry = true;
                    return await originalRequest.call(this, endpoint, options);
                } catch (refreshError) {
                    // console.log('[API] Error renovando token:', refreshError)log
                    isRefreshingToken = false;
                    refreshPromise = null;
                    handleAuthError();
                    throw error;
                }
            } else {
                // console.log('[API] No hay refresh token o ya estamos renovando, activando handleAuthError')log
                handleAuthError();
                throw error;
            }
        }
        throw error;
    }
};

// console.log('[API] Interceptor activado con fix para compradores')log

// Exportar para uso global
window.api = api;
window.authApi = authApi;
window.userApi = userApi;
window.productApi = productApi;
window.dashboardApi = dashboardApi;
window.orderApi = orderApi;
window.farmApi = farmApi;
window.chatApi = chatApi;
window.ApiError = ApiError;
window.isAuthenticated = isAuthenticated;