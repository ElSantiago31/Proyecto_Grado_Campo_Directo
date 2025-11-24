# Diagrama UML de Clases - Campo Directo

## Resumen del Sistema
Campo Directo es una plataforma que conecta campesinos directamente con compradores, eliminando intermediarios. El sistema maneja usuarios, fincas, productos, pedidos, conversaciones y transparencia de precios.

## Diagrama UML de Clases

```mermaid
classDiagram
    %% Modelo de Usuario Central
    class Usuario {
        +string nombre
        +string apellido
        +string email
        +string telefono
        +string tipo_usuario
        +date fecha_nacimiento
        +string estado
        +datetime fecha_registro
        +datetime fecha_actualizacion
        +datetime ultimo_login
        +ImageField avatar
        +decimal calificacion_promedio
        +int total_calificaciones
        
        +get_full_name() string
        +get_short_name() string
        +is_campesino() bool
        +is_comprador() bool
        +is_activo() bool
        +actualizar_calificacion(decimal) void
        +tiene_finca() bool
        +get_finca_principal() Finca
        +puede_crear_productos() bool
        +productos_disponibles_count() int
        +pedidos_como_comprador_count() int
        +pedidos_como_campesino_count() int
    }

    %% Modelo de Finca
    class Finca {
        +string nombre_finca
        +string ubicacion_departamento
        +string ubicacion_municipio
        +string direccion
        +decimal area_hectareas
        +string tipo_cultivo
        +string descripcion
        +decimal latitud
        +decimal longitud
        +string estado
        +datetime fecha_creacion
        +datetime fecha_actualizacion
        
        +ubicacion_completa() string
        +tiene_coordenadas() bool
        +productos_count() int
        +productos_disponibles_count() int
    }

    %% Modelo de Certificación
    class Certificacion {
        +string nombre
        +string descripcion
        +string entidad_certificadora
        +date fecha_obtencion
        +date fecha_vencimiento
        +string estado
        +FileField archivo_certificado
        +datetime fecha_creacion
        
        +is_vigente() bool
        +dias_para_vencer() int
    }

    %% Modelo de Categoría de Producto
    class CategoriaProducto {
        +string nombre
        +string descripcion
        +string icono
        +string estado
        +datetime fecha_creacion
        
        +productos_count() int
    }

    %% Modelo de Producto
    class Producto {
        +string nombre
        +string descripcion
        +decimal precio_por_kg
        +int stock_disponible
        +string unidad_medida
        +string estado
        +ImageField imagen_principal
        +JSONField galeria_imagenes
        +string tags
        +string calidad
        +date fecha_cosecha
        +date fecha_vencimiento
        +decimal peso_minimo_venta
        +decimal peso_maximo_venta
        +bool disponible_entrega_inmediata
        +int tiempo_preparacion_dias
        +datetime fecha_creacion
        +datetime fecha_actualizacion
        
        +is_disponible() bool
        +precio_formateado() string
        +get_tags_list() list
        +set_tags_from_list(list) void
        +get_galeria_urls() list
        +add_imagen_galeria(string) void
        +remove_imagen_galeria(string) void
        +puede_ser_comprado_por_cantidad(decimal) tuple
        +calcular_precio_total(decimal) decimal
        +reducir_stock(decimal) void
        +aumentar_stock(decimal) void
    }

    %% Modelo de Pedido
    class Pedido {
        +string id
        +decimal total
        +string estado
        +string metodo_pago
        +string notas_comprador
        +string notas_campesino
        +datetime fecha_pedido
        +datetime fecha_confirmacion
        +datetime fecha_preparacion
        +datetime fecha_entrega
        +datetime fecha_completado
        +string direccion_entrega
        +string telefono_contacto
        +date fecha_entrega_programada
        +time hora_entrega_programada
        +string codigo_seguimiento
        +int calificacion_comprador
        +int calificacion_campesino
        +string comentario_calificacion
        
        +estado_display_color() string
        +puede_ser_cancelado() bool
        +puede_ser_calificado_por_comprador() bool
        +puede_ser_calificado_por_campesino() bool
        +actualizar_estado(string, Usuario) void
        +calcular_total_desde_detalles() decimal
        +get_productos_resumen() list
    }

    %% Modelo de Detalle de Pedido
    class DetallePedido {
        +decimal cantidad
        +decimal precio_unitario
        +string nombre_producto_snapshot
        +string unidad_medida_snapshot
        
        +subtotal() decimal
    }

    %% Modelo de Conversación
    class Conversacion {
        +datetime fecha_creacion
        +datetime fecha_actualizacion
        +bool activa
        
        +ultimo_mensaje() Mensaje
        +mensajes_no_leidos_por_usuario(Usuario) int
        +marcar_mensajes_como_leidos(Usuario) void
    }

    %% Modelo de Mensaje
    class Mensaje {
        +string tipo_mensaje
        +string contenido
        +decimal precio_ofertado
        +decimal cantidad_ofertada
        +datetime fecha_envio
        +bool leido
        
        +es_oferta() bool
        +marcar_como_leido() void
    }

    %% Modelo de Transparencia de Precios
    class TransparenciaPrecios {
        +decimal precio_campo_directo
        +decimal precio_mercado_tradicional
        +string fuente_precio_referencia
        +datetime fecha_registro
        +string ciudad_referencia
        +string notas
        
        +ahorro_absoluto() decimal
        +ahorro_porcentual() decimal
        +hay_ahorro() bool
        +calcular_ahorro_por_cantidad(decimal) decimal
    }

    %% Modelo de Reporte de Impacto
    class ReporteImpacto {
        +date fecha_inicio
        +date fecha_fin
        +int total_transacciones
        +decimal ahorro_total_generado
        +int campesinos_beneficiados
        +int compradores_beneficiados
        +JSONField productos_top
        +datetime fecha_generacion
        
        +generar_reporte(date, date) ReporteImpacto
    }

    %% Relaciones
    Usuario ||--o{ Finca : posee
    Usuario ||--o{ Producto : crea
    Usuario ||--o{ Pedido : compra_como_comprador
    Usuario ||--o{ Pedido : vende_como_campesino
    Usuario ||--o{ Conversacion : participa_campesino
    Usuario ||--o{ Conversacion : participa_comprador
    Usuario ||--o{ Mensaje : envia
    
    Finca ||--o{ Certificacion : tiene
    Finca ||--o{ Producto : produce
    
    CategoriaProducto ||--o{ Producto : clasifica
    
    Producto ||--o{ DetallePedido : detalla
    Producto ||--o{ Conversacion : sobre
    Producto ||--o{ TransparenciaPrecios : compara
    
    Pedido ||--o{ DetallePedido : contiene
    
    Conversacion ||--o{ Mensaje : intercambia
    
    %% Enumeraciones
    class TipoUsuario {
        <<enumeration>>
        campesino
        comprador
    }
    
    class EstadoUsuario {
        <<enumeration>>
        activo
        inactivo
        suspendido
    }
    
    class TipoCultivo {
        <<enumeration>>
        organico
        tradicional
        hidroponico
        mixto
    }
    
    class EstadoProducto {
        <<enumeration>>
        disponible
        agotado
        temporada
        inactivo
    }
    
    class EstadoPedido {
        <<enumeration>>
        pending
        confirmed
        preparing
        ready
        completed
        cancelled
    }
    
    class MetodoPago {
        <<enumeration>>
        efectivo
        transferencia
        tarjeta
        otro
    }
    
    class TipoMensaje {
        <<enumeration>>
        texto
        oferta
        negociacion
        sistema
    }

    %% Relaciones con enumeraciones
    Usuario --> TipoUsuario
    Usuario --> EstadoUsuario
    Finca --> TipoCultivo
    Producto --> EstadoProducto
    Pedido --> EstadoPedido
    Pedido --> MetodoPago
    Mensaje --> TipoMensaje
```

