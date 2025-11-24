# Base de Datos de Producción - Campo Directo

Este documento describe el sistema de base de datos separada para datos de producción realistas en Campo Directo.

## 🎯 **Objetivo**

Tener una base de datos MySQL separada con datos realistas de producción que se puede consultar independientemente de la base de datos de desarrollo/testing.

## 🏗️ **Arquitectura**

### Configuración de Múltiples Bases de Datos

El proyecto está configurado para manejar dos bases de datos:

- **`default`**: Base de datos principal (SQLite en desarrollo, MySQL en producción)
- **`production`**: Base de datos MySQL con datos realistas de producción

### Router de Base de Datos

El archivo `campo_directo/routers.py` contiene:
- **`DatabaseRouter`**: Maneja el ruteo entre bases de datos
- **`ProductionDataManager`**: Facilita consultas a la BD de producción

## ⚙️ **Configuración**

### 1. Variables de Entorno

Agregar al archivo `.env`:

```env
# Base de datos de producción
PROD_DB_NAME=campo_directo_production
PROD_DB_USER=root
PROD_DB_PASSWORD=tu_password_mysql
PROD_DB_HOST=localhost
PROD_DB_PORT=3306
```

### 2. Crear Base de Datos MySQL

```bash
# Conectar a MySQL
mysql -u root -p

# Crear base de datos
CREATE DATABASE campo_directo_production 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

# Salir
EXIT;
```

## 📊 **Datos de Producción**

### Contenido de la Base de Datos

La BD de producción incluye:

#### 👥 **Usuarios**
- **Campesinos**: 2 usuarios con credenciales reales
- **Compradores**: 2 usuarios con credenciales reales
- Passwords: `campesino123` y `comprador123`

#### 🏡 **Fincas**
- **Finca San José** (Cundinamarca) - Orgánica
- **El Paraíso Verde** (Boyacá) - Mixta
- Con ubicaciones GPS reales y descripciones detalladas

#### 🏆 **Certificaciones**
- Certificación Orgánica
- Buenas Prácticas Agrícolas (BPA)  
- Comercio Justo
- Con fechas de vigencia realistas

#### 📋 **Categorías y Productos**
- **6 categorías**: Vegetales, Frutas, Granos, Hierbas, Tubérculos, Legumbres
- **15+ productos** con precios del mercado colombiano
- Stock, fechas de cosecha/vencimiento realistas

#### 📦 **Pedidos**
- **25 pedidos** históricos (últimos 3 meses)
- Estados: pendientes, confirmados, completados
- Detalles de pedido con múltiples productos
- Calificaciones y comentarios

## 🚀 **Uso**

### 1. Poblar Base de Datos de Producción

```bash
# Ejecutar migraciones en BD de producción
python manage.py migrate --database=production

# Crear datos realistas de producción
python manage.py create_production_data

# Para recrear todos los datos
python manage.py create_production_data --delete-existing
```

### 2. Exportar Datos a Archivos

```bash
# Generar dumps SQL y fixtures
python create_production_dump.py
```

Esto crea en la carpeta `dumps/`:
- **Dump MySQL**: `campo_directo_production_dump_YYYYMMDD_HHMMSS.sql`
- **Fixture Django**: `production_data_YYYYMMDD_HHMMSS.json`

### 3. Importar Datos

#### Opción A: Importar dump MySQL
```bash
# Crear BD si no existe
mysql -u root -p -e 'CREATE DATABASE campo_directo_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'

# Importar dump
mysql -u root -p campo_directo_production < dumps/campo_directo_production_dump_YYYYMMDD_HHMMSS.sql
```

#### Opción B: Importar fixture Django
```bash
# Ejecutar migraciones
python manage.py migrate --database=production

# Cargar fixture
python manage.py loaddata dumps/production_data_YYYYMMDD_HHMMSS.json --database=production
```

## 💻 **Consultar Datos en Código**

### Usando el ProductionDataManager

```python
from campo_directo.routers import ProductionDataManager
from users.models import Usuario
from products.models import Producto

# Obtener todos los usuarios de producción
usuarios_prod = ProductionDataManager.get_production_queryset(Usuario)

# Filtrar datos específicos
campesinos_prod = ProductionDataManager.get_production_data(
    Usuario, 
    tipo_usuario='campesino'
)

# Contar registros
total_productos = ProductionDataManager.count_production_records(Producto)
```

### Usando QuerySet directamente

