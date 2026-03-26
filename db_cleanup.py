import os
import django
import sys

# Setup de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo_directo.settings')
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def clean_test_data():
    print("Iniciando purga de datos de prueba...")
    # Emails y patrones de prueba
    test_emails = [
        'campesino@campodirecto.com',
        'comprador@campodirecto.com',
        'campesino',
        'comprador',
        'admin',
        'test@test.com'
    ]
    
    deleted_count = 0
    from orders.models import Pedido, DetallePedido
    from anti_intermediarios.models import Conversacion
    from products.models import Producto
    from farms.models import Finca, Certificacion
    
    for email in test_emails:
        users = User.objects.filter(email__icontains=email)
        for u in users:
            print(f"Eliminando usuario de prueba: {u.email} ({u.get_full_name()})")
            
            # Borrar dependencias Restringidas o Protegidas
            pedidos_como_comp = Pedido.objects.filter(comprador=u)
            for p in pedidos_como_comp:
                p.detalles.all().delete()
                p.delete()
                
            pedidos_como_camp = Pedido.objects.filter(campesino=u)
            for p in pedidos_como_camp:
                p.detalles.all().delete()
                p.delete()
                
            # Otros por si acaso
            Conversacion.objects.filter(campesino=u).delete()
            Conversacion.objects.filter(comprador=u).delete()
            
            # Ahora sí el usuario
            u.delete()
            deleted_count += 1
            
    # Cleanup orphaned data if any...
    print(f"Purga completa. Se eliminaron {deleted_count} usuarios de prueba y toda su data en cascada (fincas, productos, pedidos, etc).")
    return deleted_count

def generate_data_dictionary():
    print("Generando Diccionario de Datos...")
    
    # Exclude standard django apps that are just noise
    exclude_apps = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']
    
    markdown_output = "# Diccionario de Datos - Campo Directo\n\n"
    
    models_processed = 0
    for app_config in apps.get_app_configs():
        if app_config.name in exclude_apps or app_config.name.startswith('django.'):
            continue
            
        app_name = app_config.verbose_name or app_config.name
        markdown_output += f"## Módulo: {app_name.capitalize()}\n\n"
        
        for model in app_config.get_models():
            models_processed += 1
            table_name = model._meta.db_table
            model_name = model.__name__
            model_desc = model.__doc__.strip().split('\n')[0] if model.__doc__ else "Sin descripción"
            
            markdown_output += f"### Tabla: `{table_name}` ({model_name})\n"
            markdown_output += f"> {model_desc}\n\n"
            markdown_output += "| Campo | Tipo de Dato (Django) | Obligatorio | Llave | Descripción |\n"
            markdown_output += "|---|---|:---:|:---:|---|\n"
            
            for field in model._meta.get_fields():
                if field.is_relation and field.many_to_many and not field.related_model:
                    continue # Skip reverse m2m
                    
                field_name = field.name
                
                # Tipo de dato
                try:
                    field_type = field.get_internal_type()
                except AttributeError:
                    field_type = type(field).__name__
                    
                # Obligatorio / Null / Blank
                try:
                    is_required = not (field.null or field.blank)
                    req_str = "Sí" if is_required else "No"
                except AttributeError:
                    req_str = "N/A"
                    
                # Llaves (PK, FK)
                key_type = "PK" if getattr(field, 'primary_key', False) else ""
                if field.is_relation and hasattr(field, 'remote_field') and getattr(field.remote_field, 'parent_link', False) == False:
                    key_type = "FK" if getattr(field, 'many_to_one', False) else key_type
                if field_type == 'OneToOneField':
                    key_type = "FK, UI"
                    
                # Descripción / Help Text / Choices
                desc = getattr(field, 'help_text', '') or getattr(field, 'verbose_name', field.name)
                
                if hasattr(field, 'choices') and field.choices:
                    choices_str = ", ".join([f"{k}:{v}" for k, v in field.choices if isinstance(k, str)])
                    if choices_str:
                        desc = f"{desc}. Valores permitidos: [{choices_str}]"
                
                markdown_output += f"| `{field_name}` | {field_type} | {req_str} | {key_type} | {desc} |\n"
            
            markdown_output += "\n"
            
    with open("diccionario_datos.md", "w", encoding="utf-8") as f:
        f.write(markdown_output)
        
    print(f"Diccionario de datos generado para {models_processed} modelos. Guardado en diccionario_datos.md")

if __name__ == "__main__":
    clean_test_data()
    generate_data_dictionary()
