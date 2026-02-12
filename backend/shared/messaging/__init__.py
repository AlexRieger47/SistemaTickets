"""
Abstracciones de infraestructura de mensajería.

Proporciona clases base e interfaces para consumidores y publicadores de mensajes,
abstrayendo los detalles de implementación específicos del broker.
"""

from .interfaces import IMessageConsumer
from .base_consumer import BaseRabbitMQConsumer

__all__ = [
    'IMessageConsumer',
    'BaseRabbitMQConsumer',
]