```python
from users.models import Usuario
from products.models import Producto
from orders.models import Pedido

# Consultas directas a BD de producción
usuarios = Usuario.objects.using('production').all()
productos_disponibles = Producto.objects.using('production').filter(estado='disponible')
pedidos_completados = Pedido.objects.using('production').filter(estado='completed')
```

### En Views/APIs

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from products.models import Producto
from campo_directo.routers import ProductionDataManager

@api_view(['GET'])
def estadisticas_produccion(request):
    """
    API endpoint que retorna estadísticas de la BD de producción
    """
    # Usar datos de producción para estadísticas
    total_productos = ProductionDataManager.count_production_records(Producto)
    productos_disponibles = ProductionDataManager.get_production_data(
        Producto, 
        estado='disponible'
    ).count()
    
    return Response({
        'total_productos': total_productos,
        'productos_disponibles': productos_disponibles,
        'fuente': 'production_database'
    })
```

## 📋 **Comandos Útiles**

### Verificar datos
```bash
# Ver resumen de BD de producción
python manage.py dbshell --database=production

# Contar registros por tabla
SELECT 'usuarios' as tabla, COUNT(*) as total FROM users_usuario
UNION ALL
SELECT 'fincas' as tabla, COUNT(*) as total FROM farms_finca
UNION ALL  
SELECT 'productos' as tabla, COUNT(*) as total FROM products_producto
UNION ALL
SELECT 'pedidos' as tabla, COUNT(*) as total FROM orders_pedido;
```

### Gestión de migraciones
```bash
# Ver estado de migraciones en producción
python manage.py showmigrations --database=production

# Aplicar migraciones específicas
python manage.py migrate --database=production
```

## 🔒 **Seguridad**

### Credenciales por defecto:

**Campesinos:**
- `campesino@campodirecto.com` / `campesino123`
- `juan.perez@campodirecto.com` / `campesino123`

**Compradores:**
- `comprador@campodirecto.com` / `comprador123`
- `maria.gonzalez@campodirecto.com` / `comprador123`

> ⚠️ **Importante**: Cambiar estas credenciales antes de usar en producción real.

## 🧪 **Testing**

### Usar datos de producción en tests

```python
from django.test import TestCase, override_settings
from users.models import Usuario

class ProductionDataTestCase(TestCase):
    """
    Test case que usa datos de la BD de producción
    """
    
    def test_production_data_exists(self):
        # Verificar que hay datos en producción
        campesinos = Usuario.objects.using('production').filter(tipo_usuario='campesino')
        self.assertGreater(campesinos.count(), 0)
    
    def test_production_products_available(self):
        from products.models import Producto
        productos = Producto.objects.using('production').filter(estado='disponible')
        self.assertGreater(productos.count(), 10)
```

## 🐛 **Troubleshooting**

### Problemas Comunes

1. **Error de conexión a MySQL**
   ```
   django.db.utils.OperationalError: (2002, "Can't connect to local MySQL server")
   ```
   - Verificar que MySQL esté ejecutándose
   - Comprobar credenciales en `.env`

2. **Tablas no existen**
   ```
   django.db.utils.ProgrammingError: (1146, "Table 'campo_directo_production.users_usuario' doesn't exist")
   ```
   - Ejecutar: `python manage.py migrate --database=production`

3. **Datos duplicados**
   ```
   django.db.utils.IntegrityError: (1062, "Duplicate entry")
   ```
   - Usar: `python manage.py create_production_data --delete-existing`

### Logs y Debug

```python
# En settings.py, agregar para debug de queries
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📈 **Estadísticas Típicas**

Después de poblar la BD de producción, deberías ver aproximadamente:

- **Usuarios**: 4 (2 campesinos, 2 compradores)
- **Fincas**: 2 con ubicaciones reales
- **Certificaciones**: 3-4 certificaciones distribuidas
- **Categorías**: 6 categorías de productos
- **Productos**: 15+ productos con stock realista
- **Pedidos**: 25 pedidos con estados variados
- **Ventas totales**: ~$500,000 - $800,000 COP

---

## 🎯 **Casos de Uso Recomendados**

1. **Dashboards con datos realistas**
2. **Testing de APIs con volumen real**
3. **Demos y presentaciones**
4. **Desarrollo de reportes**
5. **Pruebas de rendimiento**
6. **Training de nuevos desarrolladores**

¡La base de datos de producción está lista para usarse! 🚀