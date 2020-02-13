FROM alpine:latest
ENV EMAIL_HOST mail # The hostname of the mail server
ENV EMAIL_PORT 993 # The port of the mail server (IMAP)
ENV EMAIL_SSL false # Use SSL
ENV EMAIL_TLS false # Use TLS
ENV EMAIL_USER "" # Username to log into the mail server, if left blank it will disable auth
ENV EMAIL_PASS "" # Password to log into the mail server
ENV EMAIL_FOLDER INBOX # Folder to look for mails
ENV EMAIL_READONLY false # Read only means it will read mails without changing state (IE marking as read when iterating)

ENV WEBDAV_URL http://webdav/ # Base URL to WebDAV
ENV WEBDAV_VERIFY false # Verify SSL (may be needed for LE depending on CAs available to container)
ENV WEBDAV_USER webdavuser # WebDAV User
ENV WEBDAV_PASS webdavpass # WebDAV Password
ENV WEBDAV_PATH . # Path to upload to (can be relative)

ENV APP_TEMP temp/ # Path where the app downloads the attachments to
ENV APP_CLEAN true # Clean temp path on each pass
ENV APP_REFRESH  300 # How often to check the mail box and upload files
ENV APP_QUIET false # turn off printing to STDOUT

#######################################################################

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
