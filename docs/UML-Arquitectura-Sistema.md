# Diagrama de Arquitectura del Sistema - Campo Directo

## Resumen de la Arquitectura
Campo Directo utiliza una arquitectura Django REST API con frontend web, base de datos relacional, y servicios externos para funcionalidades específicas como geolocalización y comparación de precios.

## Diagrama de Arquitectura del Sistema

```mermaid
graph TB
    %% Frontend Layer
    subgraph "Capa de Presentación"
        WEB[🌐 Frontend Web<br/>HTML + CSS + JavaScript]
        MOB[📱 App Móvil<br/>(Futuro)]
        API_DOC[📚 Documentación API<br/>Swagger/OpenAPI]
    end

    %% API Gateway / Load Balancer
    subgraph "Entrada del Sistema"
        LB[⚖️ Load Balancer<br/>Nginx/Apache]
        CDN[☁️ CDN<br/>Archivos Estáticos]
    end

    %% Application Layer
    subgraph "Capa de Aplicación"
        DJANGO[🎯 Django Framework]
        
        subgraph "Apps Django"
            USERS[👥 users<br/>Autenticación]
            FARMS[🚜 farms<br/>Fincas]
            PRODUCTS[🥬 products<br/>Productos]
            ORDERS[📦 orders<br/>Pedidos]
            ANTI[🚫 anti_intermediarios<br/>Comunicación]
            FRONTEND[🖥️ frontend<br/>Vistas Web]
        end
        
        subgraph "API Layer"
            DRF[🔌 Django REST Framework]
            JWT[🔐 JWT Authentication]
            SWAGGER[📋 API Documentation]
        end
    end

    %% Business Logic
    subgraph "Lógica de Negocio"
        SERIALIZERS[📄 Serializers<br/>Validación de Datos]
        PERMISSIONS[🛡️ Permisos<br/>Autorización]
        SIGNALS[⚡ Signals<br/>Eventos]
        TASKS[⏰ Tareas Async<br/>Celery (Futuro)]
    end

    %% Data Layer
    subgraph "Capa de Datos"
        DB[(🗄️ Base de Datos<br/>SQLite/MySQL)]
        REDIS[(🔴 Redis<br/>Cache/Sessions)]
        FILES[📁 Almacenamiento<br/>Media Files]
    end

    %% External Services
    subgraph "Servicios Externos"
        SIPSA[📊 SIPSA-DANE<br/>Precios de Referencia]
        MAPS[🗺️ Google Maps<br/>Geolocalización]
        EMAIL[📧 Servicio Email<br/>SMTP]
        PAYMENT[💳 Pagos<br/>(Futuro)]
        SMS[📱 SMS<br/>(Futuro)]
    end

    %% Security Layer
    subgraph "Seguridad"
        HTTPS[🔒 HTTPS/SSL]
        CSRF[🛡️ CSRF Protection]
        CORS[🌐 CORS]
        RATE[⚡ Rate Limiting]
    end

    %% Monitoring
    subgraph "Monitoreo"
        LOGS[📝 Logging]
        METRICS[📊 Metrics]
        HEALTH[❤️ Health Checks]
    end

    %% Connections
    WEB --> LB
    MOB --> LB
    API_DOC --> LB
    
    LB --> HTTPS
    HTTPS --> DJANGO
    
    DJANGO --> USERS
    DJANGO --> FARMS  
    DJANGO --> PRODUCTS
    DJANGO --> ORDERS
    DJANGO --> ANTI
    DJANGO --> FRONTEND
    
    DJANGO --> DRF
    DRF --> JWT
    DRF --> SWAGGER
    
    DJANGO --> SERIALIZERS
    DJANGO --> PERMISSIONS
    DJANGO --> SIGNALS
    DJANGO --> TASKS
    
    DJANGO --> DB
    DJANGO --> REDIS
    DJANGO --> FILES
    
    DJANGO --> SIPSA
    DJANGO --> MAPS
    DJANGO --> EMAIL
    DJANGO --> PAYMENT
    DJANGO --> SMS
    
    DJANGO --> CSRF
    DJANGO --> CORS
    DJANGO --> RATE
    
    DJANGO --> LOGS
    DJANGO --> METRICS
    DJANGO --> HEALTH
    
    CDN --> FILES
```

## Diagrama de Componentes Detallado

