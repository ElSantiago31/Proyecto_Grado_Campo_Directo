# Diagrama UML de Casos de Uso - Campo Directo

## Resumen
Este diagrama muestra los principales casos de uso del sistema Campo Directo, organizados por actores (Campesino, Comprador, Sistema) y sus interacciones.

## Diagrama de Casos de Uso

```mermaid
graph TB
    %% Actores
    subgraph "Actores"
        Campesino[👨‍🌾 Campesino]
        Comprador[🏢 Comprador] 
        Sistema[⚙️ Sistema]
        Admin[👨‍💼 Administrador]
    end

    %% Casos de Uso de Autenticación
    subgraph "Gestión de Usuarios"
        UC001[Registrarse]
        UC002[Iniciar Sesión]
        UC003[Actualizar Perfil]
        UC004[Cambiar Contraseña]
        UC005[Cerrar Sesión]
    end

    %% Casos de Uso del Campesino
    subgraph "Gestión de Fincas"
        UC010[Registrar Finca]
        UC011[Actualizar Información de Finca]
        UC012[Agregar Certificaciones]
        UC013[Gestionar Coordenadas GPS]
    end

    subgraph "Gestión de Productos"
        UC020[Crear Producto]
        UC021[Editar Producto]
        UC022[Eliminar Producto]
        UC023[Actualizar Stock]
        UC024[Subir Imágenes de Producto]
        UC025[Gestionar Categorías]
        UC026[Configurar Precios]
    end

    subgraph "Gestión de Pedidos (Campesino)"
        UC030[Ver Pedidos Recibidos]
        UC031[Confirmar Pedido]
        UC032[Actualizar Estado de Pedido]
        UC033[Cancelar Pedido]
        UC034[Programar Entrega]
        UC035[Marcar como Completado]
    end

    %% Casos de Uso del Comprador
    subgraph "Búsqueda y Compra"
        UC040[Buscar Productos]
        UC041[Filtrar por Categoría]
        UC042[Ver Detalles de Producto]
        UC043[Ver Perfil de Campesino]
        UC044[Comparar Precios]
        UC045[Crear Pedido]
        UC046[Cancelar Pedido]
    end

    subgraph "Gestión de Pedidos (Comprador)"
        UC050[Ver Mis Pedidos]
        UC051[Seguir Estado de Pedido]
        UC052[Confirmar Recepción]
        UC053[Calificar Campesino]
        UC054[Reportar Problema]
    end

    %% Casos de Uso de Comunicación
    subgraph "Sistema Anti-Intermediarios"
        UC060[Iniciar Conversación]
        UC061[Enviar Mensaje]
        UC062[Hacer Oferta de Precio]
        UC063[Negociar Condiciones]
        UC064[Ver Historial de Mensajes]
    end

    %% Casos de Uso del Sistema
    subgraph "Transparencia de Precios"
        UC070[Comparar con Precios de Mercado]
        UC071[Calcular Ahorros]
        UC072[Generar Reportes de Impacto]
        UC073[Actualizar Precios de Referencia]
    end

    subgraph "Notificaciones"
        UC080[Enviar Notificación de Pedido]
        UC081[Notificar Cambio de Estado]
        UC082[Recordar Entrega Pendiente]
        UC083[Solicitar Calificación]
    end

    %% Casos de Uso del Dashboard
    subgraph "Dashboard y Estadísticas"
        UC090[Ver Dashboard Campesino]
        UC091[Ver Dashboard Comprador]
        UC092[Ver Estadísticas de Ventas]
        UC093[Ver Actividad Reciente]
        UC094[Generar Reportes]
    end

    %% Casos de Uso de Administración
    subgraph "Administración"
        UC100[Gestionar Usuarios]
        UC101[Moderar Contenido]
        UC102[Configurar Categorías]
        UC103[Monitorear Sistema]
        UC104[Generar Reportes Globales]
    end

    %% Relaciones de los Actores con los Casos de Uso

    %% Campesino
    Campesino --> UC001
    Campesino --> UC002
    Campesino --> UC003
    Campesino --> UC004
    Campesino --> UC005
    
    Campesino --> UC010
    Campesino --> UC011
    Campesino --> UC012
    Campesino --> UC013
    
    Campesino --> UC020
    Campesino --> UC021
    Campesino --> UC022
    Campesino --> UC023
    Campesino --> UC024
    Campesino --> UC025
    Campesino --> UC026
    
    Campesino --> UC030
    Campesino --> UC031
    Campesino --> UC032
    Campesino --> UC033
    Campesino --> UC034
    Campesino --> UC035
    
    Campesino --> UC060
    Campesino --> UC061
    Campesino --> UC062
    Campesino --> UC063
    Campesino --> UC064
    
    Campesino --> UC090
    Campesino --> UC092
    Campesino --> UC093

    %% Comprador
    Comprador --> UC001
    Comprador --> UC002
    Comprador --> UC003
    Comprador --> UC004
    Comprador --> UC005
    
    Comprador --> UC040
    Comprador --> UC041
    Comprador --> UC042
    Comprador --> UC043
    Comprador --> UC044
    Comprador --> UC045
    Comprador --> UC046
    
    Comprador --> UC050
    Comprador --> UC051
    Comprador --> UC052
    Comprador --> UC053
    Comprador --> UC054
    
    Comprador --> UC060
    Comprador --> UC061
    Comprador --> UC062
    Comprador --> UC063
    Comprador --> UC064
    
    Comprador --> UC070
    Comprador --> UC071
    
    Comprador --> UC091
    Comprador --> UC093

    %% Sistema
    Sistema --> UC072
    Sistema --> UC073
    Sistema --> UC080
    Sistema --> UC081
    Sistema --> UC082
    Sistema --> UC083

    %% Administrador
    Admin --> UC100
    Admin --> UC101
    Admin --> UC102
    Admin --> UC103
    Admin --> UC104

    %% Relaciones de Dependencia e Inclusión
    UC045 -.-> UC040 : includes
    UC045 -.-> UC042 : includes
    UC031 -.-> UC030 : includes
    UC052 -.-> UC050 : includes
    UC062 -.-> UC060 : includes
    UC071 -.-> UC070 : includes

    %% Estilos
    classDef actor fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef usecase fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef system fill:#fff3e0,stroke:#e65100,stroke-width:2px

    class Campesino,Comprador,Admin actor
    class Sistema system
```

