// Login functionality for Campo Directo

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const rememberCheckbox = document.getElementById('remember');
    
    // Error message elements
    const usernameError = document.getElementById('username-error');
    const passwordError = document.getElementById('password-error');
    
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
    usernameInput.addEventListener('blur', function() {
        validateUsername();
    });
    
    passwordInput.addEventListener('blur', function() {
        validatePassword();
    });
    
    // Clear errors on input
    usernameInput.addEventListener('input', function() {
        clearError(usernameInput, usernameError);
    });
    
    passwordInput.addEventListener('input', function() {
        clearError(passwordInput, passwordError);
    });
    
    // Validation functions
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
            showError(usernameInput, usernameError, 'Por favor ingresa tu usuario o correo electrónico');
            return false;
        }
        
        // Basic email validation if it contains @
        if (username.includes('@')) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(username)) {
                showError(usernameInput, usernameError, 'Por favor ingresa un correo electrónico válido');
                return false;
            }
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
    
    function showError(input, errorElement, message) {
        input.classList.add('error');
        errorElement.textContent = message;
    }
    
    function clearError(input, errorElement) {
        input.classList.remove('error');
        errorElement.textContent = '';
    }
    
    function clearAllErrors() {
        clearError(usernameInput, usernameError);
        clearError(passwordInput, passwordError);
    }
    
    // Login using Django API
    async function performLogin() {
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        const remember = rememberCheckbox.checked;
        
        // Show loading state
        const loginBtn = document.querySelector('.login-button');
        const originalText = loginBtn.textContent;
        loginBtn.innerHTML = '<span class="button-icon">🌱</span> Ingresando...';
        loginBtn.disabled = true;
        loginBtn.classList.add('loading');
        
        try {
            // Get CSRF token
            const csrfToken = getCookie('csrftoken');
            
            // Make login request to Django API
            const response = await fetch('/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'include', // Important for session cookies
                body: JSON.stringify({
                    email: username,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Save username for remember me functionality
                if (remember) {
                    localStorage.setItem('rememberedUser', username);
                } else {
                    localStorage.removeItem('rememberedUser');
                }
                
                // Show success message
                showLoginSuccess();
                
                // Redirect to dashboard after short delay
                setTimeout(() => {
                    window.location.href = '/dashboard-redirect/';
                }, 2000);
                
            } else {
                // Show error for invalid credentials
                loginBtn.textContent = originalText;
                loginBtn.disabled = false;
                loginBtn.classList.remove('loading');
                
                const errorMessage = data.non_field_errors ? 
                    data.non_field_errors[0] : 
                    data.error || 'Credenciales incorrectas';
                
                showError(passwordInput, passwordError, errorMessage);
                
                // Shake animation for invalid login
                loginForm.classList.add('shake');
                setTimeout(() => {
                    loginForm.classList.remove('shake');
                }, 500);
            }
        } catch (error) {
            console.error('Error during login:', error);
            
            // Restore button state
            loginBtn.textContent = originalText;
            loginBtn.disabled = false;
            loginBtn.classList.remove('loading');
            
            showError(passwordInput, passwordError, 'Error de conexión. Inténtalo de nuevo.');
        }
    }
    
    function showLoginSuccess() {
        const loginBtn = document.querySelector('.login-button');
        loginBtn.innerHTML = '<span class="button-icon">✅</span> ¡Bienvenido al Campo!';
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
    
    // Forgot password handler (placeholder)
    document.querySelector('.forgot-password').addEventListener('click', function(e) {
        e.preventDefault();
        alert('Funcionalidad de recuperación de contraseña estará disponible próximamente.\n\nPor ahora, puedes usar:\nUsuario: campesino\nContraseña: campesino');
    });
});

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Add CSS classes for animations
document.head.insertAdjacentHTML('beforeend', `
<style>
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
</style>
`);