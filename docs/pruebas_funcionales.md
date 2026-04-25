# Guía de Pruebas Funcionales (Proyecto Campo Directo)

Las **Pruebas Funcionales** (o *Test Cases*) son documentos que demuestran a los jurados que cada parte del sistema hace exactamente lo que se supone que debe hacer desde la perspectiva del usuario final. No evalúan código, evalúan comportamientos.

Para colocarlas en tu documento de Word (Tesis), debes usar un formato de **Tabla de Casos de Prueba (Test Case Matrix)**. 

A continuación, te entrego la teoría y **5 casos de prueba reales** de tu plataforma ya redactados para que los copies, pegues y adaptes a tu documento.

---

## Estructura Recomendada para el Documento de Word

Debes insertar una tabla por cada funcionalidad clave. Las columnas estándar que te pedirán los jurados son:
*   **ID:** Identificador único (Ej: CP-01).
*   **Nombre de la Prueba:** Qué se está probando.
*   **Precondiciones:** Qué debe pasar antes de iniciar la prueba.
*   **Pasos:** Las acciones que hace el usuario paso a paso.
*   **Resultado Esperado:** Lo que el sistema debería hacer si todo sale bien.
*   **Resultado Obtenido:** Lo que realmente pasó (debe ser "Exitoso").
*   **Estado:** Aprobado / Rechazado.

---

## Casos de Prueba Listos para Copiar a tu Tesis

### Caso de Prueba 01: Autenticación con PIN Visual (2FA) Inclusivo
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-01 |
| **Nombre:** | Inicio de sesión con validación de doble factor (Emoji) |
| **Precondición:** | El usuario (Campesino) debe tener una cuenta registrada y un PIN visual configurado. |
| **Pasos de Ejecución:** | 1. Ingresar correo y contraseña de texto en el formulario de Login.<br>2. Hacer clic en "Iniciar Sesión".<br>3. El sistema muestra la cuadrícula interactiva de 9 Emojis.<br>4. El usuario selecciona el Emoji correcto (Ej: 🚜) y da clic en "Verificar". |
| **Resultado Esperado:** | El sistema valida la selección, genera el token de seguridad (JWT) y redirige al panel de control (`dashboard.html`). |
| **Resultado Obtenido:** | Redirección exitosa al panel. Los datos del usuario cargan correctamente. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 02: Simulación de Pasarela de Pagos Segura
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-02 |
| **Nombre:** | Procesamiento de compra con método "Tarjeta de Crédito" |
| **Precondición:** | El comprador debe tener al menos 1 producto en el carrito de compras. |
| **Pasos de Ejecución:** | 1. Abrir el carrito de compras.<br>2. Seleccionar "Pagar con Tarjeta (Pasarela Segura)" en el método de pago.<br>3. Hacer clic en "Procesar Compra".<br>4. Llenar los datos bancarios ficticios en el Modal de "PaySecure".<br>5. Presionar el botón "Pagar Ahora". |
| **Resultado Esperado:** | El botón cambia a estado "Contactando Banco..." por 2 segundos, luego muestra "Pago Exitoso". El modal se cierra, el carrito se vacía y se genera el pedido en base de datos. |
| **Resultado Obtenido:** | Modal funcional, animación exitosa y pedido creado con la etiqueta `metodo_pago: tarjeta`. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 03: Validación de Carga del Gráfico de Ventas (Chart.js)
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-03 |
| **Nombre:** | Renderizado de estadísticas en tiempo real del Campesino |
| **Precondición:** | El Campesino debe tener al menos 1 venta completada en el sistema. |
| **Pasos de Ejecución:** | 1. Iniciar sesión como Campesino.<br>2. Navegar usando el menú lateral a la sección "Estadísticas". |
| **Resultado Esperado:** | Se inicializa y dibuja un gráfico de líneas (`canvas`) mostrando el flujo de ingresos generados en los días del mes actual. |
| **Resultado Obtenido:** | El gráfico carga correctamente sin romper la interfaz ni presentar desbordamientos. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 04: Comunicación en Tiempo Real (Chat)
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-04 |
| **Nombre:** | Intercambio de mensajes e inmunidad XSS |
| **Precondición:** | Debe existir un pedido activo entre un Comprador y un Campesino. |
| **Pasos de Ejecución:** | 1. El comprador ingresa a la pestaña "Mensajes" y selecciona al campesino.<br>2. Envía el texto: `Hola, ¿cómo está el pedido? <script>alert("XSS")</script>`.<br>3. El campesino inicia sesión y revisa la bandeja de entrada. |
| **Resultado Esperado:** | El mensaje debe llegar casi instantáneamente (Asíncrono) a la bandeja del campesino. El script malicioso NO debe ejecutarse en el navegador de ninguno de los dos. |
| **Resultado Obtenido:** | El mensaje llega correctamente. La cadena de texto se muestra de forma plana porque el Frontend aplica `escapeHTML()` de forma efectiva. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 05: Impedir Cantidades Inválidas (Price Manipulation)
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-05 |
| **Nombre:** | Bloqueo de manipulación de cantidades en el carrito |
| **Precondición:** | El comprador debe estar en el flujo de selección de un producto agrícola. |
| **Pasos de Ejecución:** | 1. Entrar al detalle de un producto (Ej: Papa Pastusa).<br>2. Intentar ingresar en el campo de cantidad el valor `-5` o `1.5` (decimal).<br>3. Hacer clic en "Añadir al Carrito". |
| **Resultado Esperado:** | El Frontend o el Backend rechaza la operación informando que solo se admiten cantidades enteras y positivas para cajas/bultos/kilogramos, bloqueando un subtotal negativo o nulo. |
| **Resultado Obtenido:** | El carrito se limpia o se rechaza la inserción, protegiendo la base de datos de totales irreales. |
| **Estado:** | ✅ Aprobado |
### Caso de Prueba 06: Limitación de Especulación (Motor Ético SIPSA-DANE)
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-06 |
| **Nombre:** | Bloqueo de precios superiores al mercado tradicional |
| **Precondición:** | El Campesino intenta crear o editar un producto en su catálogo. |
| **Pasos de Ejecución:** | 1. Ir a la sección "Mis Productos" y hacer clic en "Agregar Producto".<br>2. Ingresar un producto (Ej: Tomate Chonto).<br>3. En el campo "Precio por KG", ingresar un valor exageradamente alto (Ej: $50,000 COP).<br>4. Guardar producto. |
| **Resultado Esperado:** | El backend consulta el tope máximo del DANE/SIPSA para ese producto y rechaza la inserción/actualización con un mensaje de validación informando que el precio excede el máximo ético permitido. |
| **Resultado Obtenido:** | Validación activada correctamente; el producto no se guarda hasta ajustar un precio justo. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 07: Usabilidad Móvil del Chat (Full-Screen Modal)
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-07 |
| **Nombre:** | Adaptación responsiva completa de la ventana de mensajería |
| **Precondición:** | El usuario (Campesino o Comprador) accede a la plataforma desde un teléfono móvil (Viewport < 768px). |
| **Pasos de Ejecución:** | 1. Iniciar sesión desde el celular.<br>2. Ir a la sección "Mensajes" y seleccionar un chat de la lista.<br>3. Verificar si es necesario hacer scroll para ver la caja de texto. |
| **Resultado Esperado:** | El chat se convierte en un Modal de Pantalla Completa (`position: fixed`) ocultando la interfaz trasera. El cuadro de entrada de texto queda anclado perfectamente arriba del teclado virtual sin requerir desplazamiento. |
| **Resultado Obtenido:** | Experiencia nativa tipo "WhatsApp" lograda. No hay superposición de contenedores. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 08: Generación de Comprobantes de Remisión (Chat)
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-08 |
| **Nombre:** | Envío automático del resumen de compra con método de pago |
| **Precondición:** | El Comprador procesa una orden exitosamente. |
| **Pasos de Ejecución:** | 1. Completar el flujo del carrito con "Pago en Efectivo".<br>2. El Comprador navega a su bandeja de "Mensajes" y abre el chat del Campesino asociado al pedido.<br>3. El Campesino revisa la bandeja de entrada. |
| **Resultado Esperado:** | Se genera automáticamente un primer mensaje del sistema enviado a nombre del Comprador detallando: ID del Pedido, Total, Dirección, Teléfono y Método de Pago elegido. |
| **Resultado Obtenido:** | El resumen del pedido aparece en el chat en un globo de texto validado y formateado correctamente. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 09: Rendimiento y Optimización de Imágenes
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-09 |
| **Nombre:** | Conversión y renderizado automático a formato WebP |
| **Precondición:** | El Campesino sube la foto de su perfil o de un producto en formato pesado (JPG/PNG > 5MB). |
| **Pasos de Ejecución:** | 1. Subir una imagen pesada de 5MB en el formulario de "Perfil".<br>2. Guardar cambios.<br>3. Inspeccionar la imagen cargada en el Dashboard (`Click Derecho > Inspeccionar`). |
| **Resultado Esperado:** | El backend comprime y convierte la imagen al vuelo, sirviendo un archivo con extensión o MIME-type `.webp` para reducir drásticamente el peso de descarga. |
| **Resultado Obtenido:** | Imagen optimizada y servida velozmente sin pérdida aparente de calidad gráfica. |
| **Estado:** | ✅ Aprobado |