## Descripción Detallada de Casos de Uso

### 1. Gestión de Usuarios (UC001-UC005)
**Actor Principal**: Campesino, Comprador

- **UC001 - Registrarse**: Nuevo usuario se registra proporcionando información personal y eligiendo tipo (campesino/comprador)
- **UC002 - Iniciar Sesión**: Usuario autenticado accede al sistema con email y contraseña
- **UC003 - Actualizar Perfil**: Modificar información personal, foto de perfil, datos de contacto
- **UC004 - Cambiar Contraseña**: Actualizar credenciales de acceso por seguridad
- **UC005 - Cerrar Sesión**: Terminar sesión activa del usuario

### 2. Gestión de Fincas (UC010-UC013)
**Actor Principal**: Campesino

- **UC010 - Registrar Finca**: Campesino registra nueva propiedad agrícola
- **UC011 - Actualizar Información de Finca**: Modificar datos como área, tipo de cultivo, descripción
- **UC012 - Agregar Certificaciones**: Subir documentos de certificaciones orgánicas o de calidad
- **UC013 - Gestionar Coordenadas GPS**: Establecer ubicación exacta para entregas y transparencia

### 3. Gestión de Productos (UC020-UC026)
**Actor Principal**: Campesino

- **UC020 - Crear Producto**: Registrar nuevo producto con precios, stock, descripción
- **UC021 - Editar Producto**: Actualizar información de productos existentes
- **UC022 - Eliminar Producto**: Remover productos del catálogo
- **UC023 - Actualizar Stock**: Modificar cantidades disponibles
- **UC024 - Subir Imágenes de Producto**: Gestionar galería fotográfica
- **UC025 - Gestionar Categorías**: Clasificar productos por tipo
- **UC026 - Configurar Precios**: Establecer precios por kilogramo, ofertas especiales

### 4. Búsqueda y Compra (UC040-UC046)
**Actor Principal**: Comprador

- **UC040 - Buscar Productos**: Encontrar productos por nombre, categoría, ubicación
- **UC041 - Filtrar por Categoría**: Usar filtros para refinar búsqueda
- **UC042 - Ver Detalles de Producto**: Revisar información completa, precios, campesino
- **UC043 - Ver Perfil de Campesino**: Conocer información del productor, calificaciones
- **UC044 - Comparar Precios**: Ver comparación con precios de mercado tradicional
- **UC045 - Crear Pedido**: Generar orden de compra con productos seleccionados
- **UC046 - Cancelar Pedido**: Anular pedido si está en estado permitido

