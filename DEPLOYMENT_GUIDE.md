# 🚀 Guía de Despliegue - Campo Directo

Esta guía te ayudará a desplegar Campo Directo en un servidor real de producción.

## 🎯 **Respuesta a tu Pregunta Principal**

**¡SÍ!** Los usuarios que crees se mantendrán después de reiniciar el servidor, siempre que uses una base de datos persistente (MySQL/PostgreSQL). Esto es porque:

- ✅ Los datos se guardan en la **base de datos**, no en memoria
- ✅ Al reiniciar el servidor Django, la BD **permanece intacta**
- ✅ Todos los usuarios, productos, pedidos se **conservan**

## 🏗️ **Opciones de Despliegue**

### Opción 1: VPS/Servidor Dedicado (Recomendado)
- **Proveedores**: DigitalOcean, Linode, AWS EC2, Google Cloud
- **Control total** del servidor
- **Mejor para producción** seria

### Opción 2: Hosting Compartido con Python
- **Proveedores**: PythonAnywhere, Heroku, Railway
- **Más fácil** de configurar
- **Limitaciones** en recursos

### Opción 3: Hosting Local/Casero
- **Tu propia máquina** como servidor
- **IP pública** necesaria
- **No recomendado** para producción seria

## 🛠️ **Preparación para Producción**

### 1. Configuración de Producción

Crear archivo `.env.production`:

```env
# Configuración de producción
DEBUG=False
SECRET_KEY=tu-clave-secreta-super-segura-aqui
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,tu-ip-servidor

# Base de datos principal (MySQL en producción)
DB_NAME=campo_directo_prod
DB_USER=campo_directo_user
DB_PASSWORD=password-muy-seguro
DB_HOST=localhost
DB_PORT=3306

# Base de datos de producción (datos realistas)
PROD_DB_NAME=campo_directo_production
PROD_DB_USER=campo_directo_user
PROD_DB_PASSWORD=password-muy-seguro
PROD_DB_HOST=localhost
PROD_DB_PORT=3306

# Email (para notificaciones)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-app

# Dominio
DEFAULT_FROM_EMAIL=Campo Directo <noreply@tu-dominio.com>

# Cache (Redis si está disponible)
REDIS_URL=redis://127.0.0.1:6379/1
```

### 2. Modificar Settings para Producción

Agregar al final de `settings.py`:

```python
# Configuración específica para producción
if not DEBUG:
    # Seguridad HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Configuración de archivos estáticos
    STATIC_ROOT = '/var/www/campo-directo/static/'
    MEDIA_ROOT = '/var/www/campo-directo/media/'
    
    # Configuración de sesiones
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    
    # Logging para producción
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': '/var/log/campo-directo/django.log',
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': '/var/log/campo-directo/django-error.log',
                'formatter': 'verbose',
            },
        },
        'root': {
            'handlers': ['file', 'error_file'],
        },
        'loggers': {
            'django': {
                'handlers': ['file', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
```

### 3. Crear Archivo requirements.txt

```bash
# Generar requirements actuales
pip freeze > requirements.txt
```

O crear manualmente:

```txt
Django==5.2.7
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.0
django-cors-headers==4.4.0
drf-yasg==1.21.7
django-filter==24.3
django-extensions==3.2.3
python-decouple==3.8
Pillow==10.4.0
mysqlclient==2.2.4
redis==5.0.8
gunicorn==23.0.0
psycopg2-binary==2.9.9
```

## 🖥️ **Despliegue en VPS (Ubuntu/Debian)**

### Paso 1: Configurar Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv git nginx mysql-server redis-server
sudo apt install -y build-essential python3-dev libmysqlclient-dev

# Configurar MySQL
sudo mysql_secure_installation

# Crear usuario y base de datos
sudo mysql -u root -p
```

```sql
-- En MySQL
CREATE USER 'campo_directo_user'@'localhost' IDENTIFIED BY 'password-muy-seguro';
CREATE DATABASE campo_directo_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE campo_directo_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON campo_directo_prod.* TO 'campo_directo_user'@'localhost';
GRANT ALL PRIVILEGES ON campo_directo_production.* TO 'campo_directo_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Paso 2: Clonar y Configurar Proyecto

```bash
# Crear directorio de aplicación
sudo mkdir -p /var/www/campo-directo
sudo chown $USER:$USER /var/www/campo-directo
cd /var/www/campo-directo

# Clonar proyecto (o subir archivos)
git clone https://github.com/tu-usuario/campo-directo.git .
# O si subes archivos manualmente:
# scp -r C:\Users\estef\campo-directo-django/* user@server:/var/www/campo-directo/

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración de producción
cp .env.example .env
# Editar .env con los valores correctos
nano .env
```

### Paso 3: Configurar Django

```bash
# Activar entorno virtual
source /var/www/campo-directo/venv/bin/activate

# Realizar migraciones
python manage.py migrate
python manage.py migrate --database=production

# Crear superusuario
python manage.py createsuperuser

# Poblar datos de producción
python manage.py create_production_data

# Recolectar archivos estáticos
sudo mkdir -p /var/www/campo-directo/static
sudo mkdir -p /var/www/campo-directo/media  
sudo mkdir -p /var/log/campo-directo
sudo chown -R www-data:www-data /var/www/campo-directo/static
sudo chown -R www-data:www-data /var/www/campo-directo/media
sudo chown -R www-data:www-data /var/log/campo-directo

python manage.py collectstatic --noinput
```

### Paso 4: Configurar Gunicorn

Crear `/etc/systemd/system/campo-directo.service`:

