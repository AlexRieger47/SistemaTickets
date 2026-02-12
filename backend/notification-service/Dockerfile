FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy shared library first
COPY shared/ /app/shared/

# Copy notification service files
COPY notification-service/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY notification-service/ /app/

COPY notification-service/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["sh", "/app/entrypoint.sh"]
