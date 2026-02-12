"""
Interfaces de mensajería para consumidores y publicadores.

Estas interfaces definen el contrato para el manejo de mensajes,
permitiendo diferentes implementaciones de brokers (RabbitMQ, Kafka, SQS, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IMessageConsumer(ABC):
    """
    Interfaz para consumidores de mensajes.
    
    Abstrae el broker de mensajes subyacente (RabbitMQ, Kafka, SQS, etc.),
    permitiendo a los servicios consumir mensajes sin acoplarse a infraestructura específica.
    
    Beneficios:
    - Fácil de testear (hacer mock de esta interfaz)
    - Fácil cambiar de broker (solo implementar nuevo adaptador)
    - Separación limpia entre infraestructura y lógica de negocio
    """
    
    @abstractmethod
    def start_consuming(self) -> None:
        """
        Inicia el consumo de mensajes desde la cola/tópico.
        
        Este método debe bloquear hasta que el consumidor se detenga.
        Típicamente se llama desde el hilo principal.
        """
        pass
    
    @abstractmethod
    def stop_consuming(self) -> None:
        """
        Detiene el consumo de mensajes de forma elegante.
        
        Debe limpiar conexiones y recursos.
        Debe ser seguro llamarlo múltiples veces.
        """
        pass
    
    @abstractmethod
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Procesa un mensaje recibido.
        
        Este es el manejador de lógica de negocio - cada servicio implementa
        su propia lógica aquí.
        
        Args:
            message: Datos del mensaje parseados (dict)
            
        Raises:
            Exception: Si el procesamiento falla, el mensaje será reencolado
        """
        pass
