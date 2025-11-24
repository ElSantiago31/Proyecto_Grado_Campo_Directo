// Funcionalidad para la página de registro exitoso

document.addEventListener('DOMContentLoaded', function() {
    // Mostrar datos del usuario si están disponibles
    displayUserData();
    
    // Configurar animaciones de entrada
    setupAnimations();
    
    // Auto-redirección opcional después de un tiempo
    setupAutoRedirect();
});

// Función para redirigir al menú principal
function goToMainMenu() {
    // Efecto de carga en el botón
    const btn = document.querySelector('.btn-main-menu');
    const originalText = btn.textContent;
    
    btn.textContent = 'Redirigiendo...';
    btn.disabled = true;
    btn.style.opacity = '0.7';
    
    // Simular pequeño delay para mejor UX
    setTimeout(() => {
        window.location.href = 'index.html';
    }, 500);
}

// Mostrar datos del usuario si están en sessionStorage o localStorage
function displayUserData() {
    try {
        // Intentar obtener datos del registro desde sessionStorage
        const userData = sessionStorage.getItem('registroUsuario') || localStorage.getItem('registroUsuario');
        
        if (userData) {
            const data = JSON.parse(userData);
            
            // Crear mensaje personalizado
            const personalizedMessage = createPersonalizedMessage(data);
            
            // Agregar el mensaje personalizado después del título
            const successMessage = document.querySelector('.success-message');
            if (successMessage && personalizedMessage) {
                const personalizedDiv = document.createElement('div');
                personalizedDiv.className = 'personalized-message';
                personalizedDiv.innerHTML = personalizedMessage;
                successMessage.appendChild(personalizedDiv);
            }
            
            // Limpiar datos después de mostrarlos
            sessionStorage.removeItem('registroUsuario');
            localStorage.removeItem('registroUsuario');
        }
    } catch (error) {
        console.log('No hay datos de usuario para mostrar');
    }
}

// Crear mensaje personalizado basado en los datos del usuario
function createPersonalizedMessage(data) {
    if (!data || !data.nombre) return null;
    
    const userType = data.tipoUsuario === 'campesino' ? 'Campesino' : 'Comprador';
    let message = `<p class="welcome-text">¡Bienvenido/a <strong>${data.nombre} ${data.apellido}</strong>!</p>`;
    message += `<p class="user-type">Te has registrado como <strong>${userType}</strong></p>`;
    
    if (data.nombreFinca) {
        message += `<p class="farm-name">Finca: <strong>${data.nombreFinca}</strong></p>`;
    }
    
    return message;
}

// Configurar animaciones de entrada
function setupAnimations() {
    // Animar elementos uno por uno con delay
    const elements = [
        '.success-logo',
        '.success-illustration', 
        '.success-message',
        '.success-actions'
    ];
    
    elements.forEach((selector, index) => {
        const element = document.querySelector(selector);
        if (element) {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.6s ease-out';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 200);
        }
    });
}

// Configurar auto-redirección opcional
function setupAutoRedirect() {
    // Solo si hay un parámetro específico en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const autoRedirect = urlParams.get('auto');
    
    if (autoRedirect === 'true') {
        let countdown = 10; // 10 segundos
        const btn = document.querySelector('.btn-main-menu');
        
        const updateCountdown = () => {
            btn.textContent = `Volver al menú principal (${countdown}s)`;
            countdown--;
            
            if (countdown < 0) {
                goToMainMenu();
            }
        };
        
        // Actualizar cada segundo
        updateCountdown();
        const interval = setInterval(updateCountdown, 1000);
        
        // Detener countdown si el usuario hace clic
        btn.addEventListener('click', () => {
            clearInterval(interval);
        });
    }
}

// Funciones adicionales para mejorar la experiencia

// Efecto de confetti (opcional)
function showConfetti() {
    // Crear elementos de confetti
    const colors = ['#2d5016', '#ffa500', '#4a7c24', '#ffcc00'];
    const confettiContainer = document.createElement('div');
    confettiContainer.style.position = 'fixed';
    confettiContainer.style.top = '0';
    confettiContainer.style.left = '0';
    confettiContainer.style.width = '100%';
    confettiContainer.style.height = '100%';
    confettiContainer.style.pointerEvents = 'none';
    confettiContainer.style.zIndex = '1000';
    
    document.body.appendChild(confettiContainer);
    
    // Crear partículas de confetti
    for (let i = 0; i < 50; i++) {
        createConfettiPiece(confettiContainer, colors);
    }
    
    // Remover confetti después de 3 segundos
    setTimeout(() => {
        document.body.removeChild(confettiContainer);
    }, 3000);
}

function createConfettiPiece(container, colors) {
    const confetti = document.createElement('div');
    const color = colors[Math.floor(Math.random() * colors.length)];
    
    confetti.style.position = 'absolute';
    confetti.style.width = '10px';
    confetti.style.height = '10px';
    confetti.style.backgroundColor = color;
    confetti.style.left = Math.random() * 100 + '%';
    confetti.style.top = '-10px';
    confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
    confetti.style.animation = `confettiFall ${2 + Math.random() * 3}s linear forwards`;
    
    container.appendChild(confetti);
}

// CSS para animación de confetti (se agrega dinámicamente)
const style = document.createElement('style');
style.textContent = `
    @keyframes confettiFall {
        to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
        }
    }
    
    .personalized-message {
        margin-top: 1rem;
        padding: 1rem;
        background: rgba(45, 80, 22, 0.05);
        border-radius: 8px;
        border-left: 4px solid #2d5016;
    }
    
    .welcome-text {
        font-size: 1.1rem;
        color: #2d5016;
        margin-bottom: 0.5rem;
    }
    
    .user-type, .farm-name {
        font-size: 1rem;
        color: #666;
        margin-bottom: 0.3rem;
    }
    
    .personalized-message strong {
        color: #2d5016;
    }
    
    @media (max-width: 575px) {
        .personalized-message {
            padding: 0.8rem;
            margin-top: 0.8rem;
        }
        
        .welcome-text {
            font-size: 1rem;
        }
        
        .user-type, .farm-name {
            font-size: 0.9rem;
        }
    }
`;
document.head.appendChild(style);

// Opcional: mostrar confetti al cargar la página
// showConfetti();