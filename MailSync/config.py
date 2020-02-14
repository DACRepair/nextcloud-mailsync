import os
from .mail import MailConfig

MAIL_CONF = MailConfig()
MAIL_CONF.imap_host = os.getenv('IMAP_HOST', MAIL_CONF.imap_host)
MAIL_CONF.imap_port = int(os.getenv('IMAP_PORT', MAIL_CONF.imap_port))
MAIL_CONF.imap_ssl = str(os.getenv('IMAP_SSL', 'true' if MAIL_CONF.imap_ssl else 'false')).lower() == 'true'
MAIL_CONF.imap_tls = str(os.getenv('IMAP_TLS', 'true' if MAIL_CONF.imap_tls else 'false')).lower() == 'true'
MAIL_CONF.imap_user = os.getenv('IMAP_USER', MAIL_CONF.imap_user)
MAIL_CONF.imap_pass = os.getenv('IMAP_PASS', MAIL_CONF.imap_pass)
MAIL_CONF.imap_folder = os.getenv('IMAP_FOLDER', MAIL_CONF.imap_folder)
MAIL_CONF.imap_ro = str(os.getenv('IMAP_RO', 'true' if MAIL_CONF.imap_ro else 'false')).lower() == 'true'
MAIL_CONF.smtp_host = os.getenv('SMTP_HOST', MAIL_CONF.smtp_host)
MAIL_CONF.smtp_port = int(os.getenv('SMTP_PORT', MAIL_CONF.smtp_port))
MAIL_CONF.smtp_tls = str(os.getenv('SMTP_TLS', 'true' if MAIL_CONF.smtp_tls else 'false')).lower() == 'true'
MAIL_CONF.smtp_auth = str(os.getenv('SMTP_AUTH', 'true' if MAIL_CONF.smtp_auth else 'false')).lower() == 'true'
MAIL_CONF.smtp_user = os.getenv('SMTP_USER', MAIL_CONF.smtp_user)
MAIL_CONF.smtp_pass = os.getenv('SMTP_PASS', MAIL_CONF.smtp_pass)
MAIL_CONF.temp_path = os.getenv('TEMP_PATH', MAIL_CONF.temp_path)
MAIL_CONF.temp_clean = str(os.getenv('TEMP_CLEAN', 'true' if MAIL_CONF.temp_clean else 'false')).lower() == 'true'

WEBDAV_URL = os.getenv('WEBDAV_URL', '')
WEBDAV_VERIFY = 0 if os.getenv('WEBDAV_VERIFY', 'false').lower() == 'true' else 1
WEBDAV_USER = os.getenv('WEBDAV_USER', '')
WEBDAV_PASS = os.getenv('WEBDAV_PASS', '')
WEBDAV_PATH = os.getenv('WEBDAV_PATH', '.')
