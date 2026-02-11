# Sistema de Tickets – Arquitectura de Microservicios

## 📖 Descripción general

Este proyecto implementa un **Sistema de Gestión de Tickets** basado en una **arquitectura de microservicios**, utilizando **Django** para el backend, **React + Vite** para el frontend, **PostgreSQL** como base de datos, **RabbitMQ** como broker de mensajería y **Docker / Docker Compose** para la contenerización.

El sistema sigue un enfoque **event‑driven**, donde los microservicios se comunican de manera **asíncrona** mediante eventos publicados y consumidos a través de RabbitMQ. Esto permite bajo acoplamiento, escalabilidad y una arquitectura cercana a escenarios reales de producción.

---

## 🧩 Arquitectura del sistema

El sistema está compuesto por **tres microservicios backend independientes** y un frontend desacoplado.

### 1️⃣ Ticket Service

* Expone una **API REST**
* Permite **crear y listar tickets**
* Persiste la información del ticket
* Publica el evento **`ticket.created`** cuando se registra un nuevo ticket
* Actúa como **producer** de eventos

### 2️⃣ Assignment Service

* No expone API REST
* Consume el evento **`ticket.created`**
* Asigna un **nivel de prioridad** al ticket
* Procesa los eventos de forma asíncrona
* Mantiene su propia lógica y persistencia

### 3️⃣ Notification Service

* Expone una **API REST** para consultar notificaciones
* Consume el evento **`ticket.created`**
* Registra notificaciones cuando se crea un ticket
* Procesa eventos de forma independiente

### 🎨 Frontend

* Implementado con **React + Vite**
* Consume únicamente la API del **Ticket Service**
* No tiene conocimiento de RabbitMQ ni de los otros microservicios
* Totalmente desacoplado del backend asíncrono

---

## 🔄 Comunicación asíncrona

### RabbitMQ

RabbitMQ actúa como **broker de mensajería**, permitiendo:

* Desacoplar los microservicios
* Distribuir eventos a múltiples consumidores
* Aumentar la tolerancia a fallos

El **Ticket Service** publica el evento `ticket.created` en una **exchange**, la cual enruta el mensaje hacia:

* Cola del **Assignment Service**
* Cola del **Notification Service**

Cada servicio consume el evento de forma independiente.

### Celery

Se utiliza **Celery** para implementar los **consumers** de eventos, permitiendo:

* Procesamiento asíncrono
* Manejo de tareas en segundo plano
* Mejor escalabilidad y control del flujo

---

![alt text](Img/Diagram1.png)

## 🛠️ Tecnologías utilizadas

### Backend

* Python
* Django
* Django REST Framework
* Celery

### Frontend

* React
* Vite

### Infraestructura

* PostgreSQL
* RabbitMQ
* Docker
* Docker Compose

---

## 📁 Estructura del proyecto

```text
SistemaTickets/
├── backend/
│   ├── ticket-service/
│   ├── assignment-service/
│   └── notification-service/
│
├── frontend/
│   └── tickets-frontend/
│
└── docker-compose.yml
```

Cada microservicio es:

* Un proyecto **Django independiente**
* Con su **propia base de datos**
* Con su propio entorno y dependencias

---

## ⚙️ Requisitos previos

* Docker / **Podman** (alternativa compatible)
* Docker Compose / **podman-compose**
* Git

> ⚠️ No es necesario instalar Python ni Node.js localmente si el proyecto se ejecuta completamente con contenedores.
>
> 💡 **Nota sobre Podman:** Si tu empresa no permite Docker, puedes usar **Podman** como alternativa. Simplemente reemplaza `docker-compose` por `podman-compose` en todos los comandos.

---

## 🚀 Instalación y ejecución

### 1️⃣ Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd SistemaTickets
```

### 2️⃣ Construir y levantar los contenedores

**Con Docker:**

```bash
docker-compose build
docker-compose up -d
```

**Con Podman:**

```bash
podman-compose build
podman-compose up -d
```

Esto levantará:

* Ticket Service
* Assignment Service
* Notification Service
* RabbitMQ
* PostgreSQL
* Frontend React

### 3️⃣ Verificar que los servicios estén corriendo

```bash
# Con Docker
docker-compose ps

