import datetime
import email
import glob
import os
import re
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from imapclient import IMAPClient
from smtplib import SMTP
from bs4 import BeautifulSoup


class MailConfig:
    imap_host: str = ''
    imap_port: int = 993
    imap_ssl: bool = False
    imap_tls: bool = False

    imap_user: str = ''
    imap_pass: str = ''

    imap_folder: str = 'INBOX'
    imap_ro: bool = True

    smtp_host: str = ''
    smtp_port: int = 25
    smtp_tls: bool = False

    smtp_auth: bool = True
    smtp_user: str = ''
    smtp_pass: str = ''

    temp_path: str = os.path.normpath(tempfile.mkdtemp())
    temp_clean: bool = True

    def __init__(self, **kwargs):
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs.get(key))

    def __str__(self):
        return str("Mail Config Object")

    def __repr__(self):
        return self.__str__()


class MailMessage:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') if 'id' in kwargs.keys() else None
        self.subject = kwargs.get('subject') if 'subject' in kwargs.keys() else None
        self.body_plain = kwargs.get('body_plain') if 'body_plain' in kwargs.keys() else None
        self.body_html = kwargs.get('body_html') if 'body_html' in kwargs.keys() else None
        self.date = kwargs.get('date') if 'date' in kwargs.keys() else None
        self.from_addr = kwargs.get('from') if 'from' in kwargs.keys() else None
        self.attachments = kwargs.get('attachments') if 'attachments' in kwargs.keys() else []

    def __str__(self):
        return str("<Message: {} From: {} On: {} Attachemnts: {}>".format(self.subject, self.from_addr,
                                                                          self.date.strftime('%Y%m%d-%H%M%S'),
                                                                          str(len(self.attachments))))

    def __repr__(self):
        return self.__str__()


class Mail:
    def __init__(self, config: MailConfig):
        self.config = config

        # IMAP
        if len(config.imap_host) > 0:
            self._imap = IMAPClient(config.imap_host, config.imap_port, use_uid=True, ssl=config.imap_ssl)
            if config.imap_tls:
                self._imap.starttls()
            if len(config.imap_user) > 0:
                self._imap.login(config.imap_user, config.imap_pass)
            self._imap.select_folder(config.imap_folder, readonly=config.imap_ro)

        # SMTP
        smtp_host = config.smtp_host if len(config.smtp_host) > 0 else config.imap_host
        self._smtp = SMTP(smtp_host, config.smtp_port)
        if config.smtp_tls:
            self._smtp.starttls()
        self.config.smtp_user = config.smtp_user if len(config.smtp_user) > 0 else config.imap_user
        if len(self.config.smtp_user) > 0 and config.smtp_auth:
            smtp_password = config.smtp_pass if len(config.smtp_pass) else config.imap_pass
            self._smtp.login(self.config.smtp_user, smtp_password)

    def __del__(self):
        if self.config.temp_clean:
            for file in glob.glob(os.path.normpath(self.config.temp_path + "/*")):
                os.remove(file)
            os.rmdir(self.config.temp_path)

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

    def get_mail(self, search: str = 'UNSEEN') -> [MailMessage]:
        messages = []
        for msg_id, data in self._imap.fetch(self._imap.search(search), ['RFC822']).items():
            data = email.message_from_bytes(data[b'RFC822'])

            msg_id = data.get('Message-ID')
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
                    file_path = os.path.normpath(self.config.temp_path + "/" + file_name)
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
        message['From'] = self.config.smtp_user
        message['To'] = to_addr
        message.attach(MIMEText(self._htmltostring(msg), "plain"))
        message.attach(MIMEText(msg, "html"))
        try:
            self._smtp.sendmail(self.config.smtp_user, to_addr, message.as_string())
            return True
        except:
            return False
