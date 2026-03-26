from django.core.management.base import BaseCommand
from products.models import SipsaPrecio
import zeep
import time

class Command(BaseCommand):
    help = 'Sincroniza los precios promedio de SIPSA DANE para todas las ciudades.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Iniciando descarga de precios SIPSA...'))
        url = 'https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL'
        start = time.time()
        try:
            client = zeep.Client(wsdl=url)
            res = client.service.promediosSipsaCiudad()
            if not res:
                self.stdout.write(self.style.WARNING('La respuesta de SIPSA está vacía.'))
                return
            self.stdout.write(self.style.SUCCESS(f'Se descargaron {len(res)} registros en {time.time()-start:.2f}s'))
            self.stdout.write(self.style.NOTICE('Generando listado único de registros SIPSA para base de datos...'))
            
            # Borrar historico para acelerar el guardado si se desea y no acumular repetidos (opcional)
            SipsaPrecio.objects.all().delete()
            
            nuevos_registros = []
            vistos = set()
            
            for item in res:
                ciudad_str = (item.ciudad or '').strip()
                producto_str = (item.producto or '').strip()
                precio = item.precioPromedio
                
                if not ciudad_str or not producto_str or precio is None:
                    continue
                    
                clave_unica = (ciudad_str, producto_str)
                if clave_unica not in vistos:
                    vistos.add(clave_unica)
                    nuevos_registros.append(
                        SipsaPrecio(
                            ciudad=ciudad_str,
                            producto=producto_str,
                            precio_promedio=precio,
                            fecha_captura=item.fechaCaptura
                        )
                    )
            
            self.stdout.write(self.style.NOTICE(f'Preparando {len(nuevos_registros)} registros únicos en base de datos (Bulk Insert).'))
            
            # Grabar por bloques usando atomic transaction para mayor velocidad en SQLite
            from django.db import transaction
            batch_size = 10000
            for i in range(0, len(nuevos_registros), batch_size):
                with transaction.atomic():
                    SipsaPrecio.objects.bulk_create(nuevos_registros[i:i+batch_size])
            
            self.stdout.write(self.style.SUCCESS(f'¡Sincronización completada exitosamente! {len(nuevos_registros)} guardados.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sincronizando SIPSA: {str(e)}'))
