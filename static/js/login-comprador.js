// Login JavaScript - Campo Directo (Compradores)

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const rememberCheckbox = document.getElementById('remember');
    
    // Error message elements
    const usernameError = document.getElementById('username-error');
    const passwordError = document.getElementById('password-error');
    
    // Verificar si ya está autenticado
    checkAuthenticationStatus();
    
    // Load remembered username if exists
    loadRememberedUser();
    
    // Form submission handler
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (validateForm()) {
            performLogin();
        }
    });
    
    // Real-time validation
    usernameInput.addEventListener('blur', validateUsername);
    passwordInput.addEventListener('blur', validatePassword);
    
    // Clear errors on input
    usernameInput.addEventListener('input', () => clearError(usernameInput, usernameError));
    passwordInput.addEventListener('input', () => clearError(passwordInput, passwordError));
    
    // ============================================================
    // FUNCIONES DE AUTENTICACIÓN
    // ============================================================
    
    async function checkAuthenticationStatus() {
        if (isAuthenticated()) {
            try {
                const response = await authApi.getProfile();
                if (response && response.id) {
                    // Verificar si el usuario es comprador
                    if (response.tipo_usuario === 'comprador') {
                        window.location.href = '/dashboard-comprador/';
                    } else {
                        // Si es campesino, redirigir a su dashboard
                        window.location.href = '/dashboard/';
                    }
                    return;
                }
            } catch (error) {
                // Token inválido, continuar con el login
                // console.log('Token inválido, requiere nuevo login')log
                // Limpiar tokens inválidos
                localStorage.removeItem('authToken');
                localStorage.removeItem('refreshToken');
            }
        }
    }
    
    async function performLogin() {
        const email = usernameInput.value.trim();
        const password = passwordInput.value;
        const remember = rememberCheckbox.checked;
        
        // Show loading state
        const loginBtn = document.querySelector('.login-button');
        const originalText = loginBtn.innerHTML;
        loginBtn.innerHTML = '<span class="button-icon">🛒</span> Ingresando...';
        loginBtn.disabled = true;
        loginBtn.classList.add('loading');
        
        try {
            const response = await authApi.login({ email, password });
            
            // Django JWT devuelve access y refresh tokens directamente
            if (response.access && response.refresh && response.user) {
                // Verificar que sea un comprador
                if (response.user.tipo_usuario !== 'comprador') {
                    throw new ApiError('Esta cuenta no es de comprador. Usa el login de campesinos.', 403);
                }
                
                // Save username for remember me functionality
                if (remember) {
                    localStorage.setItem('rememberedUser', email);
                } else {
                    localStorage.removeItem('rememberedUser');
                }
                
                // Show success message
                showLoginSuccess(response.user);
                
                // Redirect to comprador dashboard after short delay
                setTimeout(() => {
                    window.location.href = '/dashboard-comprador/';
                }, 2000);
            } else {
                throw new ApiError('Respuesta de login inválida', 400);
            }
            
        } catch (error) {
            // console.error('Error en login:', error)error
            
            // Restore button state
            loginBtn.innerHTML = originalText;
            loginBtn.disabled = false;
            loginBtn.classList.remove('loading');
            
            // Show appropriate error message
            if (error instanceof ApiError) {
                if (error.status === 401) {
                    showError(passwordInput, passwordError, 'Usuario o contraseña incorrectos');
                } else if (error.status === 403) {
                    showError(passwordInput, passwordError, error.message);
                } else {
                    showError(passwordInput, passwordError, 'Error en el servidor. Intenta de nuevo.');
                }
            } else {
                showError(passwordInput, passwordError, 'Error de conexión. Verifica tu internet.');
            }
            
            // Shake animation for invalid login
            loginForm.classList.add('shake');
            setTimeout(() => loginForm.classList.remove('shake'), 500);
        }
    }
    
    // ============================================================
    // FUNCIONES DE VALIDACIÓN
    // ============================================================
    
    function validateForm() {
        let isValid = true;
        
        if (!validateUsername()) {
            isValid = false;
        }
        
        if (!validatePassword()) {
            isValid = false;
        }
        
        return isValid;
    }
    
    function validateUsername() {
        const username = usernameInput.value.trim();
        
        if (!username) {
            showError(usernameInput, usernameError, 'Por favor ingresa tu correo electrónico');
            return false;
        }
        
        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(username)) {
            showError(usernameInput, usernameError, 'Por favor ingresa un correo electrónico válido');
            return false;
        }
        
        clearError(usernameInput, usernameError);
        return true;
    }
    
    function validatePassword() {
        const password = passwordInput.value;
        
        if (!password) {
            showError(passwordInput, passwordError, 'Por favor ingresa tu contraseña');
            return false;
        }
        
        if (password.length < 6) {
            showError(passwordInput, passwordError, 'La contraseña debe tener al menos 6 caracteres');
            return false;
        }
        
        clearError(passwordInput, passwordError);
        return true;
    }
    
    // ============================================================
    // FUNCIONES DE UI
    // ============================================================
    
    function showError(input, errorElement, message) {
        input.classList.add('error');
        errorElement.textContent = message;
    }
    
    function clearError(input, errorElement) {
        input.classList.remove('error');
        errorElement.textContent = '';
    }
    
    function showLoginSuccess(user) {
        const loginBtn = document.querySelector('.login-button');
        loginBtn.innerHTML = `<span class="button-icon">✅</span> ¡Bienvenido ${user.nombre}!`;
        loginBtn.style.background = 'linear-gradient(135deg, #28a745 0%, #1e7e34 100%)';
        loginBtn.classList.remove('loading');
    }
    
    function loadRememberedUser() {
        const rememberedUser = localStorage.getItem('rememberedUser');
        if (rememberedUser) {
            usernameInput.value = rememberedUser;
            rememberCheckbox.checked = true;
        }
    }
    
    // Add shake animation CSS if not exists
    if (!document.querySelector('.shake-animation')) {
        const style = document.createElement('style');
        style.className = 'shake-animation';
        style.textContent = `
            .shake {
                animation: shake 0.5s ease-in-out;
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-3px); }
                20%, 40%, 60%, 80% { transform: translateX(3px); }
            }
            
            .loading {
                opacity: 0.7;
                cursor: not-allowed;
            }
        `;
        document.head.appendChild(style);
    }
});