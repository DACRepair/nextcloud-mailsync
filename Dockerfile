FROM alpine:latest
ENV EMAIL_HOST mail
ENV EMAIL_PORT 993
ENV EMAIL_SSL false
ENV EMAIL_USER mailuser
ENV EMAIL_PASS mailpassword
ENV EMAIL_FOLDER INBOX
ENV EMAIL_READONLY false

ENV WEBDAV_URL http://webdav/
ENV WEBDAV_VERIFY false
ENV WEBDAV_USER webdavuser
ENV WEBDAV_PASS webdavpass
ENV WEBDAV_PATH .

ENV APP_TEMP temp/
ENV APP_REFRESH  300
ENV APP_QUIET false

RUN apk --no-cache add python3 curl libxslt

WORKDIR /opt
COPY server.py .
COPY requirements.txt .
RUN apk --no-cache add --virtual .deps curl-dev python3-dev libressl-dev gcc libc-dev libxml2-dev libxslt-dev \
    && pip3 install --upgrade pip \
    && pip3 install -r requirements.txt \
    && apk del .deps

ENTRYPOINT python3
CMD ./server.py