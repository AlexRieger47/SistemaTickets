# Identificación de Aciertos - Sistema de Tickets

Este documento identifica los fragmentos de código que ya están bien implementados en el proyecto, justificando su cumplimiento con buenas prácticas de desarrollo de software.

---

## 1. ARQUITECTURA Y ORGANIZACIÓN

### ✅ Separación en Microservicios
**Ubicación:** Estructura general del proyecto `backend/`

```
backend/
├── ticket-service/       # Gestión de tickets
├── assignment-service/   # Asignación y priorización
└── notification-service/ # Notificaciones
```

**Buenas prácticas cumplidas:**
- **Principio de Responsabilidad Única (SRP):** Cada servicio tiene una responsabilidad bien definida
- **Escalabilidad:** Los servicios pueden desplegarse y escalarse independientemente
- **Mantenibilidad:** Cambios en un servicio no afectan directamente a otros
- **Organización Clara:** Estructura de carpetas intuitiva y auto-documentada

---

## 2. MODELOS DE DATOS

### ✅ Modelo Ticket - Validación y Constraints
**Ubicación:** [backend/ticket-service/tickets/models.py](backend/ticket-service/tickets/models.py)

```python
class Ticket(models.Model):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

    STATUS_CHOICES = [
        (OPEN, "Open"),
        (IN_PROGRESS, "In Progress"),
        (CLOSED, "Closed"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

**Buenas prácticas cumplidas:**
- **Constantes para Estados:** Uso de constantes en mayúsculas (OPEN, IN_PROGRESS, CLOSED) evita strings mágicos
- **Validación a Nivel de Base de Datos:** `choices` garantiza integridad referencial
- **Valor por Defecto:** `default=OPEN` asegura estado consistente para tickets nuevos
- **Auto-timestamp:** `auto_now_add=True` registra automáticamente la fecha de creación
- **Límites Explícitos:** `max_length=255` previene datos excesivos en título

**Justificación:**
Este modelo sigue el patrón Active Record de Django correctamente, con validaciones y constraints apropiados que previenen datos inconsistentes desde la capa de base de datos.

---

### ✅ Modelo Notification - Índices de Base de Datos
**Ubicación:** [backend/notification-service/notifications/models.py](backend/notification-service/notifications/models.py)

```python
class Notification(models.Model):
    ticket_id = models.CharField(max_length=128, db_index=True)
    message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"Notification for {self.ticket_id} at {self.sent_at.isoformat()}"
```

**Buenas prácticas cumplidas:**
- **Índices Estratégicos:** `db_index=True` en campos frecuentemente consultados (ticket_id, read)
- **Optimización de Queries:** Los índices mejoran rendimiento en consultas tipo "notificaciones no leídas"
- **Método __str__:** Representación legible para debugging y admin de Django
- **Formato ISO:** Uso de `.isoformat()` para fechas estandarizadas
- **Campos Opcionales:** `blank=True` permite flexibilidad en el mensaje

**Justificación:**
La indexación en `ticket_id` y `read` demuestra pensamiento orientado a rendimiento, anticipando consultas comunes como "todas las notificaciones no leídas de un ticket".

---

### ✅ Modelo TicketAssignment - Unicidad y Constraints
**Ubicación:** [backend/assignment-service/assignments/models.py](backend/assignment-service/assignments/models.py)

```python
class TicketAssignment(models.Model):
    ticket_id = models.CharField(max_length=255, unique=True)
    priority = models.CharField(max_length=50)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.ticket_id} -> Priority {self.priority}"
