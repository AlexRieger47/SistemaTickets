# Tests de Infraestructura Compartida

Ejecutar tests con pytest:

```bash
cd backend/shared
pytest messaging/tests/ -v
```

## Cobertura de Tests

- `test_base_consumer.py` - Tests para el patrón Template Method de BaseRabbitMQConsumer
