-- Tabla: anti_intermediarios_conversacion
CREATE TABLE "anti_intermediarios_conversacion" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "fecha_creacion" datetime NOT NULL,
  "fecha_actualizacion" datetime NOT NULL,
  "activa" bool NOT NULL,
  "campesino_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED,
  "comprador_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED,
  "producto_id" bigint NULL REFERENCES "products_producto" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Tabla: anti_intermediarios_mensaje
CREATE TABLE "anti_intermediarios_mensaje" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "tipo_mensaje" varchar(12) NOT NULL,
  "contenido" text NOT NULL,
  "precio_ofertado" decimal NULL,
  "cantidad_ofertada" decimal NULL,
  "fecha_envio" datetime NOT NULL,
  "leido" bool NOT NULL,
  "conversacion_id" bigint NOT NULL REFERENCES "anti_intermediarios_conversacion" ("id") DEFERRABLE INITIALLY DEFERRED,
  "remitente_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Tabla: anti_intermediarios_reporteimpacto
CREATE TABLE "anti_intermediarios_reporteimpacto" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "fecha_inicio" date NOT NULL,
  "fecha_fin" date NOT NULL,
  "total_transacciones" integer unsigned NOT NULL CHECK ("total_transacciones" >= 0),
  "ahorro_total_generado" decimal NOT NULL,
  "campesinos_beneficiados" integer unsigned NOT NULL CHECK ("campesinos_beneficiados" >= 0),
  "compradores_beneficiados" integer unsigned NOT NULL CHECK ("compradores_beneficiados" >= 0),
  "productos_top" text NOT NULL CHECK (
    (
      JSON_VALID("productos_top")
      OR "productos_top" IS NULL
    )
  ),
  "fecha_generacion" datetime NOT NULL
);

-- Tabla: anti_intermediarios_transparenciaprecios
CREATE TABLE "anti_intermediarios_transparenciaprecios" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "precio_campo_directo" decimal NOT NULL,
  "precio_mercado_tradicional" decimal NOT NULL,
  "fuente_precio_referencia" varchar(100) NOT NULL,
  "fecha_registro" datetime NOT NULL,
  "ciudad_referencia" varchar(100) NOT NULL,
  "producto_id" bigint NOT NULL REFERENCES "products_producto" ("id") DEFERRABLE INITIALLY DEFERRED,
  "notas" text NOT NULL
);

-- Tabla: auth_group
CREATE TABLE "auth_group" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" varchar(150) NOT NULL UNIQUE
);

-- Tabla: auth_group_permissions
CREATE TABLE "auth_group_permissions" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED,
  "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Tabla: auth_permission
CREATE TABLE "auth_permission" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
  "codename" varchar(100) NOT NULL,
  "name" varchar(255) NOT NULL
);

-- Tabla: django_admin_log
CREATE TABLE "django_admin_log" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "object_id" text NULL,
  "object_repr" varchar(200) NOT NULL,
  "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0),
  "change_message" text NOT NULL,
  "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
  "user_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED,
  "action_time" datetime NOT NULL
);

-- Tabla: django_content_type
CREATE TABLE "django_content_type" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "app_label" varchar(100) NOT NULL,
  "model" varchar(100) NOT NULL
);

-- Tabla: django_migrations
CREATE TABLE "django_migrations" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "app" varchar(255) NOT NULL,
  "name" varchar(255) NOT NULL,
  "applied" datetime NOT NULL
);

-- Tabla: django_session
CREATE TABLE "django_session" (
  "session_key" varchar(40) NOT NULL PRIMARY KEY,
  "session_data" text NOT NULL,
  "expire_date" datetime NOT NULL
);

-- Tabla: farms_finca
CREATE TABLE "farms_finca" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "nombre_finca" varchar(150) NOT NULL,
  "ubicacion_departamento" varchar(100) NOT NULL,
  "ubicacion_municipio" varchar(100) NOT NULL,
  "direccion" text NOT NULL,
  "area_hectareas" decimal NOT NULL,
  "tipo_cultivo" varchar(15) NOT NULL,
  "descripcion" text NOT NULL,
  "latitud" decimal NULL,
  "longitud" decimal NULL,
  "estado" varchar(11) NOT NULL,
  "fecha_creacion" datetime NOT NULL,
  "fecha_actualizacion" datetime NOT NULL,
  "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Tabla: orders_detallepedido
CREATE TABLE "orders_detallepedido" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "cantidad" decimal NOT NULL,
  "precio_unitario" decimal NOT NULL,
  "nombre_producto_snapshot" varchar(150) NOT NULL,
  "unidad_medida_snapshot" varchar(7) NOT NULL,
  "producto_id" bigint NOT NULL REFERENCES "products_producto" ("id") DEFERRABLE INITIALLY DEFERRED,
  "pedido_id" varchar(20) NOT NULL REFERENCES "orders_pedido" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Tabla: orders_pedido