```ini
[Unit]
Description=Campo Directo Django App
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/campo-directo
Environment=PATH=/var/www/campo-directo/venv/bin
ExecStart=/var/www/campo-directo/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 campo_directo.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable campo-directo
sudo systemctl start campo-directo
sudo systemctl status campo-directo
```

### Paso 5: Configurar Nginx

Crear `/etc/nginx/sites-available/campo-directo`:

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Certificados SSL (usar Certbot)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_dhparam /etc/nginx/dhparam.pem;
    
    # Configuración de archivos estáticos
    location /static/ {
        alias /var/www/campo-directo/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    location /media/ {
        alias /var/www/campo-directo/media/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }
    
    # Proxy a Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;
    }
    
    # Configuraciones de seguridad
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/campo-directo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Paso 6: Configurar SSL con Certbot

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Configurar renovación automática
sudo crontab -e
# Agregar línea:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🌐 **Despliegue Fácil en PythonAnywhere**

### Opción Más Sencilla para Principiantes

1. **Crear cuenta** en [PythonAnywhere](https://www.pythonanywhere.com)

2. **Subir código** vía dashboard o Git

3. **Crear Web App Django** desde el dashboard

4. **Configurar base de datos MySQL** (incluida en planes pagos)

5. **Instalar dependencias** en consola:
   ```bash
   pip3.10 install --user -r requirements.txt
   ```

6. **Aplicar migraciones:**
   ```bash
   python manage.py migrate
   python manage.py migrate --database=production
   python manage.py create_production_data
   ```

## ✅ **Verificar Despliegue**

### Checklist de Funcionamiento:

```bash
# 1. Verificar servicios
sudo systemctl status campo-directo
sudo systemctl status nginx
sudo systemctl status mysql

# 2. Verificar logs
sudo journalctl -u campo-directo -f
sudo tail -f /var/log/campo-directo/django.log
sudo tail -f /var/log/nginx/error.log

# 3. Probar conectividad
curl https://tu-dominio.com/api/health/

# 4. Verificar base de datos
python manage.py dbshell
# SELECT COUNT(*) FROM users_usuario;
```

### Testing de Persistencia:

```bash
# 1. Crear usuario desde web o comando
python manage.py shell
# >>> from users.models import Usuario
# >>> usuario = Usuario.objects.create_user('test@test.com', 'Test User', 'password123')
# >>> usuario.save()
# >>> exit()

# 2. Reiniciar servicios
sudo systemctl restart campo-directo
sudo systemctl restart nginx

# 3. Verificar que el usuario sigue existiendo
python manage.py shell
# >>> Usuario.objects.filter(email='test@test.com').exists()
# True ✅
```

## 🔧 **Mantenimiento**

### Comandos Útiles:

```bash
# Ver usuarios activos
python manage.py shell -c "from users.models import Usuario; print(f'Usuarios: {Usuario.objects.count()}')"

# Backup de base de datos
mysqldump -u campo_directo_user -p campo_directo_prod > backup_$(date +%Y%m%d).sql

# Restaurar backup
mysql -u campo_directo_user -p campo_directo_prod < backup_20241011.sql

# Ver logs en tiempo real
sudo journalctl -u campo-directo -f

# Reiniciar aplicación tras cambios
sudo systemctl restart campo-directo
```

### Actualizaciones:

```bash
# 1. Hacer backup
mysqldump -u campo_directo_user -p campo_directo_prod > backup_pre_update.sql

# 2. Actualizar código
cd /var/www/campo-directo
git pull origin main
# O subir nuevos archivos vía SCP/SFTP

# 3. Instalar dependencias nuevas
source venv/bin/activate
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate
python manage.py collectstatic --noinput

# 5. Reiniciar servicios
sudo systemctl restart campo-directo
sudo systemctl reload nginx
```

## 🚨 **Troubleshooting**

### Problemas Comunes:

1. **"Bad Gateway" (502):**
   ```bash
   # Verificar que Gunicorn esté ejecutándose
   sudo systemctl status campo-directo
   # Ver logs
   sudo journalctl -u campo-directo -n 50
   ```

2. **Archivos estáticos no cargan:**
   ```bash
   python manage.py collectstatic --noinput
   sudo chown -R www-data:www-data /var/www/campo-directo/static
   ```

3. **Error de base de datos:**
   ```bash
   # Verificar MySQL
   sudo systemctl status mysql
   # Probar conexión
   mysql -u campo_directo_user -p campo_directo_prod -e "SELECT 1;"
   ```

4. **Error de permisos:**
   ```bash
   sudo chown -R www-data:www-data /var/www/campo-directo
   sudo chmod -R 755 /var/www/campo-directo
   ```

## 💡 **Respuesta Final a tu Pregunta**

**✅ SÍ, definitivamente los usuarios persisten tras reiniciar el servidor.**

Esto es porque:
- Los datos se almacenan en **MySQL** (base de datos persistente)
- Al reiniciar el servidor Django, **solo se reinicia la aplicación web**
- La **base de datos MySQL permanece corriendo** e intacta
- Todos los usuarios, productos, pedidos **se mantienen guardados**

**Ejemplo práctico:**
1. Despliegas en servidor → Funciona ✅
2. Usuarios se registran → Se guardan en MySQL ✅  
3. Reinicias servidor → Aplicación se reinicia ✅
4. Usuarios siguen ahí → Pueden hacer login normalmente ✅

**La persistencia está garantizada** siempre que uses una BD como MySQL/PostgreSQL (no SQLite en producción).
