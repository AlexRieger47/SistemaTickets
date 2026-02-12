"""
Manejadores de mensajes para el Servicio de Notificaciones.

Maneja eventos entrantes de RabbitMQ y delega a casos de uso.
Esta es la capa adaptadora entre infraestructura de mensajería y capa de aplicación.
"""

import logging
from typing import Dict, Any

from notifications.models import Notification

logger = logging.getLogger(__name__)


def handle_ticket_created(message: Dict[str, Any]) -> None:
    """
    Maneja el evento ticket.created.
    
    Crea un registro de notificación cuando se crea un ticket.
    Este es un handler simple que usa directamente Django ORM.
    
    TODO: Refactorizar para usar CreateNotificationUseCase cuando se implemente.
    
    Args:
        message: Datos del evento conteniendo ticket_id
    """
    ticket_id = message.get('ticket_id')
    
    if not ticket_id:
        logger.warning(f"⚠️ Mensaje recibido sin ticket_id: {message}")
        return
    
    try:
        # Crear notificación (implementación simple)
        notification = Notification.objects.create(
            ticket_id=str(ticket_id),
            message=f"Ticket {ticket_id} creado"
        )
        
        logger.info(f"✅ Notificación creada para ticket {ticket_id} (id={notification.id})")
        
    except Exception as e:
        logger.error(f"❌ Error creando notificación para ticket {ticket_id}: {e}", exc_info=True)
        raise  # Re-lanzar para activar reencolar mensaje
