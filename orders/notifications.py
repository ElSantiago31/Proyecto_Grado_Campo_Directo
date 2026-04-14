"""
Sistema de notificaciones por correo electrónico para Campo Directo.

Envía correos automáticos en los siguientes eventos:
- Nuevo pedido creado (al campesino y al comprador)
- Cambio de estado del pedido (al comprador)
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger('campo_directo')


def _enviar_correo_seguro(asunto: str, mensaje_txt: str, destinatario: str, html_mensaje: str = None):
    """
    Wrapper seguro para envío de correos. Si falla, solo registra el error
    sin interrumpir el flujo principal de la aplicación.
    """
    try:
        send_mail(
            subject=asunto,
            message=mensaje_txt,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            html_message=html_mensaje,
            fail_silently=False,
        )
        logger.info(f'Correo enviado a {destinatario}: {asunto}')
    except Exception as e:
        logger.error(f'Error enviando correo a {destinatario}: {str(e)}')


def notificar_nuevo_pedido(pedido):
    """
    Envía notificaciones cuando se crea un nuevo pedido:
    1. Al campesino: para que sepa que tiene un nuevo pedido.
    2. Al comprador: para confirmar que su orden fue recibida.
    """
    campesino = pedido.campesino
    comprador = pedido.comprador

    # ── Notificación al CAMPESINO ──────────────────────────────────────────
    asunto_campesino = f'🛒 Nuevo pedido recibido — {pedido.id}'
    mensaje_campesino = f"""
¡Hola {campesino.nombre}!

Has recibido un nuevo pedido en Campo Directo.

📦 Número de Pedido: {pedido.id}
👤 Comprador: {comprador.nombre} {comprador.apellido}
💰 Total: ${pedido.total:,.2f}
📅 Fecha: {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}

Por favor, ingresa a tu dashboard para confirmar o gestionar el pedido lo antes posible.

— El equipo de Campo Directo 🌱
"""
    html_campesino = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; background: #f9f9f9; border-radius: 10px;">
    <h2 style="color: #2d5016;">🛒 Nuevo Pedido Recibido</h2>
    <p>Hola <strong>{campesino.nombre}</strong>,</p>
    <p>Has recibido un nuevo pedido en <strong>Campo Directo</strong>.</p>
    <table style="width:100%; border-collapse:collapse; margin: 15px 0;">
        <tr style="background:#e8f5e9;"><td style="padding:8px;"><strong>Pedido</strong></td><td style="padding:8px;">{pedido.id}</td></tr>
        <tr><td style="padding:8px;"><strong>Comprador</strong></td><td style="padding:8px;">{comprador.nombre} {comprador.apellido}</td></tr>
        <tr style="background:#e8f5e9;"><td style="padding:8px;"><strong>Total</strong></td><td style="padding:8px;">${pedido.total:,.2f}</td></tr>
        <tr><td style="padding:8px;"><strong>Fecha</strong></td><td style="padding:8px;">{pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}</td></tr>
    </table>
    <p>Ingresa a tu dashboard para confirmar el pedido.</p>
    <p style="color:#666; font-size: 0.9em;">— El equipo de Campo Directo 🌱</p>
</div>
"""
    _enviar_correo_seguro(asunto_campesino, mensaje_campesino, campesino.email, html_campesino)

    # ── Confirmación al COMPRADOR ──────────────────────────────────────────
    asunto_comprador = f'✅ ¡Tu pedido fue recibido! — {pedido.id}'
    mensaje_comprador = f"""
¡Hola {comprador.nombre}!

Tu pedido en Campo Directo fue recibido con éxito.

📦 Número de Pedido: {pedido.id}
🌿 Campesino: {campesino.nombre} {campesino.apellido}
💰 Total: ${pedido.total:,.2f}
💳 Método de Pago: {pedido.get_metodo_pago_display()}
📍 Estado actual: Pendiente de confirmación

Te notificaremos cuando el campesino confirme tu pedido.

— El equipo de Campo Directo 🌱
"""
    html_comprador = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; background: #f9f9f9; border-radius: 10px;">
    <h2 style="color: #2d5016;">✅ ¡Pedido Confirmado!</h2>
    <p>Hola <strong>{comprador.nombre}</strong>,</p>
    <p>Tu pedido en <strong>Campo Directo</strong> fue recibido con éxito.</p>
    <table style="width:100%; border-collapse:collapse; margin: 15px 0;">
        <tr style="background:#e8f5e9;"><td style="padding:8px;"><strong>Pedido</strong></td><td style="padding:8px;">{pedido.id}</td></tr>
        <tr><td style="padding:8px;"><strong>Campesino</strong></td><td style="padding:8px;">{campesino.nombre} {campesino.apellido}</td></tr>
        <tr style="background:#e8f5e9;"><td style="padding:8px;"><strong>Total</strong></td><td style="padding:8px;">${pedido.total:,.2f}</td></tr>
        <tr><td style="padding:8px;"><strong>Estado</strong></td><td style="padding:8px; color: #e67e22;"><strong>Pendiente</strong></td></tr>
    </table>
    <p>Te avisaremos cuando el campesino confirme o actualice tu pedido.</p>
    <p style="color:#666; font-size: 0.9em;">— El equipo de Campo Directo 🌱</p>
</div>
"""
    _enviar_correo_seguro(asunto_comprador, mensaje_comprador, comprador.email, html_comprador)


def notificar_cambio_estado(pedido, estado_anterior: str):
    """
    Notifica al comprador cuando el campesino actualiza el estado del pedido.
    """
    ESTADOS_LEGIBLES = {
        'pending': 'Pendiente',
        'confirmed': '✅ Confirmado por el campesino',
        'preparing': '🌿 En Preparación',
        'ready': '📦 Listo para Entrega',
        'completed': '🎉 Completado',
        'cancelled': '❌ Cancelado',
    }

    # Solo notificar si el estado realmente cambió
    if pedido.estado == estado_anterior:
        return

    estado_nuevo_legible = ESTADOS_LEGIBLES.get(pedido.estado, pedido.estado)
    comprador = pedido.comprador
    campesino = pedido.campesino

    asunto = f'📬 Pedido {pedido.id} — Estado actualizado a: {estado_nuevo_legible}'
    mensaje_txt = f"""
¡Hola {comprador.nombre}!

El estado de tu pedido ha sido actualizado por {campesino.nombre}.

📦 Pedido: {pedido.id}
📊 Nuevo estado: {estado_nuevo_legible}

Ingresa a tu dashboard para ver los detalles.

— El equipo de Campo Directo 🌱
"""
    html = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; background: #f9f9f9; border-radius: 10px;">
    <h2 style="color: #2d5016;">📬 Estado de Pedido Actualizado</h2>
    <p>Hola <strong>{comprador.nombre}</strong>,</p>
    <p>El campesino <strong>{campesino.nombre}</strong> actualizó el estado de tu pedido.</p>
    <table style="width:100%; border-collapse:collapse; margin: 15px 0;">
        <tr style="background:#e8f5e9;"><td style="padding:8px;"><strong>Pedido</strong></td><td style="padding:8px;">{pedido.id}</td></tr>
        <tr><td style="padding:8px;"><strong>Nuevo Estado</strong></td><td style="padding:8px;"><strong>{estado_nuevo_legible}</strong></td></tr>
    </table>
    <p>Ingresa a tu dashboard para ver todos los detalles del pedido.</p>
    <p style="color:#666; font-size: 0.9em;">— El equipo de Campo Directo 🌱</p>
</div>
"""
    _enviar_correo_seguro(asunto, mensaje_txt, comprador.email, html)