CREATE TABLE "orders_pedido" (
  "id" varchar(20) NOT NULL PRIMARY KEY,
  "total" decimal NOT NULL,
  "estado" varchar(10) NOT NULL,
  "metodo_pago" varchar(15) NOT NULL,
  "notas_comprador" text NOT NULL,
  "notas_campesino" text NOT NULL,
  "fecha_pedido" datetime NOT NULL,
  "fecha_confirmacion" datetime NULL,
  "fecha_preparacion" datetime NULL,
  "fecha_entrega" datetime NULL,
  "fecha_completado" datetime NULL,
  "direccion_entrega" text NOT NULL,
  "telefono_contacto" varchar(20) NOT NULL,
  "fecha_entrega_programada" date NULL,
  "hora_entrega_programada" time NULL,
  "codigo_seguimiento" varchar(50) NULL UNIQUE,
  "calificacion_comprador" smallint unsigned NULL CHECK ("calificacion_comprador" >= 0),
  "calificacion_campesino" smallint unsigned NULL CHECK ("calificacion_campesino" >= 0),
  "comentario_calificacion" text NOT NULL,
  "campesino_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED,
  "comprador_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Tabla: products_categoriaproducto
CREATE TABLE "products_categoriaproducto" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "nombre" varchar(100) NOT NULL UNIQUE,
  "descripcion" text NOT NULL,
  "icono" varchar(50) NOT NULL,
  "estado" varchar(8) NOT NULL,
  "fecha_creacion" datetime NOT NULL
);

-- Tabla: products_producto
CREATE TABLE "products_producto" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "nombre" varchar(150) NOT NULL,
  "descripcion" text NOT NULL,
  "precio_por_kg" decimal NOT NULL,
  "stock_disponible" integer unsigned NOT NULL CHECK ("stock_disponible" >= 0),
  "unidad_medida" varchar(7) NOT NULL,
  "estado" varchar(10) NOT NULL,
  "galeria_imagenes" text NOT NULL CHECK (
    (
      JSON_VALID("galeria_imagenes")
      OR "galeria_imagenes" IS NULL
    )
  ),
  "tags" varchar(500) NOT NULL,
  "calidad" varchar(8) NOT NULL,
  "fecha_cosecha" date NULL,
  "fecha_vencimiento" date NULL,
  "peso_minimo_venta" decimal NOT NULL,
  "peso_maximo_venta" decimal NOT NULL,
  "disponible_entrega_inmediata" bool NOT NULL,
  "tiempo_preparacion_dias" integer unsigned NOT NULL CHECK ("tiempo_preparacion_dias" >= 0),
  "fecha_creacion" datetime NOT NULL,
  "fecha_actualizacion" datetime NOT NULL,
  "categoria_id" bigint NOT NULL REFERENCES "products_categoriaproducto" ("id") DEFERRABLE INITIALLY DEFERRED,
  "finca_id" bigint NOT NULL REFERENCES "farms_finca" ("id") DEFERRABLE INITIALLY DEFERRED,
  "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED,
  "imagen_principal" varchar(100) NULL
);

-- Tabla: sqlite_sequence
CREATE TABLE sqlite_sequence (name, seq);

-- Tabla: users_usuario
CREATE TABLE "users_usuario" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "password" varchar(128) NOT NULL,
  "last_login" datetime NULL,
  "is_superuser" bool NOT NULL,
  "is_staff" bool NOT NULL,
  "is_active" bool NOT NULL,
  "date_joined" datetime NOT NULL,
  "nombre" varchar(100) NOT NULL,
  "apellido" varchar(100) NOT NULL,
  "email" varchar(254) NOT NULL UNIQUE,
  "telefono" varchar(20) NOT NULL,
  "tipo_usuario" varchar(10) NOT NULL,
  "fecha_nacimiento" date NOT NULL,
  "estado" varchar(10) NOT NULL,
  "fecha_registro" datetime NOT NULL,
  "fecha_actualizacion" datetime NOT NULL,
  "ultimo_login" datetime NULL,
  "avatar" varchar(100) NULL,
  "calificacion_promedio" decimal NOT NULL,
  "total_calificaciones" integer unsigned NOT NULL CHECK ("total_calificaciones" >= 0),
  "direccion" varchar(255) NOT NULL
);

-- Tabla: users_usuario_groups
CREATE TABLE "users_usuario_groups" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED,
  "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Tabla: users_usuario_user_permissions
CREATE TABLE "users_usuario_user_permissions" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "usuario_id" bigint NOT NULL REFERENCES "users_usuario" ("id") DEFERRABLE INITIALLY DEFERRED,
  "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED
);
