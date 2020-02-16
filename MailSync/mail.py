import datetime
import email
import glob
import os
import re
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP, SMTP_SSL

from bs4 import BeautifulSoup
from imapclient import IMAPClient
from jinja2 import Template


class MailMessage:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') if 'id' in kwargs.keys() else None
        self.subject = kwargs.get('subject') if 'subject' in kwargs.keys() else None
        self.body_plain = kwargs.get('body_plain') if 'body_plain' in kwargs.keys() else None
        self.body_html = kwargs.get('body_html') if 'body_html' in kwargs.keys() else None
        self.date = kwargs.get('date') if 'date' in kwargs.keys() else None
        self.from_addr = kwargs.get('from_addr') if 'from_addr' in kwargs.keys() else None
        self.attachments = kwargs.get('attachments') if 'attachments' in kwargs.keys() else []

    def __str__(self):
        return str("<Message: {} From: {} On: {} Attachemnts: {}>".format(self.subject, self.from_addr,
                                                                          self.date.strftime('%Y%m%d-%H%M%S'),
                                                                          str(len(self.attachments))))

    def __repr__(self):
        return self.__str__()


class Mail:
    def __init__(self, email_host: str, email_user: str, email_pass: str, email_addr: str = None, imap_port: int = 0,
                 imap_ssl: bool = False, imap_tls: bool = False, imap_folder: str = 'INBOX', imap_ro: bool = True,
                 smtp_host: str = None, smtp_user: str = None, smtp_pass: str = None, smtp_port: int = 0,
                 smtp_ssl: bool = False, smtp_tls: bool = False):

        # A really messy cast block to help with defaults in autoconfig
        email_host = str(email_host) if email_host is not None else email_host
        email_user = str(email_user) if email_user is not None else email_user
        email_pass = str(email_pass) if email_pass is not None else email_pass
        email_addr = str(email_addr) if email_addr is not None else email_addr
        imap_port = int(imap_port) if imap_port is not None else imap_port
        imap_ssl = bool(imap_ssl) if imap_ssl is not None else imap_ssl
        imap_tls = bool(imap_tls) if imap_tls is not None else imap_tls
        imap_folder = str(imap_folder) if imap_folder is not None else imap_folder
        imap_ro = bool(imap_ro) if imap_ro is not None else imap_ro
        smtp_host = str(smtp_host) if smtp_host is not None else smtp_host
        smtp_user = str(smtp_user) if smtp_user is not None else smtp_user
        smtp_pass = str(smtp_pass) if smtp_pass is not None else smtp_pass
        smtp_port = int(smtp_port) if smtp_port is not None else smtp_port
        smtp_ssl = bool(smtp_ssl) if smtp_ssl is not None else smtp_ssl
        smtp_tls = bool(smtp_tls) if smtp_tls is not None else smtp_tls

        # Prep defaults
        self.temp_path: str = os.path.normpath(tempfile.mkdtemp())
        self.temp_clean: bool = True

        if imap_port == 0:
            imap_port = 993 if imap_ssl else 143
        if smtp_port == 0:
            smtp_port = 465 if smtp_ssl else 25

        smtp_host = email_host if smtp_host is None else smtp_host

        if smtp_user is None:
            smtp_user = email_user
            smtp_pass = email_pass

        self.email_addr = email_addr if email_addr is not None else smtp_user

        # IMAP
        self._imap = IMAPClient(email_host, imap_port, use_uid=True, ssl=imap_ssl)
        if imap_tls:
            self._imap.starttls()
        if len(email_user) > 0:
            self._imap.login(email_user, email_pass)
        self._imap.select_folder(imap_folder, readonly=imap_ro)

        # SMTP
        if smtp_ssl:
            self._smtp = SMTP_SSL(smtp_host)
            self._smtp.connect(smtp_host, smtp_port)
        else:
            self._smtp = SMTP(smtp_host)
            self._smtp.connect(smtp_host, smtp_port)
            if smtp_tls:
                self._smtp.starttls()
        if len(smtp_user) > 0:
            self._smtp.login(smtp_user, smtp_pass)

    def __del__(self):
        if self.temp_clean:
            for file in glob.glob(os.path.normpath(self.temp_path + "/*")):
                os.remove(file)
            os.rmdir(self.temp_path)

    @staticmethod
    def _htmltostring(html: str) -> str:
        html = BeautifulSoup(html, 'lxml')
        html = str(html.prettify())
        regex = re.compile('<.*?>')
        string = re.sub(regex, '', html)
        while string.endswith(' ') or string.endswith('\n') or string.startswith(' ') or string.startswith(
                '\n') or '  ' in string:
            if string.startswith(' '):
                string = string.lstrip(' ')
            elif string.startswith('\n'):
                string = string.lstrip('\n')
            elif string.endswith(' '):
                string = string.rstrip(' ')
            elif string.endswith('\n'):
                string = string.rstrip('\n')
            else:
                if '  ' in string:
                    string = string.replace('  ', ' ')
                else:
                    break
        return string.replace('\n \n', '\n').replace('\n ', '\n')

    @staticmethod
    def render(template, **kwargs):
        with open(template, 'r') as fp:
            template = fp.read()
        return Template(template).render(**kwargs)

    def get_mail(self, search: str = 'UNSEEN') -> [MailMessage]:
        messages = []
        for msg_id, data in self._imap.fetch(self._imap.search(search), ['RFC822']).items():
            data = email.message_from_bytes(data[b'RFC822'])

            msg_id = data.get('Message-ID')
            date = data.get('Date')
            if date is not None:
                date = str(data.get('Date')).split(' -')[0].split(' +')[0]
                date = datetime.datetime.strptime(date, "%a, %d %b %Y %H:%M:%S")
            subject = data.get('Subject')
            from_addr = str(data.get('From').split('<')[-1]).rstrip(">")

            attrs = []
            body_plain = None
            body_html = None
            for part in data.walk():
                if part.get_content_type() == 'text/plain':
                    body_plain = part.get_payload(decode=True)
                if part.get_content_type() == 'text/html':
                    body_html = part.get_payload(decode=True)
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                file_name = part.get_filename()
                if bool(file_name):
                    attrs.append(file_name)
            messages.append(MailMessage(id=msg_id, subject=subject, date=date, from_addr=from_addr, attachments=attrs,
                                        body_plain=body_plain, body_html=body_html))
        return messages

    def get_attachment(self, msg_id: str, attachment: [list, str]) -> [tuple]:
        if not isinstance(attachment, list):
            attachment = [attachment]
        files = []
        search = self._imap.search('(HEADER Message-ID "{}")'.format(msg_id))
        for msg_id, data in self._imap.fetch(search, ['RFC822']).items():
            data = email.message_from_bytes(data[b'RFC822'])
            for part in data.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                file_name = part.get_filename()
                if bool(file_name) and file_name in attachment:
                    file_path = os.path.normpath(self.temp_path + "/" + file_name)
                    with open(file_path, 'wb') as fp:
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                    files.append((file_name, file_path))
        return files

    def send_mail(self, to_addr: [str, list], subject: str = '', msg: str = '') -> bool:
        if isinstance(to_addr, list):
            to_addr = ", ".join(to_addr)
        message = MIMEMultipart("alternative")
        message['Subject'] = subject
        message['From'] = self.email_addr
        message['To'] = to_addr
        message.attach(MIMEText(self._htmltostring(msg), "plain"))
        message.attach(MIMEText(msg, "html"))
        try:
            self._smtp.sendmail(self.email_addr, to_addr, message.as_string())
            return True
        except:
            return False
