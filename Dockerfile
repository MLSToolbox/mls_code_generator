FROM python:3.10-alpine

WORKDIR /app

COPY ./src/requirements.txt /app
RUN pip3 install -r requirements.txt

COPY ./src /app

ENTRYPOINT ["python3"]
CMD ["server.py"]