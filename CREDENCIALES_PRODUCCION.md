# 🔐 CREDENCIALES DE PRODUCCIÓN - CAMPO DIRECTO

**Fecha de creación:** 11 de Octubre 2025
**Estado:** Usuarios listos para producción

## 🌱 CAMPESINOS

### Usuario Principal
- **Email:** `campesino@campodirecto.com`
- **Password:** `CampoDirecto2024!`
- **Nombre:** Juan Carlos Pérez Rodríguez
- **Teléfono:** 312-345-6789

### Usuario Demo
- **Email:** `juan.perez@campodirecto.com`
- **Password:** `Campesino123!`
- **Nombre:** Juan Pérez
- **Teléfono:** 314-567-8901

---

## 🛒 COMPRADORES

### Usuario Principal
- **Email:** `comprador@campodirecto.com`
- **Password:** `CampoDirecto2024!`
- **Nombre:** María José González López
- **Teléfono:** 398-765-4321

### Usuario Demo
- **Email:** `maria.gonzalez@campodirecto.com`
- **Password:** `Comprador123!`
- **Nombre:** María González
- **Teléfono:** 317-654-3210

---

## 🔧 ADMINISTRADOR

### Superusuario
- **Email:** `admin@campodirecto.com`
- **Password:** `AdminCampoDirecto2024!`
- **Nombre:** Administrador Campo Directo
- **Acceso:** Django Admin (`/admin/`) + Todos los dashboards
- **Permisos:** Superusuario completo

---

## 📱 URLs DE ACCESO

### Usuarios Finales
- **Campesinos:** `https://tudominio.com/login/`
- **Compradores:** `https://tudominio.com/login-comprador/`
- **Página Principal:** `https://tudominio.com/`

### Administración  
- **Django Admin:** `https://tudominio.com/admin/`
- **API Docs:** `https://tudominio.com/api/docs/`

---

## ⚠️ IMPORTANTE PARA PRODUCCIÓN

1. **Cambiar contraseñas** después del primer login
2. **Configurar HTTPS** obligatorio
3. **Variables de entorno** para passwords sensibles
4. **Backup regular** de la base de datos
5. **Monitoring** de intentos de login fallidos
6. **2FA** para el usuario admin (recomendado)

---

## 🔧 COMANDOS ÚTILES

### Crear nuevos usuarios de producción
```bash
python manage.py create_production_users
```

### Recrear usuarios (elimina existentes)
```bash
python manage.py create_production_users --delete-existing
```

### Cambiar password de usuario
```bash
python manage.py changepassword usuario@email.com
```

### Crear superusuario adicional
```bash
python manage.py createsuperuser
```

---

## 📊 ESTADÍSTICAS INICIALES

- **Total usuarios:** 5
- **Campesinos:** 2
- **Compradores:** 2  
- **Administradores:** 1
- **Estado:** Todos activos
- **Verificación:** Email no requerida (configuración inicial)

---

**⚡ Sistema listo para producción con autenticación JWT completa**