```mermaid
graph LR
    %% User Interface Components
    subgraph "Frontend Components"
        LOGIN[Login/Register]
        DASH_C[Dashboard Campesino]
        DASH_B[Dashboard Comprador]
        PRODUCTS_UI[Catálogo Productos]
        ORDERS_UI[Gestión Pedidos]
        CHAT[Sistema Mensajes]
        PROFILE[Gestión Perfil]
    end

    %% API Endpoints
    subgraph "API Endpoints"
        AUTH_API[/api/auth/]
        FARMS_API[/api/farms/]
        PROD_API[/api/products/]
        ORDERS_API[/api/orders/]
        ANTI_API[/api/anti-intermediarios/]
    end

    %% Business Services
    subgraph "Servicios de Negocio"
        USER_SERVICE[UserService]
        FARM_SERVICE[FarmService]
        PRODUCT_SERVICE[ProductService]
        ORDER_SERVICE[OrderService]
        CHAT_SERVICE[ChatService]
        PRICE_SERVICE[PriceComparisonService]
    end

    %% Data Models
    subgraph "Modelos de Datos"
        USER_MODEL[Usuario]
        FARM_MODEL[Finca]
        PROD_MODEL[Producto]
        ORDER_MODEL[Pedido]
        CHAT_MODEL[Conversacion/Mensaje]
        PRICE_MODEL[TransparenciaPrecios]
    end

    %% External Integrations
    subgraph "Integraciones"
        SIPSA_CLIENT[SIPSA Client]
        MAPS_CLIENT[Maps Client]
        EMAIL_CLIENT[Email Client]
    end

    %% Connections
    LOGIN --> AUTH_API
    DASH_C --> FARMS_API
    DASH_C --> PROD_API
    DASH_C --> ORDERS_API
    DASH_B --> PROD_API
    DASH_B --> ORDERS_API
    PRODUCTS_UI --> PROD_API
    ORDERS_UI --> ORDERS_API
    CHAT --> ANTI_API
    PROFILE --> AUTH_API

    AUTH_API --> USER_SERVICE
    FARMS_API --> FARM_SERVICE
    PROD_API --> PRODUCT_SERVICE
    ORDERS_API --> ORDER_SERVICE
    ANTI_API --> CHAT_SERVICE

    USER_SERVICE --> USER_MODEL
    FARM_SERVICE --> FARM_MODEL
    PRODUCT_SERVICE --> PROD_MODEL
    ORDER_SERVICE --> ORDER_MODEL
    CHAT_SERVICE --> CHAT_MODEL
    PRICE_SERVICE --> PRICE_MODEL

    PRICE_SERVICE --> SIPSA_CLIENT
    FARM_SERVICE --> MAPS_CLIENT
    USER_SERVICE --> EMAIL_CLIENT
```

## Arquitectura de Datos

```mermaid
erDiagram
    Usuario {
        int id PK
        string nombre
        string apellido
        string email UK
        string telefono
        string tipo_usuario
        date fecha_nacimiento
        string estado
        decimal calificacion_promedio
        int total_calificaciones
    }
    
    Finca {
        int id PK
        int usuario_id FK
        string nombre_finca
        string ubicacion_departamento
        string ubicacion_municipio
        decimal area_hectareas
        string tipo_cultivo
        decimal latitud
        decimal longitud
        string estado
    }
    
    CategoriaProducto {
        int id PK
        string nombre UK
        string descripcion
        string icono
        string estado
    }
    
    Producto {
        int id PK
        int usuario_id FK
        int finca_id FK
        int categoria_id FK
        string nombre
        decimal precio_por_kg
        int stock_disponible
        string unidad_medida
        string estado
        string imagen_principal
        json galeria_imagenes
    }
    
    Pedido {
        string id PK
        int comprador_id FK
        int campesino_id FK
        decimal total
        string estado
        string metodo_pago
        datetime fecha_pedido
        string codigo_seguimiento
    }
    
    DetallePedido {
        int id PK
        string pedido_id FK
        int producto_id FK
        decimal cantidad
        decimal precio_unitario
        string nombre_producto_snapshot
    }
    
    Conversacion {
        int id PK
        int campesino_id FK
        int comprador_id FK
        int producto_id FK
        boolean activa
    }
    
    Mensaje {
        int id PK
        int conversacion_id FK
        int remitente_id FK
        string tipo_mensaje
        text contenido
        decimal precio_ofertado
        datetime fecha_envio
        boolean leido
    }

    Usuario ||--o{ Finca : "campesino posee"
    Usuario ||--o{ Producto : "campesino crea"
    Usuario ||--o{ Pedido : "comprador realiza"
    Usuario ||--o{ Pedido : "campesino recibe"
    Usuario ||--o{ Conversacion : "participa"
    Usuario ||--o{ Mensaje : "envia"
    
    Finca ||--o{ Producto : "produce en"
    CategoriaProducto ||--o{ Producto : "clasifica"
    Producto ||--o{ DetallePedido : "se detalla en"
    Producto ||--o{ Conversacion : "se discute"
    
    Pedido ||--o{ DetallePedido : "contiene"
    Conversacion ||--o{ Mensaje : "intercambia"
```

