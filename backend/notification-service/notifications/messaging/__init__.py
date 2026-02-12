"""
Paquete de Infraestructura de Mensajería

Manejadores para mensajes entrantes de RabbitMQ.

## Estructura

- `consumer.py` - NotificationConsumer (extiende BaseRabbitMQConsumer)
- `handlers.py` - Manejadores de lógica de negocio (handle_ticket_created, etc.)

## Uso

El consumidor se inicia desde entrypoint.sh:

```bash
python -m notifications.messaging.consumer
```
"""
