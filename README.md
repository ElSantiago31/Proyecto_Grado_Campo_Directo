# Campo Directo - Django

![Campo Directo Logo](https://via.placeholder.com/200x100/28a745/ffffff?text=Campo+Directo)

**Campo Directo** es una plataforma digital que conecta campesinos directamente con compradores, eliminando intermediarios en la cadena de suministro agrícola.

## 🌱 Descripción del Proyecto

Esta es la versión Django de Campo Directo, migrada desde Node.js/Express, que mantiene todas las funcionalidades principales:

- **Eliminación de Intermediarios**: Conexión directa entre campesinos y compradores
- **Transparencia de Precios**: Comparación con precios de mercado tradicional
- **Sistema de Mensajería**: Comunicación directa para negociaciones
- **Gestión de Productos y Fincas**: Catálogo completo con certificaciones
- **Sistema de Pedidos**: Tracking completo desde pedido hasta entrega
- **Calificaciones y Reviews**: Sistema de confianza entre usuarios

## 🚀 Tecnologías Utilizadas

### Backend
- **Django 5.2.7** - Framework web principal
- **Django REST Framework 3.16.1** - APIs REST
- **Django REST Framework SimpleJWT** - Autenticación JWT
- **drf-yasg** - Documentación automática de APIs (Swagger/OpenAPI)

### Base de Datos
- **SQLite** - Para desarrollo
- **MySQL** - Para producción (configurado)

### Otras Dependencias
- **Pillow** - Manejo de imágenes
- **django-cors-headers** - CORS para frontend
- **django-filter** - Filtrado avanzado de APIs
- **python-decouple** - Variables de entorno

## 📋 Requisitos Previos

- Python 3.8+
- pip (gestor de paquetes de Python)
- Virtualenv (recomendado)

## ⚡ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd campo-directo-django
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
```

### 5. Ejecutar migraciones
```bash
python manage.py migrate
```

### 6. Cargar datos iniciales
```bash
# Las categorías de productos se crean automáticamente
```

### 7. Crear superusuario (opcional)
```bash
python manage.py createsuperuser
```

### 8. Ejecutar servidor de desarrollo
```bash
python manage.py runserver
```

El servidor estará disponible en: http://localhost:8000

## 🔧 Endpoints Principales

### 🌐 URLs Principales
- **API Health**: http://localhost:8000/api/health/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

### 🔐 Autenticación (`/api/auth/`)
- `POST /api/auth/register/` - Registro de usuarios
- `POST /api/auth/login/` - Inicio de sesión
- `POST /api/auth/token/refresh/` - Renovar token
- `GET /api/auth/profile/` - Perfil del usuario
- `PUT /api/auth/profile/update/` - Actualizar perfil
- `POST /api/auth/change-password/` - Cambiar contraseña
- `GET /api/auth/dashboard/` - Dashboard con estadísticas

### 📊 Estructura de la Base de Datos

#### Modelos Principales

**Usuario** (`users.Usuario`)
- Sistema de autenticación personalizado
- Tipos: Campesino y Comprador
- Sistema de calificaciones integrado
- Gestión de perfiles con avatar

**Finca** (`farms.Finca`)
- Información de ubicación y características
- Coordenadas GPS opcionales
- Sistema de certificaciones

**Producto** (`products.Producto`)
- Catálogo de productos agrícolas
- Gestión de stock y precios
- Galería de imágenes
- Sistema de tags para búsquedas

**Pedido** (`orders.Pedido`)
- Estados de pedido con tracking
- Sistema de calificaciones bilateral
- Información de entrega detallada

**Sistema Anti-Intermediarios** (`anti_intermediarios.*`)
- Mensajería directa entre usuarios
- Transparencia de precios
- Reportes de impacto

## 🏗️ Arquitectura del Proyecto

```
campo-directo-django/
├── campo_directo/           # Configuración principal de Django
│   ├── settings.py          # Configuraciones
│   ├── urls.py             # URLs principales
│   └── wsgi.py             # WSGI para producción
├── users/                  # App de usuarios y autenticación
│   ├── models.py           # Modelo Usuario personalizado
│   ├── views.py            # APIs de autenticación
│   ├── serializers.py      # Serializers DRF
│   └── urls.py             # URLs de auth
├── farms/                  # App de fincas y certificaciones
├── products/               # App de productos y categorías
├── orders/                 # App de pedidos y tracking
├── anti_intermediarios/    # App funcionalidades anti-intermediarios
├── static/                 # Archivos estáticos
├── media/                  # Archivos subidos por usuarios
├── logs/                   # Logs de la aplicación
├── requirements.txt        # Dependencias Python
├── .env                    # Variables de entorno
└── manage.py              # CLI de Django
```

## 📱 Funcionalidades por Tipo de Usuario

### 👨‍🌾 Campesinos
- ✅ Registro con creación automática de finca
- ✅ Gestión de productos y stock
- ✅ Recepción y gestión de pedidos
- ✅ Sistema de mensajería directa
- ✅ Dashboard con estadísticas de ventas

### 🛒 Compradores
- ✅ Registro y navegación de productos
- ✅ Realización de pedidos
- ✅ Comunicación directa con campesinos
- ✅ Sistema de calificaciones
- ✅ Historial de compras

## 🔒 Seguridad

- **Autenticación JWT** con refresh tokens
- **Validación de datos** en todos los endpoints
- **CORS configurado** para seguridad web
- **Rate limiting** implementado
- **Validación de archivos** subidos
- **Logs de seguridad** detallados

## 🧪 Testing

```bash
# Ejecutar tests (cuando estén implementados)
python manage.py test

# Verificar sistema
python manage.py check
```

## 🚀 Despliegue en Producción

### Variables de Entorno Requeridas
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com
DB_NAME=campo_directo
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=db_host
DB_PORT=3306
```

### Comandos de Producción
```bash
# Recolectar archivos estáticos
python manage.py collectstatic

# Ejecutar con gunicorn (instalar primero)
pip install gunicorn
gunicorn campo_directo.wsgi:application
```

## 📖 Documentación API

La documentación completa de la API está disponible en:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema JSON**: http://localhost:8000/api/schema/

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

- **Email**: soporte@campodirecto.com
- **Issues**: [GitHub Issues](https://github.com/campo-directo/django/issues)

## 🆚 Migración desde Node.js

Este proyecto es una migración completa desde la versión Node.js/Express original. Características migradas:

- ✅ Todos los modelos de datos
- ✅ Sistema de autenticación JWT
- ✅ APIs REST equivalentes
- ✅ Funcionalidades anti-intermediarios
- ✅ Sistema de archivos y uploads
- ✅ Documentación automática
- ✅ Panel de administración
- ⏳ Frontend (en proceso)

## 🎯 Próximos Pasos

1. **APIs REST Completas** - Implementar todos los endpoints
2. **Sistema de Uploads** - Manejo avanzado de archivos
3. **Frontend Migration** - Adaptar HTML/CSS/JS existente
4. **Tests Automatizados** - Suite completa de testing
5. **Optimización** - Performance y escalabilidad
6. **Documentación** - Guías de usuario detalladas

---

**Campo Directo Django** - Conectando campesinos directamente con compradores 🌱