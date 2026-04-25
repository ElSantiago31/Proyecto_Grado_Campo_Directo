# Informe Técnico Exhaustivo: Registro Histórico de Errores, Bugs y Vulnerabilidades (Proyecto Campo Directo)

A continuación, se detalla el listado definitivo, histórico y cronológico de absolutamente todos los fallos técnicos, vulnerabilidades de seguridad, problemas de arquitectura, errores de sintaxis y bugs visuales encontrados y corregidos durante todo el proceso de ingeniería de software del proyecto Campo Directo. 

La información fue extraída textualmente del control de versiones (`git log`) y los registros de depuración del servidor.

---

## 1. Seguridad Informática, Prevención de Fraudes y Accesos No Autorizados

### 1.1. Inyección de Código (XSS) y Sanitización de Backend
**Incidente:** Vulnerabilidad descubierta que permitía enviar scripts ejecutables a través del chat.
**Corrección:** Limpieza final de tokens huérfanos en `api.js` y `login-new.js` sumado a una sanitización estricta del backend y `escapeHTML()`.

### 1.2. Vulnerabilidad de Alteración de Precios (Price Manipulation)
**Incidente:** Un usuario podía alterar el JSON del carrito desde la consola del navegador para manipular los totales de la compra.
**Corrección:** Bloqueo de escritura del cliente. El backend se reconfiguró para que el precio unitario siempre se lea forzosamente de la Base de Datos.

### 1.3. Fuga Masiva de Información Confidencial (Information Leakage)
**Incidente:** Al enviar a producción, se descubrieron cientos de llamadas `console.log` que imprimían datos sensibles y tokens de la API.
**Corrección:** Hubo múltiples rondas de refactorización (commits: `Actualización error al eliminar console.log` y `limpiar tokens huerfanos que quedaron del script`). Se comentaron y eliminaron más de 239 `console.log`, `warn` y `error`.

### 1.4. Fallo Crítico en Bloqueo por PIN 2FA (LoginSerializer Bypass)
**Incidente:** Se detectó que la lógica de validación se podía eludir bajo ciertas condiciones y no bloqueaba a atacantes por fuerza bruta.
**Corrección:** Implementación de una suite de pruebas de seguridad y endurecimiento en el bloqueo por fallos en el PIN visual de 2FA.

### 1.5. Inconsistencia en Mayúsculas de Correos Electrónicos (Case Sensitivity)
**Incidente:** Correos registrados como "Juan@email.com" no podían iniciar sesión si se escribía "juan@email.com".
**Corrección:** Normalización a minúsculas (`.lower()`) universal durante el login y el registro.

### 1.6. Inestabilidad en Reglas de Suspensión y Sanciones
**Incidente:** Usuarios baneados podían seguir operando o los mensajes de error no eran claros para el Frontend.
**Corrección:** Refactorización iterativa (`fix(auth): mover validación de sanciones fuera del bloque 2FA`). Se sacaron las validaciones al flujo principal para afectar a todos de inmediato y arrojar un mensaje claro en la pantalla.

---

## 2. Arquitectura de Software, Backend (Django) y Base de Datos

### 2.1. Caídas y Crash en Carga de Productos
**Incidente:** El servidor presentaba un crash crítico en la vista de productos porque la base de datos tenía IDs en "hardcode" (fijados a fuego en el código, ej: 'Usuario Juan Carlos').
**Corrección:** `Fix de crash en productos, eliminación de hardcoding de Juan Carlos y mejoras en logs`. El código se adaptó para usar llaves relacionales dinámicas.

### 2.2. Errores Críticos 500 y Fallos de Configuración en Producción (PythonAnywhere)
**Incidente:** Django crasheaba en el servidor público al intentar recuperar el PIN o hacer peticiones a la API debido a configuraciones inválidas.
**Corrección:** 
- `Emergency Fix: Remove syntax error in PinRecoveryRequestView and add missing settings import`.
- Se forzó el uso de SQLite para el despliegue en PA free (`fix(settings): Usar SQLite incondicionalmente para despliegue`).
- Corrección de prefijos URL y actualización de `ALLOWED_HOSTS`.

### 2.3. Colapso del Panel de Administración (Django Admin)
**Incidente:** Al abrir la pestaña de conversaciones o la de ciertos pedidos, Django Admin se rompía arrojando excepciones `NoReverseMatch` y `FieldError`.
**Corrección:** Inclusión explícita de campos ocultos (`fix: agregar 'id' a readonly_fields en PedidoAdmin`) y actualización de namespaces de las URLs de `accounts` a `users`.

### 2.4. Crash Aritmético en Pedidos Nulos
**Incidente:** El sistema se detenía y estallaba matemáticamente si se alteraban detalles del pedido hacia valores vacíos (`None`).
**Corrección:** `fix: proteger subtotal contra None y recalcular total del pedido automaticamente al editar detalles`.

