# Shared Infrastructure Library

This package contains reusable infrastructure components shared across microservices.

## Purpose

Eliminates code duplication by centralizing common infrastructure patterns:
- Message broker abstractions (RabbitMQ, Kafka, etc.)
- Event publishers/consumers
- Common utilities

## Structure

```
shared/
├── __init__.py
└── messaging/
    ├── __init__.py
    ├── interfaces.py        # IMessageConsumer, IMessagePublisher
    ├── base_consumer.py     # BaseRabbitMQConsumer (Template Method)
    └── base_publisher.py    # BaseRabbitMQPublisher (future)
```

## Usage

### Using the RabbitMQ Consumer

```python
from shared.messaging.base_consumer import BaseRabbitMQConsumer

class MyServiceConsumer(BaseRabbitMQConsumer):
    def get_exchange_name(self) -> str:
        return 'my_exchange'
    
    def get_queue_name(self) -> str:
        return 'my_queue'
    
    def get_routing_key(self) -> str:
        return ''  # fanout
    
    def handle_message(self, message: dict) -> None:
        # Your business logic here
        process_event(message)

# Run
consumer = MyServiceConsumer()
consumer.start_consuming()
```

## Benefits

- **60+ lines of RabbitMQ setup → 25 lines per service**
- **Change exchange/QoS: 1 file instead of N services**
- **New consumer: 4 methods instead of copying 60 lines**
- **Easy to test: mock handle_message() only**
- **Easy to switch brokers: new adapter in shared/**

## Installation

Add to your service's Python path:

```python
import sys
sys.path.insert(0, '/path/to/backend')
from shared.messaging import BaseRabbitMQConsumer
```

Or use as a pip package (future):

```bash
pip install -e ../shared
```
