# Documentación Técnica UML - Campo Directo (Proceso Verificado)

Esta documentación refleja el flujo transaccional real del sistema, incluyendo automatizaciones de chat y notificaciones por correo electrónico.

## 1. Diagrama de Clases (Estructura de Datos)

```mermaid
classDiagram
    class Usuario {
        +String email
        +String nombre
        +Enum tipo_usuario
    }

    class Producto {
        +String nombre
        +Decimal precio_por_kg
        +Integer stock_disponible
        +reducir_stock(cantidad)
    }

    class Pedido {
        +String id (ORD-XXXX)
        +Decimal total
        +Enum estado
        +actualizar_estado(nuevo_estado)
    }

    class ItemPedido {
        +Decimal cantidad
        +Decimal precio_unitario
    }

    class Conversacion {
        +Boolean activa
        +DateTime fecha_actualizacion
    }

    class Mensaje {
        +String contenido
        +Enum tipo_mensaje
    }

    Usuario "1" -- "*" Pedido : participa
    Pedido "1" -- "1..*" ItemPedido : contiene
    Producto "1" -- "*" ItemPedido : referenciado
    Usuario "1" -- "*" Conversacion : chatea
    Conversacion "1" -- "*" Mensaje : contiene
```

---

## 2. Diagrama de Casos de Uso (Flujo de Usuario)

```mermaid
graph TD
    subgraph "Interfaz Cliente (Mercado/Dashboard)"
        UC1(Seleccionar Productos y Cantidad)
        UC2(Gestionar Carrito Frontend)
        UC3(Procesar Compra en Mis Pedidos)
        UC4(Consultar Estado y Chat)
    end

    subgraph "Interfaz Campesino (Dashboard)"
        UC5(Visualizar Nuevo Pedido)
        UC6(Aceptar/Confirmar Compra)
        UC7(Actualizar Estados de Logística)
    end

    Co[Comprador] --> UC1
    UC1 --> UC2
    UC2 --> UC3
    UC3 --> UC4
    
    C[Campesino] --> UC5
    UC5 --> UC6
    UC6 --> UC7
```

---

## 3. Diagrama de Secuencia: "Coreografía del Pedido"

Este diagrama muestra cómo un solo clic en "Procesar Compra" desencadena múltiples acciones automáticas en el servidor.

```mermaid
sequenceDiagram
    autonumber
    participant B as Comprador
    participant S as Sistema (Backend)
    participant Chat as Módulo Chat
    participant Mail as Servidor de Correo
    participant F as Campesino

    Note over B: En sección "Mis Pedidos"
    B->>S: Clic en "Procesar Compra"
    
    rect rgb(240, 247, 237)
        Note right of S: Proceso Atómico (Atomic Transaction)
        S->>S: Crear registro Pedido (ORD-XXXX)
        S->>S: Reducir Stock de Productos (reducir_stock)
        
        S->>Chat: Crear Conversación Automática
        S->>Chat: Enviar Mensaje: "¡Hola! He realizado el pedido..."
        
        S->>Mail: Enviar Confirmación (notificar_nuevo_pedido)
    end

    Mail-->>B: Email: ¡Tu pedido fue recibido!
    Mail-->>F: Email: ¡Tienes un nuevo pedido!

    Note over F: Dashboard: Sección "Pedidos"
    F->>S: Cambia Estado a "Confirmado"
    S->>Mail: Enviar Notificación (notificar_cambio_estado)
    Mail-->>B: Email: Pedido aceptado por el campesino
    
    loop Proceso de Logística
        F->>S: Actualiza a: En Preparación -> Listo -> Completado
        S->>Mail: Notifica cambio de estado al Comprador
    end
```

---

## 4. Diagrama de Estados (Ciclo Logístico Real)

Los nombres de los estados coinciden exactamente con los `ESTADO_CHOICES` del código.

```mermaid
stateDiagram-v2
    [*] --> pending: Compra Procesada
    pending --> confirmed: Campesino Acepta (Envia Email)
    confirmed --> preparing: En Preparación (Logística)
    preparing --> ready: Listo para Entrega (En tránsito)
    ready --> completed: Recibido por Comprador
    pending --> cancelled: Cancelado (Restaura Stock)
    confirmed --> cancelled: Cancelado por logística
```

---

## 5. Arquitectura de Notificaciones Automatizadas

```mermaid
flowchart TD
    Trigger[Procesar Compra] --> Order[Crear Pedido]
    Order --> Stock[Descontar Stock]
    Order --> Chat[Instanciar Chat Campesino/Comprador]
    Chat --> Msg[Enviar Mensaje Predefinido]
    Order --> Email[Disparar Notificaciones por Correo]
    Email --> E1[Aviso al Campesino]
    Email --> E2[Confirmación al Comprador]
```

> [!TIP]
> **Dato verificado en código:** El mensaje del chat utiliza los datos reales de la dirección y teléfono del comprador capturados en el proceso de compra.