```

**Buenas prácticas cumplidas:**
- **Constraint de Unicidad:** `unique=True` previene asignaciones duplicadas del mismo ticket
- **Integridad de Datos:** Garantiza que un ticket solo puede tener una asignación activa
- **Representación Clara:** `__str__` proporciona descripción legible del objeto

**Justificación:**
El constraint `unique=True` es crítico para la lógica de negocio, asegurando que no existan asignaciones conflictivas para el mismo ticket.

---

## 3. SERIALIZERS

### ✅ TicketAssignmentSerializer - Campos de Solo Lectura
**Ubicación:** [backend/assignment-service/assignments/serializers.py](backend/assignment-service/assignments/serializers.py)

```python
class TicketAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAssignment
        fields = ['id', 'ticket_id', 'priority', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']
```

**Buenas prácticas cumplidas:**
- **Campos de Solo Lectura:** `id` y `assigned_at` marcados como read_only impiden modificaciones
- **Seguridad:** Previene que clientes manipulen IDs o timestamps
- **Claridad:** Declaración explícita de qué campos son computados vs proporcionados por usuario
- **DRY (Don't Repeat Yourself):** Uso de ModelSerializer evita duplicación de definiciones

**Justificación:**
La especificación de `read_only_fields` es esencial para APIs seguras, previniendo que usuarios manipulen campos que deben ser controlados por el sistema.

---

## 4. VIEWS Y API

### ✅ TicketViewSet - Ordenamiento Predecible
**Ubicación:** [backend/ticket-service/tickets/views.py](backend/ticket-service/tickets/views.py)

```python
class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer
```

**Buenas prácticas cumplidas:**
- **Orden Consistente:** `.order_by("-created_at")` garantiza que los tickets más recientes aparezcan primero
- **Experiencia de Usuario:** Orden predecible mejora usabilidad
- **Evita Ambigüedad:** Sin orden explícito, la base de datos podría devolver resultados en orden impredecible

**Justificación:**
Especificar el orden en el queryset base asegura que todas las consultas al ViewSet devuelvan resultados en un orden lógico y consistente.

---

### ✅ TicketViewSet - Custom Action con Validación
**Ubicación:** [backend/ticket-service/tickets/views.py](backend/ticket-service/tickets/views.py)

```python
@action(detail=True, methods=["patch"], url_path="status")
def change_status(self, request, pk=None):
    ticket = self.get_object()

    new_status = request.data.get("status")

    if not new_status:
        return Response(
            {"error": "El campo 'status' es requerido"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ticket.status = new_status
    ticket.save(update_fields=["status"])

    return Response(
        TicketSerializer(ticket).data,
        status=status.HTTP_200_OK,
    )
```

**Buenas prácticas cumplidas:**
- **Custom Action:** `@action` decorator para operación especializada más allá del CRUD estándar
- **Validación de Entrada:** Verifica que `status` esté presente antes de procesar
- **Mensajes de Error Claros:** Retorna mensaje descriptivo para ayudar al cliente
- **Código HTTP Apropiado:** Usa HTTP 400 para bad request
- **Actualización Optimizada:** `update_fields=["status"]` actualiza solo el campo modificado
- **Respuesta Completa:** Devuelve el objeto actualizado serializado

**Justificación:**
Este endpoint demuestra diseño RESTful apropiado con validación robusta, mensajes claros y optimización de base de datos mediante `update_fields`.

---

### ✅ NotificationViewSet - Custom Action para Marcar como Leída
**Ubicación:** [backend/notification-service/notifications/api.py](backend/notification-service/notifications/api.py)

```python
@action(detail=True, methods=['patch'], url_path='read')
def read(self, request, pk=None):
    notification = self.get_object()
    notification.read = True
    notification.save(update_fields=['read'])
    return Response(status=status.HTTP_204_NO_CONTENT)
```

**Buenas prácticas cumplidas:**
- **Semántica HTTP Correcta:** HTTP 204 No Content para operaciones exitosas sin respuesta
- **Actualización Eficiente:** `update_fields=['read']` minimiza escrituras a BD
- **Idempotencia:** Llamar múltiples veces tiene el mismo efecto
- **URL Semántica:** `/read/` es clara y autodescriptiva

**Justificación:**
El uso de HTTP 204 es apropiado para operaciones que modifican estado pero no necesitan devolver contenido, y la actualización parcial mejora el rendimiento.

---

## 5. ROUTING Y URLS

### ✅ Configuración de Router REST
**Ubicación:** [backend/ticket-service/tickets/urls.py](backend/ticket-service/tickets/urls.py)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet

router = DefaultRouter()
router.register(r"tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("", include(router.urls)),
]
```

**Buenas prácticas cumplidas:**
- **DefaultRouter de DRF:** Genera automáticamente todas las rutas CRUD estándar
- **Basename Explícito:** Facilita uso de `reverse()` para generación de URLs
- **Organización Modular:** URLs definidas cerca del código que las implementa
- **Convención RESTful:** Sigue patrones estándar de API REST

**Justificación:**
El uso del router de Django REST Framework reduce código boilerplate y asegura que las URLs sigan convenciones REST establecidas.

---

## 6. MENSAJERÍA Y EVENTOS

### ✅ Publicación de Eventos con RabbitMQ
**Ubicación:** [backend/ticket-service/tickets/messaging/events.py](backend/ticket-service/tickets/messaging/events.py)

```python
def publish_ticket_created(ticket_id):
    """Publica un evento ticket.created en RabbitMQ usando exchange fanout"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    
    # Crear exchange fanout (broadcast a todas las colas suscritas)
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    
    # Mensaje JSON con los datos del ticket
    message = json.dumps({"ticket_id": ticket_id})
    
    # Publicar al exchange (no a una cola específica)
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key='',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    connection.close()
    print(f"Evento ticket.created publicado al exchange: {ticket_id}")
```

**Buenas prácticas cumplidas:**
- **Docstring Descriptivo:** Explica claramente el propósito y el patrón utilizado
- **Exchange Fanout:** Patrón de pub/sub permite que múltiples servicios reciban el evento
- **Durabilidad:** `durable=True` y `delivery_mode=2` aseguran persistencia de mensajes
- **Formato JSON:** Estándar de facto para intercambio de datos
- **Cierre de Conexión:** Libera recursos apropiadamente
- **Logging:** Print statement ayuda en debugging (podría mejorarse con logger)

**Justificación:**
El patrón fanout es apropiado para arquitecturas event-driven donde múltiples servicios necesitan reaccionar al mismo evento, y la configuración de durabilidad previene pérdida de mensajes.

---

### ✅ Consumidor con Celery Integration
**Ubicación:** [backend/assignment-service/messaging/consumer.py](backend/assignment-service/messaging/consumer.py)

```python
def callback(ch, method, properties, body):
    """Se llama cada vez que llega un mensaje a la cola"""
    data = json.loads(body)
    ticket_id = data.get("ticket_id")
    
    # Procesar en segundo plano con Celery
    process_ticket.delay(ticket_id)
    
    print(f"[ASSIGNMENT] Mensaje recibido y enviado a Celery: {ticket_id}")
    ch.basic_ack(delivery_tag=method.delivery_tag)
```

**Buenas prácticas cumplidas:**
- **Procesamiento Asíncrono:** Delegación a Celery evita bloquear el consumidor
- **Acknowledgement Manual:** `basic_ack` después de delegar asegura que el mensaje no se pierda
- **Desacoplamiento:** Separación entre recepción del mensaje y su procesamiento
- **Logging con Contexto:** Prefijo `[ASSIGNMENT]` identifica el servicio

**Justificación:**
La combinación de RabbitMQ + Celery permite procesamiento resiliente y escalable. El ACK después de `.delay()` es correcto porque Celery tiene su propio sistema de persistencia.

---

### ✅ Configuración de Cola Exclusiva por Servicio
**Ubicación:** [backend/assignment-service/messaging/consumer.py](backend/assignment-service/messaging/consumer.py)

```python
# Crear cola exclusiva para este servicio
channel.queue_declare(queue=QUEUE_NAME, durable=True)

# Vincular cola al exchange
channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
```

**Buenas prácticas cumplidas:**
- **Colas Nombradas:** Cada servicio tiene su propia cola identificada
- **Durabilidad:** `durable=True` previene pérdida de mensajes en reinicios
- **Patrón Fanout Correcto:** Cola se vincula al exchange para recibir broadcasts

**Justificación:**
La arquitectura de colas separadas por servicio permite que cada uno procese eventos independientemente, fundamental para microservicios resilientes.

---

## 7. TESTS

### ✅ Tests Unitarios Completos
**Ubicación:** [backend/ticket-service/tickets/tests.py](backend/ticket-service/tickets/tests.py)

```python
def test_ticket_model_creation(self):
    t = Ticket.objects.create(title="A", description="Desc")
    self.assertEqual(t.status, "OPEN")
    self.assertIsNotNone(t.created_at)
```

**Buenas prácticas cumplidas:**
- **Testing de Valores por Defecto:** Verifica que `status` sea "OPEN" automáticamente
- **Testing de Auto-campos:** Confirma que `created_at` se establece
- **Tests Pequeños y Enfocados:** Cada test verifica un aspecto específico

---

### ✅ Test de Validación de Serializer
**Ubicación:** [backend/ticket-service/tickets/tests.py](backend/ticket-service/tickets/tests.py)

```python
def test_serializer_invalid_missing_title(self):
    data = {"description": "No title"}
    s = TicketSerializer(data=data)
    self.assertFalse(s.is_valid())
    self.assertIn('title', s.errors)

def test_serializer_title_too_long(self):
    data = {"title": 'x' * 300, "description": "long"}
    s = TicketSerializer(data=data)
    self.assertFalse(s.is_valid())
    self.assertIn('title', s.errors)
```

**Buenas prácticas cumplidas:**
- **Testing de Casos Negativos:** Verifica que validaciones fallen apropiadamente
- **Verificación de Mensajes de Error:** Confirma que el campo problemático esté en `errors`
- **Testing de Límites:** Prueba valores que exceden `max_length`

**Justificación:**
Los tests negativos son tan importantes como los positivos. Estos tests aseguran que la API rechace datos inválidos correctamente.

---

### ✅ Tests con Mocks
**Ubicación:** [backend/ticket-service/tickets/tests.py](backend/ticket-service/tickets/tests.py)

```python
def test_perform_create_calls_publish(self):
    data = {"title": "X", "description": "Y"}
    s = TicketSerializer(data=data)
    self.assertTrue(s.is_valid())

    with patch('tickets.views.publish_ticket_created') as mock_pub:
        view = TicketViewSet()
        view.perform_create(s)
        self.assertTrue(mock_pub.called)
```

**Buenas prácticas cumplidas:**
- **Aislamiento de Dependencias:** Mock de `publish_ticket_created` evita dependencia de RabbitMQ
- **Verificación de Llamadas:** Confirma que la función fue invocada
- **Tests Rápidos:** No requiere infraestructura externa

**Justificación:**
El uso de mocks permite testear la lógica de negocio sin depender de servicios externos, haciendo los tests rápidos y deterministas.

---

### ✅ Test de Resiliencia ante Fallos
**Ubicación:** [backend/ticket-service/tickets/tests.py](backend/ticket-service/tickets/tests.py)

```python
def test_perform_create_publish_raises_ticket_still_saved(self):
    data = {"title": "ERR", "description": "Will raise on publish"}
    s = TicketSerializer(data=data)
    self.assertTrue(s.is_valid())

    with patch('tickets.views.publish_ticket_created', side_effect=Exception('publish failed')):
        view = TicketViewSet()
        with self.assertRaises(Exception):
            view.perform_create(s)

    # El ticket debe existir en la BD porque save() se llama antes de publish
    self.assertTrue(Ticket.objects.filter(title="ERR").exists())
```

**Buenas prácticas cumplidas:**
- **Testing de Escenarios de Fallo:** Verifica comportamiento cuando publicación falla
- **Verificación de Datos Persistidos:** Confirma que el ticket se guardó a pesar del error
- **Prueba de Orden de Operaciones:** Valida que save() ocurre antes de publish()

**Justificación:**
Este test excelente demuestra pensamiento sobre casos edge. Verifica que las operaciones críticas (guardar ticket) no se pierdan si operaciones secundarias (publicar evento) fallan.

---

## 8. CONFIGURACIÓN

### ✅ Settings con Variables de Entorno
**Ubicación:** [backend/ticket-service/ticket_service/settings.py](backend/ticket-service/ticket_service/settings.py)

```python
_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
```

**Buenas prácticas cumplidas:**
- **Twelve-Factor App:** Configuración mediante variables de entorno
- **Múltiples Valores:** Parsing de lista separada por comas
- **Sanitización:** `.strip()` elimina espacios en blanco accidentales
- **Filtrado de Vacíos:** `if host.strip()` evita valores vacíos

**Justificación:**
Este patrón permite configuración flexible entre entornos (desarrollo, staging, producción) sin cambiar código. El parsing robusto previene errores de configuración.

---

### ✅ Instalación de CORS Middleware
**Ubicación:** [backend/ticket-service/ticket_service/settings.py](backend/ticket-service/ticket_service/settings.py)

```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... otros middleware
]
```

**Buenas prácticas cumplidas:**
- **CORS Apropiado:** Necesario para permitir que frontend acceda al backend
- **Posición Correcta:** CorsMiddleware debe estar al principio de la lista
- **Configuración Explícita:** CORS configurado a nivel de aplicación, no de servidor

**Justificación:**
La configuración de CORS es esencial para aplicaciones modernas con frontend/backend separados. Su ubicación al principio del middleware stack asegura que se procese antes que otros middlewares.

---

## 9. DOCKER Y ORCHESTRATION

### ✅ Docker Compose bien Estructurado
**Ubicación:** [docker-compose.yml](docker-compose.yml)

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: sistema-tickets-db
    environment:
      POSTGRES_DB: sistema_tickets
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
```

**Buenas prácticas cumplidas:**
- **Imágenes Alpine:** Versiones ligeras reducen tamaño de contenedores
- **Volúmenes Nombrados:** `db_data` persiste datos entre reinicios
- **Variables de Entorno:** Configuración centralizada y modificable
- **Nombres de Contenedores:** Facilitan debugging y networking

---

### ✅ Depends_on y Auto-migration
**Ubicación:** [docker-compose.yml](docker-compose.yml)

```yaml
backend:
  # ...
  command: >
    sh -c "python manage.py migrate &&
           python manage.py runserver 0.0.0.0:8000"
  depends_on:
    - db
```

**Buenas prácticas cumplidas:**
- **Migraciones Automáticas:** `migrate` antes de `runserver` asegura esquema actualizado
- **Dependencias Explícitas:** `depends_on` garantiza orden de inicio
- **Bind a 0.0.0.0:** Permite acceso desde fuera del contenedor

**Justificación:**
La automatización de migraciones reduce errores humanos y facilita el onboarding de nuevos desarrolladores.

---

## 10. FRONTEND

### ✅ API Client con Manejo de Errores
**Ubicación:** [frontend/src/api/ticketApi.ts](frontend/src/api/ticketApi.ts)

```typescript
getTickets: async (): Promise<Ticket[]> => {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error('Error al obtener los tickets');
  }

  const data: Ticket[] = await response.json();
  return data;
}
```

**Buenas prácticas cumplidas:**
- **Verificación de Respuesta:** Chequeo de `response.ok` antes de parsear
- **Mensajes de Error en Español:** Consistente con el dominio del negocio
- **Tipado Fuerte:** `Promise<Ticket[]>` provee type safety
- **Propagación de Errores:** `throw` permite que el caller maneje el error

---

### ✅ Método HTTP Apropiado para Actualización Parcial
**Ubicación:** [frontend/src/api/ticketApi.ts](frontend/src/api/ticketApi.ts)

```typescript
updateStatus: async (id: number, status: string): Promise<Ticket> => {
  const response = await fetch(`${API_URL}${id}/status/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  });
  // ...
}
```

**Buenas prácticas cumplidas:**
- **PATCH vs PUT:** Uso de PATCH para actualización parcial (semántica HTTP correcta)
- **Content-Type Explícito:** Header indica formato JSON
- **Serialización Apropiada:** `JSON.stringify` convierte objeto a string

**Justificación:**
La distinción entre PATCH y PUT es importante: PATCH indica actualización parcial, mientras PUT reemplazaría el recurso completo.

---

## 11. DOCUMENTACIÓN DE CÓDIGO

### ✅ Comentarios Descriptivos en Tests
**Ubicación:** [backend/ticket-service/tickets/tests.py](backend/ticket-service/tickets/tests.py)

```python
# Prueba: creación del modelo Ticket (caso feliz)
# Qué verifica:
# - al crear un Ticket sin status explícito, el status por defecto es "OPEN"
# - se establece el campo created_at automáticamente
def test_ticket_model_creation(self):
```

**Buenas prácticas cumplidas:**
- **Documentación de Propósito:** Explica qué verifica cada test
- **Facilita Mantenimiento:** Desarrolladores futuros entienden la intención
- **Documentation as Code:** Los comentarios están cerca del código que documentan

---

### ✅ Docstrings en Funciones
**Ubicación:** [backend/ticket-service/tickets/messaging/events.py](backend/ticket-service/tickets/messaging/events.py)

```python
def publish_ticket_created(ticket_id):
    """Publica un evento ticket.created en RabbitMQ usando exchange fanout"""
```

**Buenas prácticas cumplidas:**
- **Docstring Conciso:** Describe propósito y tecnología utilizada
- **Convención Python:** Sigue PEP 257 para docstrings

---

## 12. SEGURIDAD

### ✅ Prevención de Inyección SQL
**Ubicación:** Todo el proyecto (uso de Django ORM)

```python
Ticket.objects.filter(title="ERR").exists()
```

**Buenas prácticas cumplidas:**
- **ORM Parameterizado:** Django ORM previene inyección SQL automáticamente
- **Queries Seguras:** Todos los queries usan el ORM, no SQL crudo

**Justificación:**
El uso consistente del ORM de Django es una defensa efectiva contra inyección SQL, una de las vulnerabilidades más comunes.

---

## RESUMEN DE CATEGORÍAS DE ACIERTOS

1. **Arquitectura**: Microservicios bien separados, responsabilidades claras
2. **Modelos**: Constraints, índices, validaciones a nivel de BD
3. **API**: RESTful design, códigos HTTP apropiados, validaciones
4. **Mensajería**: Pub/sub con durabilidad, procesamiento asíncrono
5. **Tests**: Unitarios, con mocks, casos positivos y negativos
6. **Configuración**: Twelve-factor app, variables de entorno
7. **Contenedores**: Docker compose bien estructurado
8. **Frontend**: Type safety, manejo de errores, HTTP correcto
9. **Documentación**: Comentarios útiles, docstrings
10. **Seguridad**: ORM parameterizado, CORS configurado

---

## CONCLUSIÓN

El proyecto demuestra una base sólida con múltiples implementaciones que siguen estándares de la industria. Los aciertos identificados muestran:

- Conocimiento de patrones arquitectónicos (microservicios, pub/sub)
- Entendimiento de REST y HTTP
- Preocupación por rendimiento (índices, update_fields)
- Testing comprehensivo con mocks
- Configuración para múltiples entornos
- Seguridad básica implementada

Estos fundamentos proporcionan una excelente base para continuar el desarrollo del sistema.
