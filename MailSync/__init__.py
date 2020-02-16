import os
import time

from .config import Config
from .logging import Logging
from .mail import Mail
from .webdav import WebDAV


class App:
    def __init__(self):
        # Config Setup
        self.config = Config()
        config_file = os.path.normpath(os.getcwd() + "/config.ini")
        if os.path.isfile(os.path.normpath(os.getcwd() + "/config.ini")):
            self.config.read(config_file)

        self.log = Logging(__name__, self.config.get('app', 'loglevel', fallback='NOTSET'))

        # Mail setup
        self.mail = Mail(**self.config.gen_conf_dict('mail', Mail))

        # WebDAV Setup
        self.webdav = WebDAV(**self.config.gen_conf_dict('webdav', WebDAV))
        self.dav_basepath = str(self.config.get('webdav', 'base_path', fallback='/')).rstrip("/") + "/"
        self.webdav.mkdir(self.dav_basepath) if self.webdav.check(self.dav_basepath) else None

        self.log.info("Application Initialized.")

    def sync(self):
        messages = self.mail.get_mail()
        for message in messages:
            attachments = []
            if not len(message.attachments) > 0 or message.from_addr.lower() == self.mail.email_addr.lower():
                if message.from_addr.lower() == self.mail.email_addr.lower():
                    continue
                self.log.warn('Found Email: "{}" From: "{}" with no attachments.'.format(message.subject,
                                                                                         message.from_addr))
                self.mail.send_mail(message.from_addr, "Document Manager: Failure",
                                    self.mail.render('templates/error.html', err_msg="There was/were no attachment(s)",
                                                     message=message))
                continue

            self.log.info('Found Email: "{}" From: "{}" with attachments.'.format(message.subject, message.from_addr))
            attachments.extend(self.mail.get_attachment(message.id, message.attachments))
            for file_name, local_path in attachments:
                remote_path = self.dav_basepath + message.date.strftime('%Y%m%d-%H%M%S') + "-" + file_name
                self.webdav.upload(remote_path, local_path)
            self.mail.send_mail(message.from_addr, "Document Manager: Success",
                                self.mail.render('templates/reply.html', message=message))
        return len(messages)

    def run(self):
        while True:
            self.log.info("Checking mail...")
            processed = self.sync()
            self.log.info("Processed {} messages.".format(processed))
            if not self.config.getboolean('app', 'daemon', fallback=False):
                break
            else:
                time.sleep(self.config.getint('app', 'refresh', fallback=300))
