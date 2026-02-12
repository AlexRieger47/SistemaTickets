"""
Implementación base de consumidor RabbitMQ usando patrón Template Method.

Este módulo centraliza toda la lógica de setup de RabbitMQ (conexión, exchange, cola, binding),
eliminando la duplicación de código entre microservicios.

Cada servicio solo necesita:
1. Extender BaseRabbitMQConsumer
2. Implementar 4 métodos: get_exchange_name(), get_queue_name(), get_routing_key(), handle_message()

Beneficios:
- 60+ líneas de código de setup RabbitMQ en UN solo lugar
- Manejo de errores y logging consistente
- Fácil agregar nuevos consumidores (25 líneas vs 60+)
- Cambiar exchange/QoS: editar 1 archivo en vez de N servicios
"""

import os
import json
import logging
from abc import abstractmethod
from typing import Dict, Any
from .interfaces import IMessageConsumer

logger = logging.getLogger(__name__)


class BaseRabbitMQConsumer(IMessageConsumer):
    """
    Patrón Template Method para consumidores RabbitMQ.
    
    Implementa el flujo completo:
    1. Conectar a RabbitMQ
    2. Declarar exchange
    3. Declarar cola
    4. Vincular cola al exchange
    5. Configurar QoS
    6. Consumir mensajes con manejo de ack/nack
    
    Las subclases solo implementan:
    - get_exchange_name() → configuración del exchange
    - get_queue_name() → configuración de la cola
    - get_routing_key() → configuración de routing
    - handle_message() → lógica de negocio
    
    Ejemplo:
        class NotificationConsumer(BaseRabbitMQConsumer):
            def get_exchange_name(self) -> str:
                return 'ticket_events'
            
            def get_queue_name(self) -> str:
                return 'notification_queue'
            
            def get_routing_key(self) -> str:
                return ''  # fanout
            
            def handle_message(self, message: dict) -> None:
                create_notification(message['ticket_id'])
    """
    
    # ========== HOOKS DEL TEMPLATE METHOD (IMPLEMENTAR EN SUBCLASES) ==========
    
    @abstractmethod
    def get_exchange_name(self) -> str:
        """
        Retorna el nombre del exchange de RabbitMQ para consumir.
        
        Ejemplo: 'ticket_events'
        """
        pass
    
    @abstractmethod
    def get_queue_name(self) -> str:
        """
        Retorna el nombre de la cola para este consumidor.
        
        Ejemplo: 'notification_queue', 'assignment_queue'
        Cada servicio debe tener su propia cola.
        """
        pass
    
    @abstractmethod
    def get_routing_key(self) -> str:
        """
        Retorna el routing key para vincular la cola al exchange.
        
        - Para exchanges fanout: retornar '' (string vacío)
        - Para exchanges topic: retornar patrón como 'ticket.#' o 'ticket.created'
        - Para exchanges direct: retornar routing key exacto
        """
        pass
    
    @abstractmethod
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Procesa el mensaje recibido.
        
        Aquí va tu lógica de negocio.
        Delega a casos de uso, handlers, o tareas Celery.
        
        Args:
            message: Mensaje JSON parseado como dict
            
        Raises:
            Exception: Si el procesamiento falla, el mensaje será reencolado
        """
        pass
    
    # ========== IMPLEMENTACIÓN DEL TEMPLATE METHOD (NO SOBREESCRIBIR) ==========
    
    def __init__(self, rabbitmq_host: str = None):
        """
        Inicializa el consumidor RabbitMQ.
        
        Args:
            rabbitmq_host: Host de RabbitMQ (default: env RABBITMQ_HOST o 'rabbitmq')
        """
        self.rabbitmq_host = rabbitmq_host or os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.connection = None
        self.channel = None
        self._consuming = False
    
    def start_consuming(self) -> None:
        """
        Template Method: orquesta el flujo completo del consumidor.
        
        Pasos:
        1. Conectar a RabbitMQ
        2. Declarar exchange (vía hook)
        3. Declarar cola (vía hook)
        4. Vincular cola al exchange (vía hook)
        5. Configurar QoS (prefetch)
        6. Iniciar consumo con manejo de ack/nack
        
        Este método NUNCA necesita ser modificado - toda la variabilidad
        se maneja a través de los hooks abstractos arriba.
        """
        import pika
        
        try:
            # Paso 1: Conectar a RabbitMQ
            logger.info(f"🔌 Conectando a RabbitMQ: {self.rabbitmq_host}")
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            self.channel = self.connection.channel()
            logger.info("✅ Conexión establecida")
            
            # Paso 2: Declarar exchange (vía hook)
            exchange_name = self.get_exchange_name()
            logger.info(f"📢 Declarando exchange: {exchange_name}")
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type='fanout',
                durable=True
            )
            
            # Paso 3: Declarar cola (vía hook)
            queue_name = self.get_queue_name()
            logger.info(f"📥 Declarando cola: {queue_name}")
            self.channel.queue_declare(
                queue=queue_name,
                durable=True
            )
            
            # Paso 4: Vincular cola al exchange (vía hook)
            routing_key = self.get_routing_key()
            logger.info(f"🔗 Vinculando {queue_name} → {exchange_name} (routing_key: '{routing_key}')")
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=queue_name,
                routing_key=routing_key
            )
            
            # Paso 5: Configurar QoS (CENTRALIZADO - aplica a todos los consumidores)
            self.channel.basic_qos(prefetch_count=1)
            logger.debug("⚙️ QoS configurado: prefetch_count=1")
            
            # Paso 6: Definir callback wrapper para manejo de ack/nack
            def _callback_wrapper(ch, method, properties, body):
                """
                Envuelve handle_message() con:
                - Deserialización JSON
                - Manejo de errores
                - Ack/nack manual
                - Logging
                """
                try:
                    # Parsear mensaje
                    message = json.loads(body)
                    logger.info(f"📨 Mensaje recibido: {message}")
                    
                    # Delegar a lógica de negocio (hook)
                    self.handle_message(message)
                    
                    # ACK: mensaje procesado exitosamente
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.debug(f"✅ ACK enviado para delivery_tag: {method.delivery_tag}")
                    
                except json.JSONDecodeError as e:
                    # JSON inválido: no reencolar (mensaje malo)
                    logger.error(f"❌ JSON inválido en mensaje: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    
                except Exception as e:
                    # Error de procesamiento: reencolar para reintentar
                    logger.error(f"❌ Error procesando mensaje: {e}", exc_info=True)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Paso 7: Iniciar consumo
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=_callback_wrapper,
                auto_ack=False  # Ack manual para confiabilidad
            )
            
            self._consuming = True
            logger.info(f"🔄 Consumidor iniciado. Esperando mensajes en '{queue_name}'...")
            logger.info("Presiona Ctrl+C para detener")
            
            # Bloquear aquí hasta que se detenga
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("⏸️ Consumidor detenido por el usuario (Ctrl+C)")
            self.stop_consuming()
            
        except Exception as e:
            logger.error(f"❌ Error crítico en consumidor: {e}", exc_info=True)
            self.stop_consuming()
            raise
    
    def stop_consuming(self) -> None:
        """
        Detiene el consumo de mensajes y cierra conexiones de forma elegante.
        
        Seguro llamar múltiples veces.
        """
        if self._consuming and self.channel:
            try:
                logger.info("⏹️ Deteniendo consumidor...")
                self.channel.stop_consuming()
                self._consuming = False
            except Exception as e:
                logger.warning(f"⚠️ Error deteniendo consumidor: {e}")
        
        if self.connection and not self.connection.is_closed:
            try:
                logger.info("🔌 Cerrando conexión a RabbitMQ...")
                self.connection.close()
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexión: {e}")
        
        logger.info("✅ Consumidor detenido")