## Flujo de Datos Principal

```mermaid
sequenceDiagram
    participant C as Comprador
    participant WEB as Frontend
    participant API as Django API
    participant DB as Database
    participant EXT as Servicios Externos
    participant CAM as Campesino

    %% Flujo de Búsqueda y Compra
    C->>WEB: Buscar productos
    WEB->>API: GET /api/products/?search=tomate
    API->>DB: Query productos
    DB-->>API: Lista productos
    API->>EXT: Obtener precios SIPSA
    EXT-->>API: Precios mercado
    API-->>WEB: Productos + comparación
    WEB-->>C: Mostrar resultados
    
    %% Flujo de Pedido
    C->>WEB: Crear pedido
    WEB->>API: POST /api/orders/
    API->>DB: Crear pedido
    API->>DB: Actualizar stock
    DB-->>API: Pedido creado
    API->>EXT: Enviar notificación
    EXT->>CAM: Email/SMS nuevo pedido
    API-->>WEB: Confirmación
    WEB-->>C: Pedido creado exitosamente
    
    %% Flujo de Actualización Estado
    CAM->>WEB: Actualizar estado pedido
    WEB->>API: PATCH /api/orders/{id}/actualizar_estado/
    API->>DB: Actualizar estado
    DB-->>API: Estado actualizado
    API->>EXT: Notificar comprador
    EXT->>C: Notificación cambio estado
    API-->>WEB: Confirmación
    WEB-->>CAM: Estado actualizado
```

## Tecnologías y Dependencias

### Backend
- **Framework**: Django 4.x
- **API**: Django REST Framework
- **Autenticación**: JWT (Simple JWT)
- **Base de Datos**: SQLite (desarrollo), MySQL (producción)
- **Cache**: Redis (futuro)
- **Documentación**: drf-yasg (Swagger)
- **Validación**: Django Serializers
- **Archivos**: Django File Handling

### Frontend
- **Tecnología**: HTML5 + CSS3 + JavaScript (Vanilla)
- **UI Framework**: Bootstrap 5
- **Iconos**: Font Awesome
- **Charts**: Chart.js
- **AJAX**: Fetch API

### Infraestructura
- **Servidor Web**: Nginx/Apache
- **WSGI**: Gunicorn
- **Base de Datos**: MySQL/PostgreSQL
- **Cache**: Redis
- **Archivos Estáticos**: CDN/S3 (futuro)
- **SSL**: Let's Encrypt

### Servicios Externos
- **Precios**: SIPSA-DANE API
- **Mapas**: Google Maps API
- **Email**: SMTP (Gmail, SendGrid)
- **Pagos**: PSE, Bancolombia (futuro)
- **SMS**: Twilio (futuro)

## Seguridad

### Autenticación y Autorización
- Sistema dual: Sesiones Django + JWT
- Permisos basados en roles (campesino/comprador)
- Rate limiting por IP/usuario
- CORS configurado para dominios específicos

### Protección de Datos
- HTTPS obligatorio en producción
- Validación CSRF en formularios
- Sanitización de inputs
- Encriptación de contraseñas (PBKDF2)
- Validación de archivos subidos

### Auditoría
- Logging completo de acciones críticas
- Timestamps en todas las entidades
- Tracking de cambios en pedidos
- Monitoreo de intentos de acceso fallidos

## Escalabilidad

### Horizontal
- Load balancer para múltiples instancias Django
- Base de datos con replicas de lectura
- CDN para archivos estáticos
- Cache distribuido con Redis Cluster

### Vertical
- Optimización de queries ORM
- Índices en campos críticos
- Paginación en listados grandes
- Lazy loading de relaciones

### Monitoreo
- Health checks automáticos
- Métricas de rendimiento
- Alertas por errores críticos
- Dashboard de administración

Este diagrama UML de arquitectura proporciona una visión completa del sistema Campo Directo, mostrando cómo los diferentes componentes interactúan entre sí para proporcionar una plataforma robusta y escalable que conecta directamente campesinos con compradores.