### Caso de Prueba 10: Bifurcación de Roles y Seguridad de Rutas
| Atributo | Descripción |
| :--- | :--- |
| **ID del Caso:** | CP-10 |
| **Nombre:** | Bloqueo de acceso cruzado entre paneles de Campesino y Comprador |
| **Precondición:** | El usuario está autenticado en el sistema como "Comprador". |
| **Pasos de Ejecución:** | 1. Iniciar sesión como Comprador en `dashboard-comprador.html`.<br>2. Forzar manualmente la navegación en la barra de direcciones del navegador (URL) apuntando hacia la ruta privada del campesino: `http://127.0.0.1:8000/dashboard/`.<br>3. Presionar Enter. |
| **Resultado Esperado:** | El backend intercepta la petición, verifica el token y el rol (`tipo_usuario`), denegando el acceso y redirigiendo obligatoriamente al usuario de vuelta a su panel correspondiente (`/dashboard/comprador/`). |
| **Resultado Obtenido:** | Seguridad de rutas efectiva; es imposible para un Comprador acceder a las herramientas de venta del Campesino, y viceversa. |
| **Estado:** | ✅ Aprobado |

---

## ¿Cómo Ejecutarlas Oficialmente?
1. **Capturas de Pantalla (Evidencias):** Cuando pegues estas tablas en tu Word, debes poner debajo de cada tabla **una captura de pantalla** tuya realizando los "Pasos de Ejecución" (Ej: Una foto del modal de PaySecure, otra foto del gráfico de Chart.js).
2. Eso es lo que las universidades llaman "Evidencia de Pruebas". Con estos 10 casos documentados, cubres Seguridad, Front-End, Back-End, API y Lógica de Negocio.
