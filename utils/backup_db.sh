#!/bin/bash

# ==============================================================================
# Script de Backup Automático de MySQL para PythonAnywhere
# ==============================================================================
# Este script está diseñado para ser ejecutado mediante una Tarea Programada (Scheduled Task).
# Crea un volcado (.sql) de la base de datos de producción y lo comprime.
# Solo mantiene las copias de los últimos 7 días para no exceder la cuota de disco.

# 1. Cargar variables de entorno desde el archivo .env principal
source /home/$USER/Proyecto_Grado_Campo_Directo/.env

# 2. Configurar el directorio de backups
BACKUP_DIR="/home/$USER/Proyecto_Grado_Campo_Directo/backups"
mkdir -p "$BACKUP_DIR"

# 3. Definir el nombre del archivo con fecha y hora actual
DATE=$(date +%Y-%m-%d_%H-%M-%S)
FILE_NAME="backup_${PROD_DB_NAME}_${DATE}.sql.gz"
FILE_PATH="${BACKUP_DIR}/${FILE_NAME}"

# 4. Generar el backup y comprimirlo al vuelo
echo "Iniciando backup de la base de datos: $PROD_DB_NAME..."
mysqldump -u "$PROD_DB_USER" -h "$PROD_DB_HOST" -p"$PROD_DB_PASSWORD" "$PROD_DB_NAME" | gzip > "$FILE_PATH"

if [ $? -eq 0 ]; then
    echo "✅ Backup creado exitosamente en: $FILE_PATH"
else
    echo "❌ Error al crear el backup."
    exit 1
fi

# 5. Limpieza: Eliminar backups más antiguos que 7 días
echo "Eliminando backups con más de 7 días de antigüedad..."
find "$BACKUP_DIR" -type f -name "backup_*.sql.gz" -mtime +7 -exec rm {} \;

echo "Proceso de mantenimiento finalizado."
