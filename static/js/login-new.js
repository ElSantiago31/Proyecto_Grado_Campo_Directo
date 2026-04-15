// Login JavaScript - Campo Directo (Versión con API)

document.addEventListener('DOMContentLoaded', function () {
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
    loginForm.addEventListener('submit', function (e) {
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

    // Variables globales para el 2FA Visual
    const visual2faModal = document.getElementById('visual2faModal');
    const visual2faBox = document.getElementById('visual2faBox');
    const close2faBtn = document.getElementById('close2faBtn');
    const btnLoginEmojis = document.querySelectorAll('.btn-login-emoji');
    const error2faMsg = document.getElementById('error2faMsg');
    
    let resolve2faPromise = null;

    if(close2faBtn) {
        close2faBtn.addEventListener('click', () => {
            visual2faModal.style.display = 'none';
        });
    }

    btnLoginEmojis.forEach(btn => {
        btn.addEventListener('click', function() {
            const val = this.getAttribute('data-value');
            if (resolve2faPromise) {
                resolve2faPromise(val);
            }
        });
    });

    async function checkAuthenticationStatus() {
        // CIRCUIT BREAKER: Si acabamos de ser rebotados por Django (falta de Cookie de sesión)
        // entonces NO debemos auto-redireccionar usando el JWT, pues creará un loop infinito.
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('next')) {
            // console.warn("Detectado 'next' en URL: Django rechazó la Cookie de Sesión. Limpiando JWT fantasma...")warn
            localStorage.removeItem('refreshToken');
            if (authApi) authApi.setAuthToken(null); // Assuming 'authApi' is the correct global/available API object
            return; // Detener auto-login
        }

        if (isAuthenticated()) {
            try {
                const response = await authApi.getProfile();
                if (response && response.id) {
                    // Usuario ya autenticado, redirigir al dashboard correcto
                    if (response.tipo_usuario === 'comprador') {
                        window.location.href = '/dashboard-comprador/';
                    } else {
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
        const email = usernameInput.value.trim().toLowerCase();
        const password = passwordInput.value;
        const remember = rememberCheckbox.checked;

        // Mostrar Modal 2FA en vez de hacer request inmediato
        if(visual2faModal) {
            visual2faModal.style.display = 'flex';
            error2faMsg.textContent = '';
            error2faMsg.style.color = '#dc3545';
        }

        // Definimos la función resolver del ciclo 2FA
        resolve2faPromise = async (imagen_2fa) => {
            error2faMsg.style.color = '#5a9e2f';
            error2faMsg.textContent = 'Validando seguridad...';

            try {
                // Hacer el request oficial de Login incluyendo imagen_2fa
                const response = await authApi.login({ email, password, imagen_2fa });

                // Éxito absoluto (Credenciales + 2FA OK)
                if(visual2faModal) visual2faModal.style.display = 'none';
                
                if (response.access && response.refresh) {
                    if (remember) {
                        localStorage.setItem('rememberedUser', email);
                    } else {
                        localStorage.removeItem('rememberedUser');
                    }

                    const loginBtn = document.querySelector('.login-button');
                    loginBtn.innerHTML = '<span class="button-icon">✅</span> Ingreso exitoso!';
                    loginBtn.classList.add('success');

                    setTimeout(() => {
                        if (response.user && response.user.tipo_usuario === 'comprador') {
                            window.location.href = '/dashboard-comprador/';
                        } else {
                            window.location.href = '/dashboard/';
                        }
                    }, 1000);
                } else {
                    throw new ApiError('Respuesta de login inválida', 400);
                }
            } catch (error) {
                // console.error('Error de login o 2FA:', error)error
                
                // Analizar si el rechazo fue por 2FA (401 + mensaje específico) o si fue contraseña
                let isVisualError = false;
                if (error.details && error.details.non_field_errors) {
                    const textError = JSON.stringify(error.details.non_field_errors).toLowerCase();
                    if (textError.includes('visual') || textError.includes('2fa')) {
                        isVisualError = true;
                    }
                }
                
                if (isVisualError) {
                    // Fallo solo el PIN Visual: mostrar el mensaje exacto del servidor
                    error2faMsg.style.color = '#dc3545';
                    const serverMsg = error.details?.non_field_errors?.[0] || '❌ PIN Visual incorrecto. Intenta de nuevo.';
                    error2faMsg.textContent = serverMsg;
                    
                    // Efecto Shake en la ventanita del Modal
                    if(visual2faBox) {
                        visual2faBox.style.transform = 'translateX(10px)';
                        setTimeout(() => visual2faBox.style.transform = 'translateX(-10px)', 100);
                        setTimeout(() => visual2faBox.style.transform = 'translateX(10px)', 200);
                        setTimeout(() => visual2faBox.style.transform = 'translate(0)', 300);
                    }
                } else {
                    // Contraseña incorrecta, inactivo, servidor caído...
                    if(visual2faModal) visual2faModal.style.display = 'none';
                    
                    let customErrorMessage = null;
                    if (error.details && error.details.non_field_errors) {
                        customErrorMessage = error.details.non_field_errors[0];
                    }

                    if (error instanceof ApiError) {
                        if (customErrorMessage) {
                            showError(passwordInput, passwordError, 'Acceso restringido');
                            showNotification(customErrorMessage, 'error');
                        } else if (error.status === 401) {
                            showError(passwordInput, passwordError, 'Usuario o contraseña incorrectos');
                        } else if (error.status === 403) {
                            showNotification('Tu cuenta está restringida. Contacta a soporte.', 'error');
                            showError(passwordInput, passwordError, 'Usuario inactivo o suspendido');
                        } else {
                            showError(passwordInput, passwordError, 'Credenciales denegadas por el servidor.');
                        }
                    } else {
                        showError(passwordInput, passwordError, 'Error de conexión. Verifica tu internet.');
                    }

                    // Shake animation main form
                    loginForm.classList.add('shake');
                    setTimeout(() => loginForm.classList.remove('shake'), 500);
                }
            }
        };
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

        // Show success animation
        const formContainer = document.querySelector('.login-right-section');
        if (formContainer) {
            formContainer.classList.add('login-success');
        }
    }

    function loadRememberedUser() {
        const rememberedUser = localStorage.getItem('rememberedUser');
        if (rememberedUser) {
            usernameInput.value = rememberedUser;
            rememberCheckbox.checked = true;
        }
    }
    // ============================================================
    // UTILIDADES
    // ============================================================

    function showNotification(message, type = 'info') {
        // Simple notification system
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
                type === 'success' ? '#28a745' : '#2d5016',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }
});

// Add CSS for animations (if not already present)
if (!document.querySelector('#login-styles')) {
    document.head.insertAdjacentHTML('beforeend', `
    <style id="login-styles">
    .shake {
        animation: shake 0.5s;
    }

    @keyframes shake {
        0%, 20%, 40%, 60%, 80% {
            transform: translateX(-5px);
        }
        10%, 30%, 50%, 70%, 90% {
            transform: translateX(5px);
        }
        100% {
            transform: translateX(0);
        }
    }

    .login-success {
        animation: successPulse 0.5s ease-in-out;
    }

    @keyframes successPulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.02);
        }
        100% {
            transform: scale(1);
        }
    }

    .login-button:disabled {
        cursor: not-allowed;
        opacity: 0.8;
    }

    .login-button.loading {
        pointer-events: none;
        opacity: 0.8;
    }

    .form-input.error {
        border-color: #dc3545;
        box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
    }

    .error-message {
        color: #dc3545;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: block;
    }
    </style>
    `);
}