FROM python:3.10-alpine

ARG ENVIRONMENT=local

WORKDIR /app

COPY ./src/requirements.txt /app
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir --timeout=120 --retries=5 -r requirements.txt

# Copiar src como fallback para builds standalone (sin docker compose).
# Cuando se usa docker compose, el bind mount ./src:/app lo sobreescribe.
COPY ./src /app

ENV EXECUTION_MODE="prod"
ENV ENVIRONMENT=${ENVIRONMENT}

ENTRYPOINT ["python3"]
CMD ["server.py"]
