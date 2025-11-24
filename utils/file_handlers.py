"""
Utilidades para el manejo de archivos y uploads
"""

import os
import uuid
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from PIL import Image
from decimal import Decimal


@deconstructible
class FileUploadHandler:
    """
    Manejador personalizado para uploads de archivos
    """
    
    def __init__(self, path_prefix='', allowed_extensions=None, max_size=None):
        self.path_prefix = path_prefix
        self.allowed_extensions = allowed_extensions or []
        self.max_size = max_size  # en bytes
    
    def __call__(self, instance, filename):
        """
        Genera un path único para el archivo
        """
        # Obtener extensión
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Generar nombre único
        unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else str(uuid.uuid4().hex)
        
        # Construir path
        path = f"{self.path_prefix}/{unique_filename}" if self.path_prefix else unique_filename
        
        return path


@deconstructible
class ImageUploadHandler(FileUploadHandler):
    """
    Manejador específico para imágenes
    """
    
    def __init__(self, path_prefix='images', max_size=5*1024*1024):  # 5MB por defecto
        super().__init__(
            path_prefix=path_prefix,
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
            max_size=max_size
        )


@deconstructible
class DocumentUploadHandler(FileUploadHandler):
    """
    Manejador específico para documentos
    """
    
    def __init__(self, path_prefix='documents', max_size=10*1024*1024):  # 10MB por defecto
        super().__init__(
            path_prefix=path_prefix,
            allowed_extensions=['pdf', 'doc', 'docx', 'txt'],
            max_size=max_size
        )


def validate_image_file(file):
    """
    Valida que el archivo sea una imagen válida
    """
    # Validar tamaño
    if file.size > 5 * 1024 * 1024:  # 5MB
        raise ValidationError('El archivo de imagen no puede superar los 5MB')
    
    # Validar extensión del archivo
    filename = file.name.lower() if file.name else ''
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise ValidationError('Tipo de archivo no permitido. Use: JPG, JPEG, PNG, GIF, WebP')
    
    # Validar que se puede abrir como imagen usando PIL
    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)  # Reset file pointer después de verify
    except Exception:
        raise ValidationError('El archivo no es una imagen válida')


def validate_document_file(file):
    """
    Valida que el archivo sea un documento válido
    """
    # Validar tamaño
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise ValidationError('El archivo de documento no puede superar los 10MB')
    
    # Validar extensión
    filename = file.name.lower() if file.name else ''
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
    
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise ValidationError('Tipo de documento no permitido. Use: PDF, DOC, DOCX, TXT')
    
    # Validación básica de contenido - leer algunos bytes para verificar que no está vacío
    try:
        file.seek(0)
        content = file.read(100)  # Leer primeros 100 bytes
        file.seek(0)  # Reset file pointer
        
        if len(content) < 10:  # Archivo muy pequeño, probablemente corrupto
            raise ValidationError('El archivo parece estar corrupto o vacío')
            
    except Exception:
        raise ValidationError('Error al validar el archivo de documento')


def optimize_image(image_path, max_width=800, max_height=600, quality=85):
    """
    Optimiza una imagen redimensionándola y comprimiéndola
    """
    try:
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar manteniendo aspect ratio
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Guardar optimizada
            img.save(image_path, optimize=True, quality=quality)
            
    except Exception as e:
        raise ValidationError(f'Error al optimizar la imagen: {str(e)}')


def generate_thumbnail(image_path, thumbnail_path, size=(150, 150)):
    """
    Genera un thumbnail de una imagen
    """
    try:
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Crear thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Guardar thumbnail
            img.save(thumbnail_path, optimize=True, quality=80)
            
    except Exception as e:
        raise ValidationError(f'Error al generar thumbnail: {str(e)}')


def get_file_size_display(size_bytes):
    """
    Convierte bytes a una representación legible
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size = Decimal(str(size_bytes))
    
    for i, name in enumerate(size_names):
        if size < 1024 or i == len(size_names) - 1:
            if i == 0:
                return f"{int(size)} {name}"
            else:
                return f"{size:.1f} {name}"
        size = size / 1024
    
    return f"{size:.1f} GB"


def validate_file_extension(filename, allowed_extensions):
    """
    Valida la extensión de un archivo
    """
    if not filename:
        raise ValidationError('Nombre de archivo requerido')
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if not ext or ext not in [ext.lower() for ext in allowed_extensions]:
        raise ValidationError(
            f'Extensión de archivo no permitida. Extensiones permitidas: {", ".join(allowed_extensions)}'
        )


# Handlers pre-configurados para diferentes tipos
image_upload_handler = ImageUploadHandler('products/images')
profile_image_handler = ImageUploadHandler('users/profiles')
farm_image_handler = ImageUploadHandler('farms/images')
document_upload_handler = DocumentUploadHandler('documents')
certificate_upload_handler = DocumentUploadHandler('certificates')