### 2.5. Errores Estructurales de Importación y Logging
**Incidente:** Impresiones de depuración rompían el I/O del servidor.
**Corrección:** Configuración explícita del logger 'users' en `settings.py` y limpieza profunda de impresiones genéricas. 

---

## 3. Lógica del Chat y Asignación de Roles

### 3.1. Condiciones de Carrera (Race Conditions) y Bugs en renderMessages
**Incidente:** Bug crítico donde la pantalla de chat no se limpiaba al cambiar de conversación, combinando los mensajes de dos clientes distintos.
**Corrección:** Se reparó el bug en la función de renderizado para forzar la actualización de los mensajes en tiempo real.

### 3.2. Error Estructural de Atribución de Autoría
**Incidente:** El sistema intentaba deducir quién enviaba el mensaje asumiendo perfiles fijos (comprador vs campesino), causando inestabilidad al cambiar entre roles.
**Corrección:** Refactorización del Core de WebSockets: usar el ID real del perfil extraído desde la BD en lugar de adivinar por el string de rol. Se solucionó también el nombre incorrecto de contacto al cambiar de roles en el dashboard.

---

## 4. Frontend, Interfaz (UI/UX), Javascript y Diseño Responsivo

### 4.1. Excepciones Sintácticas Críticas en Javascript (Syntax Errors)
**Incidente:** Pantalla blanca total en el dashboard del comprador tras un despliegue fallido.
**Corrección:** Dos rondas de commits (`Correccin llaves sin cerrar`, `Correción cierre de llave " ') "`, y `correción de dashboard.comprador.js ya que en el anterior commit se borró un cierre estricto de javascript`).

### 4.2. Inconsistencia del DOM en la Carga de Javascript
**Incidente:** El PIN visual (Emojis) a veces no dejaba hacer clic al arrancar la página.
**Corrección:** Forzar la lógica de PIN a esperar el evento `DOMContentLoaded`. También se revirtió un intento fallido de hacer 4 emojis, dejándolo en 1 sola figura sólida.

### 4.3. Excepciones Asíncronas y Promesas Vacías (`forEach Error`)
**Incidente:** Fallo masivo en el dashboard al iterar reseñas porque la API devolvía tipos de datos inesperados.
**Corrección:** `fix(dashboard): leer correctamente las reseñas retornadas por la API para evitar forEach error`. Inclusión de chequeo de arrays `Array.isArray()`.

### 4.4. Problemas de Accesibilidad y Duplicidad en la Vista
**Incidente:** Interfaz inmanejable por iconos superpuestos y duplicidad de monedas.
**Corrección:**
- `Corregir símbolo de moneda duplicado en el resumen del dashboard` ($$ 15.000).
- `Fix responsive mobile navigation and icon overlaps in farmer and buyer dashboards`.
- Solución al colapso del menú *drawer* móvil y los desplegables de filtros.
- Restauración y centrado del modal de reseñas que aparecía descuadrado o inactivo.

### 4.5. Validaciones Matemáticas en el Carrito de Compras
**Incidente:** El carrito de compras aceptaba cifras decimales erróneas en unidades que debían ser exactas.
**Corrección:** `fix: carrito ahora solo permite cantidades enteras y oculta selector de metodo`.

### 4.6. Desconexión de Rutas Locales
**Incidente:** Los scripts no reflejaban los últimos cambios realizados por el desarrollador.
**Corrección:** Reparación de enrutamientos de Django: `fix(dashboard): actualizar javascript base en directorio static en vez de staticfiles`.

### 4.7. Fallos Ocultos de Gráficos (Chart.js)
**Incidente:** Gráfico de ventas no se mostraba (tamaño 0x0) debido a que la librería `Chart.js` intentaba dibujarlo dentro de un contenedor invisible (`display: none`).
**Corrección:** Diferimiento de la instanciación gráfica hasta el momento exacto en el que el navegador aplica la clase de "Pestaña Activa".

### 4.8 Manejo Ciego de Errores (Error Parsing)
**Incidente:** "Error en la petición". El Frontend arrojaba errores incomprensibles.
**Corrección:** Adaptación integral del manejador de peticiones para leer correctamente `ApiError.details` y traducirlo a "Contraseña incorrecta".

### 4.9 Fallos Responsivos en el Módulo de Chat
**Incidente:** Al abrir una conversación en un dispositivo móvil, el chat quedaba inoperable. El estado vacío ("Bandeja de Entrada") se superponía al chat activo bloqueando el botón de retroceso debido a una regla `!important` conflictiva. Además, la altura del contenedor provocaba que la caja de texto quedara fuera de la pantalla, obligando al usuario a deslizar (scroll) la página entera.
**Corrección:** Refactorización de las reglas CSS (`dashboard.css`) para aislar los estados por ID y sustitución de la altura estática (`82vh`) por un cálculo dinámico (`calc(100vh - 220px)`) para garantizar el encaje perfecto del teclado y el chat dentro de la pantalla sin scroll vertical.
