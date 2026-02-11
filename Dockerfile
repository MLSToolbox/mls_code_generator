FROM python:3.10-alpine

# Build arguments
ARG ENVIRONMENT=local

WORKDIR /app

COPY ./src/requirements.txt /app
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir --timeout=120 --retries=5 -r requirements.txt

COPY ./src /app

# Environment variables
ENV EXECUTION_MODE="prod"
ENV ENVIRONMENT=${ENVIRONMENT}

ENTRYPOINT ["python3"]
CMD ["server.py"]