### 5. Gestión de Pedidos (UC030-UC035, UC050-UC054)
**Actores**: Campesino (UC030-UC035), Comprador (UC050-UC054)

#### Campesino:
- **UC030 - Ver Pedidos Recibidos**: Lista de órdenes de compradores
- **UC031 - Confirmar Pedido**: Aceptar pedido y comprometerse a entrega
- **UC032 - Actualizar Estado de Pedido**: Cambiar estado (preparando, listo, etc.)
- **UC033 - Cancelar Pedido**: Rechazar pedido con justificación
- **UC034 - Programar Entrega**: Establecer fecha y hora de entrega
- **UC035 - Marcar como Completado**: Finalizar transacción

#### Comprador:
- **UC050 - Ver Mis Pedidos**: Historial y estado de órdenes realizadas
- **UC051 - Seguir Estado de Pedido**: Monitorear progreso con código de seguimiento
- **UC052 - Confirmar Recepción**: Validar que recibió el producto
- **UC053 - Calificar Campesino**: Evaluar calidad y servicio del productor
- **UC054 - Reportar Problema**: Informar inconvenientes con el pedido

### 6. Sistema Anti-Intermediarios (UC060-UC064)
**Actores**: Campesino, Comprador

- **UC060 - Iniciar Conversación**: Crear canal de comunicación directa
- **UC061 - Enviar Mensaje**: Intercambio de mensajes de texto
- **UC062 - Hacer Oferta de Precio**: Proponer precio diferente al publicado
- **UC063 - Negociar Condiciones**: Acordar términos de cantidad, entrega, pago
- **UC064 - Ver Historial de Mensajes**: Revisar conversaciones anteriores

### 7. Transparencia de Precios (UC070-UC073)
**Actores**: Comprador, Sistema

- **UC070 - Comparar con Precios de Mercado**: Ver diferencias con precios SIPSA-DANE
- **UC071 - Calcular Ahorros**: Mostrar ahorro al comprar directo
- **UC072 - Generar Reportes de Impacto**: Sistema calcula beneficios globales
- **UC073 - Actualizar Precios de Referencia**: Actualizar datos de mercado tradicional

### 8. Dashboard y Estadísticas (UC090-UC094)
**Actores**: Campesino, Comprador

- **UC090 - Ver Dashboard Campesino**: Panel con ventas, pedidos, productos
- **UC091 - Ver Dashboard Comprador**: Panel con compras, ahorros, favoritos
- **UC092 - Ver Estadísticas de Ventas**: Métricas de desempeño del campesino
- **UC093 - Ver Actividad Reciente**: Últimas transacciones y movimientos
- **UC094 - Generar Reportes**: Crear informes personalizados

### 9. Administración (UC100-UC104)
**Actor Principal**: Administrador

- **UC100 - Gestionar Usuarios**: CRUD de usuarios, activar/desactivar cuentas
- **UC101 - Moderar Contenido**: Revisar productos, mensajes, reportes
- **UC102 - Configurar Categorías**: Gestionar taxonomía de productos
- **UC103 - Monitorear Sistema**: Supervisar rendimiento y errores
- **UC104 - Generar Reportes Globales**: Estadísticas generales de la plataforma

## Flujos Principales

### Flujo de Compra Completa
1. Comprador busca productos (UC040)
2. Ve detalles y compara precios (UC042, UC044)
3. Inicia conversación con campesino (UC060)
4. Negocia condiciones (UC063)
5. Crea pedido (UC045)
6. Campesino confirma pedido (UC031)
7. Campesino actualiza estados (UC032)
8. Comprador confirma recepción (UC052)
9. Ambos se califican mutuamente (UC053)

### Flujo de Gestión de Productos
1. Campesino registra finca (UC010)
2. Crea productos (UC020)
3. Sube imágenes (UC024)
4. Actualiza stock regularmente (UC023)
5. Gestiona pedidos recibidos (UC030-UC035)
6. Revisa estadísticas (UC090, UC092)

## Actores Secundarios

- **Sistema de Pagos**: Procesa transacciones
- **Servicio de Geolocalización**: Proporciona coordenadas GPS
- **API SIPSA-DANE**: Fuente de precios de referencia
- **Sistema de Notificaciones**: Envía alertas y recordatorios
- **Servicio de Almacenamiento**: Maneja imágenes y archivos