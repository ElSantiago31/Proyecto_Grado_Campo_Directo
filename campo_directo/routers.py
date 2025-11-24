"""
Router de base de datos para Campo Directo
Permite dirigir consultas específicas a la base de datos de producción
"""

class DatabaseRouter:
    """
    Router que permite consultar datos de la base de datos de producción
    cuando se especifica explícitamente
    """

    # Apps que deben usar la base de datos de producción cuando se especifica
    production_apps = {'users', 'farms', 'products', 'orders'}

    def db_for_read(self, model, **hints):
        """
        Determinar qué base de datos usar para leer un modelo específico
        """
        # Si se especifica usar producción en el contexto
        if hasattr(model, '_state') and hasattr(model._state, 'db') and model._state.db == 'production':
            return 'production'
        
        # Si el modelo tiene un atributo especial para producción
        if hasattr(model, '_use_production_db') and model._use_production_db:
            return 'production'
            
        # Por defecto usar la base de datos default
        return None

    def db_for_write(self, model, **hints):
        """
        Determinar qué base de datos usar para escribir un modelo específico
        """
        # Por defecto, las escrituras van a la BD default
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Permitir migraciones solo en la base de datos apropiada
        """
        if db == 'production':
            # Solo permitir migraciones de apps específicas en producción
            return app_label in self.production_apps
        elif db == 'default':
            # Permitir todas las migraciones en default
            return True
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permitir relaciones entre objetos
        """
        db_set = {'default', 'production'}
        if hasattr(obj1, '_state') and hasattr(obj2, '_state'):
            if obj1._state.db in db_set and obj2._state.db in db_set:
                return True
        return None


class ProductionDataManager:
    """
    Manager helper para consultar datos de producción fácilmente
    """
    
    @staticmethod
    def get_production_queryset(model_class):
        """
        Obtener un queryset que consulte la base de datos de producción
        """
        return model_class.objects.using('production')
    
    @staticmethod
    def get_production_data(model_class, **filters):
        """
        Obtener datos específicos de la base de datos de producción
        """
        return model_class.objects.using('production').filter(**filters)
    
    @staticmethod
    def count_production_records(model_class):
        """
        Contar registros en la base de datos de producción
        """
        return model_class.objects.using('production').count()