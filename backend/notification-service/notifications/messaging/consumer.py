"""
Consumidor RabbitMQ para el Servicio de Notificaciones.

Escucha el exchange ticket_events y crea notificaciones
cuando los tickets son creados o actualizados.

Esta implementación usa el patrón Template Method de shared.messaging,
eliminando la duplicación de setup de RabbitMQ.
"""

import os
import sys
import django
import logging

# Agregar directorio base al path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, base_dir)

# Agregar shared al path (2 niveles arriba)
shared_path = os.path.join(base_dir, '..', '..')
sys.path.insert(0, shared_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notification_service.settings")
django.setup()

from shared.messaging.base_consumer import BaseRabbitMQConsumer
from notifications.messaging.handlers import handle_ticket_created

logger = logging.getLogger(__name__)


class NotificationConsumer(BaseRabbitMQConsumer):
    """
    Consumidor para el Servicio de Notificaciones.
    
    Escucha el exchange 'ticket_events' en la cola 'notification_queue'.
    Cuando llega un evento ticket.created, crea un registro de notificación.
    
    Implementación:
    - Extiende BaseRabbitMQConsumer (Template Method)
    - Solo implementa: hooks de configuración + lógica de negocio
    - Todo el setup de RabbitMQ es manejado por la clase base (60+ líneas eliminadas)
    
    Beneficios:
    - Sin duplicación de setup RabbitMQ
    - Simple de testear (mock de handle_message)
    - Fácil de mantener (cambiar exchange: 1 lugar)
    """
    
    def get_exchange_name(self) -> str:
        """Exchange donde se publican los eventos de tickets."""
        return os.getenv('RABBITMQ_EXCHANGE_NAME', 'ticket_events')
    
    def get_queue_name(self) -> str:
        """Cola exclusiva para el servicio de notificaciones."""
        return os.getenv('RABBITMQ_QUEUE_NOTIFICATION', 'notification_queue')
    
    def get_routing_key(self) -> str:
        """
        Routing key para el binding.
        String vacío para exchange fanout (recibe todos los mensajes).
        """
        return ''
    
    def handle_message(self, message: dict) -> None:
        """
        Lógica de negocio: procesar eventos de tickets.
        
        Delega al handler que crea registros de notificación.
        
        Args:
            message: Datos del evento con ticket_id
        """
        logger.info(f"🔔 Procesando evento de ticket: {message}")
        handle_ticket_created(message)


if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Iniciar consumidor
    consumer = NotificationConsumer()
    consumer.start_consuming()