## Descripción de las Entidades Principales

### 1. Usuario
- **Propósito**: Entidad central que representa tanto campesinos como compradores
- **Características**: Sistema de autenticación basado en email, calificaciones, perfil completo
- **Tipos**: Campesino (vende productos) y Comprador (adquiere productos)

### 2. Finca
- **Propósito**: Representa las propiedades agrícolas de los campesinos
- **Características**: Ubicación geográfica, tipo de cultivo, certificaciones
- **Relación**: Un campesino puede tener múltiples fincas

### 3. Producto
- **Propósito**: Productos agrícolas ofrecidos por los campesinos
- **Características**: Precios, stock, imágenes, categorización
- **Funciones**: Gestión de inventario, cálculos de precios

### 4. Pedido
- **Propósito**: Transacciones entre compradores y campesinos
- **Características**: Estados de seguimiento, métodos de pago, calificaciones
- **Flujo**: Desde pending hasta completed con estados intermedios

### 5. Conversación y Mensaje
- **Propósito**: Sistema de comunicación directa
- **Características**: Mensajes de texto, ofertas de precio, negociación
- **Funcionalidad**: Anti-intermediario, transparencia en negociación

### 6. TransparenciaPrecios
- **Propósito**: Comparación con precios de mercado tradicional
- **Características**: Cálculo de ahorros, fuentes de referencia
- **Objetivo**: Demostrar beneficios de compra directa

## Patrones de Diseño Implementados

1. **Model-View-Controller (MVC)**: Separación clara entre modelos, vistas y lógica de control
2. **Factory Pattern**: Para creación de diferentes tipos de usuarios
3. **Observer Pattern**: Para actualizaciones de estado de pedidos
4. **Strategy Pattern**: Para diferentes métodos de pago y cálculos de precios

## Principios SOLID Aplicados

- **Single Responsibility**: Cada modelo tiene una responsabilidad específica
- **Open/Closed**: Extensible a nuevos tipos de productos y estados
- **Liskov Substitution**: Herencia correcta en modelo de Usuario
- **Interface Segregation**: APIs específicas para cada tipo de usuario
- **Dependency Inversion**: Uso de abstracciones en lugar de implementaciones concretas