# Con Podman
podman-compose ps
```

Todos los servicios deben mostrar estado `Up`.

### 4️⃣ Crear superusuarios (Opcional)

Para acceder al panel de administración de Django de cada servicio:

**Ticket Service:**
```bash
podman exec -it sistema-tickets-backend python manage.py createsuperuser
```

**Notification Service:**
```bash
podman exec -it notification-service python manage.py createsuperuser
```

**Assignment Service:**
```bash
podman exec -it assessment-service-backend python manage.py createsuperuser
```

> 💡 **Superusuarios creados automáticamente:**
> - Usuario: `admin`
> - Contraseña: `admin123`
> - Estos se crean durante el primer `podman-compose up` si no existen

---

## 🌐 Accesos

### Frontend
* **Tickets Frontend:** [http://localhost:5173](http://localhost:5173)
* **Notifications Frontend:** [http://localhost:5174](http://localhost:5174)

### APIs Backend
* **Ticket Service API:** [http://localhost:8000/api/tickets/](http://localhost:8000/api/tickets/)
* **Ticket Service Admin:** [http://localhost:8000/admin/](http://localhost:8000/admin/)
* **Notification Service API:** [http://localhost:8001/api/notifications/](http://localhost:8001/api/notifications/)
* **Notification Service Admin:** [http://localhost:8001/admin/](http://localhost:8001/admin/)
* **Assignment Service:** [http://localhost:8002](http://localhost:8002) *(No expone API REST pública)*

### Infraestructura
* **RabbitMQ Management:** [http://localhost:15672](http://localhost:15672)
  * Usuario: `guest`
  * Contraseña: `guest`

### Credenciales Admin Django
* Usuario: `admin`
* Contraseña: `admin123`

---

## 🔄 Actualización del software

Cuando existan cambios en el código:

```bash
git pull
podman-compose down
podman-compose build
podman-compose up -d
```

Si solo hay cambios de código (sin nuevas dependencias):

```bash
podman-compose restart
```

## 🔍 Comandos útiles

### Ver logs de un servicio
```bash
podman logs -f sistema-tickets-backend
podman logs -f notification-service
podman logs -f assessment-service-backend
```

### Ejecutar comandos dentro de un contenedor
```bash
podman exec -it sistema-tickets-backend python manage.py shell
```

### Detener todos los servicios
```bash
podman-compose down
```

### Reconstruir un servicio específico
```bash
podman-compose build backend
podman-compose up -d backend
```

---

## ▶️ Uso del sistema

### Flujo principal

1. El usuario crea un ticket desde el frontend
2. El frontend envía un `POST` al **Ticket Service**
3. El Ticket Service guarda el ticket y publica el evento `ticket.created`
4. RabbitMQ distribuye el evento
5. Assignment Service y Notification Service consumen el evento
6. Cada servicio procesa el evento de forma independiente

---

## 🧪 Consideraciones de calidad

* Cada microservicio:

  * Tiene su **propia base de datos**
  * No accede a la base de datos de otros servicios
  * Mantiene independencia funcional

* El frontend:

  * Solo se comunica con el Ticket Service
  * No depende de la mensajería asíncrona

* QA valida:

  * Flujo de eventos
  * Desacoplamiento
  * Pruebas unitarias e integración

---

## 👥 Roles del equipo

* **Backend Developer 1:** Ticket Service
* **Backend Developer 2:** Assignment Service & Notification Service
* **QA Engineer:** Pruebas, validación del flujo asíncrono y documentación

---

## ✅ Conclusión

Este proyecto demuestra:

* Implementación correcta de microservicios
* Comunicación asíncrona real basada en eventos
* Separación clara de responsabilidades
* Integración frontend-backend desacoplada
* Buenas prácticas de contenerización con Docker
