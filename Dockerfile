FROM alpine:latest

RUN apk --no-cache add curl libxslt openssl python3 ca-certificates

WORKDIR /opt
COPY server.py .
COPY requirements.txt .
COPY MailSync/ ./MailSync/
COPY templates/ ./templates/
RUN ls -lah

RUN apk --no-cache add --virtual .deps curl-dev python3-dev libressl-dev gcc libc-dev libxml2-dev libxslt-dev \
    && pip3 install --upgrade pip \
    && pip3 install -r requirements.txt \
    && apk del .deps

CMD ["python3", "./server.py"]