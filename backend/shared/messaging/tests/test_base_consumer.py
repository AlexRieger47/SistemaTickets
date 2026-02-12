"""
Tests para la infraestructura centralizada de consumidores RabbitMQ.

Prueba la implementación del patrón Template Method en BaseRabbitMQConsumer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from shared.messaging.base_consumer import BaseRabbitMQConsumer


class MockConsumer(BaseRabbitMQConsumer):
    """Consumidor mock para propósitos de testing."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_messages = []
    
    def get_exchange_name(self) -> str:
        return 'test_exchange'
    
    def get_queue_name(self) -> str:
        return 'test_queue'
    
    def get_routing_key(self) -> str:
        return ''
    
    def handle_message(self, message: dict) -> None:
        """Almacena mensajes procesados para aserciones."""
        self.processed_messages.append(message)


class TestBaseRabbitMQConsumer:
    """Suite de tests para el Template Method BaseRabbitMQConsumer."""
    
    def test_consumer_initialization(self):
        """Prueba que el consumidor se inicializa con valores por defecto correctos."""
        consumer = MockConsumer()
        
        assert consumer.rabbitmq_host == 'rabbitmq'
        assert consumer.connection is None
        assert consumer.channel is None
        assert consumer._consuming is False
    
    def test_consumer_initialization_with_custom_host(self):
        """Prueba que el consumidor se inicializa con host personalizado."""
        consumer = MockConsumer(rabbitmq_host='custom-rabbitmq')
        
        assert consumer.rabbitmq_host == 'custom-rabbitmq'
    
    def test_get_exchange_name_hook(self):
        """Prueba que el hook get_exchange_name es llamado."""
        consumer = MockConsumer()
        
        assert consumer.get_exchange_name() == 'test_exchange'
    
    def test_get_queue_name_hook(self):
        """Prueba que el hook get_queue_name es llamado."""
        consumer = MockConsumer()
        
        assert consumer.get_queue_name() == 'test_queue'
    
    def test_get_routing_key_hook(self):
        """Prueba que el hook get_routing_key es llamado."""
        consumer = MockConsumer()
        
        assert consumer.get_routing_key() == ''
    
    def test_handle_message_hook(self):
        """Prueba que el hook handle_message procesa mensajes."""
        consumer = MockConsumer()
        message = {'ticket_id': '123', 'event': 'ticket.created'}
        
        consumer.handle_message(message)
        
        assert len(consumer.processed_messages) == 1
        assert consumer.processed_messages[0] == message
    
    def test_handle_message_idempotent(self):
        """Prueba que handle_message puede procesar múltiples mensajes."""
        consumer = MockConsumer()
        
        consumer.handle_message({'ticket_id': '1'})
        consumer.handle_message({'ticket_id': '2'})
        consumer.handle_message({'ticket_id': '3'})
        
        assert len(consumer.processed_messages) == 3
    
    @patch('shared.messaging.base_consumer.pika')
    def test_start_consuming_connects_to_rabbitmq(self, mock_pika):
        """Prueba que start_consuming establece conexión con RabbitMQ."""
        # Setup mock
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        # Hacer que start_consuming retorne inmediatamente (no consumir realmente)
        def mock_start_consuming():
            pass
        mock_channel.start_consuming = mock_start_consuming
        
        # Ejecutar
        consumer = MockConsumer()
        consumer.start_consuming()
        
        # Verificar que se intentó conectar
        mock_pika.BlockingConnection.assert_called_once()
        mock_connection.channel.assert_called_once()
    
    @patch('shared.messaging.base_consumer.pika')
    def test_start_consuming_declares_exchange(self, mock_pika):
        """Prueba que start_consuming declara el exchange vía hook."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.start_consuming = lambda: None
        
        consumer = MockConsumer()
        consumer.start_consuming()
        
        # Verificar que exchange_declare fue llamado con valor del hook
        mock_channel.exchange_declare.assert_called_once_with(
            exchange='test_exchange',
            exchange_type='fanout',
            durable=True
        )
    
    @patch('shared.messaging.base_consumer.pika')
    def test_start_consuming_declares_queue(self, mock_pika):
        """Prueba que start_consuming declara la cola vía hook."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.start_consuming = lambda: None
        
        consumer = MockConsumer()
        consumer.start_consuming()
        
        # Verificar que queue_declare fue llamado con valor del hook
        mock_channel.queue_declare.assert_called_once_with(
            queue='test_queue',
            durable=True
        )
    
    @patch('shared.messaging.base_consumer.pika')
    def test_start_consuming_binds_queue(self, mock_pika):
        """Prueba que start_consuming vincula la cola al exchange vía hooks."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.start_consuming = lambda: None
        
        consumer = MockConsumer()
        consumer.start_consuming()
        
        # Verificar que queue_bind fue llamado con valores de los hooks
        mock_channel.queue_bind.assert_called_once_with(
            exchange='test_exchange',
            queue='test_queue',
            routing_key=''
        )
    
    @patch('shared.messaging.base_consumer.pika')
    def test_start_consuming_configures_qos(self, mock_pika):
        """Prueba que start_consuming configura QoS."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.start_consuming = lambda: None
        
        consumer = MockConsumer()
        consumer.start_consuming()
        
        # Verificar que QoS fue configurado
        mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)
    
    def test_stop_consuming_is_safe_to_call_multiple_times(self):
        """Prueba que stop_consuming puede ser llamado múltiples veces de forma segura."""
        consumer = MockConsumer()
        
        # No debería lanzar excepción
        consumer.stop_consuming()
        consumer.stop_consuming()
        consumer.stop_consuming()


class TestInterfaceContract:
    """Prueba que MockConsumer adhiere a la interfaz IMessageConsumer."""
    
    def test_consumer_implements_interface(self):
        """Prueba que el consumidor implementa métodos requeridos de la interfaz."""
        from shared.messaging.interfaces import IMessageConsumer
        
        consumer = MockConsumer()
        
        # Verificar que es instancia de la interfaz
        assert isinstance(consumer, IMessageConsumer)
    
    def test_consumer_has_start_consuming_method(self):
        """Prueba que el consumidor tiene el método start_consuming."""
        consumer = MockConsumer()
        
        assert hasattr(consumer, 'start_consuming')
        assert callable(consumer.start_consuming)
    
    def test_consumer_has_stop_consuming_method(self):
        """Prueba que el consumidor tiene el método stop_consuming."""
        consumer = MockConsumer()
        
        assert hasattr(consumer, 'stop_consuming')
        assert callable(consumer.stop_consuming)
    
    def test_consumer_has_handle_message_method(self):
        """Prueba que el consumidor tiene el método handle_message."""
        consumer = MockConsumer()
        
        assert hasattr(consumer, 'handle_message')
        assert callable(consumer.handle_message)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
