"""
Script para comprimir y convertir las imágenes estáticas a WebP.
Reduce el peso promedio de 1.4 MB por imagen a menos de 50 KB.

Uso:
    python compress_images.py
"""

import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Instalando Pillow...")
    os.system("pip install Pillow")
    from PIL import Image

STATIC_IMAGES_DIR = Path(__file__).parent / "static" / "images"

# Configuración de compresión por imagen
# formato: 'nombre_archivo': (max_width, max_height, calidad_webp)
IMAGE_CONFIG = {
    "LogoCampoDirecto.png": (400, 400, 85),
    "campesino.png": (400, 400, 85),
    "logo.png": (400, 400, 85),
    "LogoCampesinos.png": (600, 600, 85),
    "Logo paginas2.png": (600, 400, 85),
    "LogoCel.png": (400, 400, 85),
    "LogoRegistroExitoso.png": (500, 500, 85),
    "registroExitoso.png": (800, 800, 85),
    "registroExitosoMovil.png": (600, 800, 85),
    "campesino.png": (400, 400, 85),
    "comprador_fondo_blanco.png": (400, 400, 85),
    "comprador_transparente.png": (400, 400, 85),
    "Diseño comprador (2).png": (800, 800, 85),
    "mockups campesino.png": (800, 600, 85),
}

def compress_image(input_path: Path, max_w: int, max_h: int, quality: int = 85):
    """Abre una imagen, la redimensiona si hace falta y la guarda como WebP."""
    output_path = input_path.with_suffix(".webp")
    
    try:
        with Image.open(input_path) as img:
            # Preservar transparencia para PNG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            
            # Redimensionar manteniendo proporciones si es mayor que el límite
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            
            # Guardar como WebP
            img.save(output_path, "WEBP", quality=quality, optimize=True)
            
            original_kb = input_path.stat().st_size / 1024
            webp_kb = output_path.stat().st_size / 1024
            saving_pct = (1 - webp_kb / original_kb) * 100
            
            print(f"  [OK] {input_path.name}")
            print(f"       {original_kb:.0f} KB -> {webp_kb:.0f} KB  (ahorro: {saving_pct:.0f}%)")
            return True
    except Exception as e:
        print(f"  [ERROR] Error con {input_path.name}: {e}")
        return False


def main():
    print("[*] Comprimiendo imagenes estaticas a WebP...\n")
    
    total_original = 0
    total_webp = 0
    count = 0
    
    for filename, (max_w, max_h, quality) in IMAGE_CONFIG.items():
        input_path = STATIC_IMAGES_DIR / filename
        if input_path.exists():
            size_before = input_path.stat().st_size
            if compress_image(input_path, max_w, max_h, quality):
                output_path = input_path.with_suffix(".webp")
                size_after = output_path.stat().st_size
                total_original += size_before
                total_webp += size_after
                count += 1
        else:
            print(f"  [SKIP] No encontrada: {filename}")
    
    print(f"\n[RESUMEN]")
    print(f"   Imagenes procesadas: {count}")
    print(f"   Peso original total:  {total_original / 1024 / 1024:.1f} MB")
    print(f"   Peso WebP total:      {total_webp / 1024 / 1024:.1f} MB")
    print(f"   Ahorro total:         {(1 - total_webp/total_original)*100:.0f}%")
    print("\n[DONE] Archivos .webp listos en static/images/")
    print("   Recuerda ejecutar: python manage.py collectstatic --noinput")


if __name__ == "__main__":
    main()
