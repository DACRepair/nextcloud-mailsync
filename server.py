import datetime
import email
import os
import time
from glob import glob

from imapclient import IMAPClient
from webdav import client as wdcli

#################################################################
#################################################################
# Email Config
EMAIL_HOST = os.getenv('EMAIL_HOST', 'mail')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '993'))

EMAIL_SSL = os.getenv('EMAIL_SSL', 'false').lower() == 'true'
EMAIL_TLS = os.getenv('EMAIL_TLS', 'false').lower() == 'true'

EMAIL_USER = os.getenv('EMAIL_USER', 'mailuser')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'maillpassword')

EMAIL_FOLDER = os.getenv('EMAIL_FOLDER', 'INBOX')
EMAIL_READONLY = os.getenv('EMAIL_READONLY').lower() == 'true'

# WebDAV Config
WEBDAV_URL = os.getenv('WEBDAV_URL', 'http://webdav/')
WEBDAV_VERIFY = 0 if os.getenv('WEBDAV_VERIFY', 'false').lower() == 'true' else 1

WEBDAV_USER = os.getenv('WEBDAV_USER', 'webdavuser')
WEBDAV_PASS = os.getenv('WEBDAV_PASS', 'webdavpass')

WEBDAV_PATH = os.getenv('WEBDAV_PATH', '.')

# App Config
APP_TEMP = os.getenv('APP_TEMP', 'temp/')
APP_REFRESH = int(os.getenv('APP_REFRESH', '300'))
APP_QUIET = not os.getenv('APP_QUIET', 'false').lower() == 'true'

#################################################################
#################################################################
# Set up temp
temp_dir = os.path.normpath(APP_TEMP)
os.mkdir(temp_dir) if not os.path.isdir(temp_dir) else None

# Setup Clients
# Email
mail = IMAPClient(EMAIL_HOST, EMAIL_PORT, use_uid=True, ssl=EMAIL_SSL)
if EMAIL_TLS:
    mail.starttls()
mail.login(EMAIL_USER, EMAIL_PASS)
mail.select_folder(EMAIL_FOLDER, readonly=EMAIL_READONLY)

# WebDAV
webdav = wdcli.Client({'webdav_hostname': WEBDAV_URL, 'webdav_login': WEBDAV_USER, 'webdav_password': WEBDAV_PASS})
webdav.default_options['SSL_VERIFYHOST'] = WEBDAV_VERIFY
webdav.default_options['SSL_VERIFYPEER'] = WEBDAV_VERIFY
webdav.mkdir(WEBDAV_PATH) if not webdav.check(WEBDAV_PATH) else None


#################################################################
#################################################################
def do_sync():
    if APP_QUIET:
        print("Syncing Email Attachments")
    messages = mail.search('UNSEEN')
    for msg_id, data in mail.fetch(messages, ['RFC822']).items():
        data = email.message_from_bytes(data[b'RFC822'])

        date = datetime.datetime.strptime(str(data.get('Date')).split(' -')[0], "%a, %d %b %Y %H:%M:%S")
        date = date.strftime('%Y%m%d-%H%M%S')
        subject = data.get('Subject')
        from_addr = data.get('From')
        for part in data.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            file_name = part.get_filename()
            if bool(file_name):
                file_path = os.path.normpath(temp_dir + '/' + date + "-" + file_name)
                with open(file_path, 'wb') as fp:
                    fp.write(part.get_payload(decode=True))
                    fp.close()
                dav_path = WEBDAV_PATH.rstrip('/') + '/' + date + "-" + file_name
                webdav.upload(dav_path, file_path)
                if APP_QUIET:
                    print('Uploaded: "{}". Message: "{}" From: {}'.format(dav_path, subject, from_addr))

    for file in glob(temp_dir.rstrip('/') + '/*'):
        os.remove(os.path.normpath(file))


while True:
    do_sync()
    time.sleep(APP_REFRESH)
